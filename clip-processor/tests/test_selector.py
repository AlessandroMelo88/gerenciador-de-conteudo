"""
test_selector.py — Testes unitários para selector.py (AI-02, AI-03).

Estado inicial: RED — todos falham com NotImplementedError.
Após implementação: GREEN.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from src.selector import (
    select_moments,
    insert_selected_moments,
    _clean_reason,
    _parse_moments,
    MAX_REASON_CHARS,
)


SAMPLE_TRANSCRIPT = {
    'video_id': 'dQw4w9WgXcQ',
    'text': 'Texto completo do vídeo',
    'segments': [
        {'start': 0.0, 'end': 60.0, 'text': 'Análise do gol de placa do Vini Jr'},
        {'start': 60.0, 'end': 120.0, 'text': 'Debate sobre o melhor jogador da temporada'},
        {'start': 120.0, 'end': 300.0, 'text': 'Tática do Ancelotti explicada'},
    ],
}

SAMPLE_MOMENTS = [
    {'start_time': 0.0, 'end_time': 60.0, 'score': 9, 'reason': 'Análise tática profunda'},
    {'start_time': 100.0, 'end_time': 160.0, 'score': 8, 'reason': 'Debate acalorado'},
    {'start_time': 200.0, 'end_time': 245.0, 'score': 7, 'reason': 'Revelação de bastidores'},
]


class TestCleanReason:
    """Justificativa do momento não pode carregar o raciocínio do modelo (visto em 15/09/2026)."""

    def test_colapsa_espacos_e_quebras(self):
        assert _clean_reason('Análise\n  tática   profunda\n') == 'Análise tática profunda'

    def test_ausente_vira_string_vazia(self):
        """insert_selected_moments lê moment['reason'] direto — não pode faltar a chave."""
        assert _clean_reason(None) == ''

    def test_corta_raciocinio_longo_do_modelo(self):
        raciocinio = (
            'Vou selecionar o trecho de 0s a 454s? Não, o início é fraco. '
            'Vou selecionar de 120s a 454s? Não atinge 420s. ' * 20
        )
        resultado = _clean_reason(raciocinio)

        assert len(resultado) == MAX_REASON_CHARS + 1  # +1 pela reticência
        assert resultado.endswith('…')

    def test_parse_moments_aplica_limpeza(self):
        """A limpeza tem que valer para os dois caminhos de IA, que passam por _parse_moments."""
        bruto = json.dumps({
            'moments': [{
                'start_time': 0,
                'end_time': 60,
                'score': 9,
                'reason': 'x' * (MAX_REASON_CHARS + 50),
            }]
        })

        momentos = _parse_moments(bruto)

        assert len(momentos[0]['reason']) == MAX_REASON_CHARS + 1

    def test_parse_moments_preenche_reason_ausente(self):
        bruto = json.dumps({'moments': [{'start_time': 0, 'end_time': 60, 'score': 9}]})

        momentos = _parse_moments(bruto)

        assert momentos[0]['reason'] == ''


class TestSelectMoments:

    def test_returns_moments_list(self, sample_video_id):
        """AI-02: select_moments() retorna lista de dicts com start_time, end_time, score, reason."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': SAMPLE_MOMENTS}))]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic)

        assert isinstance(result, list)
        assert len(result) > 0
        first = result[0]
        assert 'start_time' in first
        assert 'end_time' in first
        assert 'score' in first
        assert 'reason' in first

    def test_transcript_formatted_with_timestamps(self, sample_video_id):
        """AI-02: O texto enviado ao Haiku inclui timestamps no formato [Ns-Ns] por segmento."""
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': SAMPLE_MOMENTS}))]
        mock_anthropic.messages.create.return_value = mock_response

        select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic)

        # Verificar que o conteúdo enviado ao Haiku tem formato [Ns-Ns]
        call_args = mock_anthropic.messages.create.call_args
        messages = call_args[1]['messages'] if 'messages' in call_args[1] else call_args[0][3] if len(call_args[0]) > 3 else None
        # Alternativa: verificar o kwarg 'messages'
        kwargs = call_args.kwargs if hasattr(call_args, 'kwargs') else call_args[1]
        user_content = kwargs['messages'][0]['content']
        assert '[0s-60s]' in user_content or '[0s-' in user_content

    def test_shortform_abaixo_de_15s_descartado(self, sample_video_id):
        """Momento com menos de 15 s é descartado: em 3-5 s não há assunto.

        Esticar 3 s até 30 s não cria assunto — só adiciona contexto aleatório em volta
        de uma interjeição. Abaixo do piso de esticamento, descarta.
        """
        mock_anthropic = MagicMock()
        short_moments = [
            {'start_time': 10.0, 'end_time': 13.0, 'score': 9, 'reason': 'Irrelevante de 3s'},
            {'start_time': 20.0, 'end_time': 25.0, 'score': 8, 'reason': 'Irrelevante de 5s'},
            {'start_time': 100.0, 'end_time': 140.0, 'score': 9, 'reason': 'Corte válido de 40s'},
        ]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': short_moments}))]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic, fmt='curto')

        assert len(result) == 1
        assert result[0]['start_time'] == 100.0
        assert result[0]['end_time'] == 140.0

    def test_shortform_entre_15s_e_30s_esticado(self, sample_video_id):
        """Momento de 15 s a 30 s é esticado até MIN_SHORTFORM_SECONDS, não descartado.

        Decisão do operador (15/09/2026): clip de 2-5 s não é assunto, mas a partir de 15 s
        já existe conteúdo e vale completar os 30 s com o contexto em volta.
        """
        mock_anthropic = MagicMock()
        moments = [{'start_time': 50.0, 'end_time': 70.0, 'score': 9, 'reason': 'Tem assunto, mas só 20s'}]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': moments}))]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic, fmt='curto')

        assert len(result) == 1
        duracao = result[0]['end_time'] - result[0]['start_time']
        assert duracao == 30.0, f'esperava 30 s após o esticamento, veio {duracao}'
        # Esticou para os dois lados, sem sair do vídeo
        assert result[0]['start_time'] >= 0.0
        assert result[0]['start_time'] < 50.0

    def test_shortform_acima_do_teto_limitado(self, sample_video_id):
        """Momento maior que MAX_SHORTFORM_SECONDS (180 s, teto do Shorts) é cortado no teto."""
        mock_anthropic = MagicMock()
        moments = [{'start_time': 10.0, 'end_time': 300.0, 'score': 9, 'reason': 'Longo demais para short'}]
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({'moments': moments}))]
        mock_anthropic.messages.create.return_value = mock_response

        result = select_moments(SAMPLE_TRANSCRIPT, anthropic_client=mock_anthropic, fmt='curto')

        assert len(result) == 1
        assert result[0]['end_time'] - result[0]['start_time'] <= 180.0


