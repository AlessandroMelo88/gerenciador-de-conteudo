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
# A pasta `assets/` é a fonte de verdade da identidade visual por canal. O disk
# `branding` preserva os caminhos enviados pelo painel e as marcas d'água.
ASSETS_ROOT = Path(os.environ.get('ASSETS_DIR', '/app/assets')).resolve()
CHANNELS_ROOT = (ASSETS_ROOT / 'channels').resolve()
MEDIA_ROOT = Path(os.environ.get('BRANDING_DIR', '/app/branding')).resolve()

DEFAULT_STILL_DURATION_SECONDS = 3
DEFAULT_MUSIC_VOLUME = 0.24
MUSIC_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac'}
VISUAL_ASSET_NAMES = {
    'intro': ('intro.mp4', 'intro.jpg', 'intro.jpeg', 'intro.png', 'intro.webp'),
    'outro': (
        'encerramento.mp4',
        'encerramento.jpg',
        'encerramento.jpeg',
        'encerramento.png',
        'encerramento.webp',
    ),
}


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
    if destination_channel_id is None:
        return None

    normalized = [
        dict(candidate)
        for candidate in candidates
        if candidate.get('destination_channel_id') == destination_channel_id
    ]
    if not normalized:
        return None
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


def _channel_directory(channel_slug: object) -> Path | None:
    """Retorna a pasta de um canal sem permitir escapar de ``channels``."""
    if not channel_slug:
        return None

    slug = str(channel_slug).strip()
    if not slug or Path(slug).name != slug or slug in {'.', '..'}:
        return None

    try:
        channel_dir = (CHANNELS_ROOT / slug).resolve()
        if not channel_dir.is_relative_to(CHANNELS_ROOT):
            return None
    except (OSError, ValueError):
        return None

    return channel_dir


def _resolve_channel_asset(channel_slug: object, kind: str) -> Path | None:
    channel_dir = _channel_directory(channel_slug)
    if channel_dir is None:
        return None

    for filename in VISUAL_ASSET_NAMES.get(kind, ()):
        candidate = channel_dir / filename
        if candidate.is_file():
            return candidate
    return None


def _resolve_audio_asset(clip_id: int, channel_slug: object = None) -> Path | None:
    channel_dir = _channel_directory(channel_slug)
    if channel_dir is None:
        return None

    channel_audio = channel_dir / 'audio'
    if not channel_audio.is_dir():
        return None
    candidates = sorted(
        path
        for path in channel_audio.iterdir()
        if path.is_file() and path.suffix.lower() in MUSIC_EXTENSIONS
    )
    if not candidates:
        return None
    return candidates[abs(int(clip_id)) % len(candidates)]


def resolve_filesystem_media_assets(
    *, channel_slug: str | None, video_format: str, clip_id: int
) -> dict[str, dict[str, object]]:
    """Resolve a identidade canônica dos vídeos longos.

    Dentro de cada canal, o vídeo é preferido à imagem para intro e
    encerramento. A imagem é o fallback para canais que ainda não têm a versão
    em vídeo. As faixas de ``audio`` são alternadas de forma determinística pelo
    id do clip, para que a seleção seja reproduzível.
    """
    if video_format != 'longo':
        return {}

    resolved: dict[str, dict[str, object]] = {}
    for kind in ('intro', 'outro'):
        path = _resolve_channel_asset(channel_slug, kind)
        if path is None:
            continue
        resolved[kind] = {
            'kind': kind,
            'name': path.name,
            'path': str(path.relative_to(ASSETS_ROOT)),
            'absolute_path': str(path),
            'duration_seconds': DEFAULT_STILL_DURATION_SECONDS,
            'source': 'filesystem',
        }

    music_path = _resolve_audio_asset(clip_id, channel_slug)
    if music_path is not None:
        resolved['music'] = {
            'kind': 'music',
            'name': music_path.name,
            'path': str(music_path.relative_to(ASSETS_ROOT)),
            'absolute_path': str(music_path),
            'music_volume': DEFAULT_MUSIC_VOLUME,
            'source': 'filesystem',
        }

    return resolved


def resolve_media_assets(
    conn,
    *,
    destination_channel_id: int | None,
    video_format: str,
    clip_id: int,
    channel_slug: str | None = None,
) -> dict[str, dict[str, object]]:
    """Busca e valida a identidade de um vídeo longo.

    Todos os assets precisam estar associados a um canal de destino. Arquivos
    e registros globais antigos ficam preservados, mas não são selecionados.
    Shorts não carregam intro, encerramento ou música.
    """
    if video_format != 'longo':
        return {}

    resolved = resolve_filesystem_media_assets(
        channel_slug=channel_slug,
        video_format=video_format,
        clip_id=clip_id,
    )

    if destination_channel_id is None:
        return resolved

    for kind in MEDIA_KINDS:
        if kind in resolved:
            continue
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT id, kind, name, path, destination_channel_id, format, '
                    'duration_seconds, music_volume, priority '
                    'FROM media_assets '
                    'WHERE kind = %s AND active = TRUE '
                    'AND (format IS NULL OR format = %s) '
                    'AND destination_channel_id = %s '
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
