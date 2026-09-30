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


# ---------------------------------------------------------------------------
# Lote 5 (release/rico) — títulos editoriais, JSON tolerante, tags e créditos
# ---------------------------------------------------------------------------

import pytest
from unittest.mock import patch

from src import metadata_generator as mg


def _anthropic_returning(payload):
    client = MagicMock()
    text = payload if isinstance(payload, str) else json.dumps(payload)
    client.messages.create.return_value = MagicMock(content=[MagicMock(text=text)])
    return client


GOOD = {
    'title': 'Por que o VAR mudou tudo no clássico',
    'description': 'Análise do lance que decidiu o jogo.',
    'tags': ['futebol', 'var'],
}


class TestTituloEditorial:

    @pytest.mark.parametrize('titulo', [
        'Vídeo longo sobre o clássico',
        'Shorts: o lance que ninguém viu',
        'Corte do debate mais quente',
        'O gol aos 30s que decidiu',
    ])
    def test_rotulo_generico_e_rejeitado_no_modo_estrito(self, titulo):
        with pytest.raises(ValueError):
            mg._normalize_metadata({**GOOD, 'title': titulo}, SAMPLE_CONTEXT, strict=True)

    def test_titulo_igual_ao_original_e_rejeitado_no_modo_estrito(self):
        with pytest.raises(ValueError):
            mg._normalize_metadata(
                {**GOOD, 'title': 'DEBATE quente depois do clássico!'}, SAMPLE_CONTEXT, strict=True
            )

    def test_campos_vazios_sao_rejeitados_no_modo_estrito(self):
        for campo in ('title', 'description', 'tags'):
            with pytest.raises(ValueError):
                mg._normalize_metadata({**GOOD, campo: ''}, SAMPLE_CONTEXT, strict=True)

    def test_modo_padrao_nao_rejeita_rotulo(self):
        """update_clip_metadata e o fallback final nunca podem travar o pipeline."""
        out = mg._normalize_metadata({**GOOD, 'title': 'Shorts do jogo'}, SAMPLE_CONTEXT)
        assert out['title'] == 'Shorts do jogo'

    def test_titulo_com_rotulo_da_anthropic_cai_para_groq(self):
        anthropic = _anthropic_returning({**GOOD, 'title': 'Vídeo longo do clássico'})
        with patch.object(mg, '_generate_via_groq', return_value=GOOD) as groq:
            out = generate_metadata(SAMPLE_CONTEXT, anthropic_client=anthropic)
        groq.assert_called_once()
        assert out['title'] == GOOD['title']

    def test_ordem_anthropic_groq_titulo_bruto(self):
        """Se as duas IAs falham, o título bruto do vídeo é o último recurso (regra do CLAUDE.md)."""
        anthropic = MagicMock()
        anthropic.messages.create.side_effect = RuntimeError('sem chave')
        with patch.object(mg, '_generate_via_groq', side_effect=RuntimeError('groq fora')):
            out = generate_metadata(SAMPLE_CONTEXT, anthropic_client=anthropic)
        assert out['title'] == SAMPLE_CONTEXT['source_title']
        assert out['tags']

    def test_titulo_longo_corta_em_palavra(self):
        titulo = ' '.join(['palavra'] * 30)
        out = mg._normalize_metadata({**GOOD, 'title': titulo})
        assert len(out['title']) <= 100
        assert out['title'].endswith('palavra')

    def test_prompts_de_sistema_pedem_titulo_sem_rotulo(self):
        assert 'rótulos' in mg.SYSTEM_PROMPT
        assert 'rótulos' in mg.POLITICA_METADATA_PROMPT


class TestSaidaDaIa:

    def test_json_em_cerca_markdown_e_aceito(self):
        raw = '```json\n' + json.dumps(GOOD) + '\n```'
        out = generate_metadata(SAMPLE_CONTEXT, anthropic_client=_anthropic_returning(raw))
        assert out['title'] == GOOD['title']

    def test_json_com_texto_ao_redor(self):
        assert mg._safe_json_loads('Claro! ' + json.dumps(GOOD) + ' pronto.') == GOOD
        assert mg._safe_json_loads('') == {}
        assert mg._safe_json_loads('sem json') == {}

    def test_tags_deduplicadas_sem_hashtag(self):
        out = mg._normalize_metadata({**GOOD, 'tags': ['#Futebol', 'futebol', 'VAR', ' var ', '']})
        assert out['tags'] == ['Futebol', 'VAR']

    def test_tags_em_string(self):
        assert mg._normalize_tags('a, b, A') == ['a', 'b']

    def test_descricao_enorme_e_truncada_em_bytes(self):
        out = mg._normalize_metadata({**GOOD, 'description': 'Frase com acentuação. ' * 400})
        assert len(out['description'].encode('utf-8')) <= mg.MAX_GENERATED_DESCRIPTION_BYTES


class TestCreditos:

    def test_arroba_duplicada_e_colapsada(self):
        out = mg.append_credits('Desc', 'Créditos: @{channel_handle}', '@sportv')
        assert out == 'Desc\n\nCréditos: @sportv'

    def test_descricao_e_encurtada_para_caber_os_creditos(self):
        longa = 'Palavra ' * 700
        out = mg.append_credits(longa, 'Créditos: @{channel_handle}', 'canal')
        assert out.endswith('Créditos: @canal')
        assert len(out.encode('utf-8')) <= mg.YOUTUBE_DESCRIPTION_MAX_BYTES
