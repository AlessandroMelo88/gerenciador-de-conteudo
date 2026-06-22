"""
test_metadata_generator.py — Testes Phase 4 VID-04.

Estado inicial do Plan 04-01: RED controlado por NotImplementedError.
"""
import json
from unittest.mock import MagicMock

from src.metadata_generator import generate_metadata, update_clip_metadata


SAMPLE_CONTEXT = {
    'source_title': 'Debate quente depois do clássico',
    'reason': 'Discussão intensa sobre arbitragem',
    'score': 9,
    'start_time': 120.0,
    'end_time': 420.0,
    'transcript_excerpt': 'Foi pênalti ou não foi? O debate esquentou no estúdio.',
}


class TestMetadataGenerator:

    def test_generate_metadata_returns_title_description_tags(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [MagicMock(text=json.dumps({
            'title': 'Polêmica no clássico: foi pênalti?',
            'description': 'Debate completo sobre o lance mais polêmico.',
            'tags': ['futebol', 'classico', 'arbitragem'],
        }))]
        mock_anthropic.messages.create.return_value = response

        metadata = generate_metadata(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        assert set(metadata.keys()) == {'title', 'description', 'tags'}
        assert isinstance(metadata['tags'], list)

    def test_title_is_trimmed_to_100_chars(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [MagicMock(text=json.dumps({
            'title': 'A' * 150,
            'description': 'Descricao',
            'tags': ['futebol'],
        }))]
        mock_anthropic.messages.create.return_value = response

        metadata = generate_metadata(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        assert len(metadata['title']) <= 100

    def test_generate_metadata_uses_structured_output(self):
        mock_anthropic = MagicMock()
        response = MagicMock()
        response.content = [MagicMock(text=json.dumps({
            'title': 'Titulo',
            'description': 'Descricao',
            'tags': ['futebol'],
        }))]
        mock_anthropic.messages.create.return_value = response

        generate_metadata(SAMPLE_CONTEXT, anthropic_client=mock_anthropic)

        kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert kwargs['model'] == 'claude-haiku-4-5'
        assert 'output_config' in kwargs


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
