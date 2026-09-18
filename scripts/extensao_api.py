"""
extensao_api.py — API local que a extensão "Transcrever esta aula" chama.

Roda dentro do local_download_worker, **só em 127.0.0.1**. A extensão manda o link
da aba e a sessão do site dessa aba; aqui:

1. a sessão vira `cookies.txt` (formato Netscape, o que o yt-dlp lê), substituindo
   só as linhas daquele site e preservando as dos outros;
2. o link entra na fila `transcription_jobs` no banco;
3. o laço do worker é acordado, para não esperar o intervalo de 60 s.

A sessão nunca sai do Mac: nem para o servidor, nem para o repositório.

Qualquer página aberta no Chrome consegue fazer requisição para 127.0.0.1. Quem
separa a extensão de um site malicioso é o cabeçalho `Origin`: só extensão manda
`chrome-extension://...`, e página nenhuma consegue forjá-lo.
"""
import importlib.util
import json
import os
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_tw_spec = importlib.util.spec_from_file_location(
    'transcription_worker', Path(__file__).resolve().parent / 'transcription_worker.py')
_tw = importlib.util.module_from_spec(_tw_spec)
_tw_spec.loader.exec_module(_tw)

PORT = int(os.environ.get('TRANSCRICAO_EXTENSAO_PORT', 8765))
HEADER = '# Netscape HTTP Cookie File\n'

# Sufixos de dois níveis mais comuns; o resto usa os dois últimos rótulos.
_SEGUNDO_NIVEL = {'com', 'net', 'org', 'gov', 'edu', 'co'}


def registrable_domain(host: str) -> str:
    """hub.asimov.academy -> asimov.academy; cursos.exemplo.com.br -> exemplo.com.br."""
    partes = host.lower().strip('.').split('.')
    if len(partes) >= 3 and len(partes[-1]) == 2 and partes[-2] in _SEGUNDO_NIVEL:
        return '.'.join(partes[-3:])
    return '.'.join(partes[-2:])


def _pertence(domain: str, site: str) -> bool:
    d = domain.lower().lstrip('.')
    return d == site or d.endswith('.' + site)


def cookie_to_netscape(c: dict) -> str:
    """Um cookie da API chrome.cookies numa linha do formato Netscape."""
    domain = c['domain']
    include_sub = 'TRUE' if domain.startswith('.') else 'FALSE'
    expiry = int(c.get('expirationDate') or 0)  # sem validade = cookie de sessão
    prefix = '#HttpOnly_' if c.get('httpOnly') else ''
    secure = 'TRUE' if c.get('secure') else 'FALSE'
    return f"{prefix}{domain}\t{include_sub}\t{c.get('path') or '/'}\t{secure}\t{expiry}\t{c['name']}\t{c['value']}"


def merge_cookies(cookies_file: Path, site: str, cookies: list[dict]) -> None:
    """Troca as linhas de `site` pelas recebidas e mantém as dos outros sites.

    Grava num temporário e renomeia (nunca deixa o arquivo pela metade para o
    yt-dlp ler), com permissão 600: é sessão logada.
    """
    cookies_file = Path(cookies_file)
    cookies_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    mantidas = []
    if cookies_file.exists():
        for linha in cookies_file.read_text().splitlines():
            if not linha.strip() or (linha.startswith('#') and not linha.startswith('#HttpOnly_')):
                continue
            dominio = linha.split('\t', 1)[0].removeprefix('#HttpOnly_')
            if not _pertence(dominio, site):
                mantidas.append(linha)

    novas = [cookie_to_netscape(c) for c in cookies if _pertence(c.get('domain', ''), site)]
    conteudo = HEADER + ''.join(l + '\n' for l in mantidas + novas)

    fd, tmp = tempfile.mkstemp(dir=cookies_file.parent, prefix='.cookies-')
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(conteudo)
        os.replace(tmp, cookies_file)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _origem_permitida(origin: str | None) -> bool:
    return bool(origin) and origin.startswith('chrome-extension://')


def handle_transcrever(body: bytes, origin: str | None, run_sql, cookies_file: Path, wake) -> tuple[int, dict]:
    """Regra do POST /transcrever, sem HTTP — é o que os testes exercitam."""
    if not _origem_permitida(origin):
        return 403, {'ok': False, 'erro': 'Só a extensão pode chamar esta API.'}
    try:
        dados = json.loads(body)
        url = str(dados['url']).strip()
        cookies = list(dados.get('cookies') or [])
    except (ValueError, KeyError, TypeError):
        return 400, {'ok': False, 'erro': 'Pedido inválido.'}
    if not url.startswith(('http://', 'https://')) or len(url) > 500:
        return 400, {'ok': False, 'erro': 'Link inválido.'}

    host = url.split('://', 1)[1].split('/', 1)[0].split(':', 1)[0]
    merge_cookies(cookies_file, registrable_domain(host), cookies)

    resposta = (run_sql(
        "INSERT INTO transcription_jobs (source_url, status, progress_percent, created_at, updated_at) "
        f"VALUES ({_tw.dollar_quote(url)}, 'pending', 0, NOW(), NOW()) RETURNING id;"
    ) or '').strip()
    job_id = resposta.splitlines()[0] if resposta else ''
    if not job_id.isdigit():
        return 502, {'ok': False, 'erro': 'Não consegui falar com o banco no servidor.'}

    wake()
    return 200, {'ok': True, 'job_id': int(job_id)}


def make_server(port: int, run_sql, cookies_file: Path, wake) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _responde(self, status: int, dados: dict) -> None:
            corpo = json.dumps(dados).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            origin = self.headers.get('Origin')
            if _origem_permitida(origin):
                self.send_header('Access-Control-Allow-Origin', origin)
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Length', str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_OPTIONS(self):
            self._responde(204 if _origem_permitida(self.headers.get('Origin')) else 403, {})

        def do_GET(self):
            if self.path != '/status':
                return self._responde(404, {'ok': False})
            self._responde(200, {'ok': True})

        def do_POST(self):
            if self.path != '/transcrever':
                return self._responde(404, {'ok': False})
            tamanho = min(int(self.headers.get('Content-Length') or 0), 2_000_000)
            status, dados = handle_transcrever(self.rfile.read(tamanho), self.headers.get('Origin'),
                                               run_sql, cookies_file, wake)
            self._responde(status, dados)

        def log_message(self, *args):  # não despeja cookies nem links no log do launchd
            pass

    return HTTPServer(('127.0.0.1', port), Handler)