class TestInsertMoments:

    def test_score_7_inserted(self, mock_db_conn):
        """AI-03: Momento com score=7 é inserido em generated_clips com status pending_cut."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 7, 'reason': 'Bom momento'}]

        count = insert_selected_moments(mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=moments)

        assert count == 1
        mock_db_conn.cursor().__enter__().execute.assert_called()
        call_args = mock_db_conn.cursor().__enter__().execute.call_args
        params = call_args[0][1]
        assert 'pending_cut' in params

    def test_score_6_discarded(self, mock_db_conn):
        """AI-03: Momento com score=6 não é inserido — count retorna 0."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 6, 'reason': 'Mediano'}]

        # Mock: lookup de destination_channel retorna target_niche/id
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol'},  # source_videos JOIN source_channels
            {'id': 1},                    # destination_channels WHERE niche=futebol
        ]

        count = insert_selected_moments(mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=moments)

        assert count == 0
        # SELECTs são chamados (lookup do canal), mas INSERT não deve ocorrer
        insert_calls = [
            c for c in cursor.execute.call_args_list
            if c.args and 'INSERT' in str(c.args[0]).upper()
        ]
        assert len(insert_calls) == 0, 'Momento com score < 7 não deve gerar INSERT'

    def test_overlap_keeps_higher_score(self, mock_db_conn):
        """AI-03: Dois momentos sobrepostos — apenas o de maior score é inserido."""
        overlapping = [
            {'start_time': 0.0, 'end_time': 400.0, 'score': 8, 'reason': 'Score maior'},
            {'start_time': 200.0, 'end_time': 600.0, 'score': 7, 'reason': 'Score menor — overlap'},
        ]

        count = insert_selected_moments(mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=overlapping)

        # Apenas 1 momento deve ser inserido (o de score 8)
        assert count == 1

    def test_max_3_moments(self, mock_db_conn):
        """AI-03: Máximo 3 momentos inseridos mesmo se mais de 3 com score >= 7 forem passados."""
        many_moments = [
            {'start_time': i * 400.0, 'end_time': i * 400.0 + 360.0, 'score': 8, 'reason': f'Momento {i}'}
            for i in range(5)  # 5 momentos não-sobrepostos com score 8
        ]

        # Mock: lookup de destination_channel
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol'},
            {'id': 2},
        ]

        count = insert_selected_moments(mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=many_moments)

        assert count <= 3


