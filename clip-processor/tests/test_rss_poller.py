"""
Testes ACQU-01: detecção de vídeos novos via RSS.

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
