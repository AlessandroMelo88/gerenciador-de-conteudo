"""
Testes para pipeline_runner.py — ciclo completo do pipeline.
"""
import pytest
from unittest.mock import MagicMock, patch, call

from src.pipeline_runner import (
    run_pipeline_once,
    run_ingest_cycle,
    _discard_failed_download,
    _download_pending_videos,
    _select_pending_videos,
    _niche_windows,
    CANDIDATES_PER_SLOT,
    DOWNLOAD_WINDOW_FUTEBOL,
    DOWNLOAD_WINDOW_POLITICA,
    DOWNLOAD_WINDOW_PER_CHANNEL,
)


@pytest.fixture(autouse=True)
def _janela_fixa(request):
    """Isola os testes da consulta a destination_channels: 1 canal por nicho."""
    if request.node.cls is TestNicheWindows:
        yield
        return
    with patch('src.pipeline_runner._niche_windows',
               return_value=[('futebol', DOWNLOAD_WINDOW_FUTEBOL), ('politica', DOWNLOAD_WINDOW_POLITICA)]):
        yield


class TestNicheWindows:
    """Teto = DOWNLOAD_WINDOW_PER_CHANNEL por canal destino ativo do nicho."""

    def _conn(self, rows=None, error=None):
        cur = MagicMock()
        if error:
            cur.execute.side_effect = error
        cur.fetchall.return_value = rows
        cur.__enter__ = lambda s: s
        cur.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cur
        return conn

    def test_dez_por_canal_destino_ativo(self):
        conn = self._conn([{'niche': 'politica', 'n': 1}, {'niche': 'futebol', 'n': 1}])
        assert _niche_windows(conn) == [
            ('futebol', DOWNLOAD_WINDOW_PER_CHANNEL),
            ('politica', DOWNLOAD_WINDOW_PER_CHANNEL),
        ]

    def test_canal_novo_soma_mais_dez(self):
        conn = self._conn([{'niche': 'futebol', 'n': 2}, {'niche': 'politica', 'n': 1}])
        assert dict(_niche_windows(conn)) == {
            'futebol': 2 * DOWNLOAD_WINDOW_PER_CHANNEL,
            'politica': DOWNLOAD_WINDOW_PER_CHANNEL,
        }

    def test_total_com_dois_canais_e_vinte(self):
        conn = self._conn([{'niche': 'futebol', 'n': 1}, {'niche': 'politica', 'n': 1}])
        assert sum(w for _, w in _niche_windows(conn)) == 20

    def test_sem_canal_destino_ativo_nao_baixa(self):
        assert _niche_windows(self._conn([])) == []

    def test_falha_na_consulta_usa_padrao(self):
        conn = self._conn(error=RuntimeError('db fora'))
        assert _niche_windows(conn) == [('futebol', DOWNLOAD_WINDOW_FUTEBOL), ('politica', DOWNLOAD_WINDOW_POLITICA)]


