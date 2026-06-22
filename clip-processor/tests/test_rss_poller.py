"""
Testes ACQU-01: detecção de vídeos novos via RSS.
Testes AI-04: integração do pipeline de IA (transcriber + selector) no rss_poller.

Módulo alvo: src.rss_poller
Exports esperados: poll_all_channels(db_conn, redis_client)

RED state: imports falham pois src/rss_poller.py ainda não existe.
"""
from src.rss_poller import poll_all_channels


class TestPollAllChannels:

    def test_poll_detects_new_videos(self, mock_db_conn, mock_redis, sample_rss_xml, mocker):
        """Dado feed RSS com 2 entradas nunca vistas, poll_all_channels()
        insere 2 registros no DB com status 'pending'."""
        # Arrange: canal ativo no DB
        channel = {
            'id': 1,
            'youtube_channel_id': 'UCxxx',
            'channel_name': 'Futebol Canal',
            'rss_url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCxxx',
        }
        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [channel]

        # Mock: RSS fetch retorna sample_rss_xml
        mocker.patch('src.rss_poller.requests.get', return_value=mocker.MagicMock(
            status_code=200,
            text=sample_rss_xml,
        ))

        # Mock: nenhum vídeo já visto (is_seen retorna False)
        mocker.patch('src.rss_poller.is_seen', return_value=False)

        # Mock: insert_video não levanta exceção
        mock_insert = mocker.patch('src.rss_poller.insert_video')

        # Act
        poll_all_channels(mock_db_conn, mock_redis)

        # Assert: insert_video chamado 2 vezes (uma por entrada do feed)
        assert mock_insert.call_count == 2

    def test_poll_skips_seen_videos(self, mock_db_conn, mock_redis, sample_rss_xml, mocker):
        """Dado vídeo já no Redis (is_seen retorna True),
        poll não chama insert_video para esse vídeo."""
        channel = {
            'id': 1,
            'youtube_channel_id': 'UCxxx',
            'channel_name': 'Futebol Canal',
            'rss_url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCxxx',
        }
        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [channel]

        mocker.patch('src.rss_poller.requests.get', return_value=mocker.MagicMock(
            status_code=200,
            text=sample_rss_xml,
        ))

        # Todos os vídeos já foram vistos
        mocker.patch('src.rss_poller.is_seen', return_value=True)
        mock_insert = mocker.patch('src.rss_poller.insert_video')

        poll_all_channels(mock_db_conn, mock_redis)

        # Assert: insert_video nunca chamado
        mock_insert.assert_not_called()

    def test_poll_handles_empty_feed(self, mock_db_conn, mock_redis, mocker):
        """Feed sem entradas não levanta exceção."""
        channel = {
            'id': 1,
            'youtube_channel_id': 'UCxxx',
            'channel_name': 'Futebol Canal',
            'rss_url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCxxx',
        }
        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [channel]

        empty_feed = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <title>Canal Vazio</title>
