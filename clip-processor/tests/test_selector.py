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

        count = insert_selected_moments(mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=moments)

        assert count == 0
        mock_db_conn.cursor().__enter__().execute.assert_not_called()

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

        count = insert_selected_moments(mock_db_conn, source_video_id=1, video_id='dQw4w9WgXcQ', moments=many_moments)

        assert count <= 3