class TestRunPipelineOnce:
    def test_calls_poll_then_download_then_publish(self):
        """Deve chamar poll → download → publish em ordem."""
        call_order = []

        def fake_poll(**kwargs):
            call_order.append('poll')

        def fake_download(conn):
            call_order.append('download')

        def fake_publish(conn, redis, **kwargs):
            call_order.append('publish')
            return 0

        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels', side_effect=fake_poll), \
             patch('src.pipeline_runner._download_pending_videos', side_effect=fake_download), \
             patch('src.pipeline_runner.publish_pending_clips', side_effect=fake_publish), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

        assert call_order == ['poll', 'download', 'publish']

    def test_reuses_injected_db_and_redis(self):
        """Conexões injetadas devem ser passadas para os sub-módulos."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels') as mock_poll, \
             patch('src.pipeline_runner._download_pending_videos'), \
             patch('src.pipeline_runner.publish_pending_clips') as mock_pub, \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

        # poll_all_channels deve receber a conexão injetada
        mock_poll.assert_called_once_with(db_conn=mock_conn, redis_client=mock_redis)

        # publish_pending_clips deve receber conn e redis
        pub_args = mock_pub.call_args
        assert pub_args[0][0] is mock_conn
        assert pub_args[0][1] is mock_redis

    def test_does_not_close_injected_db_connection(self):
        """Conexão injetada não deve ser fechada pelo runner (responsabilidade do caller)."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner._download_pending_videos'), \
             patch('src.pipeline_runner.publish_pending_clips'), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

        mock_conn.close.assert_not_called()

    def test_publish_failure_does_not_propagate(self):
        """Erro em publish_pending_clips não deve propagar — scheduler continua."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner._download_pending_videos'), \
             patch('src.pipeline_runner.publish_pending_clips',
                   side_effect=Exception('publish bombed')), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

    def test_poll_failure_does_not_skip_publish(self):
        """Erro em poll_all_channels não deve impedir tentativa de publicação."""
        call_order = []

        mock_conn = MagicMock()
        mock_redis = MagicMock()

        def fake_poll(**kwargs):
            call_order.append('poll_failed')
            raise Exception('poll bombed')

        def fake_publish(conn, redis, **kwargs):
            call_order.append('publish')
            return 0

        with patch('src.pipeline_runner.poll_all_channels', side_effect=fake_poll), \
             patch('src.pipeline_runner._download_pending_videos'), \
             patch('src.pipeline_runner.publish_pending_clips', side_effect=fake_publish), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

        assert 'poll_failed' in call_order
        assert 'publish' in call_order

    def test_creates_own_connection_when_none_injected(self):
        """Sem injeção, deve criar e fechar a própria conexão."""
        mock_conn = MagicMock()
        mock_redis_instance = MagicMock()

        with patch('src.pipeline_runner.get_db_connection', return_value=mock_conn) as mock_get_db, \
             patch('src.pipeline_runner.redis_lib.Redis', return_value=mock_redis_instance), \
             patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner._download_pending_videos'), \
             patch('src.pipeline_runner.publish_pending_clips'), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once()

        mock_get_db.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_download_failure_does_not_propagate(self):
        """Erro em _download_pending_videos não deve propagar."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner._download_pending_videos',
                   side_effect=Exception('disk full')), \
             patch('src.pipeline_runner.publish_pending_clips', return_value=0), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)


class TestSelectPendingVideos:
    """Testes para _select_pending_videos — janela por nicho e justiça por canal."""

    def _make_cursor(self, fetchone_results, fetchall_results):
        cur = MagicMock()
        cur.fetchone.side_effect = fetchone_results
        cur.fetchall.side_effect = fetchall_results
        cur.__enter__ = lambda s: s
        cur.__exit__ = MagicMock(return_value=False)
        return cur

    def _ocupacao(self, por_canal: dict):
        """Linhas do COUNT agrupado por canal de origem."""
        return [{'channel_id': cid, 'c': n} for cid, n in por_canal.items()]

    def _vid(self, youtube_video_id, channel_id=1):
        return {'youtube_video_id': youtube_video_id, 'channel_id': channel_id}

    def test_empty_window_fills_up_to_ceiling(self):
        """Janela vazia (sem ocupação) deve buscar até o teto de cada nicho."""
        mock_conn = MagicMock()
        futebol_vids = [self._vid('fut1', 1), self._vid('fut2', 2)]
        politica_vids = [self._vid('pol1', 3), self._vid('pol2', 4), self._vid('pol3', 5)]
        cur = self._make_cursor(
            fetchone_results=[{'c': 9}, {'c': 9}],  # canais de origem ativos por nicho
            fetchall_results=[[], futebol_vids, [], politica_vids],
        )
        mock_conn.cursor.return_value = cur

        result = _select_pending_videos(mock_conn)

        assert result == ['fut1', 'fut2', 'pol1', 'pol2', 'pol3']

    def test_full_window_skips_niche_entirely(self):
        """Nicho já na janela cheia não gera SELECT de candidatos nem consulta o teto."""
        mock_conn = MagicMock()
        cur = self._make_cursor(
            fetchone_results=[{'c': 9}],
            fetchall_results=[
                self._ocupacao({1: DOWNLOAD_WINDOW_FUTEBOL}),  # futebol cheio
                [],                                            # politica vazia
                [self._vid('pol1', 3)],
            ],
        )
        mock_conn.cursor.return_value = cur

        result = _select_pending_videos(mock_conn)

        assert result == ['pol1']
        # futebol: só o COUNT. politica: COUNT + canais ativos + SELECT = 4 execute
        assert cur.execute.call_count == 4

    def test_deficit_limits_query_to_missing_slots(self):
        """Déficit de 1 vaga pede candidatos suficientes pra intercalar, mas devolve 1."""
        mock_conn = MagicMock()
        cur = self._make_cursor(
            fetchone_results=[{'c': 9}],
            fetchall_results=[
                self._ocupacao({1: DOWNLOAD_WINDOW_FUTEBOL - 1}),
                [self._vid('fut1', 2), self._vid('fut2', 3)],
                self._ocupacao({4: DOWNLOAD_WINDOW_POLITICA}),
            ],
        )
        mock_conn.cursor.return_value = cur

        result = _select_pending_videos(mock_conn)

        assert result == ['fut1']
        select_call = cur.execute.call_args_list[2]
        assert select_call.args[1][-1] == 1 * CANDIDATES_PER_SLOT

    def test_filters_by_freshness_cutoff(self):
        """SELECT deve restringir a published_at de até FRESHNESS_DAYS dias atrás."""
        from datetime import datetime, timedelta
        from src.pipeline_runner import SAO_PAULO_TZ, FRESHNESS_DAYS

        mock_conn = MagicMock()
        cur = self._make_cursor(
            fetchone_results=[{'c': 9}],
            fetchall_results=[[], [], self._ocupacao({1: DOWNLOAD_WINDOW_POLITICA})],
        )
        mock_conn.cursor.return_value = cur

        _select_pending_videos(mock_conn)

        expected_cutoff = (datetime.now(SAO_PAULO_TZ) - timedelta(days=FRESHNESS_DAYS)).date()
        select_call = cur.execute.call_args_list[2]
        assert select_call.args[1][2] == expected_cutoff

    def test_canal_prolifico_nao_toma_a_janela_inteira(self):
        """10 vagas livres e 2 canais ativos: cada canal leva no máximo 5, intercalando."""
        mock_conn = MagicMock()
        prolifico = [self._vid(f'p{i}', 7) for i in range(10)]
        pequeno = [self._vid('q1', 8), self._vid('q2', 8)]
        cur = self._make_cursor(
            fetchone_results=[{'c': 2}],
            fetchall_results=[
                [],                       # futebol sem ocupação
                prolifico + pequeno,      # candidatos: canal 7 domina a ordem do SQL
                self._ocupacao({1: DOWNLOAD_WINDOW_POLITICA}),  # politica cheia
            ],
        )
        mock_conn.cursor.return_value = cur

        result = _select_pending_videos(mock_conn)

        assert result.count('q1') == 1 and result.count('q2') == 1
        do_prolifico = [v for v in result if v.startswith('p')]
        assert len(do_prolifico) == 5, 'canal prolífico passou do teto de 5 vagas'
        assert result[:2] == ['p0', 'q1'], 'não intercalou os canais'

    def test_canal_que_ja_ocupa_vaga_escolhe_depois(self):
        """Quem já tem vídeo na janela perde a vez para quem não tem (anti-fome)."""
        mock_conn = MagicMock()
        cur = self._make_cursor(
            fetchone_results=[{'c': 2}],
            fetchall_results=[
                self._ocupacao({7: 3}),
                [self._vid('p1', 7), self._vid('q1', 8)],
                self._ocupacao({1: DOWNLOAD_WINDOW_POLITICA}),
            ],
        )
        mock_conn.cursor.return_value = cur

        result = _select_pending_videos(mock_conn)

        assert result[0] == 'q1'


