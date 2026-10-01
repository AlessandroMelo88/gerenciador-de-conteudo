"""Coleta de métricas: lotes de 50, falha de API, clip sem video_id e frequência."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src import metrics_collector as mc

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _limpa_estado(monkeypatch):
    mc._calls_today.clear()
    monkeypatch.delenv('METRICS_COLLECTOR_ENABLED', raising=False)
    monkeypatch.delenv('METRICS_MAX_CALLS_PER_CHANNEL_DAY', raising=False)


def _clip(i, *, age=timedelta(hours=2), last=None, slug='canal-a', vid='auto'):
    return {
        'id': i,
        'youtube_video_id': f'vid{i}' if vid == 'auto' else vid,
        'published_at': NOW - age,
        'channel_slug': slug,
        'last_collected': last,
    }


def _conn(rows):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = rows
    return conn, cur


def _service(items_for=None, error=None):
    """YouTube falso: videos().list(...).execute() devolve statistics dos ids pedidos."""
    service = MagicMock()
    calls = []

    def list_(**kw):
        calls.append(kw)
        req = MagicMock()
        if error:
            req.execute.side_effect = error
        else:
            ids = kw['id'].split(',')
            req.execute.return_value = {'items': [
                {'id': v, 'statistics': {'viewCount': '10', 'likeCount': '2', 'commentCount': '1'}}
                for v in ids
            ]}
        return req

    service.videos.return_value.list.side_effect = list_
    service.calls = calls
    return service


def _inserts(cur):
    return [c for c in cur.execute.call_args_list if 'INSERT INTO clip_metrics' in c[0][0]]


class TestFrequencia:
    def test_nunca_coletado_esta_devido(self):
        assert mc.is_due(NOW - timedelta(hours=1), None, NOW)

    def test_fresco_espera_6h(self):
        pub = NOW - timedelta(days=2)
        assert not mc.is_due(pub, NOW - timedelta(hours=3), NOW)
        assert mc.is_due(pub, NOW - timedelta(hours=6), NOW)

    def test_fresco_tolera_folga_de_minutos(self):
        assert mc.is_due(NOW - timedelta(days=2), NOW - timedelta(hours=5, minutes=57), NOW)

    def test_mais_velho_que_7_dias_coleta_1x_por_dia(self):
        pub = NOW - timedelta(days=10)
        assert not mc.is_due(pub, NOW - timedelta(hours=12), NOW)
        assert mc.is_due(pub, NOW - timedelta(hours=24), NOW)

    def test_para_apos_30_dias(self):
        assert not mc.is_due(NOW - timedelta(days=31), None, NOW)
        assert mc.is_due(NOW - timedelta(days=29), None, NOW)

    def test_sem_published_at_nao_coleta(self):
        assert not mc.is_due(None, None, NOW)

    def test_datas_naive_sao_tratadas_como_utc(self):
        naive = (NOW - timedelta(hours=1)).replace(tzinfo=None)
        assert mc.is_due(naive, None, NOW)


class TestColeta:
    def test_grava_uma_linha_por_clip(self):
        conn, cur = _conn([_clip(1), _clip(2)])
        svc = _service()
        total = mc.run_metrics_collection_once(conn, NOW, lambda slug: svc)
        assert total == 2
        ins = _inserts(cur)
        assert [c[0][1] for c in ins] == [(1, NOW, 10, 2, 1), (2, NOW, 10, 2, 1)]
        conn.commit.assert_called()
        assert svc.calls[0]['part'] == 'statistics'

    def test_lotes_de_50(self):
        conn, cur = _conn([_clip(i) for i in range(1, 121)])
        svc = _service()
        total = mc.run_metrics_collection_once(conn, NOW, lambda slug: svc)
        assert total == 120
        assert [len(c['id'].split(',')) for c in svc.calls] == [50, 50, 20]

    def test_clip_sem_video_id_nao_vai_para_a_api(self):
        conn, cur = _conn([_clip(1, vid=None), _clip(2, vid=''), _clip(3)])
        svc = _service()
        mc.run_metrics_collection_once(conn, NOW, lambda slug: svc)
        assert svc.calls[0]['id'] == 'vid3'
        # a consulta ainda filtra no banco o que é nulo ou vazio
        sql = cur.execute.call_args_list[0][0][0]
        assert 'youtube_video_id IS NOT NULL' in sql

    def test_so_clips_devidos(self):
        conn, _ = _conn([_clip(1, last=NOW - timedelta(hours=1)), _clip(2)])
        svc = _service()
        mc.run_metrics_collection_once(conn, NOW, lambda slug: svc)
        assert svc.calls[0]['id'] == 'vid2'

    def test_nada_devido_nao_chama_api(self):
        conn, _ = _conn([_clip(1, last=NOW - timedelta(hours=1))])
        called = []
        assert mc.run_metrics_collection_once(conn, NOW, lambda s: called.append(s)) == 0
        assert called == []

    def test_agrupa_por_canal_e_usa_credencial_de_cada_um(self):
        conn, _ = _conn([_clip(1, slug='a'), _clip(2, slug='b'), _clip(3, slug=None)])
        pedidos = []

        def service_for(slug):
            pedidos.append(slug)
            return _service()

        assert mc.run_metrics_collection_once(conn, NOW, service_for) == 3
        assert sorted(pedidos, key=str) == [None, 'a', 'b']

    def test_estatistica_oculta_vira_null(self):
        conn, cur = _conn([_clip(1)])
        svc = MagicMock()
        svc.videos.return_value.list.return_value.execute.return_value = {
            'items': [{'id': 'vid1', 'statistics': {'viewCount': '77'}}]}
        mc.run_metrics_collection_once(conn, NOW, lambda s: svc)
        assert _inserts(cur)[0][0][1] == (1, NOW, 77, None, None)

    def test_video_ausente_na_resposta_e_ignorado(self):
        conn, cur = _conn([_clip(1), _clip(2)])
        svc = MagicMock()
        svc.videos.return_value.list.return_value.execute.return_value = {
            'items': [{'id': 'vid2', 'statistics': {'viewCount': '5'}}]}
        assert mc.run_metrics_collection_once(conn, NOW, lambda s: svc) == 1


class TestResiliencia:
    def test_falha_da_api_nao_levanta_e_nao_grava(self):
        conn, cur = _conn([_clip(1)])
        svc = _service(error=RuntimeError('quotaExceeded'))
        assert mc.run_metrics_collection_once(conn, NOW, lambda s: svc) == 0
        assert _inserts(cur) == []

    def test_falha_em_um_lote_nao_impede_os_seguintes(self):
        conn, _ = _conn([_clip(i) for i in range(1, 61)])
        svc = MagicMock()
        ok = {'items': [{'id': f'vid{i}', 'statistics': {'viewCount': '1'}} for i in range(51, 61)]}
        svc.videos.return_value.list.return_value.execute.side_effect = [RuntimeError('boom'), ok]
        assert mc.run_metrics_collection_once(conn, NOW, lambda s: svc) == 10

    def test_credencial_ausente_pula_o_canal_e_segue_com_os_outros(self):
        conn, _ = _conn([_clip(1, slug='sem-token'), _clip(2, slug='ok')])

        def service_for(slug):
            if slug == 'sem-token':
                raise FileNotFoundError('token')
            return _service()

        assert mc.run_metrics_collection_once(conn, NOW, service_for) == 1

    def test_falha_de_banco_nao_levanta(self):
        conn = MagicMock()
        conn.cursor.side_effect = RuntimeError('db fora')
        assert mc.run_metrics_collection_once(conn, NOW, lambda s: _service()) == 0

    def test_falha_ao_gravar_faz_rollback_e_segue(self):
        conn, cur = _conn([_clip(1)])
        cur.execute.side_effect = [None, RuntimeError('tabela inexistente')]
        assert mc.run_metrics_collection_once(conn, NOW, lambda s: _service()) == 0
        conn.rollback.assert_called()

    def test_teto_diario_de_chamadas_por_canal(self, monkeypatch):
        monkeypatch.setenv('METRICS_MAX_CALLS_PER_CHANNEL_DAY', '1')
        conn, _ = _conn([_clip(i) for i in range(1, 101)])
        svc = _service()
        assert mc.run_metrics_collection_once(conn, NOW, lambda s: svc) == 50
        assert len(svc.calls) == 1

    def test_desligado_por_env_nao_faz_nada(self, monkeypatch):
        monkeypatch.setenv('METRICS_COLLECTOR_ENABLED', 'false')
        conn, _ = _conn([_clip(1)])
        assert mc.run_metrics_collection_once(conn, NOW, lambda s: _service()) == 0
        conn.cursor.assert_not_called()


def test_job_registrado_no_scheduler():
    pytest.importorskip('flask')
    import src.main as m
    ids = [j.id for j in m.scheduler.get_jobs()]
    assert 'metrics_collector' in ids
