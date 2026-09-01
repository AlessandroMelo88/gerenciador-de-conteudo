"""
test_clip_pipeline.py — Integração Phase 4 no rss_poller.

Estado inicial do Plan 04-01: RED controlado por atributo/função ausente.
"""
from src.rss_poller import poll_all_channels


class TestClipPipelineIntegration:

    def _make_cursor(self, mock_db_conn, channel_rows=None, downloaded_rows=None, clip_rows=None):
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.side_effect = [
            channel_rows or [],
            downloaded_rows or [],
            clip_rows or [],
        ]
        return cursor

    def test_pending_cut_clips_trigger_processing(self, mock_db_conn, mock_redis, mocker):
        self._make_cursor(
            mock_db_conn,
            clip_rows=[{'id': 10}, {'id': 11}],
        )
        mock_process = mocker.patch('src.rss_poller.process_clip', create=True)

        poll_all_channels(mock_db_conn, mock_redis)

        assert mock_process.call_count == 2
        mock_process.assert_any_call(mock_db_conn, 10)
        mock_process.assert_any_call(mock_db_conn, 11)

    def test_clip_processing_failure_does_not_abort_poll(self, mock_db_conn, mock_redis, mocker):
        self._make_cursor(
            mock_db_conn,
            clip_rows=[{'id': 10}, {'id': 11}],
        )
        processed = []

        def process_side_effect(conn, clip_id):
            processed.append(clip_id)
            if clip_id == 10:
                raise RuntimeError('ffmpeg failed')

        mocker.patch('src.rss_poller.process_clip', side_effect=process_side_effect, create=True)

        poll_all_channels(mock_db_conn, mock_redis)

        assert processed == [10, 11]
