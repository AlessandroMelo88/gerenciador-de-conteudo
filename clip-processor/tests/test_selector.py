"""
test_selector.py — Testes unitários para selector.py (AI-02, AI-03).

Estado inicial: RED — todos falham com NotImplementedError.
Após implementação: GREEN.
"""
import json
import pytest
from unittest.mock import MagicMock
from src.selector import select_moments, insert_selected_moments


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
    {'start_time': 0.0, 'end_time': 360.0, 'score': 9, 'reason': 'Análise tática profunda'},
    {'start_time': 400.0, 'end_time': 700.0, 'score': 8, 'reason': 'Debate acalorado'},
    {'start_time': 800.0, 'end_time': 1100.0, 'score': 7, 'reason': 'Revelação de bastidores'},
]


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
