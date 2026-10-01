"""Recovery de estados presos (transcribing/publishing/cutting), PIPELINE_ENABLED e /health.

Regras que estes testes travam:
- nenhum recovery apaga arquivo nem mexe no Redis (raw de clip em corte fica; video:* intacto);
- cutting volta a pending_cut no boot (sem espera) ou, no job periódico, só após CUTTING_STUCK_HOURS;
- publishing com youtube_video_id vira published (nunca reenvia); sem id volta à fila, com carência longa.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.db import (
    CUTTING_STUCK_HOURS,
    PUBLISHING_STUCK_MINUTES,
    SELECTING_STUCK_HOURS,
    recover_cutting_on_boot,
    recover_stuck_cutting,
    recover_stuck_publishing,
    recover_stuck_transcribing,
    update_status,
)


def _executed(mock_db_conn):
    cursor = mock_db_conn.cursor.return_value.__enter__.return_value
    return cursor, [c[0] for c in cursor.execute.call_args_list]


class TestRecoverStuckTranscribing:
    def test_com_raw_volta_para_downloaded_e_sem_raw_vai_para_failed(self, mock_db_conn):
        recover_stuck_transcribing(mock_db_conn)

        cursor, calls = _executed(mock_db_conn)
        sqls = [c[0] for c in calls]
        assert any("status='downloaded'" in s and 'local_path IS NOT NULL' in s for s in sqls)
        assert any("status='failed'" in s and 'local_path IS NULL' in s for s in sqls)
        assert all("status='transcribing'" in s and 'updated_at' in s for s in sqls)
        assert all(c[1] == (SELECTING_STUCK_HOURS,) for c in calls)
        mock_db_conn.commit.assert_called_once()

    def test_so_faz_update_em_source_videos(self, mock_db_conn):
        recover_stuck_transcribing(mock_db_conn)
        _, calls = _executed(mock_db_conn)
        for sql, _params in calls:
            assert sql.startswith('UPDATE source_videos')
            assert 'DELETE' not in sql.upper()


class TestRecoverStuckPublishing:
    def test_com_youtube_id_vira_published_e_sem_id_volta_para_pending(self, mock_db_conn):
        recover_stuck_publishing(mock_db_conn)

        cursor, calls = _executed(mock_db_conn)
        assert len(calls) == 2
        (sql_pub, params_pub), (sql_pend, params_pend) = calls
        assert "SET status='published'" in sql_pub
        assert 'youtube_video_id IS NOT NULL' in sql_pub
        assert 'COALESCE(published_at' in sql_pub
        assert "SET status='pending'" in sql_pend
        assert 'youtube_video_id IS NULL' in sql_pend
        for sql in (sql_pub, sql_pend):
            assert "status='publishing'" in sql
            assert 'updated_at <' in sql
        assert params_pub == params_pend == (PUBLISHING_STUCK_MINUTES,)
        assert PUBLISHING_STUCK_MINUTES >= 60
        mock_db_conn.commit.assert_called_once()

    def test_nunca_devolve_a_fila_um_clip_com_youtube_id(self, mock_db_conn):
        recover_stuck_publishing(mock_db_conn)

        _, calls = _executed(mock_db_conn)
        for sql, _ in calls:
            if "SET status='pending'" in sql:
                assert 'youtube_video_id IS NULL' in sql
                assert 'NOT NULL' not in sql


class TestRecoverStuckCutting:
    def test_exige_carencia_e_so_troca_status(self, mock_db_conn):
        recover_stuck_cutting(mock_db_conn)

        _, calls = _executed(mock_db_conn)
        assert len(calls) == 1
        sql, params = calls[0]
        assert sql.startswith('UPDATE generated_clips')
        assert "SET status='pending_cut'" in sql
        assert "status='cutting'" in sql
        assert 'updated_at <' in sql
        assert 'DELETE' not in sql.upper()
        assert params == (CUTTING_STUCK_HOURS,)
        assert CUTTING_STUCK_HOURS >= 2
        mock_db_conn.commit.assert_called_once()


class TestRecoverCuttingOnBoot:
    def test_cutting_volta_para_pending_cut_sem_apagar_nada(self, mock_db_conn):
        recover_cutting_on_boot(mock_db_conn)

        cursor, calls = _executed(mock_db_conn)
        assert len(calls) == 1
        sql = calls[0][0]
        assert sql.startswith('UPDATE generated_clips')
        assert "status='pending_cut'" in sql
        assert "WHERE status='cutting'" in sql
        mock_db_conn.commit.assert_called_once()


class TestUpdateStatusRenovaUpdatedAt:
    """Sem trigger no banco, a idade dos recoveries depende disto."""

    @pytest.mark.parametrize('kwargs', [{}, {'local_path': '/x.mp4'}, {'clear_local_path': True}])
    def test_updated_at_renovado(self, mock_db_conn, kwargs):
        update_status(mock_db_conn, 'abc', 'transcribing', **kwargs)
        _, calls = _executed(mock_db_conn)
        assert 'updated_at=NOW()' in calls[0][0]


class TestRunRecoveryOnce:
    def _run(self, **kwargs):
        import src.main as main

        conn = MagicMock()
        names = [
            'recover_stuck_downloads',
            'recover_stuck_transcribing',
            'recover_stuck_selecting',
            'recover_stuck_publishing',
            'recover_stuck_cutting',
            'finalize_settled_source_videos',
            'recover_cutting_on_boot',
        ]
        patches = {n: patch.object(main, n) for n in names}
        mocks = {n: p.start() for n, p in patches.items()}
        try:
            with patch.object(main, 'get_db_connection', return_value=conn):
                main.run_recovery_once(**kwargs)
        finally:
            for p in patches.values():
                p.stop()
        return conn, mocks

    def test_periodico_so_recupera_cutting_pelo_tempo_limite(self):
        conn, mocks = self._run()
        mocks['recover_stuck_transcribing'].assert_called_once_with(conn)
        mocks['recover_stuck_publishing'].assert_called_once_with(conn)
        mocks['recover_stuck_cutting'].assert_called_once_with(conn)
        mocks['recover_cutting_on_boot'].assert_not_called()

    def test_finalize_roda_depois_dos_recoveries_de_clip(self):
        import src.main as main

        ordem = []
        conn = MagicMock()
        with patch.object(main, 'get_db_connection', return_value=conn), \
             patch.object(main, 'recover_stuck_downloads'), \
             patch.object(main, 'recover_stuck_transcribing'), \
             patch.object(main, 'recover_stuck_selecting'), \
             patch.object(main, 'recover_stuck_publishing', side_effect=lambda c: ordem.append('publishing')), \
             patch.object(main, 'recover_stuck_cutting', side_effect=lambda c: ordem.append('cutting')), \
             patch.object(main, 'finalize_settled_source_videos', side_effect=lambda c: ordem.append('finalize')):
            main.run_recovery_once()
        assert ordem == ['publishing', 'cutting', 'finalize']

    def test_boot_recupera_cutting(self):
        conn, mocks = self._run(recover_cutting=True)
        mocks['recover_cutting_on_boot'].assert_called_once_with(conn)


class TestPipelineEnabled:
    @pytest.mark.parametrize('value,expected', [
        (None, True), ('true', True), ('1', True), ('false', False), ('0', False), ('off', False),
    ])
    def test_flag(self, monkeypatch, value, expected):
        import src.main as main

        if value is None:
            monkeypatch.delenv('PIPELINE_ENABLED', raising=False)
        else:
            monkeypatch.setenv('PIPELINE_ENABLED', value)
        assert main.pipeline_enabled() is expected

    def test_desligado_nao_roda_ingest_nem_publish(self, monkeypatch):
        import src.main as main

        monkeypatch.setenv('PIPELINE_ENABLED', 'false')
        with patch.object(main, 'run_ingest_cycle') as ingest, \
                patch.object(main, 'run_publish_only') as publish:
            main.run_ingest_if_enabled()
            main.run_publish_if_enabled()
        ingest.assert_not_called()
        publish.assert_not_called()

    def test_ligado_roda_ingest_e_publish(self, monkeypatch):
        import src.main as main

        monkeypatch.setenv('PIPELINE_ENABLED', 'true')
        with patch.object(main, 'run_ingest_cycle') as ingest, \
                patch.object(main, 'run_publish_only') as publish:
            main.run_ingest_if_enabled()
            main.run_publish_if_enabled()
        ingest.assert_called_once()
        publish.assert_called_once()


def test_health_responde_sem_auth_e_sem_dependencias():
    from src.internal_api import app

    app.config['TESTING'] = True
    with app.test_client() as client:
        resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json() == {'status': 'ok'}
