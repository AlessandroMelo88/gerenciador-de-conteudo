"""
test_metadata_generator.py — Testes Phase 4 VID-04.

Cobertura de geração estrita de metadata e da chamada dedicada da thumbnail.
"""

import json
from unittest.mock import MagicMock

import pytest

from src.metadata_generator import (
    _build_prompt,
    _build_thumbnail_prompt,
    _get_thumbnail_system_prompt,
    _normalize_metadata,
    append_credits,
    generate_metadata,
    generate_thumbnail_text,
    update_clip_metadata,
)

SAMPLE_CONTEXT = {
    'source_title': 'Debate quente depois do clássico',
    'reason': 'Discussão intensa sobre arbitragem',
    'score': 9,
    'start_time': 120.0,
    'end_time': 420.0,
    'transcript_excerpt': 'Foi pênalti ou não foi? O debate esquentou no estúdio.',
}


class TestMetadataGenerator:
    def test_database_profile_replaces_legacy_metadata_identity(self):
        prompt = _build_prompt(
            {
                **SAMPLE_CONTEXT,
                'niche': 'futebol',
                'prompt_profile': {
                    'metadata_short_prompt': 'PERFIL DE METADATA DE INTELIGÊNCIA',
                },
            }
        )

        assert 'PERFIL DE METADATA DE INTELIGÊNCIA' in prompt
        assert 'Hacker Libertário' not in prompt

    def test_thumbnail_profile_is_sent_to_both_prompt_layers(self):
        context = {
            **SAMPLE_CONTEXT,
            'prompt_profile': {'thumbnail_prompt': 'Destaque uma descoberta técnica literal.'},
        }

        assert 'Destaque uma descoberta técnica literal.' in _build_thumbnail_prompt(context)
        assert 'Destaque uma descoberta técnica literal.' in _get_thumbnail_system_prompt(context)

    def test_prompt_requires_new_seo_title_and_explanatory_description(self):
        prompt = _build_prompt(
            {
                **SAMPLE_CONTEXT,
                'source_title': 'FABIO AKITA - Flow #588',
            }
        )

        assert 'nunca copie, repita ou use esse título como título final' in prompt
        assert 'descrição deve ser completa e boa para SEO' in prompt
        assert 'FABIO AKITA - Flow #588' in prompt

    def test_hacker_prompt_uses_channel_positioning_and_actionable_seo(self):
        prompt = _build_prompt({**SAMPLE_CONTEXT, 'niche': 'hacker-libertario'})

        assert 'Hacker Libertário' in prompt
        assert 'palavra-chave principal' in prompt
        assert 'no máximo 3 hashtags relevantes' in prompt
        assert 'Linux' in prompt

    def test_original_source_title_is_rejected_without_fallback(self):
        with pytest.raises(ValueError, match='repetiu o título original'):
            _normalize_metadata(
                {
                    'title': 'FABIO AKITA - Flow #588',
                    'description': 'Descrição contextualizada.',
                    'tags': ['tecnologia'],
                },
                {
                    'source_title': 'FABIO AKITA - Flow #588',
                    'reason': 'A importância de entender como a tecnologia muda o trabalho.',
                    'transcript_excerpt': 'A tecnologia muda o trabalho quando deixa de ser tratada como mágica.',
                },
            )

    @pytest.mark.parametrize(
        'title',
        [
            'Claude Code grátis pra sempre | Vídeo longo',
            'Claude Code grátis pra sempre | VIDEO LONGO',
            'Long video: como usar várias contas free tier',
            'O debate decisivo do clássico | Corte',
            'Neymar surpreende em 30s',
            'A análise definitiva para Shorts',
        ],
    )
    def test_generic_long_video_label_is_rejected(self, title):
        with pytest.raises(ValueError, match='rótulo genérico de formato'):
            _normalize_metadata(
                {
                    'title': title,
                    'description': 'Descrição contextualizada.',
                    'tags': ['tecnologia'],
                },
                {**SAMPLE_CONTEXT, 'format': 'longo'},
            )

    def test_prompt_forbids_format_labels_and_wasted_title_words(self):
        prompt = _build_prompt({**SAMPLE_CONTEXT, 'format': 'longo'})

        assert 'Vídeo longo' in prompt
        assert 'desperdiça palavras' in prompt
        assert 'vender o assunto' in prompt

    def test_specific_long_title_is_allowed(self):
        metadata = _normalize_metadata(
            {
                'title': 'Claude Code sem pagar? O esquema de várias contas free tier',
                'description': 'Descrição contextualizada.',
                'tags': ['tecnologia'],
            },
            {**SAMPLE_CONTEXT, 'format': 'longo'},
        )

        assert metadata['title'] == 'Claude Code sem pagar? O esquema de várias contas free tier'

    def test_missing_metadata_fails_without_fallback(self):
        with pytest.raises(ValueError, match='não retornou um título'):
            _normalize_metadata({'title': '', 'description': '', 'tags': []}, SAMPLE_CONTEXT)

    def test_tags_are_normalized_without_hashtags_or_duplicates(self):
        metadata = _normalize_metadata(
            {
                'title': 'A polêmica do clássico que dividiu o estúdio',
                'description': 'O debate explica o lance e as opiniões do estúdio.',
                'tags': ['#Linux', 'linux', 'Open Source', '#open source'],
            },
            SAMPLE_CONTEXT,
        )

        assert metadata['tags'] == ['Linux', 'Open Source']

    def test_generate_metadata_returns_only_seo_metadata(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'title': 'Polêmica no clássico: foi pênalti?',
                        'description': 'Debate completo sobre o lance mais polêmico.',
                        'tags': ['futebol', 'classico', 'arbitragem'],
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        metadata = generate_metadata(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        assert set(metadata.keys()) == {'title', 'description', 'tags'}
        assert isinstance(metadata['tags'], list)

    def test_thumbnail_prompt_is_dedicated_and_requests_best_literal_phrase(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'thumbnail_text': 'Foi pênalti ou não foi?',
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        thumbnail_text = generate_thumbnail_text(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        assert thumbnail_text == 'Foi pênalti ou não foi?'
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        prompt = kwargs['messages'][0]['content']
        assert prompt == _build_thumbnail_prompt(SAMPLE_CONTEXT)
        assert 'potencial de clique' in prompt
        assert 'sequência contínua e literal' in prompt
        assert 'title, description, tags' not in prompt
        assert kwargs['output_config']['format']['schema']['required'] == ['thumbnail_text']
        assert 'Sua única tarefa' in kwargs['system']

    def test_non_literal_thumbnail_text_uses_literal_transcript_fallback(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'thumbnail_text': 'O árbitro roubou o jogo',
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        thumbnail_text = generate_thumbnail_text(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        assert thumbnail_text == 'Foi pênalti ou não foi? O debate esquentou'
        assert thumbnail_text in SAMPLE_CONTEXT['transcript_excerpt']

    def test_thumbnail_provider_failure_is_not_replaced_by_another_provider(
        self, mocker, monkeypatch
    ):
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'configured')
        mock_claude = mocker.patch(
            'src.metadata_generator._generate_thumbnail_via_anthropic',
            side_effect=RuntimeError('Claude indisponível'),
        )
        mock_groq = mocker.patch('src.metadata_generator._generate_thumbnail_via_groq')

        with pytest.raises(RuntimeError, match='Claude indisponível'):
            generate_thumbnail_text(SAMPLE_CONTEXT)

        mock_claude.assert_called_once_with(SAMPLE_CONTEXT, None)
        mock_groq.assert_not_called()

    def test_title_over_100_chars_is_trimmed_to_youtube_limit(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'title': 'A' * 150,
                        'description': 'Descricao',
                        'tags': ['futebol'],
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        metadata = generate_metadata(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        assert len(metadata['title']) <= 100

    def test_thumbnail_text_over_limits_is_trimmed_without_leaving_transcript(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'thumbnail_text': (
                            'Foi pênalti ou não foi? O debate esquentou no estúdio agora'
                        ),
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        thumbnail_text = generate_thumbnail_text(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        assert thumbnail_text == 'Foi pênalti ou não foi? O debate esquentou no estúdio'
        assert len(thumbnail_text) <= 64
        assert len(thumbnail_text.split()) <= 10

    def test_long_video_metadata_does_not_use_shorts_tags(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'title': 'DeepSeek Harness e arquitetura de plugins',
                        'description': 'Análise técnica completa sobre o Harness.',
                        'tags': ['ia', 'cortes', 'shorts', 'opensource'],
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        metadata = generate_metadata(
            {**SAMPLE_CONTEXT, 'format': 'longo', 'niche': 'hacker-libertario'},
            anthropic_client=mock_anthropic,
        )

        assert metadata['tags'] == ['ia', 'opensource']

    def test_generate_metadata_uses_structured_output(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'title': 'Titulo',
                        'description': 'Descricao',
                        'tags': ['futebol'],
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        generate_metadata(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert kwargs['model'] == 'claude-haiku-4-5'
        assert 'output_config' in kwargs

    def test_fact_check_instruction_is_sent_in_system_and_user_prompts(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'title': 'Titulo',
                        'description': 'Descricao',
                        'tags': ['futebol'],
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        generate_metadata(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert 'pesquise na internet' in kwargs['system']
        assert 'Verificação de fake news' in kwargs['system']
        assert 'pesquise na internet' in kwargs['messages'][0]['content']

    def test_positive_selection_fact_check_is_carried_to_description(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'title': 'Titulo',
                        'description': 'Descricao factual',
                        'tags': ['futebol'],
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        metadata = generate_metadata(
            {**SAMPLE_CONTEXT, 'reason': 'Análise | Fake news: positivo'},
            anthropic_client=mock_anthropic,
        )

        assert metadata['description'].endswith('Fact Check: E os fatos reais.')
        assert metadata['description'] == 'Descricao factual\n\nFact Check: E os fatos reais.'

    def test_negative_selection_fact_check_is_not_added_to_description(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        'title': 'Titulo',
                        'description': 'Descricao factual',
                        'tags': ['futebol'],
                    }
                )
            )
        ]
        mock_anthropic.messages.create.return_value = response

        metadata = generate_metadata(
            {**SAMPLE_CONTEXT, 'reason': 'Análise | Fake news: negativo'},
            anthropic_client=mock_anthropic,
        )

        assert metadata['description'] == 'Descricao factual'
        assert 'Fake news' not in metadata['description']

    def test_generated_fact_check_label_is_removed_without_positive_verdict(self):
        metadata = _normalize_metadata(
            {
                'title': 'Titulo',
                'description': 'Descricao factual\nFake news: negativo\nContinuação da descrição',
                'tags': ['futebol'],
            },
            SAMPLE_CONTEXT,
        )

        assert metadata['description'] == 'Descricao factual\nContinuação da descrição'


class TestMetadataPersistence:
    def test_update_clip_metadata_persists_fields(self, mock_db_conn):
        metadata = {
            'title': 'Titulo',
            'description': 'Descricao',
            'tags': ['futebol', 'cortes'],
        }

        update_clip_metadata(mock_db_conn, 10, metadata)

        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args.args
        assert 'UPDATE generated_clips' in sql
        assert params == ('Titulo', 'Descricao', 'futebol,cortes', 10)
        mock_db_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Wave 2 — RED tests: append_credits (COPY-02)
# Estes testes falham até a implementação em Wave 3-4.
# ---------------------------------------------------------------------------


class TestAppendCredits:
    """Testes RED para append_credits (COPY-02)."""

    def test_append_credits_formats_template_with_channel_handle(self):
        """COPY-02: template com {channel_handle} é substituído pelo handle real."""
        from src.metadata_generator import append_credits

        result = append_credits(
            'Descrição do clip',
            'Créditos: @{channel_handle}',
            'sportv',
        )
        assert result == 'Descrição do clip\n\nCréditos: @sportv'

    def test_append_credits_empty_template_returns_description_unchanged(self):
        """COPY-02: template vazio → retorna descrição sem modificação."""
        from src.metadata_generator import append_credits

        result = append_credits('Descrição', '', 'sportv')
        assert result == 'Descrição'

    def test_append_credits_empty_handle_returns_description_unchanged(self):
        """COPY-02: handle vazio → retorna descrição sem modificação."""
        from src.metadata_generator import append_credits

        result = append_credits('Descrição', 'Créditos: @{channel_handle}', '')
        assert result == 'Descrição'

    def test_append_credits_never_outputs_double_at_sign(self):
        result = append_credits(
            'Descrição do clip',
            'Créditos: @{channel_handle}',
            '@FlowPodcast',
        )

        assert result == 'Descrição do clip\n\nCréditos: @FlowPodcast'
        assert '@@' not in result

    def test_append_credits_normalizes_double_at_in_template(self):
        result = append_credits(
            'Descrição do clip',
            'Créditos: @@{channel_handle}',
            'FlowPodcast',
        )

        assert result == 'Descrição do clip\n\nCréditos: @FlowPodcast'