class TestDownloadPendingVideos:
    def _make_cursor_with_side_effect(self, fetchone_results, fetchall_results):
        """Cursor fake cujo fetchone e fetchall caem num default depois da lista informada."""
        pending_one = list(fetchone_results)
        pending_all = list(fetchall_results)

        def _fetchone():
            return pending_one.pop(0) if pending_one else {'paused': 0, 'c': 0}

        def _fetchall():
            return pending_all.pop(0) if pending_all else []

        cur = MagicMock()
        cur.fetchone.side_effect = _fetchone
        cur.fetchall.side_effect = _fetchall
        cur.__enter__ = lambda s: s
        cur.__exit__ = MagicMock(return_value=False)
        return cur

    def test_successful_download_updates_status_to_downloaded(self):
        """Download bem-sucedido deve atualizar status para downloaded com local_path."""
        mock_conn = MagicMock()
        cur = self._make_cursor_with_side_effect(
            fetchone_results=[{'c': 0}, {'c': 0}],
            fetchall_results=[[], [], [{'youtube_video_id': 'abc123', 'channel_id': 1}]],
        )
        mock_conn.cursor.return_value = cur

        with patch('src.pipeline_runner.download_video', return_value=True) as mock_dl, \
             patch('src.pipeline_runner.update_status') as mock_upd:
            _download_pending_videos(mock_conn)

        mock_upd.assert_any_call(mock_conn, 'abc123', 'downloading')
        mock_upd.assert_any_call(mock_conn, 'abc123', 'downloaded',
                                  local_path='/app/videos/abc123.mp4')

    def test_failed_download_updates_status_to_failed(self):
        """Download falho deve marcar failed já limpando local_path (libera a vaga)."""
        mock_conn = MagicMock()
        cur = self._make_cursor_with_side_effect(
            fetchone_results=[{'c': 0}, {'c': 0}],
            fetchall_results=[[], [], [{'youtube_video_id': 'xyz999', 'channel_id': 1}]],
        )
        mock_conn.cursor.return_value = cur

        with patch('src.pipeline_runner.download_video', return_value=False), \
             patch('src.pipeline_runner.update_status') as mock_upd:
            _download_pending_videos(mock_conn)

        mock_upd.assert_any_call(mock_conn, 'xyz999', 'failed', clear_local_path=True)

    def test_no_pending_videos_does_nothing(self):
        """Sem vídeos pending, não deve chamar download_video."""
        mock_conn = MagicMock()
        cur = self._make_cursor_with_side_effect(
            fetchone_results=[{'c': 0}, {'c': 0}],
            fetchall_results=[[], [], []],
        )
        mock_conn.cursor.return_value = cur

        with patch('src.pipeline_runner.download_video') as mock_dl:
            _download_pending_videos(mock_conn)

        mock_dl.assert_not_called()

    def test_window_full_does_nothing(self):
        """Janela já cheia nos dois nichos não deve chamar download_video."""
        mock_conn = MagicMock()
        cur = self._make_cursor_with_side_effect(
            fetchone_results=[{'c': DOWNLOAD_WINDOW_FUTEBOL}, {'c': DOWNLOAD_WINDOW_POLITICA}],
            fetchall_results=[[]],
        )
        mock_conn.cursor.return_value = cur

        with patch('src.pipeline_runner.download_video') as mock_dl:
            _download_pending_videos(mock_conn)

        mock_dl.assert_not_called()

    def test_downloads_futebol_then_politica_in_sequence(self):
        """Ordem fixa: repõe futebol primeiro, depois política."""
        mock_conn = MagicMock()
        futebol_vids = [
            {'youtube_video_id': 'fut1', 'channel_id': 1},
            {'youtube_video_id': 'fut2', 'channel_id': 2},
        ]
        politica_vids = [
            {'youtube_video_id': 'pol1', 'channel_id': 3},
            {'youtube_video_id': 'pol2', 'channel_id': 4},
            {'youtube_video_id': 'pol3', 'channel_id': 5},
        ]
        cur = self._make_cursor_with_side_effect(
            fetchone_results=[{'c': 9}, {'c': 9}],
            fetchall_results=[[], [], futebol_vids, [], politica_vids],
        )
        mock_conn.cursor.return_value = cur

        with patch('src.pipeline_runner.download_video', return_value=True) as mock_dl, \
             patch('src.pipeline_runner.update_status'):
            _download_pending_videos(mock_conn)

        downloaded_order = [call.args[0] for call in mock_dl.call_args_list]
        assert downloaded_order == ['fut1', 'fut2', 'pol1', 'pol2', 'pol3']

    def test_scheduler_compatible_coalesce(self):
        """Importar main.py não deve iniciar o scheduler (coalesce = True verificado via import)."""
        pytest.importorskip('flask')
        import src.main as main_module

        job = None
        for j in main_module.scheduler.get_jobs():
            if j.id == 'ingest_cycle':
                job = j
                break

        assert job is not None, 'Job ingest_cycle não encontrado no scheduler'
        assert job.coalesce is True, 'coalesce deve ser True'
        assert job.max_instances == 1, 'max_instances deve ser 1'


