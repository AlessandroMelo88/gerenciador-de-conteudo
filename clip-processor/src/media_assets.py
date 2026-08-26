"""Resolve assets de pós-produção configurados pelo painel.

O banco guarda somente o caminho relativo ao volume compartilhado de branding.
A escolha é determinística: primeiro respeita o escopo mais específico (canal e
formato), depois a prioridade configurada e, por fim, alterna entre assets
equivalentes usando o id do clip.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path

MEDIA_KINDS = ('intro', 'outro', 'music')
MEDIA_ROOT = Path(os.environ.get('BRANDING_DIR', '/app/branding')).resolve()


def _log(message: str) -> None:
    print(f'[MEDIA] {message}', flush=True)


def _as_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    if not isinstance(value, (int, float, str)):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _asset_specificity(
    asset: Mapping[str, object], destination_channel_id: int | None, video_format: str
) -> int:
    channel_match = (
        destination_channel_id is not None
        and asset.get('destination_channel_id') == destination_channel_id
    )
    format_match = asset.get('format') == video_format

    if channel_match and format_match:
        return 0
    if channel_match:
        return 1
    if format_match:
        return 2
    return 3


def choose_media_asset(
    candidates: Sequence[Mapping[str, object]],
    *,
    destination_channel_id: int | None,
    video_format: str,
    clip_id: int,
) -> dict[str, object] | None:
    """Escolhe um asset entre candidatos já filtrados por tipo e status.

    A ordem da regra é escopo > prioridade > rotação. A rotação evita que uma
    biblioteca com várias intros ativas use sempre o mesmo arquivo sem exigir
    aleatoriedade, o que facilita reproduzir um clip em testes.
    """
    if not candidates:
        return None

    normalized = [dict(candidate) for candidate in candidates]
    best_specificity = min(
        _asset_specificity(candidate, destination_channel_id, video_format)
        for candidate in normalized
    )
    scoped = [
        candidate
        for candidate in normalized
        if _asset_specificity(candidate, destination_channel_id, video_format) == best_specificity
    ]
    highest_priority = max(_as_int(candidate.get('priority')) for candidate in scoped)
    prioritized = [
        candidate for candidate in scoped if _as_int(candidate.get('priority')) == highest_priority
    ]
    prioritized.sort(key=lambda candidate: _as_int(candidate.get('id')))
    return prioritized[abs(int(clip_id)) % len(prioritized)]


def _resolve_asset_path(raw_path: object) -> Path | None:
    if not raw_path:
        return None

    candidate = Path(str(raw_path))
    if not candidate.is_absolute():
        candidate = MEDIA_ROOT / candidate

    try:
        resolved = candidate.resolve()
        if not resolved.is_relative_to(MEDIA_ROOT):
            return None
    except (OSError, ValueError):
        return None

    return resolved


def resolve_media_assets(
    conn,
    *,
    destination_channel_id: int | None,
    video_format: str,
    clip_id: int,
) -> dict[str, dict[str, object]]:
    """Busca e valida intro, encerramento e música para um clip.

    Falha de leitura da tabela ou arquivo ausente não interrompe a produção:
    nesse caso o clip segue sem o asset problemático e o motivo fica no log.
    """
    resolved: dict[str, dict[str, object]] = {}

    for kind in MEDIA_KINDS:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT id, kind, name, path, destination_channel_id, format, '
                    'duration_seconds, music_volume, priority '
                    'FROM media_assets '
                    'WHERE kind = %s AND active = TRUE '
                    'AND (format IS NULL OR format = %s) '
                    'AND (destination_channel_id IS NULL OR destination_channel_id = %s) '
                    'ORDER BY priority DESC, id ASC',
                    (kind, video_format, destination_channel_id),
                )
                candidates = cur.fetchall() or []
        except Exception as exc:
            # Uma exceção SQL aborta a transação PostgreSQL. Como a biblioteca
            # de assets é opcional, desfazemos apenas essa leitura para que o
            # caller ainda consiga atualizar o clip e seguir sem branding.
            try:
                conn.rollback()
            except Exception:
                pass
            _log(f'Não foi possível ler assets do tipo {kind}: {exc}')
            continue

        selected = choose_media_asset(
            candidates,
            destination_channel_id=destination_channel_id,
            video_format=video_format,
            clip_id=clip_id,
        )
        if selected is None:
            continue

        absolute_path = _resolve_asset_path(selected.get('path'))
        if absolute_path is None or not absolute_path.is_file():
            _log(
                f'Asset {selected.get("name", selected.get("id"))} não encontrado no volume compartilhado'
            )
            continue

        selected['absolute_path'] = str(absolute_path)
        resolved[kind] = selected

    return resolved
