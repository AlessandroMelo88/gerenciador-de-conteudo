"""
extensao_api.py — API local que a extensão "Transcrever esta aula" chama.

Roda dentro do local_download_worker, **só em 127.0.0.1**. A extensão manda o link
da aba e a sessão do site dessa aba; aqui:

1. a sessão vira `cookies.txt` (formato Netscape, o que o yt-dlp lê), substituindo
   só as linhas daquele site e preservando as dos outros;
2. o link entra na fila `transcription_jobs` no banco;
3. o laço do worker é acordado, para não esperar o intervalo de 60 s.

Player HLS (Hotmart): a extensão também manda `media_url` (o .m3u8 que o player pediu),
`media_referer` e `title`. O endereço é assinado, então NÃO vai ao banco: fica no
`~/.config/canaldecortes/media-urls.json` (0600), como o cookies.txt, e o worker baixa
só o áudio a partir dele.

A sessão nunca sai do Mac: nem para o servidor, nem para o repositório.

Qualquer página aberta no Chrome consegue fazer requisição para 127.0.0.1. Quem
separa a extensão de um site malicioso é o cabeçalho `Origin`: só extensão manda
`chrome-extension://...`, e página nenhuma consegue forjá-lo.
"""
import importlib.util
import json
import os
import tempfile
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_tw_spec = importlib.util.spec_from_file_location(
    'transcription_worker', Path(__file__).resolve().parent / 'transcription_worker.py')
_tw = importlib.util.module_from_spec(_tw_spec)
_tw_spec.loader.exec_module(_tw)

PORT = int(os.environ.get('TRANSCRICAO_EXTENSAO_PORT', 8765))
HEADER = '# Netscape HTTP Cookie File\n'

# Sufixos de dois níveis mais comuns; o resto usa os dois últimos rótulos.
# Hosts aceitos para o endereço da mídia (sufixo). TRANSCRICAO_MEDIA_HOSTS=a.com,b.com soma
# outros; o resto é recusado com 400 — a API não vira proxy para baixar qualquer coisa.
MEDIA_HOSTS_PADRAO = ('hotmart.com', 'pandavideo.com.br')
MEDIA_URL_MAX = 4000
MEDIA_REFERER_MAX = 1000
TITLE_MAX = 500

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


def media_hosts() -> tuple[str, ...]:
    extras = tuple(h.strip().lower().lstrip('.') for h in
                   (os.environ.get('TRANSCRICAO_MEDIA_HOSTS') or '').split(',') if h.strip())
    return MEDIA_HOSTS_PADRAO + extras


def _host_permitido(url: str) -> bool:
    try:
        parts = urllib.parse.urlsplit(url)
        host = (parts.hostname or '').lower()
    except ValueError:
        return False
    return (parts.scheme == 'https' and not parts.username and not parts.password
            and any(host == h or host.endswith('.' + h) for h in media_hosts()))


def validar_media(media_url, media_referer, title) -> tuple[dict | None, str | None]:
    """(campos limpos, None) ou (None, motivo). Sem media_url, nada a validar."""
    if media_url in (None, ''):
        return None, None
    if not isinstance(media_url, str) or len(media_url) > MEDIA_URL_MAX:
        return None, 'Endereço de mídia inválido.'
    if not _host_permitido(media_url) or '.m3u8' not in urllib.parse.urlsplit(media_url).path:
        return None, 'Endereço de mídia não permitido (só playlist .m3u8 https de hosts liberados).'
    referer = media_referer or ''
    if not isinstance(referer, str) or len(referer) > MEDIA_REFERER_MAX or (referer and not _host_permitido(referer)):
        return None, 'Referer de mídia não permitido.'
    titulo = ''.join(c for c in str(title or '') if c.isprintable()).strip()[:TITLE_MAX]
    return {'media_url': media_url, 'referer': referer, 'title': titulo}, None


def _origem_permitida(origin: str | None) -> bool:
    return bool(origin) and origin.startswith('chrome-extension://')


def handle_transcrever(body: bytes, origin: str | None, run_sql, cookies_file: Path, wake,
                       media_file: Path | None = None) -> tuple[int, dict]:
    """Regra do POST /transcrever, sem HTTP — é o que os testes exercitam."""
    if not _origem_permitida(origin):
        return 403, {'ok': False, 'erro': 'Só a extensão pode chamar esta API.'}
    try:
        dados = json.loads(body)
        url = str(dados['url']).strip()
        cookies = list(dados.get('cookies') or [])
        media, erro_media = validar_media(dados.get('media_url'), dados.get('media_referer'),
                                          dados.get('title'))
    except (ValueError, KeyError, TypeError):
        return 400, {'ok': False, 'erro': 'Pedido inválido.'}
    if not url.startswith(('http://', 'https://')) or len(url) > 500:
        return 400, {'ok': False, 'erro': 'Link inválido.'}

    if erro_media:
        return 400, {'ok': False, 'erro': erro_media}
    titulo = ''.join(c for c in str(dados.get('title') or '') if c.isprintable()).strip()[:TITLE_MAX]

    host = url.split('://', 1)[1].split('/', 1)[0].split(':', 1)[0]
    merge_cookies(cookies_file, registrable_domain(host), cookies)

    colunas, valores = 'source_url', _tw.dollar_quote(url)
    if titulo:
        colunas, valores = colunas + ', title', valores + ', ' + _tw.dollar_quote(titulo)
    resposta = (run_sql(
        f"INSERT INTO transcription_jobs ({colunas}, status, progress_percent, created_at, updated_at) "
        f"VALUES ({valores}, 'pending', 0, NOW(), NOW()) RETURNING id;"
    ) or '').strip()
    job_id = resposta.splitlines()[0] if resposta else ''
    if not job_id.isdigit():
        return 502, {'ok': False, 'erro': 'Não consegui falar com o banco no servidor.'}

    if media:
        # Só depois do job existir; antes do wake(), para o worker já encontrar o endereço.
        _tw.save_media_entry(url, media['media_url'], media['referer'], media['title'], path=media_file)

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
