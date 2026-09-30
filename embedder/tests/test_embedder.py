"""Testes do sidecar de embeddings.

Rodar (de dentro de embedder/):  python -m pytest tests -q
Os testes com FakeModel não baixam nada. Os de modelo real (marcados `real`) só
rodam com EMBEDDER_TEST_REAL=1 e exigem o modelo em cache/rede.
"""
import math
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

import embed_lib  # noqa: E402
from app import create_app  # noqa: E402

TOKEN = 'segredo-de-teste'
AUTH = {'Authorization': f'Bearer {TOKEN}'}


class FakeModel:
    """Vetor de 384 dimensões determinístico, NÃO normalizado, para provar que a lib normaliza."""

    def __init__(self, dim=384):
        self.dim = dim
        self.seen = []

    def encode(self, texts, batch_size=32):
        self.seen.extend(texts)
        return [[float((i + len(t)) % 7 + 1) for i in range(self.dim)] for t in texts]


def _embedder(dim=384, model=None):
    model = model or FakeModel(dim)
    return embed_lib.Embedder(name='fake/e5', dim=dim, loader=lambda name: model), model


def _client(token=TOKEN, dim=384, loader_falha=False):
    if loader_falha:
        def loader(name):
            raise OSError('sem modelo')
        embedder = embed_lib.Embedder(name='fake/e5', dim=dim, loader=loader)
    else:
        embedder, _ = _embedder(dim)
    return TestClient(create_app(embedder=embedder, token=token)), embedder


class TestEmbedLib:
    def test_prefixos_do_e5(self):
        assert embed_lib.add_prefix(['a'], 'query') == ['query: a']
        assert embed_lib.add_prefix(['a', 'b'], 'passage') == ['passage: a', 'passage: b']

    def test_kind_invalido(self):
        with pytest.raises(embed_lib.EmbedderError):
            embed_lib.add_prefix(['a'], 'outro')

    def test_normaliza_l2(self):
        v = embed_lib.l2_normalize([3, 4])
        assert v == pytest.approx([0.6, 0.8])
        assert embed_lib.l2_normalize([0, 0]) == [0.0, 0.0]

    def test_embed_aplica_prefixo_e_normaliza(self):
        embedder, model = _embedder()
        vectors = embedder.embed(['olá'], 'passage')

        assert model.seen == ['passage: olá']
        assert len(vectors[0]) == 384
        assert math.sqrt(sum(x * x for x in vectors[0])) == pytest.approx(1.0)

    def test_lista_vazia_nao_carrega_modelo(self):
        embedder, _ = _embedder()
        assert embedder.embed([], 'query') == []
        assert embedder.loaded is False

    def test_dimensao_errada_e_erro(self):
        embedder, _ = _embedder(dim=384, model=FakeModel(dim=10))
        with pytest.raises(embed_lib.EmbedderError):
            embedder.embed(['x'], 'query')

    def test_falha_de_carga_vira_embedder_error(self):
        _, embedder = _client(loader_falha=True)
        with pytest.raises(embed_lib.EmbedderError):
            embedder.load()


class TestApi:
    def test_health_com_modelo_carregado(self):
        with _client()[0] as client:  # o `with` dispara o lifespan (carga do modelo)
            res = client.get('/health')
        assert res.status_code == 200
        assert res.json() == {'status': 'ok', 'model': 'fake/e5', 'dim': 384}

    def test_health_503_sem_modelo(self):
        with _client(loader_falha=True)[0] as client:
            assert client.get('/health').status_code == 503

    def test_embed_devolve_contrato(self):
        with _client()[0] as client:
            res = client.post('/embed', json={'texts': ['a', 'b'], 'kind': 'query'}, headers=AUTH)
        body = res.json()
        assert res.status_code == 200
        assert body['model'] == 'fake/e5' and body['dim'] == 384
        assert len(body['vectors']) == 2 and len(body['vectors'][0]) == 384
        assert math.sqrt(sum(x * x for x in body['vectors'][0])) == pytest.approx(1.0, abs=1e-6)

    @pytest.mark.parametrize('headers', [
        {},
        {'Authorization': 'Bearer errado'},
        {'Authorization': TOKEN},                # sem esquema
        {'Authorization': 'Basic ' + TOKEN},
        {'Authorization': 'Bearer '},
    ])
    def test_sem_token_valido_401(self, headers):
        with _client()[0] as client:
            res = client.post('/embed', json={'texts': ['a'], 'kind': 'query'}, headers=headers)
        assert res.status_code == 401

    def test_token_vazio_no_servidor_fecha_tudo(self):
        with _client(token='')[0] as client:
            for headers in ({}, {'Authorization': 'Bearer '}, {'Authorization': 'Bearer x'}):
                res = client.post('/embed', json={'texts': ['a'], 'kind': 'query'}, headers=headers)
                assert res.status_code == 401

    def test_auth_vem_antes_da_validacao(self):
        with _client()[0] as client:
            assert client.post('/embed', json={'texts': []}).status_code == 401

    @pytest.mark.parametrize('payload', [
        {'texts': [], 'kind': 'query'},
        {'texts': ['a'], 'kind': 'outro'},
        {'texts': ['a']},
        {'kind': 'query'},
        {'texts': [1, 2], 'kind': 'query'},
        {'texts': ['a'] * 65, 'kind': 'query'},
        {'texts': ['x' * 8001], 'kind': 'query'},
    ])
    def test_payload_invalido_422(self, payload):
        with _client()[0] as client:
            assert client.post('/embed', json=payload, headers=AUTH).status_code == 422

    def test_modelo_nao_carregado_503(self):
        with _client(loader_falha=True)[0] as client:
            res = client.post('/embed', json={'texts': ['a'], 'kind': 'query'}, headers=AUTH)
        assert res.status_code == 503

    def test_sem_docs_publicas(self):
        with _client()[0] as client:
            assert client.get('/docs').status_code == 404
            assert client.get('/openapi.json').status_code == 404


@pytest.mark.skipif(os.environ.get('EMBEDDER_TEST_REAL') != '1',
                    reason='modelo real só com EMBEDDER_TEST_REAL=1')
class TestModeloReal:
    def test_dim_384_norma_1_e_similaridade_faz_sentido(self):
        embedder = embed_lib.Embedder()
        client = TestClient(create_app(embedder=embedder, token=TOKEN))
        with client:
            q = client.post('/embed', json={'texts': ['como validar uma oferta?'], 'kind': 'query'},
                            headers=AUTH).json()
            p = client.post('/embed', json={'texts': [
                'Para validar a oferta, venda antes de construir o produto.',
                'A receita de bolo leva três ovos e farinha.',
            ], 'kind': 'passage'}, headers=AUTH).json()
        assert q['dim'] == 384 and len(q['vectors'][0]) == 384
        assert math.sqrt(sum(x * x for x in q['vectors'][0])) == pytest.approx(1.0, abs=1e-4)

        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))

        assert dot(q['vectors'][0], p['vectors'][0]) > dot(q['vectors'][0], p['vectors'][1])