class TestInsertMomentsDestinationChannel:
    """MCAN-02: insert_selected_moments persiste destination_channel_id em generated_clips."""

    def test_destination_channel_id_persisted_in_insert(self, mock_db_conn):
        """MCAN-02: INSERT inclui destination_channel_id quando canal-destino existe para o nicho."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 8, 'reason': 'Gol'}]

        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        # Primeiro SELECT: target_niche do canal de origem
        # Segundo SELECT: id do canal-destino para o nicho
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol'},  # source_videos JOIN source_channels
            {'id': 42},                   # destination_channels WHERE niche='futebol'
        ]

        count = insert_selected_moments(mock_db_conn, source_video_id=5, video_id='abc123', moments=moments)

        assert count == 1
        # Verificar que o INSERT inclui destination_channel_id
        insert_calls = [
            c for c in cursor.execute.call_args_list
            if c.args and 'INSERT' in str(c.args[0]).upper()
        ]
        assert len(insert_calls) == 1, 'Deve haver exatamente 1 INSERT'
        params = insert_calls[0].args[1]
        assert 42 in params, f'destination_channel_id=42 deve estar nos params do INSERT. Params: {params}'

    def test_destination_channel_id_null_when_niche_is_null(self, mock_db_conn):
        """MCAN-02: Quando target_niche é NULL, destination_channel_id fica NULL (sem erro)."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 9, 'reason': 'Debate'}]

        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        # Primeiro SELECT: target_niche = NULL
        cursor.fetchone.side_effect = [
            {'target_niche': None},  # sem nicho definido
        ]

        count = insert_selected_moments(mock_db_conn, source_video_id=5, video_id='abc123', moments=moments)

        assert count == 1
        # INSERT deve ter None como destination_channel_id
        insert_calls = [
            c for c in cursor.execute.call_args_list
            if c.args and 'INSERT' in str(c.args[0]).upper()
        ]
        assert len(insert_calls) == 1
        params = insert_calls[0].args[1]
        assert None in params, f'destination_channel_id=None deve estar nos params. Params: {params}'

    def test_destination_channel_id_null_when_no_active_destination(self, mock_db_conn):
        """MCAN-02: Quando não há canal-destino ativo para o nicho, destination_channel_id=NULL."""
        moments = [{'start_time': 0.0, 'end_time': 360.0, 'score': 8, 'reason': 'Análise'}]

        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            {'target_niche': 'futebol'},  # nicho existe
            None,                          # mas não há canal-destino ativo
        ]

        count = insert_selected_moments(mock_db_conn, source_video_id=5, video_id='abc123', moments=moments)

        assert count == 1
        insert_calls = [
            c for c in cursor.execute.call_args_list
            if c.args and 'INSERT' in str(c.args[0]).upper()
        ]
        assert len(insert_calls) == 1
        params = insert_calls[0].args[1]
        assert None in params, f'destination_channel_id=None quando sem destino ativo. Params: {params}'


# ---------------------------------------------------------------------------
# Lote 5 (release/rico) — regras de fronteira/retenção no prompt e clamp de tempos
# ---------------------------------------------------------------------------

from src import selector as sel


class TestPromptsDoSeletor:

    @pytest.mark.parametrize('nome', [
        'SYSTEM_PROMPT', 'LONG_SYSTEM_PROMPT', 'POLITICA_SYSTEM_PROMPT', 'POLITICA_LONG_SYSTEM_PROMPT',
    ])
    def test_todos_os_prompts_pedem_fechamento_de_frase_e_excluem_publicidade(self, nome):
        prompt = getattr(sel, nome)
        assert 'FECHAMENTO DE FRASE' in prompt
        assert 'PUBLICIDADE' in prompt
        # o contrato de saída (JSON com start_time/end_time em segundos) continua no fim
        assert prompt.rstrip().endswith('"reason": "<string>"}]}')

    @pytest.mark.parametrize('nome', ['SYSTEM_PROMPT', 'POLITICA_SYSTEM_PROMPT'])
    def test_prompts_curtos_tem_criterios_de_retencao(self, nome):
        prompt = getattr(sel, nome)
        assert 'RETENÇÃO DO FORMATO CURTO' in prompt
        assert 'RETENÇÃO DO FORMATO LONGO' not in prompt

    @pytest.mark.parametrize('nome', ['LONG_SYSTEM_PROMPT', 'POLITICA_LONG_SYSTEM_PROMPT'])
    def test_prompts_longos_tem_criterios_de_retencao(self, nome):
        prompt = getattr(sel, nome)
        assert 'RETENÇÃO DO FORMATO LONGO' in prompt
        assert 'RETENÇÃO DO FORMATO CURTO' not in prompt

    def test_prompt_enviado_ao_provider_inclui_as_regras(self):
        client = MagicMock()
        client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps({'moments': SAMPLE_MOMENTS}))]
        )
        select_moments(SAMPLE_TRANSCRIPT, anthropic_client=client, fmt='curto')
        assert 'FECHAMENTO DE FRASE' in client.messages.create.call_args.kwargs['system']