class TestDiscardFailedDownload:
    """Download falho não pode deixar arquivo em disco nem local_path preenchido.

    A janela de download conta `local_path IS NOT NULL`, então 'failed' com a
    coluna suja ocupava vaga pra sempre e travava o pipeline inteiro.
    """

    def _make_conn(self, clips_need_raw=0):
        cur = MagicMock()
        cur.fetchone.side_effect = lambda: {'paused': 0, 'c': clips_need_raw}
        cur.__enter__ = lambda s: s
        cur.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cur
        return conn

    def test_removes_raw_file_and_clears_local_path(self, tmp_path):
        """Arquivo parcial em disco é apagado ANTES do UPDATE, e local_path vira NULL."""
        raw = tmp_path / 'xyz999.mp4'
        raw.write_bytes(b'parcial')
        part = tmp_path / 'xyz999.mp4.part'
        part.write_bytes(b'frag')
        conn = self._make_conn()

        seen_on_update = {}

        def fake_update(*args, **kwargs):
            seen_on_update['file_existed'] = raw.exists()

        with patch('src.pipeline_runner.VIDEOS_DIR', str(tmp_path)), \
             patch('src.pipeline_runner.update_status', side_effect=fake_update) as mock_upd:
            _discard_failed_download(conn, 'xyz999')

        assert not raw.exists(), 'raw deveria ter sido apagado'
        assert not part.exists(), 'artefato .part deveria ter sido apagado'
        assert seen_on_update['file_existed'] is False, 'apagar disco vem antes do UPDATE'
        mock_upd.assert_called_once_with(conn, 'xyz999', 'failed', clear_local_path=True)

    def test_missing_file_still_clears_local_path(self, tmp_path):
        """Sem arquivo em disco (falha antes de escrever nada), segue e limpa a coluna."""
        conn = self._make_conn()

        with patch('src.pipeline_runner.VIDEOS_DIR', str(tmp_path)), \
             patch('src.pipeline_runner.update_status') as mock_upd:
            _discard_failed_download(conn, 'nada404')

        mock_upd.assert_called_once_with(conn, 'nada404', 'failed', clear_local_path=True)

    def test_keeps_local_path_when_file_removal_fails(self, tmp_path):
        """Se o arquivo sobrevive à remoção, não limpa local_path — banco não divergir do disco."""
        raw = tmp_path / 'trava01.mp4'
        raw.write_bytes(b'preso')
        conn = self._make_conn()

        with patch('src.pipeline_runner.VIDEOS_DIR', str(tmp_path)), \
             patch('src.pipeline_runner._cleanup_partial'), \
             patch('src.pipeline_runner.update_status') as mock_upd:
            _discard_failed_download(conn, 'trava01')

        assert raw.exists()
        mock_upd.assert_called_once_with(conn, 'trava01', 'failed')

    def test_preserves_raw_when_clips_still_need_it(self, tmp_path):
        """Clip em pending_cut/cutting ainda lê o raw — não apaga nem zera local_path."""
        raw = tmp_path / 'vivo123.mp4'
        raw.write_bytes(b'necessario')
        conn = self._make_conn(clips_need_raw=1)

        with patch('src.pipeline_runner.VIDEOS_DIR', str(tmp_path)), \
             patch('src.pipeline_runner.update_status') as mock_upd:
            _discard_failed_download(conn, 'vivo123')

        assert raw.exists(), 'raw de clip em corte não pode ser apagado'
        mock_upd.assert_called_once_with(conn, 'vivo123', 'failed')


