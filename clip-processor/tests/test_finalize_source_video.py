"""
Bug 17 — vídeo em 'selecting' com todos os clips em estado terminal
(rejected/failed) precisa ser encerrado sozinho, liberando a vaga da janela.

Antes, `_maybe_finalize_source_video` só encerrava quando ao menos um clip
tinha sido publicado: vídeo com todos os clips rejeitados segurava a vaga
para sempre.
"""
from unittest.mock import MagicMock, patch

from src.publisher import (
    NON_TERMINAL_CLIP_STATUSES,
    _maybe_finalize_source_video,
    finalize_settled_source_videos,
)


class FakeCursor:
    """Cursor que responde por trecho de SQL e registra tudo que foi executado."""

    def __init__(self, counts, clips, settled=None):
        self.counts = counts
        self.clips = clips
        self.settled = settled or []
        self.executed = []
        self._last = ''

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self._last = sql

    def fetchone(self):
        if 'non_terminal_count' in self._last:
            return self.counts
        return None

    def fetchall(self):
        if 'FROM source_videos' in self._last:
            return self.settled
        if 'clip_path, thumbnail_path' in self._last:
            return self.clips
        return []


def make_conn(counts, clips=None, settled=None):
    cursor = FakeCursor(counts, clips or [], settled)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


def source_update(cursor):
    return [
        (sql, params) for sql, params in cursor.executed
        if sql.startswith('UPDATE source_videos')
    ]


class TestFinalizeSourceVideo:

    def test_todos_rejeitados_apaga_raw_e_libera_vaga(self, tmp_path):
        raw = tmp_path / 'abc.mp4'
        raw.write_bytes(b'raw')
        clip = tmp_path / '101.mp4'
        clip.write_bytes(b'clip')
        conn, cursor = make_conn(
            {'total_count': 3, 'non_terminal_count': 0, 'published_count': 0},
            clips=[{'clip_path': str(clip), 'thumbnail_path': None}],
        )

        assert _maybe_finalize_source_video(conn, 10, str(raw)) is True

        assert not raw.exists()
        assert not clip.exists()
        updates = source_update(cursor)
        assert len(updates) == 1
        sql, params = updates[0]
        assert 'local_path=NULL' in sql
        assert params == ('failed', 10)

    def test_publicado_e_rejeitado_encerra_como_published(self, tmp_path):
        raw = tmp_path / 'abc.mp4'
        raw.write_bytes(b'raw')
        conn, cursor = make_conn(
            {'total_count': 3, 'non_terminal_count': 0, 'published_count': 1},
        )

        assert _maybe_finalize_source_video(conn, 10, str(raw)) is True

        assert not raw.exists()
        assert source_update(cursor)[0][1] == ('published', 10)

    def test_clip_ainda_precisa_do_raw_nao_toca_em_nada(self, tmp_path):
        """pending_cut/cutting contam como não-terminal: raw fica, vaga fica."""
        assert 'pending_cut' in NON_TERMINAL_CLIP_STATUSES
        assert 'cutting' in NON_TERMINAL_CLIP_STATUSES
        raw = tmp_path / 'abc.mp4'
        raw.write_bytes(b'raw')
        conn, cursor = make_conn(
            {'total_count': 3, 'non_terminal_count': 1, 'published_count': 0},
        )

        assert _maybe_finalize_source_video(conn, 10, str(raw)) is False

        assert raw.exists()
        assert source_update(cursor) == []

    def test_video_sem_clip_nao_e_encerrado_aqui(self, tmp_path):
        """Sem clip nenhum é caso do recover_stuck_selecting, não deste."""
        raw = tmp_path / 'abc.mp4'
        raw.write_bytes(b'raw')
        conn, cursor = make_conn(
            {'total_count': 0, 'non_terminal_count': 0, 'published_count': 0},
        )

        assert _maybe_finalize_source_video(conn, 10, str(raw)) is False

        assert raw.exists()
        assert source_update(cursor) == []

    def test_raw_que_nao_saiu_do_disco_nao_atualiza_banco(self, tmp_path):
        """Apagar arquivo antes do banco, e conferir: se o rm falhou, banco fica como está."""
        raw = tmp_path / 'abc.mp4'
        raw.write_bytes(b'raw')
        conn, cursor = make_conn(
            {'total_count': 2, 'non_terminal_count': 0, 'published_count': 0},
        )

        with patch('src.publisher.os.remove', side_effect=OSError('busy')):
            assert _maybe_finalize_source_video(conn, 10, str(raw)) is False

        assert raw.exists()
        assert source_update(cursor) == []


class TestFinalizeSettledSourceVideos:

    def test_varre_selecting_com_clips_todos_terminais(self):
        conn, cursor = make_conn(
            {'total_count': 1, 'non_terminal_count': 0, 'published_count': 0},
            settled=[
                {'id': 1, 'local_path': None},
                {'id': 2, 'local_path': None},
            ],
        )

        assert finalize_settled_source_videos(conn) == 2

        sweep_sql, sweep_params = cursor.executed[0]
        assert "sv.status = 'selecting'" in sweep_sql
        assert 'EXISTS' in sweep_sql and 'NOT EXISTS' in sweep_sql
        assert sweep_params == (NON_TERMINAL_CLIP_STATUSES,)
        assert [p for _, p in source_update(cursor)] == [('failed', 1), ('failed', 2)]

    def test_falha_num_video_nao_impede_os_outros(self):
        conn, _ = make_conn(
            {'total_count': 1, 'non_terminal_count': 0, 'published_count': 0},
            settled=[{'id': 1, 'local_path': None}, {'id': 2, 'local_path': None}],
        )

        calls = []

        def finalize(_conn, vid, _path):
            calls.append(vid)
            if vid == 1:
                raise RuntimeError('db caiu')
            return True

        with patch('src.publisher._maybe_finalize_source_video', side_effect=finalize):
            assert finalize_settled_source_videos(conn) == 1
        assert calls == [1, 2]


def test_recovery_periodico_chama_a_varredura():
    import src.main as main

    conn = MagicMock()
    with patch.object(main, 'get_db_connection', return_value=conn), \
            patch.object(main, 'recover_stuck_downloads'), \
            patch.object(main, 'recover_stuck_selecting'), \
            patch.object(main, 'finalize_settled_source_videos') as sweep:
        main.run_recovery_once()
    sweep.assert_called_once_with(conn)
