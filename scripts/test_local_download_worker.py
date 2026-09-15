"""Testes da janela de download do local_download_worker.

Rodar: python3 -m pytest scripts/test_local_download_worker.py -q
"""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    'local_download_worker', Path(__file__).with_name('local_download_worker.py')
)
worker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(worker)


class FakeRemote:
    """Responde às queries do worker: contagem da janela e lista de pendentes."""

    def __init__(self, occupancy, pending_rows=3, channels=None):
        self.occupancy = occupancy
        self.channels = channels if channels is not None else {'politica': 1, 'futebol': 1}
        self.pending_rows = pending_rows
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        if query.startswith('UPDATE'):
            return ''
        if 'FROM destination_channels' in query:
            return '\n'.join(f'{n}\t{c}' for n, c in self.channels.items())
        niche = 'futebol' if "'futebol'" in query else 'politica'
        if 'COUNT(DISTINCT' in query:
            value = self.occupancy[niche]
            return '' if value is None else str(value)
        limit = int(query.rsplit('LIMIT', 1)[1].strip(' ;\n'))
        rows = min(limit, self.pending_rows)
        return '\n'.join(f'{i}\tvid{niche}{i}\tTítulo {i}\tcurto' for i in range(1, rows + 1))


@pytest.fixture
def windows(monkeypatch):
    monkeypatch.setattr(worker, 'DOWNLOAD_WINDOW_PER_CHANNEL', 10)


def test_janela_e_dez_por_canal_destino(monkeypatch, windows):
    monkeypatch.setattr(worker, 'run_remote_mysql', FakeRemote({}, channels={'politica': 1, 'futebol': 1}))
    assert worker.niche_windows() == {'futebol': 10, 'politica': 10}


def test_canal_destino_novo_soma_dez(monkeypatch, windows):
    monkeypatch.setattr(worker, 'run_remote_mysql', FakeRemote({}, channels={'futebol': 2, 'politica': 1}))
    assert worker.niche_windows() == {'futebol': 20, 'politica': 10}


def test_sem_canal_destino_nao_baixa(monkeypatch, windows):
    fake = FakeRemote({'futebol': 0, 'politica': 0}, channels={})
    monkeypatch.setattr(worker, 'run_remote_mysql', fake)
    assert worker.fetch_pending_videos() == []
    assert not any('COUNT(DISTINCT' in q for q in fake.queries)


def test_window_deficit_nunca_negativo():
    assert worker.window_deficit(3, 10) == 7
    assert worker.window_deficit(10, 10) == 0
    assert worker.window_deficit(377, 6) == 0


def test_janela_cheia_nao_busca_nada(monkeypatch, windows):
    fake = FakeRemote({'futebol': 35, 'politica': 337})
    monkeypatch.setattr(worker, 'run_remote_mysql', fake)

    assert worker.fetch_pending_videos() == []
    assert not any('LIMIT' in q for q in fake.queries)


def test_busca_so_o_deficit_de_cada_nicho(monkeypatch, windows):
    fake = FakeRemote({'futebol': 8, 'politica': 10}, pending_rows=10)
    monkeypatch.setattr(worker, 'run_remote_mysql', fake)

    videos = worker.fetch_pending_videos()

    assert len(videos) == 2
    assert all(v['youtube_video_id'].startswith('vidfutebol') for v in videos)
    assert any('LIMIT 2' in q for q in fake.queries)


def test_falha_na_contagem_nao_baixa_nada(monkeypatch, windows):
    fake = FakeRemote({'futebol': None, 'politica': None})
    monkeypatch.setattr(worker, 'run_remote_mysql', fake)

    assert worker.fetch_pending_videos() == []


def test_ciclo_processa_um_video_por_vez(monkeypatch):
    monkeypatch.setattr(worker, 'fetch_pending_videos',
                        lambda: [{'id': 1}, {'id': 2}, {'id': 3}])
    processed = []
    monkeypatch.setattr(worker, 'process_single_video', processed.append)

    assert worker.run_cycle() == 1
    assert processed == [{'id': 1}]
