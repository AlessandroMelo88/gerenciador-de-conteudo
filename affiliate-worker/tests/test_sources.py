import json

import pytest
import requests

from affiliate_worker.sources import manual, mercadolivre
from tests.conftest import FakeResponse, FakeSession


def test_import_csv_ponto_e_virgula_com_preco_em_reais(tmp_path):
    f = tmp_path / 'ofertas.csv'
    f.write_text(
        'network;external_id;niche;title;affiliate_url;price;commission_percent\n'
        'hotmart;HP1;politica;Curso de Oratória;https://go.hotmart.com/X;R$ 1.297,00;50\n'
        'kiwify;K2;;Ebook;;49,90;\n',
        encoding='utf-8')
    offers = manual.load_file(f, default_niche='politica')
    assert len(offers) == 2
    assert offers[0].price_cents == 129700 and offers[0].commission_percent == 50.0
    assert offers[0].validate() == []
    assert offers[1].niche == 'politica' and offers[1].price_cents == 4990
    assert not offers[1].has_affiliate_url()


def test_import_json_lista_e_objeto(tmp_path):
    item = {'network': 'amazon', 'niche': 'futebol', 'title': 'Bola', 'affiliate_url': 'https://amzn.to/x'}
    f1 = tmp_path / 'a.json'
    f1.write_text(json.dumps([item]))
    f2 = tmp_path / 'b.json'
    f2.write_text(json.dumps({'offers': [item, item]}))
    assert len(manual.load_file(f1)) == 1
    assert len(manual.load_file(f2)) == 2


def test_import_erros(tmp_path):
    bad = tmp_path / 'x.json'
    bad.write_text('{nope')
    with pytest.raises(manual.OfferImportError):
        manual.load_file(bad)
    with pytest.raises(manual.OfferImportError):
        manual.load_file(tmp_path / 'naoexiste.csv')
    txt = tmp_path / 'x.txt'
    txt.write_text('a')
    with pytest.raises(manual.OfferImportError):
        manual.load_file(txt)


ML_BODY = {'paging': {'total': 2}, 'results': [
    {'id': 'MLB1', 'title': 'Chuteira Society', 'price': 199.9, 'currency_id': 'BRL',
     'permalink': 'https://produto.mercadolivre.com.br/MLB-1', 'thumbnail': 'http://http2.mlstatic.com/a.jpg'},
    {'id': 'MLB2', 'title': 'Meião', 'price': 29, 'currency_id': 'BRL', 'permalink': 'https://p/2', 'thumbnail': ''},
]}


def test_ml_busca_ok_sem_affiliate_url():
    session = FakeSession([FakeResponse(200, ML_BODY)])
    res = mercadolivre.search('chuteira', 'futebol', 20, session=session, token='')
    assert res.ok and len(res.candidates) == 2
    c = res.candidates[0]
    assert c.network == 'mercadolivre' and c.external_id == 'MLB1' and c.price_cents == 19990
    assert c.affiliate_url is None and c.image_url.startswith('https://')
    assert session.calls[0]['url'].endswith('/sites/MLB/search')
    assert session.calls[0]['timeout']
    assert 'Authorization' not in session.calls[0]['headers']


@pytest.mark.parametrize('status', [401, 403])
def test_ml_401_403_erro_amigavel(status):
    session = FakeSession([FakeResponse(status, {'message': 'forbidden'})])
    res = mercadolivre.search('chuteira', 'futebol', session=session, token='')
    assert not res.ok and 'MERCADOLIVRE_ACCESS_TOKEN' in res.error and res.candidates == []


def test_ml_timeout_e_json_invalido():
    res = mercadolivre.search('x', 'futebol', session=FakeSession([requests.Timeout()]), token='')
    assert not res.ok and 'timeout' in res.error
    res = mercadolivre.search('x', 'futebol', session=FakeSession([FakeResponse(200, None)]), token='')
    assert not res.ok and 'JSON' in res.error


def test_ml_token_vai_no_header():
    session = FakeSession([FakeResponse(200, ML_BODY)])
    mercadolivre.search('x', 'futebol', session=session, token='tok')
    assert session.calls[0]['headers']['Authorization'] == 'Bearer tok'
