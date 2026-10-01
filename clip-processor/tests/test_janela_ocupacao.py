"""Bug 17 — decisão registrada: a ocupação da janela CONTA clip em 'pending'.

Clip aguardando aprovação mantém em disco o raw do vídeo-fonte e os arquivos do
clip (o raw só sai em `_maybe_finalize_source_video`). Parar de contar `pending`
reabriria a ingestão sem teto de disco — a causa do bug 12 (306 vídeos, disco
cheio). A trava é política; o que o operador precisa é ser avisado (watchdog,
`download_window_waiting_approval`) e o TTL de 48h rejeita o que ninguém decide.

Este teste fixa a regra: se alguém tirar `pending` da conta, ele quebra e manda
ler este docstring e o bug 17 em Docs/operacao/BUGS.md.
"""
from unittest.mock import MagicMock

from src.pipeline_runner import _select_pending_videos


def _sqls_de_ocupacao():
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    # mesma linha serve às duas consultas: canais destino e ocupação por canal
    cur.fetchall.return_value = [{'niche': 'futebol', 'n': 1, 'channel_id': 1, 'c': 99}]
    cur.fetchone.return_value = {'c': 1}
    conn = MagicMock()
    conn.cursor.return_value = cur
    _select_pending_videos(conn)
    return [c.args[0] for c in cur.execute.call_args_list if 'COUNT(DISTINCT sv.id)' in c.args[0]]


def test_ocupacao_conta_clip_pending_e_estados_ativos():
    sqls = _sqls_de_ocupacao()
    assert sqls, 'a consulta de ocupação deixou de existir'
    for sql in sqls:
        assert "gc.status IN ('pending_cut', 'pending', 'cutting', 'approved')" in sql
        assert 'sv.local_path IS NOT NULL' in sql
        assert "'selecting'" in sql
