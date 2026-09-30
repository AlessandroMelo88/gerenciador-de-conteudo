"""Perfis de prompt: perfil ausente, válido e quebrado nunca derrubam o pipeline."""
import json
from unittest.mock import MagicMock

from src.prompt_profiles import (
    apply_profile_layer,
    load_profile_for_source_video,
    profile_from_row,
    profile_matches_niche,
    profile_prompt,
)


def test_profile_from_row_normalises_prefixed_database_columns():
    profile = profile_from_row(
        {
            'prompt_profile_id': 7,
            'prompt_profile_slug': 'tecnologia',
            'prompt_profile_name': 'Tecnologia',
            'prompt_profile_niche': 'tech',
            'prompt_profile_niche_aliases': '["ia", "linux"]',
            'prompt_profile_selection_short_prompt': 'Selecione insights técnicos.',
        }
    )

    assert profile == {
        'id': 7,
        'slug': 'tecnologia',
        'name': 'Tecnologia',
        'niche': 'tech',
        'niche_aliases': ['ia', 'linux'],
        'selection_short_prompt': 'Selecione insights técnicos.',
        'selection_long_prompt': None,
        'metadata_short_prompt': None,
        'metadata_long_prompt': None,
        'thumbnail_prompt': None,
    }


def test_profile_helpers_accept_direct_profile_dicts():
    profile = {
        'slug': 'tecnologia',
        'niche': 'tech',
        'niche_aliases': ['ia', 'linux'],
        'thumbnail_prompt': 'Destaque descoberta técnica.',
    }

    assert profile_matches_niche(profile, 'ia') is True
    assert profile_matches_niche(profile, 'futebol') is False
    assert profile_prompt(profile, 'thumbnail_prompt') == 'Destaque descoberta técnica.'
    assert profile_prompt(profile, 'selection_short_prompt') is None


def test_profile_from_row_com_aliases_json_quebrado_nao_levanta():
    profile = profile_from_row({'prompt_profile_slug': 'x', 'prompt_profile_niche_aliases': '{nao-json'})
    assert profile['niche_aliases'] == []


def _conn_returning(row=None, error=None):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    if error:
        cur.execute.side_effect = error
    cur.fetchone.return_value = row
    return conn


def test_apply_profile_layer_sem_perfil_devolve_prompt_base():
    assert apply_profile_layer('BASE', None, 'selection_short_prompt') == 'BASE'
    assert apply_profile_layer('BASE', {'selection_short_prompt': '  '}, 'selection_short_prompt') == 'BASE'
    assert apply_profile_layer('BASE', {'slug': 'x'}, 'campo_inexistente') == 'BASE'


def test_apply_profile_layer_com_perfil_mantem_base_e_acrescenta():
    out = apply_profile_layer('BASE', {'selection_short_prompt': 'REGRA'}, 'selection_short_prompt')
    assert out.startswith('BASE')
    assert out.endswith('REGRA')


def test_load_profile_sem_linha_retorna_none():
    assert load_profile_for_source_video(_conn_returning(row=None), 5) is None


def test_load_profile_valido():
    conn = _conn_returning(row={'prompt_profile_slug': 'mbl', 'prompt_profile_selection_short_prompt': 'X'})
    profile = load_profile_for_source_video(conn, 5)
    assert profile['slug'] == 'mbl'
    assert profile['selection_short_prompt'] == 'X'


def test_load_profile_tabela_ausente_nao_levanta_e_faz_rollback():
    conn = _conn_returning(error=RuntimeError('relation "prompt_profiles" does not exist'))
    assert load_profile_for_source_video(conn, 5) is None
    conn.rollback.assert_called_once()


def test_load_profile_sem_conn_ou_id():
    assert load_profile_for_source_video(None, 5) is None
    assert load_profile_for_source_video(MagicMock(), None) is None


def test_select_moments_usa_camada_do_perfil_e_sem_perfil_igual_ao_padrao():
    from src.selector import SYSTEM_PROMPT, select_moments

    transcript = {'video_id': 'v', 'text': 't', 'segments': [{'start': 0, 'end': 40, 'text': 'fala'}]}
    resp = MagicMock()
    resp.content = [MagicMock(text=json.dumps({'moments': []}))]

    def system_of(profile):
        client = MagicMock()
        client.messages.create.return_value = resp
        select_moments(transcript, anthropic_client=client, prompt_profile=profile)
        return client.messages.create.call_args.kwargs['system']

    assert system_of(None) == SYSTEM_PROMPT
    layered = system_of({'selection_short_prompt': 'REGRA-DO-CANAL'})
    assert layered.startswith(SYSTEM_PROMPT) and 'REGRA-DO-CANAL' in layered


def test_metadata_prompt_usa_perfil_por_formato():
    from src.metadata_generator import SYSTEM_PROMPT, _resolve_system_prompt

    assert _resolve_system_prompt({'niche': 'futebol'}) == SYSTEM_PROMPT
    profile = {'metadata_short_prompt': 'CURTO', 'metadata_long_prompt': 'LONGO'}
    assert _resolve_system_prompt({'niche': 'futebol', 'prompt_profile': profile}).endswith('CURTO')
    longo = _resolve_system_prompt({'niche': 'futebol', 'format': 'longo', 'prompt_profile': profile})
    assert longo.endswith('LONGO')
