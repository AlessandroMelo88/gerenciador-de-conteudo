"""Helpers para transportar perfis de prompt do PostgreSQL até os providers de IA.

O banco devolve as colunas com o prefixo ``prompt_profile_`` para evitar colisões
com os campos do canal, vídeo e clip. O restante do pipeline trabalha com um
dict de perfil pequeno e estável, sem conhecer a forma da query.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

PROFILE_FIELDS = (
    'selection_short_prompt',
    'selection_long_prompt',
    'metadata_short_prompt',
    'metadata_long_prompt',
    'thumbnail_prompt',
)

PROMPT_PROFILE_SQL_COLUMNS = (
    'pp.id AS prompt_profile_id, '
    'pp.slug AS prompt_profile_slug, '
    'pp.name AS prompt_profile_name, '
    'pp.niche AS prompt_profile_niche, '
    'pp.niche_aliases AS prompt_profile_niche_aliases, '
    'pp.selection_short_prompt AS prompt_profile_selection_short_prompt, '
    'pp.selection_long_prompt AS prompt_profile_selection_long_prompt, '
    'pp.metadata_short_prompt AS prompt_profile_metadata_short_prompt, '
    'pp.metadata_long_prompt AS prompt_profile_metadata_long_prompt, '
    'pp.thumbnail_prompt AS prompt_profile_thumbnail_prompt'
)


def _first_value(row: Mapping[str, object], field: str) -> object:
    value = row.get(f'prompt_profile_{field}')
    if value is None:
        value = row.get(field)
    return value


def _normalise_aliases(value: object) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = []
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def profile_from_row(row: Mapping[str, object] | None) -> dict[str, object] | None:
    """Converte uma linha SQL em perfil ou ``None`` quando não há perfil ativo."""
    if not row:
        return None

    slug = _first_value(row, 'slug')
    if not isinstance(slug, str) or not slug.strip():
        return None

    profile: dict[str, object] = {
        'id': _first_value(row, 'id'),
        'slug': slug.strip(),
        'name': _first_value(row, 'name') or slug.strip(),
        'niche': _first_value(row, 'niche'),
        'niche_aliases': _normalise_aliases(_first_value(row, 'niche_aliases')),
    }
    for field in PROFILE_FIELDS:
        profile[field] = _first_value(row, field)
    return profile


def profile_prompt(profile: Mapping[str, object] | None, field: str) -> str | None:
    """Retorna uma instrução textual não vazia do perfil."""
    if not profile or field not in PROFILE_FIELDS:
        return None
    value = profile.get(field)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def profile_matches_niche(profile: Mapping[str, object] | None, niche: object) -> bool:
    """Confirma que o perfil pode ser usado pelo nicho configurado."""
    if not profile or not isinstance(niche, str) or not niche.strip():
        return True

    configured_niche = niche.strip().casefold()
    candidates = [profile.get('slug'), profile.get('niche')]
    aliases = profile.get('niche_aliases', [])
    if isinstance(aliases, list):
        candidates.extend(aliases)
    return any(
        isinstance(candidate, str) and candidate.strip().casefold() == configured_niche
        for candidate in candidates
    )


def apply_profile_layer(
    base_prompt: str,
    profile: Mapping[str, object] | None,
    field: str,
) -> str:
    """Acrescenta a camada do perfil ao prompt-base do pipeline.

    A camada vem DEPOIS do prompt-base, que continua sendo a fonte do contrato
    de saída (JSON, duração, schema). Sem perfil, ou com campo vazio, devolve o
    prompt-base intacto: é o comportamento anterior à existência de perfis.
    """
    instruction = profile_prompt(profile, field)
    if not instruction:
        return base_prompt
    return f'{base_prompt}\n\nInstruções adicionais do perfil do canal:\n{instruction}'


_PROFILE_LOOKUP_SQL = (
    'SELECT ' + PROMPT_PROFILE_SQL_COLUMNS + ' '
    'FROM source_videos sv '
    'JOIN source_channels sc ON sc.id = sv.channel_id '
    'JOIN prompt_profiles pp ON pp.id = sc.prompt_profile_id AND pp.active = TRUE '
    'WHERE sv.id = %s'
)


def load_profile_for_source_video(conn, source_video_id: object) -> dict[str, object] | None:
    """Busca o perfil ativo do canal-fonte de um vídeo; ``None`` se não houver.

    Nunca levanta: tabela/coluna ausente (migration não rodada), perfil inativo,
    linha sem perfil ou erro de conexão viram ``None`` e o pipeline segue com os
    prompts padrão. O perfil é opcional em toda a cadeia.
    """
    if conn is None or source_video_id is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(_PROFILE_LOOKUP_SQL, (source_video_id,))
            row = cur.fetchone()
        return profile_from_row(row) if isinstance(row, Mapping) else None
    except Exception as exc:  # noqa: BLE001 - perfil é opcional, nunca derruba o pipeline
        print(f'[PROFILE] Sem perfil de prompt para source_video {source_video_id}: {exc}', flush=True)
        try:
            conn.rollback()  # PostgreSQL deixa a transação abortada após erro de query
        except Exception:  # noqa: BLE001
            pass
        return None
