import json

import pytest
import requests

from affiliate_worker import cli
from affiliate_worker.api_client import ApiClient
from affiliate_worker.storage import Storage
from tests.conftest import FakeResponse, FakeSession, make_offer


@pytest.fixture
def storage(tmp_path):
    return Storage(tmp_path / 'data')


@pytest.fixture
def no_http(monkeypatch):
    def boom(*a, **k):
        raise AssertionError('HTTP não deveria ser chamado')
    monkeypatch.setattr(requests.Session, 'request', boom)
    monkeypatch.setattr(requests, 'post', boom)


def _args(**kw):
    import argparse
    return argparse.Namespace(**kw)


def test_dry_run_nao_chama_http(storage, no_http, capsys):
    storage.save_ready([make_offer(), make_offer(external_id='HP2')])
    rc = cli.cmd_push(_args(dry_run=True, force=False), storage)
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 1 and len(out[0]['offers']) == 2
    assert 'status' not in out[0]['offers'][0]
    assert not storage.pushed_path.exists()


def test_item_sem_affiliate_url_fica_fora_do_push(storage, no_http, capsys):
    storage.save_ready([make_offer(), make_offer(external_id='SEMLINK', affiliate_url=None)])
    cli.cmd_push(_args(dry_run=True, force=False), storage)
    captured = capsys.readouterr()
    payload = json.loads(captured.out)[0]['offers']
    assert [p['external_id'] for p in payload] == ['HP1']
    assert 'SEM affiliate_url' in captured.err


def test_push_real_registra_pushed_e_marca_enviado(storage):
    storage.save_ready([make_offer()])
    body = {'created': 1, 'updated': 0, 'skipped': 0,
            'offers': [{'id': 9, 'slug': 'curso', 'status': 'draft', 'result': 'created',
                        'tracking_url': 'https://painel/o/curso'}]}
    session = FakeSession([FakeResponse(200, body)])
    client = ApiClient('https://painel', 'tok', session=session, sleep=lambda s: None)
    assert cli.cmd_push(_args(dry_run=False, force=False), storage, client=client) == 0
    lines = [json.loads(l) for l in storage.pushed_path.read_text().splitlines()]
    assert lines[0]['result'] == 'created' and lines[0]['server_id'] == 9
    [saved] = storage.load_ready()
    assert saved.pushed_at and saved.server_status == 'draft'
    # segundo push não reenvia
    assert cli.cmd_push(_args(dry_run=False, force=False), storage, client=client) == 0
    assert len(session.calls) == 1


def test_push_401_aborta(storage):
    storage.save_ready([make_offer()])
    client = ApiClient('https://painel', 'tok', session=FakeSession([FakeResponse(401)]), sleep=lambda s: None)
    assert cli.cmd_push(_args(dry_run=False, force=False), storage, client=client) == 1
    assert json.loads(storage.pushed_path.read_text().splitlines()[-1])['result'] == 'aborted'
    assert not storage.load_ready()[0].pushed_at


def test_push_422_registra_erro(storage, capsys):
    storage.save_ready([make_offer()])
    body = {'message': 'invalid', 'errors': {'offers.0.niche': ['Nicho não existe.']}}
    client = ApiClient('https://painel', 'tok', session=FakeSession([FakeResponse(422, body)]), sleep=lambda s: None)
    assert cli.cmd_push(_args(dry_run=False, force=False), storage, client=client) == 1
    assert 'Nicho não existe.' in capsys.readouterr().err
    rec = json.loads(storage.pushed_path.read_text().splitlines()[0])
    assert rec['status_code'] == 422 and rec['errors'] == ['Nicho não existe.']


def test_push_sem_config_retorna_erro(storage, no_http):
    storage.save_ready([make_offer()])
    assert cli.cmd_push(_args(dry_run=False, force=False), storage) == 1


def test_import_mescla_por_chave(storage, tmp_path):
    f = tmp_path / 'o.json'
    f.write_text(json.dumps([{'network': 'hotmart', 'external_id': 'A', 'niche': 'politica',
                              'title': 'v1', 'affiliate_url': 'https://h/a'}]))
    assert cli.cmd_import(_args(file=str(f), niche=None), storage) == 0
    f.write_text(json.dumps([{'network': 'hotmart', 'external_id': 'A', 'niche': 'politica',
                              'title': 'v2', 'affiliate_url': 'https://h/a'}]))
    cli.cmd_import(_args(file=str(f), niche=None), storage)
    [o] = storage.load_ready()
    assert o.title == 'v2'


def test_run_dry_run_ponta_a_ponta(tmp_path, no_http, capsys):
    f = tmp_path / 'o.csv'
    f.write_text('network,external_id,niche,title,affiliate_url\n'
                 'amazon,B01,futebol,Camisa Retrô,https://amzn.to/abc\n', encoding='utf-8')
    rc = cli.main(['--data-dir', str(tmp_path / 'd'), 'run', '--file', str(f), '--provider', 'template', '--dry-run'])
    assert rc == 0
    [offer] = json.loads(capsys.readouterr().out)[0]['offers']
    assert offer['copy_short'] and offer['cta_text'] and offer['ai_provider'] == 'manual'


def test_search_ml_403_nao_quebra(tmp_path, monkeypatch, capsys):
    from affiliate_worker.sources import mercadolivre
    monkeypatch.setattr(mercadolivre.requests, 'Session', lambda: FakeSession([FakeResponse(403)]))
    rc = cli.main(['--data-dir', str(tmp_path / 'd'), 'search', '--query', 'chuteira', '--niche', 'futebol'])
    assert rc == 1
    assert 'MERCADOLIVRE_ACCESS_TOKEN' in capsys.readouterr().err
