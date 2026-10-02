"""Retenção: leitura da Analytics API, upsert, janela, cota e escopo (SPEC-001)."""
from datetime import datetime, timezone
from unittest.mock import MagicMock

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
