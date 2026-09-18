"""Testes da API local que a extensão do Chrome chama no worker do Mac.

Rodar: python3 -m pytest scripts/test_extensao_api.py -q
"""
import importlib.util
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location('extensao_api', Path(__file__).with_name('extensao_api.py'))
api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(api)

ORIGEM_EXTENSAO = 'chrome-extension://abcdefghijklmnopabcdefghijklmnop'


def _cookie(domain='.asimov.academy', name='sessionid', value='v1', **kw):
    base = {'domain': domain, 'path': '/', 'secure': True, 'httpOnly': False,
            'hostOnly': not domain.startswith('.'), 'name': name, 'value': value,
            'expirationDate': 1893456000.5}
    base.update(kw)
    return base


class TestFormatoNetscape:
    def test_linha_de_cookie_de_dominio(self):
        linha = api.cookie_to_netscape(_cookie())

        assert linha == '.asimov.academy\tTRUE\t/\tTRUE\t1893456000\tsessionid\tv1'

    def test_cookie_so_do_host_nao_vale_para_subdominio(self):
        linha = api.cookie_to_netscape(_cookie(domain='hub.asimov.academy'))

        assert linha.split('\t')[:2] == ['hub.asimov.academy', 'FALSE']

    def test_http_only_ganha_o_prefixo_que_o_yt_dlp_entende(self):
        linha = api.cookie_to_netscape(_cookie(httpOnly=True))

        assert linha.startswith('#HttpOnly_.asimov.academy\t')

    def test_cookie_de_sessao_sem_validade_vira_zero(self):
        cookie = _cookie()
        del cookie['expirationDate']

        assert api.cookie_to_netscape(cookie).split('\t')[4] == '0'


class TestJuntarCookies:
    def test_substitui_so_o_site_enviado_e_preserva_os_outros(self, tmp_path):
        arquivo = tmp_path / 'cookies.txt'
        arquivo.write_text(
            '# Netscape HTTP Cookie File\n'
            '.hotmart.com\tTRUE\t/\tTRUE\t0\thot\tvelho\n'
            '.asimov.academy\tTRUE\t/\tTRUE\t0\tsessionid\tvelho\n'
        )

        api.merge_cookies(arquivo, 'asimov.academy', [_cookie(value='novo')])

        texto = arquivo.read_text()
        assert 'hot\tvelho' in texto
        assert 'sessionid\tnovo' in texto
        assert 'sessionid\tvelho' not in texto

    def test_http_only_antigo_do_mesmo_site_tambem_sai(self, tmp_path):
        arquivo = tmp_path / 'cookies.txt'
        arquivo.write_text('#HttpOnly_hub.asimov.academy\tFALSE\t/\tTRUE\t0\tcsrf\tvelho\n')

        api.merge_cookies(arquivo, 'asimov.academy', [_cookie(value='novo')])

        assert 'csrf\tvelho' not in arquivo.read_text()

    def test_cria_o_arquivo_fechado_so_para_o_dono(self, tmp_path):
        arquivo = tmp_path / 'sub' / 'cookies.txt'

        api.merge_cookies(arquivo, 'asimov.academy', [_cookie()])

        assert arquivo.read_text().startswith('# Netscape HTTP Cookie File\n')
        assert oct(arquivo.stat().st_mode & 0o777) == '0o600'

    def test_nao_confunde_dominio_parecido(self, tmp_path):
        arquivo = tmp_path / 'cookies.txt'
        arquivo.write_text('.fakeasimov.academy\tTRUE\t/\tTRUE\t0\tx\tfica\n')

        api.merge_cookies(arquivo, 'asimov.academy', [_cookie()])

        assert 'x\tfica' in arquivo.read_text()


class TestDominioRegistravel:
    @pytest.mark.parametrize('host, esperado', [
        ('hub.asimov.academy', 'asimov.academy'),
        ('hotmart.com', 'hotmart.com'),
        ('www.hotmart.com', 'hotmart.com'),
        ('cursos.exemplo.com.br', 'exemplo.com.br'),
    ])
    def test_extrai_o_site(self, host, esperado):
        assert api.registrable_domain(host) == esperado


