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

    def __init__(self, occupancy, pending_rows=3, channels=None, source_channels=1,
                 pending_por_canal=None):
        # occupancy: por nicho, um int (tudo num canal só) ou dict {channel_id: vagas}
        self.occupancy = occupancy
        self.channels = channels if channels is not None else {'politica': 1, 'futebol': 1}
        self.pending_rows = pending_rows
        self.source_channels = source_channels
        # pending_por_canal: lista de channel_id, na ordem em que o SQL devolveria
        self.pending_por_canal = pending_por_canal
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        if query.startswith('UPDATE'):
            return ''
        if 'FROM destination_channels' in query:
            return '\n'.join(f'{n}\t{c}' for n, c in self.channels.items())
        niche = 'futebol' if "'futebol'" in query else 'politica'
        if 'FROM source_channels' in query:
            return str(self.source_channels)
        if 'COUNT(DISTINCT' in query:
            value = self.occupancy[niche]
            if value is None:
                return 'erro'
            if isinstance(value, dict):
                return '\n'.join(f'{cid}\t{n}' for cid, n in value.items())
            return f'1\t{value}' if value else ''
        limit = int(query.rsplit('LIMIT', 1)[1].strip(' ;\n'))
        if self.pending_por_canal is not None:
            canais = self.pending_por_canal[:limit]
        else:
            canais = ['1'] * min(limit, self.pending_rows)
        return '\n'.join(
            f'{i}\tvid{niche}{i}\tTítulo {i}\tcurto\t{cid}'
            for i, cid in enumerate(canais, start=1)
        )


@pytest.fixture
def windows(monkeypatch):
    monkeypatch.setattr(worker, 'DOWNLOAD_WINDOW_PER_CHANNEL', 10)


def test_janela_e_dez_por_canal_destino(monkeypatch, windows):
    monkeypatch.setattr(worker, 'run_remote_sql', FakeRemote({}, channels={'politica': 1, 'futebol': 1}))
    assert worker.niche_windows() == {'futebol': 10, 'politica': 10}


def test_canal_destino_novo_soma_dez(monkeypatch, windows):
    monkeypatch.setattr(worker, 'run_remote_sql', FakeRemote({}, channels={'futebol': 2, 'politica': 1}))
    assert worker.niche_windows() == {'futebol': 20, 'politica': 10}


def test_sem_canal_destino_nao_baixa(monkeypatch, windows):
    fake = FakeRemote({'futebol': 0, 'politica': 0}, channels={})
    monkeypatch.setattr(worker, 'run_remote_sql', fake)
    assert worker.fetch_pending_videos() == []
    assert not any('COUNT(DISTINCT' in q for q in fake.queries)


def test_window_deficit_nunca_negativo():
    assert worker.window_deficit(3, 10) == 7
    assert worker.window_deficit(10, 10) == 0
    assert worker.window_deficit(377, 6) == 0


def test_janela_cheia_nao_busca_nada(monkeypatch, windows):
    fake = FakeRemote({'futebol': 35, 'politica': 337})
    monkeypatch.setattr(worker, 'run_remote_sql', fake)

    assert worker.fetch_pending_videos() == []
    assert not any('LIMIT' in q for q in fake.queries)


def test_busca_so_o_deficit_de_cada_nicho(monkeypatch, windows):
    fake = FakeRemote({'futebol': 8, 'politica': 10}, pending_rows=10, source_channels=1)
    monkeypatch.setattr(worker, 'run_remote_sql', fake)

    videos = worker.fetch_pending_videos()

    assert len(videos) == 2
    assert all(v['youtube_video_id'].startswith('vidfutebol') for v in videos)
    # pede mais candidatos que vagas para ter o que intercalar, mas devolve só o déficit
    assert any(f'LIMIT {2 * worker.CANDIDATES_PER_SLOT}' in q for q in fake.queries)


def test_um_canal_prolifico_nao_toma_a_janela_toda(monkeypatch, windows):
    """10 vagas livres, 2 canais de origem ativos: teto de 5 por canal, intercalando."""
    fake = FakeRemote(
        {'futebol': {}, 'politica': 10},
        source_channels=2,
        pending_por_canal=['7'] * 20 + ['8'] * 3,
    )
    monkeypatch.setattr(worker, 'run_remote_sql', fake)

    videos = worker.fetch_pending_videos()

    por_canal = {}
    for v in videos:
        por_canal[v['channel_id']] = por_canal.get(v['channel_id'], 0) + 1
    assert por_canal == {'7': 5, '8': 3}, por_canal
    assert [v['channel_id'] for v in videos[:2]] == ['7', '8'], 'não intercalou'


def test_canal_que_ja_ocupa_a_janela_escolhe_por_ultimo(monkeypatch, windows):
    fake = FakeRemote(
        {'futebol': {'7': 4}, 'politica': 10},
        source_channels=2,
        pending_por_canal=['7', '8'],
    )
    monkeypatch.setattr(worker, 'run_remote_sql', fake)

    videos = worker.fetch_pending_videos()

    assert videos[0]['channel_id'] == '8'


def test_expurgo_poupa_canal_que_nunca_baixou(monkeypatch, windows):
    fake = FakeRemote({'futebol': 10, 'politica': 10})
    monkeypatch.setattr(worker, 'run_remote_sql', fake)

    worker.fetch_pending_videos()

    expurgo = next(q for q in fake.queries if q.startswith('UPDATE'))
    assert 'channel_id IN (' in expurgo
    assert "'published'" in expurgo


def test_falha_na_contagem_nao_baixa_nada(monkeypatch, windows):
    fake = FakeRemote({'futebol': None, 'politica': None})
    monkeypatch.setattr(worker, 'run_remote_sql', fake)

    assert worker.fetch_pending_videos() == []


def test_ciclo_processa_um_video_por_vez(monkeypatch):
    monkeypatch.setattr(worker, 'process_transcription', lambda: False)
    monkeypatch.setattr(worker, 'fetch_pending_videos',
                        lambda: [{'id': 1}, {'id': 2}, {'id': 3}])
    processed = []
    monkeypatch.setattr(worker, 'process_single_video', processed.append)

    assert worker.run_cycle() == 1
    assert processed == [{'id': 1}]


def test_ciclo_transcreve_antes_de_baixar(monkeypatch):
    ordem = []
    monkeypatch.setattr(worker, 'process_transcription', lambda: ordem.append('transcricao') or True)
    monkeypatch.setattr(worker, 'fetch_pending_videos', lambda: ordem.append('download') or [])

    assert worker.run_cycle() == 1, 'ciclo com transcrição conta como trabalho feito'
    assert ordem == ['transcricao', 'download']


def test_erro_na_transcricao_nao_derruba_o_ciclo(monkeypatch):
    def quebra(**_):
        raise RuntimeError('ssh caiu')
    monkeypatch.setattr(worker.transcription_worker, 'process_one_job', quebra)

    assert worker.process_transcription() is False