class TestClampDeLimites:

    def test_tempo_alem_do_fim_do_video_e_cortado(self):
        out = sel._clamp_moment_bounds(
            [{'start_time': 250.0, 'end_time': 900.0, 'score': 9, 'reason': 'x'}], 300.0
        )
        assert out[0]['end_time'] == 300.0
        assert out[0]['start_time'] == 250.0

    def test_tempo_negativo_vira_zero(self):
        out = sel._clamp_moment_bounds([{'start_time': -5.0, 'end_time': 40.0}], 300.0)
        assert out[0]['start_time'] == 0.0

    def test_momento_totalmente_fora_colapsa_e_e_descartado_no_select(self):
        client = MagicMock()
        moments = [{'start_time': 400.0, 'end_time': 500.0, 'score': 9, 'reason': 'fora do vídeo'}]
        client.messages.create.return_value = MagicMock(content=[MagicMock(text=json.dumps({'moments': moments}))])
        assert select_moments(SAMPLE_TRANSCRIPT, anthropic_client=client, fmt='curto') == []

    def test_sem_duracao_devolve_intacto(self):
        moments = [{'start_time': 1.0, 'end_time': 2.0}]
        assert sel._clamp_moment_bounds(moments, 0.0) == moments


class TestFallbackGroq:

    def test_sem_chave_anthropic_usa_groq(self, monkeypatch):
        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        with patch.object(sel, '_select_via_groq', return_value=[
            {'start_time': 100.0, 'end_time': 140.0, 'score': 9, 'reason': 'ok'}
        ]) as groq:
            out = select_moments(SAMPLE_TRANSCRIPT, fmt='curto')
        groq.assert_called_once()
        assert out and out[0]['start_time'] == 100.0


class TestLogDeSelecaoVazia:
    """06/10/2026: 30 de 73 vídeos (41%) viraram failed com "0 momento(s)" e nenhuma linha de log.

    Eram Shorts de ~60s e o modelo devolvia {"moments": []} — o único caminho mudo do módulo.
    """

    def test_lista_vazia_do_modelo_e_registrada(self, capsys):
        resultado = _parse_moments(json.dumps({'moments': []}), transcript_chars=812)

        assert resultado == []
        log = capsys.readouterr().out
        assert '[SELECTOR] Nenhum momento aproveitável: 0 na resposta crua' in log
        assert '0 após a limpeza' in log
        assert 'transcrição de 812 chars' in log
        assert 'lista vazia' in log

    def test_momentos_todos_invalidos_sao_registrados_com_a_contagem_crua(self, capsys):
        bruto = json.dumps({'moments': [
            {'start_time': 100, 'end_time': 100, 'score': 9, 'reason': 'colapsado'},
            {'start_time': 200, 'end_time': 150, 'score': 8, 'reason': 'invertido'},
        ]})

        resultado = _parse_moments(bruto, transcript_chars=4096)

        assert resultado == []
        log = capsys.readouterr().out
        assert '[SELECTOR] Nenhum momento aproveitável: 2 na resposta crua' in log
        assert 'transcrição de 4096 chars' in log
        assert 'end <= start' in log
        assert 'lista vazia' not in log

    def test_caminho_feliz_nao_polui_o_log(self, capsys):
        bruto = json.dumps({'moments': [
            {'start_time': 10, 'end_time': 70, 'score': 9, 'reason': 'ok'},
        ]})

        resultado = _parse_moments(bruto, transcript_chars=4096)

        assert len(resultado) == 1
        assert 'Nenhum momento aproveitável' not in capsys.readouterr().out

    def test_select_moments_vazio_apos_filtros_registra_linha_final(self, capsys, monkeypatch):
        """Distingue "a IA não achou nada" de "os filtros descartaram tudo" — o rss_poller não distingue."""
        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        # 10s: abaixo do piso de esticamento do formato curto, descartado pelos filtros
        with patch.object(sel, '_select_via_groq', return_value=[
            {'start_time': 100.0, 'end_time': 110.0, 'score': 9, 'reason': 'curto demais'}
        ]):
            resultado = select_moments(SAMPLE_TRANSCRIPT, fmt='curto')

        assert resultado == []
        log = capsys.readouterr().out
        assert '[SELECTOR] Nenhum momento sobrou após os filtros' in log
        assert '1 momento(s) vieram do modelo' in log
