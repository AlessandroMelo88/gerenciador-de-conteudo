"""Retenção: leitura da Analytics API, upsert, janela, cota e escopo (SPEC-001)."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src import retention_collector as rc

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)

ORDEM_PADRAO = ['video', 'day', 'views', 'estimatedMinutesWatched', 'averageViewDuration',
                'averageViewPercentage', 'likes', 'comments', 'shares', 'subscribersGained']


def _resposta(linhas, ordem=None):
    """Resposta da API no formato columnHeaders + rows."""
    ordem = ordem or ORDEM_PADRAO
    return {
        'columnHeaders': [{'name': nome} for nome in ordem],
        'rows': [[linha[nome] for nome in ordem] for linha in linhas],
    }


def test_parse_report_mapeia_colunas():
    resposta = _resposta([{
        'video': 'abc123', 'day': '2026-10-01', 'views': 120, 'estimatedMinutesWatched': 40,
        'averageViewDuration': 31, 'averageViewPercentage': 62.5, 'likes': 9, 'comments': 2,
        'shares': 1, 'subscribersGained': 3,
    }])

    linhas = rc.parse_report(resposta)

    assert linhas == [{
        'youtube_video_id': 'abc123', 'date': '2026-10-01', 'views': 120,
        'estimated_minutes_watched': 40, 'average_view_duration': 31,
        'average_view_percentage': 62.5, 'likes': 9, 'comments': 2, 'shares': 1,
        'subscribers_gained': 3,
    }]


def test_parse_report_respeita_ordem_diferente_da_pedida():
    """A API não garante a ordem das colunas; ler por posição gravaria retenção em views."""
    ordem = ['day', 'averageViewPercentage', 'video', 'views', 'estimatedMinutesWatched',
             'averageViewDuration', 'likes', 'comments', 'shares', 'subscribersGained']
    resposta = _resposta([{
        'video': 'xyz', 'day': '2026-10-01', 'views': 10, 'estimatedMinutesWatched': 1,
        'averageViewDuration': 5, 'averageViewPercentage': 88.0, 'likes': 0, 'comments': 0,
        'shares': 0, 'subscribersGained': 0,
    }], ordem=ordem)

    linha = rc.parse_report(resposta)[0]

    assert linha['youtube_video_id'] == 'xyz'
    assert linha['average_view_percentage'] == 88.0
    assert linha['views'] == 10


def test_parse_report_ignora_coluna_desconhecida():
    resposta = {
        'columnHeaders': [{'name': 'video'}, {'name': 'day'}, {'name': 'metricaNova'}],
        'rows': [['abc', '2026-10-01', 7]],
    }

    linha = rc.parse_report(resposta)[0]

    assert linha['youtube_video_id'] == 'abc'
    assert 'metricaNova' not in linha


def test_parse_report_sem_rows_devolve_lista_vazia():
    assert rc.parse_report({'columnHeaders': [], 'rows': []}) == []
    assert rc.parse_report({}) == []
    assert rc.parse_report(None) == []


def _conn_upsert(rowcount):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.rowcount = rowcount
    return conn, cur


_LINHA = {
    'youtube_video_id': 'abc', 'date': '2026-10-01', 'views': 120,
    'estimated_minutes_watched': 40, 'average_view_duration': 31,
    'average_view_percentage': 62.5,
}


def test_upsert_atualiza_quando_o_dia_ja_existe():
    """O YouTube revisa o dado de um dia; coletar de novo atualiza, nunca duplica."""
    conn, cur = _conn_upsert(rowcount=1)  # o UPDATE achou a linha

    gravadas = rc.upsert_linhas(conn, {'abc': 7}, [_LINHA])

    assert gravadas == 1
    sqls = [c.args[0] for c in cur.execute.call_args_list]
    assert any(sql.startswith('UPDATE clip_daily_metrics') for sql in sqls)
    assert not any(sql.startswith('INSERT INTO clip_daily_metrics') for sql in sqls)


def test_upsert_insere_quando_o_dia_e_novo():
    conn, cur = _conn_upsert(rowcount=0)  # o UPDATE não achou nada

    gravadas = rc.upsert_linhas(conn, {'abc': 7}, [_LINHA])

    assert gravadas == 1
    sqls = [c.args[0] for c in cur.execute.call_args_list]
    assert any(sql.startswith('INSERT INTO clip_daily_metrics') for sql in sqls)


def test_upsert_ignora_video_que_nao_e_de_clip_conhecido():
    conn, cur = _conn_upsert(rowcount=0)

    gravadas = rc.upsert_linhas(conn, {'abc': 7}, [{'youtube_video_id': 'outro', 'date': '2026-10-01'}])

    assert gravadas == 0
    assert cur.execute.call_count == 0


def test_upsert_ignora_linha_sem_data():
    conn, cur = _conn_upsert(rowcount=0)

    assert rc.upsert_linhas(conn, {'abc': 7}, [{'youtube_video_id': 'abc'}]) == 0
    assert cur.execute.call_count == 0


def test_upsert_nao_usa_sintaxe_de_um_banco_so():
    """db.py fala PostgreSQL e MySQL: ON CONFLICT / ON DUPLICATE KEY quebrariam em um dos dois."""
    conn, cur = _conn_upsert(rowcount=0)

    rc.upsert_linhas(conn, {'abc': 7}, [_LINHA])

    sqls = ' '.join(c.args[0] for c in cur.execute.call_args_list).upper()
    assert 'ON CONFLICT' not in sqls
    assert 'ON DUPLICATE KEY' not in sqls


@pytest.fixture(autouse=True)
def _limpa_estado(monkeypatch):
    rc._calls_today.clear()
    monkeypatch.delenv('RETENTION_COLLECTOR_ENABLED', raising=False)
    monkeypatch.delenv('RETENTION_MAX_CALLS_PER_CHANNEL_DAY', raising=False)


def _clip(i, *, dias=2, slug='canal-a'):
    return {
        'id': i,
        'youtube_video_id': f'vid{i}',
        'published_at': NOW - timedelta(days=dias),
        'channel_slug': slug,
    }


def _conn_ciclo(rows):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = rows
    cur.rowcount = 0
    return conn


def _service(linhas=None, erro=None):
    """Analytics falso: reports().query(...).execute() devolve columnHeaders + rows."""
    service = MagicMock()
    chamadas = []

    def query(**kw):
        chamadas.append(kw)
        req = MagicMock()
        if erro:
            req.execute.side_effect = erro
        else:
            req.execute.return_value = _resposta(linhas or [])
        return req

    service.reports.return_value.query.side_effect = query
    service.chamadas = chamadas
    return service


def test_ciclo_grava_a_retencao_dos_clips_publicados():
    conn = _conn_ciclo([_clip(7)])
    service = _service([{
        'video': 'vid7', 'day': '2026-10-01', 'views': 120, 'estimatedMinutesWatched': 40,
        'averageViewDuration': 31, 'averageViewPercentage': 62.5, 'likes': 9, 'comments': 2,
        'shares': 1, 'subscribersGained': 3,
    }])

    gravadas = rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda slug: service)

    assert gravadas == 1
    assert service.chamadas[0]['ids'] == 'channel==MINE'
    assert 'averageViewPercentage' in service.chamadas[0]['metrics']
    assert service.chamadas[0]['dimensions'] == 'video,day'
    # O dia corrente ainda não fechou na Analytics: a janela termina ontem.
    assert service.chamadas[0]['endDate'] == '2026-10-01'


def test_desligado_por_env_nao_chama_a_api(monkeypatch):
    monkeypatch.setenv('RETENTION_COLLECTOR_ENABLED', 'false')
    conn = _conn_ciclo([_clip(7)])
    service = _service()

    assert rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service) == 0
    assert service.chamadas == []


def test_token_sem_escopo_de_analytics_nao_derruba_o_ciclo():
    """Estado real de produção até o dono re-autorizar: a chamada falha e o pipeline segue."""
    conn = _conn_ciclo([_clip(7)])
    service = _service(erro=Exception(
        'insufficientPermissions: Request had insufficient authentication scopes.'))

    assert rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service) == 0


def test_credencial_ausente_nao_derruba_o_ciclo():
    conn = _conn_ciclo([_clip(7)])

    def service_for(slug):
        raise FileNotFoundError('Token OAuth não encontrado')

    assert rc.run_retention_collection_once(conn=conn, now=NOW, service_for=service_for) == 0


def test_dia_sem_audiencia_nao_vira_linha_zerada():
    """A API simplesmente não devolve linha; gravar zero mentiria sobre a medição."""
    conn = _conn_ciclo([_clip(7)])
    service = _service([])

    assert rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service) == 0
    cur = conn.cursor.return_value.__enter__.return_value
    sqls = ' '.join(str(c.args[0]) for c in cur.execute.call_args_list)
    assert 'INSERT INTO clip_daily_metrics' not in sqls


def test_teto_de_chamadas_por_canal_interrompe_o_canal(monkeypatch):
    monkeypatch.setenv('RETENTION_MAX_CALLS_PER_CHANNEL_DAY', '1')
    conn = _conn_ciclo([_clip(i) for i in range(1, 120)])  # mais de um lote de 50
    service = _service([])

    rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service)

    assert len(service.chamadas) == 1


def test_clip_mais_velho_que_a_janela_nao_entra():
    conn = _conn_ciclo([])
    service = _service([])

    rc.run_retention_collection_once(conn=conn, now=NOW, service_for=lambda s: service)

    cur = conn.cursor.return_value.__enter__.return_value
    corte = cur.execute.call_args_list[0].args[1][-1]
    assert corte == NOW - timedelta(days=rc.STOP_DAYS)


def test_cada_canal_usa_sua_propria_credencial():
    conn = _conn_ciclo([_clip(1, slug='canal-a'), _clip(2, slug='canal-b')])
    pedidos = []

    def service_for(slug):
        pedidos.append(slug)
        return _service([])

    rc.run_retention_collection_once(conn=conn, now=NOW, service_for=service_for)

    assert sorted(pedidos) == ['canal-a', 'canal-b']


def test_scheduler_agenda_a_coleta_de_retencao_uma_vez_por_dia():
    """A Analytics consolida por dia; coletar de hora em hora só gastaria cota."""
    import src.main as main

    jobs = {j.id: j for j in main.scheduler.get_jobs()}

    assert 'retention_collector' in jobs, 'o job de retenção não foi agendado'
    assert jobs['retention_collector'].trigger.interval == timedelta(hours=24)