</feed>"""

        mocker.patch('src.rss_poller.requests.get', return_value=mocker.MagicMock(
            status_code=200,
            text=empty_feed,
        ))

        mocker.patch('src.rss_poller.is_seen', return_value=False)
        mock_insert = mocker.patch('src.rss_poller.insert_video')

        # Act — não deve levantar exceção
        poll_all_channels(mock_db_conn, mock_redis)

        mock_insert.assert_not_called()


class TestAIPipelineIntegration:
    """AI-04: Testes de integração do pipeline de IA no rss_poller."""

    def _make_downloaded_cursor(self, mock_db_conn, video_rows, channel_rows=None):
        """Configura mock_db_conn para retornar canais e vídeos downloaded em fetchall().

        O rss_poller faz duas queries fetchall:
          1. SELECT canais ativos (retorna lista vazia aqui para não poluir)
          2. SELECT vídeos downloaded (retorna video_rows)
        """
        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        if channel_rows is None:
            channel_rows = []
        mock_cursor.fetchall.side_effect = [channel_rows, video_rows]
        return mock_cursor

    def test_downloaded_videos_trigger_ai_pipeline(self, mock_db_conn, mock_redis, mocker):
        """AI-04: poll_all_channels chama _process_ai_pipeline para cada vídeo com status downloaded."""
        video_rows = [
            {'youtube_video_id': 'vid001aaaaaa', 'local_path': '/app/videos/vid001aaaaaa.mp4'},
        ]
        self._make_downloaded_cursor(mock_db_conn, video_rows)

        mocker.patch('src.rss_poller.requests.get', return_value=mocker.MagicMock(
            status_code=200, text='<feed/>'
        ))

        mock_pipeline = mocker.patch('src.rss_poller._process_ai_pipeline')

        poll_all_channels(mock_db_conn, mock_redis)

        # Pipeline deve ter sido chamado para o vídeo downloaded
        mock_pipeline.assert_called_once_with(mock_db_conn, 'vid001aaaaaa', '/app/videos/vid001aaaaaa.mp4')

    def test_ai_pipeline_failure_does_not_abort_poll(self, mock_db_conn, mock_redis, mocker):
        """AI-04: Falha no pipeline de IA de um vídeo não aborta os demais."""
        video_rows = [
            {'youtube_video_id': 'vid001aaaaaa', 'local_path': '/app/videos/vid001aaaaaa.mp4'},
            {'youtube_video_id': 'vid002bbbbbb', 'local_path': '/app/videos/vid002bbbbbb.mp4'},
        ]
        self._make_downloaded_cursor(mock_db_conn, video_rows)

        mocker.patch('src.rss_poller.requests.get', return_value=mocker.MagicMock(
            status_code=200, text='<feed/>'
        ))

        # Primeiro vídeo levanta exceção, segundo deve ser processado mesmo assim
        call_count = []

        def pipeline_side_effect(conn, vid_id, vid_path):
            call_count.append(vid_id)
            if vid_id == 'vid001aaaaaa':
                raise Exception('Falha simulada na transcrição')

        mocker.patch('src.rss_poller._process_ai_pipeline', side_effect=pipeline_side_effect)

        # Act — não deve levantar exceção
        poll_all_channels(mock_db_conn, mock_redis)

        # Ambos os vídeos devem ter sido tentados
        assert 'vid001aaaaaa' in call_count
        assert 'vid002bbbbbb' in call_count

    def test_process_ai_pipeline_calls_transcribe_and_select(self, mock_db_conn, mocker):
        """AI-04: _process_ai_pipeline chama transcribe_video e select_moments em sequência."""
        from src.rss_poller import _process_ai_pipeline

        mock_transcript = {
            'video_id': 'vid001aaaaaa',
            'text': 'Texto',
            'segments': [{'start': 0.0, 'end': 60.0, 'text': 'Análise'}],
        }

        mocker.patch('src.rss_poller.transcribe_video', return_value=mock_transcript)
        mock_save = mocker.patch('src.rss_poller.save_transcript')
        mock_select = mocker.patch('src.rss_poller.select_moments', return_value=[])
        mock_insert = mocker.patch('src.rss_poller.insert_selected_moments', return_value=0)

        # Configurar cursor para retornar source_video_id
        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {'id': 42}

        _process_ai_pipeline(mock_db_conn, 'vid001aaaaaa', '/app/videos/vid001aaaaaa.mp4')

        # Verificar que transcribe foi chamado
        import src.rss_poller as rss_mod
        rss_mod.transcribe_video.assert_called_once_with(
            'vid001aaaaaa', '/app/videos/vid001aaaaaa.mp4', groq_client=None
        )
        # Verificar que save_transcript foi chamado após transcrição bem-sucedida
        mock_save.assert_called_once_with(mock_db_conn, 'vid001aaaaaa', mock_transcript)
        # Verificar que select_moments foi chamado
        mock_select.assert_called_once_with(mock_transcript, anthropic_client=None)

    def test_process_ai_pipeline_transcription_failure_marks_failed(self, mock_db_conn, mocker):
        """AI-04: Falha na transcrição (None) marca vídeo como failed e não chama select_moments."""
        from src.rss_poller import _process_ai_pipeline

        mocker.patch('src.rss_poller.transcribe_video', return_value=None)
        mock_update = mocker.patch('src.rss_poller.update_status')
        mock_select = mocker.patch('src.rss_poller.select_moments')

        _process_ai_pipeline(mock_db_conn, 'vid001aaaaaa', '/app/videos/vid001aaaaaa.mp4')

        # update_status deve ter sido chamado com 'failed'
        calls = [str(c) for c in mock_update.call_args_list]
        assert any('failed' in c for c in calls)

        # select_moments NÃO deve ter sido chamado
        mock_select.assert_not_called()

    def test_process_ai_pipeline_status_transitions(self, mock_db_conn, mocker):
        """AI-04: Pipeline atualiza status: transcribing → (save) → selecting."""
        from src.rss_poller import _process_ai_pipeline

        mock_transcript = {
            'video_id': 'vid001aaaaaa',
            'text': 'Texto',
            'segments': [],
        }

        mocker.patch('src.rss_poller.transcribe_video', return_value=mock_transcript)
        mocker.patch('src.rss_poller.save_transcript')
        mocker.patch('src.rss_poller.select_moments', return_value=[])
        mocker.patch('src.rss_poller.insert_selected_moments', return_value=0)

        status_calls = []

        def capture_update(conn, vid_id, status):
            status_calls.append(status)

        mocker.patch('src.rss_poller.update_status', side_effect=capture_update)

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {'id': 99}

        _process_ai_pipeline(mock_db_conn, 'vid001aaaaaa', '/app/videos/vid001aaaaaa.mp4')

        # Status deve ter transitado: transcribing → selecting
        assert 'transcribing' in status_calls
        assert 'selecting' in status_calls
        # A ordem importa: transcribing deve vir antes de selecting
        assert status_calls.index('transcribing') < status_calls.index('selecting')


# ---------------------------------------------------------------------------
# Wave 2 — RED tests: Blacklist guard (COPY-03)
# Estes testes falham até a implementação em Wave 3-4.
# ---------------------------------------------------------------------------

class TestBlacklistGuard:
    """Testes RED para blacklist guard no rss_poller (COPY-03)."""

    def test_blacklisted_channel_does_not_trigger_insert_video(
        self, mock_db_conn, mock_redis, mocker
    ):
        """COPY-03: canal com blacklisted=True não chama insert_video.

        O guard deve checar blacklisted ANTES de inserir — evita desperdício
        de Groq + Claude + FFmpeg em conteúdo proibido.
        """
        blacklisted_channel = {
            'id': 2,
            'youtube_channel_id': 'UCblacklisted',
            'channel_name': 'Canal Bloqueado',
            'rss_url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCblacklisted',
            'blacklisted': True,
            'target_niche': 'futebol',
        }
        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [blacklisted_channel]

        sample_rss = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <yt:videoId>vid_blocked_01</yt:videoId>
    <title>Vídeo de canal bloqueado</title>
    <published>2026-06-18T10:00:00+00:00</published>
  </entry>
</feed>"""

        mocker.patch('src.rss_poller.requests.get', return_value=mocker.MagicMock(
            status_code=200,
            text=sample_rss,
        ))
        mocker.patch('src.rss_poller.is_seen', return_value=False)
        mock_insert = mocker.patch('src.rss_poller.insert_video')

        poll_all_channels(mock_db_conn, mock_redis)

        mock_insert.assert_not_called()

    def test_non_blacklisted_channel_calls_insert_video(
        self, mock_db_conn, mock_redis, sample_rss_xml, mocker
    ):
        """COPY-03: canal com blacklisted=False (ou None) chama insert_video normalmente."""
        active_channel = {
            'id': 1,
            'youtube_channel_id': 'UCxxx',
            'channel_name': 'Canal Ativo',
            'rss_url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCxxx',
            'blacklisted': False,
            'target_niche': 'futebol',
        }
        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [active_channel]

        mocker.patch('src.rss_poller.requests.get', return_value=mocker.MagicMock(
            status_code=200,
            text=sample_rss_xml,
        ))
        mocker.patch('src.rss_poller.is_seen', return_value=False)
        mock_insert = mocker.patch('src.rss_poller.insert_video')

        poll_all_channels(mock_db_conn, mock_redis)

        assert mock_insert.call_count >= 1
