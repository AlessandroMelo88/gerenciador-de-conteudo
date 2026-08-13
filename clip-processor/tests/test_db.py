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
from src.db import (
    SELECTING_STUCK_HOURS,
    insert_video,
    recover_stuck_downloads,
    recover_stuck_selecting,
    update_status,
)


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

    def test_clear_local_path_sets_null(self, mock_db_conn):
        """clear_local_path=True deve gravar local_path=NULL (libera vaga da janela)."""
        update_status(mock_db_conn, video_id='xyz999', status='failed', clear_local_path=True)

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        sql_call = mock_cursor.execute.call_args[0][0]
        assert 'local_path=NULL' in sql_call.replace(' = ', '=')

        params = mock_cursor.execute.call_args[0][1]
        assert params == ('failed', 'xyz999')


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


class TestRecoverStuckSelecting:

    def test_selecting_sem_arquivo_vai_para_failed(self, mock_db_conn):
        """'selecting' com local_path NULL precisa de saída própria.

        As duas queries originais exigem `local_path IS NOT NULL`, então registro
        que teve o arquivo limpo por fora ficava preso pra sempre — nenhum
        restart alcançava. Sem raw em disco não há seleção pra reprocessar, então
        o destino é 'failed'.
        """
        recover_stuck_selecting(mock_db_conn)

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        executed = [call[0][0] for call in mock_cursor.execute.call_args_list]

        no_file_sql = [
            sql for sql in executed
            if 'local_path IS NULL' in sql and "status='failed'" in sql
        ]
        assert len(no_file_sql) == 1, 'falta a query de selecting sem arquivo'

        # Respeita a mesma carência das demais — não atropela seleção em curso.
        sql = no_file_sql[0]
        assert 'updated_at' in sql
        idx = executed.index(sql)
        assert mock_cursor.execute.call_args_list[idx][0][1] == (SELECTING_STUCK_HOURS,)

    def test_nao_toca_em_selecting_com_arquivo_no_caminho_sem_arquivo(self, mock_db_conn):
        """A query de 'sem arquivo' não pode capturar quem ainda tem o raw."""
        recover_stuck_selecting(mock_db_conn)

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        for call in mock_cursor.execute.call_args_list:
            sql = call[0][0]
            if "status='failed'" in sql:
                assert 'local_path IS NULL' in sql
                assert 'local_path IS NOT NULL' not in sql


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