class TestPedido:
    def _handle(self, body, origin=ORIGEM_EXTENSAO, tmp_path=None):
        chamadas = {'sql': [], 'acordou': 0}

        def run_sql(q):
            chamadas['sql'].append(q)
            return '42'

        status, resposta = api.handle_transcrever(
            body=json.dumps(body).encode(), origin=origin, run_sql=run_sql,
            cookies_file=tmp_path / 'cookies.txt', wake=lambda: chamadas.__setitem__('acordou', 1),
        )
        return status, resposta, chamadas

    def test_enfileira_e_guarda_cookies(self, tmp_path):
        status, resposta, chamadas = self._handle(
            {'url': 'https://hub.asimov.academy/curso/atividade/x/', 'cookies': [_cookie()]}, tmp_path=tmp_path)

        assert status == 200 and resposta == {'ok': True, 'job_id': 42}
        insert = chamadas['sql'][0]
        assert insert.startswith('INSERT INTO transcription_jobs')
        assert 'https://hub.asimov.academy/curso/atividade/x/' in insert
        assert 'sessionid\tv1' in (tmp_path / 'cookies.txt').read_text()
        assert chamadas['acordou'] == 1, 'acorda o worker para não esperar o ciclo de 60 s'

    def test_recusa_pedido_que_nao_vem_de_extensao(self, tmp_path):
        """Qualquer site aberto no Chrome consegue chamar 127.0.0.1; só extensão manda
        Origin chrome-extension://, e página nenhuma consegue forjar esse cabeçalho."""
        status, _, chamadas = self._handle({'url': 'https://x.com/a', 'cookies': []},
                                           origin='https://site-malicioso.com', tmp_path=tmp_path)

        assert status == 403
        assert chamadas['sql'] == []
        assert not (tmp_path / 'cookies.txt').exists()

    def test_recusa_pedido_sem_origin(self, tmp_path):
        status, _, _ = self._handle({'url': 'https://x.com/a', 'cookies': []}, origin=None, tmp_path=tmp_path)

        assert status == 403

    def test_recusa_link_que_nao_e_http(self, tmp_path):
        status, resposta, chamadas = self._handle({'url': 'javascript:alert(1)', 'cookies': []}, tmp_path=tmp_path)

        assert status == 400 and chamadas['sql'] == []

    def test_so_grava_cookie_do_proprio_site_da_aula(self, tmp_path):
        """A extensão manda só o site da aba; se vier cookie de outro domínio, descarta."""
        self._handle({'url': 'https://hub.asimov.academy/a', 'cookies': [
            _cookie(), _cookie(domain='.google.com', name='SID', value='nao'),
        ]}, tmp_path=tmp_path)

        texto = (tmp_path / 'cookies.txt').read_text()
        assert 'google' not in texto and 'sessionid' in texto

    def test_banco_fora_do_ar_responde_erro(self, tmp_path):
        status, resposta = api.handle_transcrever(
            body=json.dumps({'url': 'https://a.com/x', 'cookies': []}).encode(), origin=ORIGEM_EXTENSAO,
            run_sql=lambda q: '', cookies_file=tmp_path / 'c.txt', wake=lambda: None)

        assert status == 502 and resposta['ok'] is False

    def test_corpo_invalido_e_400(self, tmp_path):
        status, _ = api.handle_transcrever(body=b'nao json', origin=ORIGEM_EXTENSAO,
                                           run_sql=lambda q: '1', cookies_file=tmp_path / 'c', wake=lambda: None)

        assert status == 400


class TestServidor:
    def test_ouve_so_na_maquina_local(self):
        servidor = api.make_server(port=0, run_sql=lambda q: '1',
                                   cookies_file=Path('/tmp/nao-usado.txt'), wake=lambda: None)
        try:
            assert servidor.server_address[0] == '127.0.0.1'
        finally:
            servidor.server_close()

    def test_status_responde_para_a_extensao_saber_que_o_mac_esta_ligado(self):
        servidor = api.make_server(port=0, run_sql=lambda q: '1',
                                   cookies_file=Path('/tmp/nao-usado.txt'), wake=lambda: None)
        threading.Thread(target=servidor.handle_request, daemon=True).start()
        try:
            req = urllib.request.Request(f'http://127.0.0.1:{servidor.server_address[1]}/status',
                                         headers={'Origin': ORIGEM_EXTENSAO})
            with urllib.request.urlopen(req, timeout=5) as resp:
                assert json.loads(resp.read()) == {'ok': True}
        finally:
            servidor.server_close()
