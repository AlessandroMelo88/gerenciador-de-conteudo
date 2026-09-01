from src.prompt_profiles import profile_from_row, profile_matches_niche, profile_prompt


def test_profile_from_row_normalises_prefixed_database_columns():
    profile = profile_from_row(
        {
            'prompt_profile_id': 7,
            'prompt_profile_slug': 'conteudo-inteligencia',
            'prompt_profile_name': 'Conteúdo de Inteligência',
            'prompt_profile_niche': 'hacker-libertario',
            'prompt_profile_niche_aliases': '["tecnologia", "ia"]',
            'prompt_profile_selection_short_prompt': 'Selecione insights técnicos.',
        }
    )

    assert profile == {
        'id': 7,
        'slug': 'conteudo-inteligencia',
        'name': 'Conteúdo de Inteligência',
        'niche': 'hacker-libertario',
        'niche_aliases': ['tecnologia', 'ia'],
        'selection_short_prompt': 'Selecione insights técnicos.',
        'selection_long_prompt': None,
        'metadata_short_prompt': None,
        'metadata_long_prompt': None,
        'thumbnail_prompt': None,
    }


def test_profile_helpers_accept_direct_profile_dicts():
    profile = {
        'slug': 'conteudo-inteligencia',
        'niche': 'hacker-libertario',
        'niche_aliases': ['tecnologia', 'ia'],
        'thumbnail_prompt': 'Destaque descoberta técnica.',
    }

    assert profile_matches_niche(profile, 'tecnologia') is True
    assert profile_matches_niche(profile, 'futebol') is False
    assert profile_prompt(profile, 'thumbnail_prompt') == 'Destaque descoberta técnica.'
    assert profile_prompt(profile, 'selection_short_prompt') is None
