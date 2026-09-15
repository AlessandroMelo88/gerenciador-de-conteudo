import pytest
import requests

from affiliate_worker.api_client import ApiClient, ApiError
from tests.conftest import FakeResponse, FakeSession

OK_BODY = {'created': 1, 'updated': 0, 'skipped': 0,
           'offers': [{'id': 7, 'slug': 's', 'status': 'draft', 'result': 'created', 'tracking_url': 'https://p/o/s'}]}


def client(session, **kw):
    sleeps = []
    c = ApiClient('https://painel.test/', 'segredo', session=session, backoff=0.01, sleep=sleeps.append, **kw)
    return c, sleeps


def items(n):
    return [{'network': 'manual', 'title': f't{i}', 'niche': 'futebol', 'affiliate_url': 'https://x'} for i in range(n)]


def test_200_e_header_bearer():
    session = FakeSession([FakeResponse(200, OK_BODY)])
    c, sleeps = client(session)
    [res] = c.push(items(1))
    assert res.ok and res.body['created'] == 1
    call = session.calls[0]
    assert call['url'] == 'https://painel.test/api/offers'
    assert call['headers']['Authorization'] == 'Bearer segredo'
    assert call['json'] == {'offers': items(1)}
    assert sleeps == []
    assert 'segredo' not in repr(c)


def test_lotes_de_100():
    session = FakeSession([FakeResponse(200, OK_BODY)])
    c, _ = client(session)
    results = c.push(items(230))
    assert [len(call['json']['offers']) for call in session.calls] == [100, 100, 30]
    assert len(results) == 3


def test_lote_acima_de_100_rejeitado():
    c, _ = client(FakeSession([FakeResponse(200, OK_BODY)]))
    with pytest.raises(ValueError):
        c.post_batch(items(101))


def test_retry_em_429_respeita_retry_after():
    session = FakeSession([FakeResponse(429, {}, headers={'Retry-After': '3'}), FakeResponse(200, OK_BODY)])
    c, sleeps = client(session)
    [res] = c.push(items(1))
    assert res.ok and len(session.calls) == 2
    assert sleeps == [3.0]


def test_retry_em_503_depois_sucesso():
    session = FakeSession([FakeResponse(503), FakeResponse(503), FakeResponse(200, OK_BODY)])
    c, sleeps = client(session)
    [res] = c.push(items(1))
    assert res.ok and len(session.calls) == 3 and len(sleeps) == 2


def test_503_persistente_levanta_erro_amigavel():
    session = FakeSession([FakeResponse(503)])
    c, sleeps = client(session, max_retries=2)
    with pytest.raises(ApiError) as exc:
        c.push(items(1))
    assert exc.value.status == 503 and 'token' in str(exc.value)
    assert len(session.calls) == 3


def test_retry_em_timeout():
    session = FakeSession([requests.Timeout('lento'), FakeResponse(200, OK_BODY)])
    c, _ = client(session)
    [res] = c.push(items(1))
    assert res.ok and len(session.calls) == 2


def test_500_esgota_tentativas_sem_excecao():
    session = FakeSession([FakeResponse(500)])
    c, _ = client(session, max_retries=1)
    [res] = c.push(items(1))
    assert not res.ok and len(session.calls) == 2 and 'tentativas' in res.error


def test_401_sem_retry():
    session = FakeSession([FakeResponse(401, {'message': 'Unauthenticated.'})])
    c, sleeps = client(session)
    with pytest.raises(ApiError) as exc:
        c.push(items(150))
    assert exc.value.status == 401
    assert len(session.calls) == 1 and sleeps == []
    assert 'segredo' not in str(exc.value)


def test_422_sem_retry_mapeia_erros_e_segue_proximo_lote():
    body = {'message': 'The given data was invalid.',
            'errors': {'offers.1.title': ['O campo title é obrigatório.'], 'offers': ['geral']}}
    session = FakeSession([FakeResponse(422, body), FakeResponse(200, OK_BODY)])
    c, sleeps = client(session)
    r1, r2 = c.push(items(101))
    assert not r1.ok and r1.status == 422
    assert r1.item_errors[1] == ['O campo title é obrigatório.']
    assert r1.item_errors[-1] == ['geral']
    assert r2.ok and len(session.calls) == 2 and sleeps == []


def test_config_ausente():
    with pytest.raises(ApiError):
        ApiClient('', 'x')
    with pytest.raises(ApiError):
        ApiClient('https://a', '')
