from affiliate_worker.models import Offer, chunked, is_http_url
from tests.conftest import make_offer


def test_oferta_valida_sem_erros():
    assert make_offer().validate() == []


def test_url_javascript_rejeitada():
    errors = make_offer(affiliate_url='javascript:alert(1)').validate()
    assert any('affiliate_url' in e for e in errors)
    assert not is_http_url('javascript:alert(1)')
    assert not is_http_url('data:text/html,x')
    assert not is_http_url('/relativa')
    assert not is_http_url('https://')
    assert is_http_url('http://exemplo.com/a?b=1')


def test_network_invalido():
    assert any('network' in e for e in make_offer(network='ebay').validate())


def test_titulo_longo():
    assert any('title' in e for e in make_offer(title='x' * 256).validate())
    assert make_offer(title='x' * 255).validate() == []


def test_sem_affiliate_url_e_erro():
    errors = make_offer(affiliate_url=None).validate()
    assert any('affiliate_url ausente' in e for e in errors)


def test_outros_campos():
    errors = make_offer(image_url='ftp://x/y.jpg', currency='reais', price_cents=-1,
                        commission_percent=150, ai_provider='openai', copy_short='a' * 281).validate()
    joined = ' '.join(errors)
    for campo in ('image_url', 'currency', 'price_cents', 'commission_percent', 'ai_provider', 'copy_short'):
        assert campo in joined


def test_payload_sem_status_e_sem_controle_local():
    offer = Offer.from_dict({'network': 'Hotmart', 'title': 'T', 'niche': 'politica',
                             'affiliate_url': 'https://a.b', 'status': 'active', 'price_cents': '1990',
                             'currency': 'brl', 'commission_percent': '40,5'})
    offer.pushed_at = '2026-01-01'
    payload = offer.to_payload()
    assert 'status' not in payload and 'pushed_at' not in payload
    assert payload['network'] == 'hotmart'
    assert payload['price_cents'] == 1990 and payload['currency'] == 'BRL'
    assert payload['commission_percent'] == 40.5
    assert any('status' in w for w in offer.extra_warnings)


def test_chunked_100():
    batches = chunked(list(range(250)), 100)
    assert [len(b) for b in batches] == [100, 100, 50]
