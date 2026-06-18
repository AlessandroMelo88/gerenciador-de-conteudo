"""
Testes ORC-02: operações de banco de dados do pipeline.

Módulo alvo: src.db
Exports esperados:
  - get_db_connection() -> connection
  - update_status(conn, video_id, status, local_path=None)
  - insert_video(conn, video_id, channel_id, title, published_at)
  - recover_stuck_downloads(conn)

RED state: imports falham pois src/db.py ainda não existe.
"""
from src.db import update_status, insert_video, recover_stuck_downloads


class TestUpdateStatus:

    def test_status_update(self, mock_db_conn):
        """update_status() executa SQL UPDATE com status correto."""
        update_status(mock_db_conn, video_id=1, status='downloading')

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.assert_called_once()

        # Verificar que o SQL contém UPDATE e o status correto
        sql_call = mock_cursor.execute.call_args[0][0]
        assert 'UPDATE' in sql_call.upper()
        assert 'status' in sql_call.lower()

        # Verificar que os parâmetros incluem o status e o video_id
        params = mock_cursor.execute.call_args[0][1]
        assert 'downloading' in params
        assert 1 in params

    def test_status_update_with_path(self, mock_db_conn):
        """update_status() com local_path inclui local_path no SQL."""
        local_path = '/data/videos/dQw4w9WgXcQ.mp4'

        update_status(mock_db_conn, video_id=1, status='downloaded', local_path=local_path)

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.assert_called_once()

        # Verificar que local_path está nos parâmetros
        params = mock_cursor.execute.call_args[0][1]
        assert local_path in params
        assert 'downloaded' in params


class TestRecoverStuckDownloads:

    def test_recover_stuck_downloads(self, mock_db_conn):
        """recover_stuck_downloads() executa UPDATE SET status='pending'
        WHERE status='downloading'."""
        recover_stuck_downloads(mock_db_conn)

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.assert_called_once()

        sql_call = mock_cursor.execute.call_args[0][0]
        assert 'UPDATE' in sql_call.upper()
        assert 'pending' in sql_call.lower() or 'pending' in str(mock_cursor.execute.call_args)
        assert 'downloading' in sql_call.lower() or 'downloading' in str(mock_cursor.execute.call_args)


class TestInsertVideo:

    def test_insert_video(self, mock_db_conn):
        """insert_video() executa INSERT com todos os campos corretos."""
        video_id = 'dQw4w9WgXcQ'
        channel_id = 1
        title = 'Gol incrível do Vini Jr'
        published_at = '2026-06-18T10:00:00+00:00'

        insert_video(mock_db_conn, video_id, channel_id, title, published_at)

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.assert_called_once()

        sql_call = mock_cursor.execute.call_args[0][0]
        assert 'INSERT' in sql_call.upper()

        params = mock_cursor.execute.call_args[0][1]
        assert video_id in params
        assert channel_id in params
        assert title in params