class TestRunIngestCycle:
    def test_calls_poll_then_download_in_order(self):
        """Deve chamar poll → download em ordem, sem publish."""
        call_order = []

        def fake_poll(**kwargs):
            call_order.append('poll')

        def fake_download(conn):
            call_order.append('download')

        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels', side_effect=fake_poll), \
             patch('src.pipeline_runner._download_pending_videos', side_effect=fake_download), \
             patch('src.pipeline_runner.publish_pending_clips') as mock_pub:
            run_ingest_cycle(db_conn=mock_conn, redis_client=mock_redis)

        assert call_order == ['poll', 'download']
        mock_pub.assert_not_called()

    def test_download_failure_does_not_propagate(self):
        """Erro em _download_pending_videos não deve propagar."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner._download_pending_videos',
                   side_effect=Exception('disk full')):
            run_ingest_cycle(db_conn=mock_conn, redis_client=mock_redis)

    def test_poll_failure_does_not_skip_download(self):
        """Erro em poll_all_channels não deve impedir tentativa de download."""
        call_order = []
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        def fake_poll(**kwargs):
            call_order.append('poll_failed')
            raise Exception('poll bombed')

        def fake_download(conn):
            call_order.append('download')

        with patch('src.pipeline_runner.poll_all_channels', side_effect=fake_poll), \
             patch('src.pipeline_runner._download_pending_videos', side_effect=fake_download):
            run_ingest_cycle(db_conn=mock_conn, redis_client=mock_redis)

        assert call_order == ['poll_failed', 'download']

    def test_creates_own_connection_when_none_injected(self):
        """Sem injeção, deve criar e fechar a própria conexão."""
        mock_conn = MagicMock()
        mock_redis_instance = MagicMock()

        with patch('src.pipeline_runner.get_db_connection', return_value=mock_conn) as mock_get_db, \
             patch('src.pipeline_runner.redis_lib.Redis', return_value=mock_redis_instance), \
             patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner._download_pending_videos'):
            run_ingest_cycle()

        mock_get_db.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_does_not_close_injected_db_connection(self):
        """Conexão injetada não deve ser fechada pelo runner."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner._download_pending_videos'):
            run_ingest_cycle(db_conn=mock_conn, redis_client=mock_redis)

        mock_conn.close.assert_not_called()
