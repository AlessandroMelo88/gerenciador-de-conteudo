"""
transcription_worker.py — Transcrição multiplataforma, executada no Mac.

O painel grava um job `pending` em `transcription_jobs`; o `local_download_worker`
chama `process_one_job` a cada ciclo. Aqui:

1. reivindica um job de forma atômica (FOR UPDATE SKIP LOCKED);
2. baixa a aula (vídeo até 720p) com yt-dlp pelo IP residencial — qualquer site que o yt-dlp
   aceite (YouTube, TikTok, Instagram, Vimeo...). No servidor o YouTube bloqueia
   IP de datacenter ("Sign in to confirm you're not a bot");
3. converte para mono 16 kHz e corta em pedaços de 20 min (cabe no limite de
   25 MB da API);
4. transcreve cada pedaço no Groq Whisper e remonta os timestamps;
5. guarda o arquivo da aula em `conteudo-cursos/aulas/<id>.<ext>`, no Mac e na
   A1 (mesma árvore nos dois), para o botão "Baixar aula" do painel;
6. grava título, duração, plataforma, texto corrido e .srt **no banco** — é a
   base de conhecimento, não um arquivo que se perde.

Até 17/09/2026 isso rodava no servidor com whisper.cpp a 1× tempo real e batia
no timeout de 1800 s em qualquer vídeo acima de ~90 min.

As dependências externas (download, corte, transcrição) entram por parâmetro em
`process_one_job`, para os testes não tocarem rede nem ffmpeg.
"""
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path

GROQ_URL = 'https://api.groq.com/openai/v1/audio/transcriptions'
GROQ_MODEL = 'whisper-large-v3-turbo'  # o mesmo do pipeline (clip-processor/src/transcriber.py)
# O Cloudflare na frente do Groq recusa o User-Agent padrão do urllib
# ("Python-urllib/3.x") com HTTP 403 "error code: 1010".
USER_AGENT = 'canaldecortes-transcricao/1.0'

CHUNK_SECONDS = 1200        # 20 min a 32 kbps ≈ 4,8 MB, longe do teto de 25 MB
PARAGRAPH_GAP_SECONDS = 1.5  # pausa maior que isso abre parágrafo novo no texto
STUCK_MINUTES = 60           # job preso em andamento há mais que isso volta como falha

PROJECT_ENV = Path(__file__).resolve().parent.parent / '.env'

# Arquivo da aula. A mesma árvore existe no Mac (aqui) e na A1 (bind de
# /mnt/videos/conteudo-cursos no container php): o disco `conteudo-cursos` do painel
# aponta para as duas. Fora de public/ — é material pago, só sai por rota autenticada.
LOCAL_CURSOS_DIR = Path(__file__).resolve().parent.parent / 'painel/storage/app/private/conteudo-cursos'

# Vídeo até 720p basta para rever a aula e segura o tamanho (~1 GB por hora de aula).
# Fonte só de áudio (podcast) cai no `b` e vem como áudio mesmo.
MEDIA_FORMAT = 'bv*[height<=720]+ba/b[height<=720]/b'

# Login de plataforma de curso (Hotmart, Asimov, Vimeo...). Arquivo Netscape
# exportado pela extensão "Get cookies.txt LOCALLY" do Chrome. Fica só no Mac:
# fora do repositório (público) e fora do servidor. Nunca `--cookies-from-browser`,
# que abre a caixa do chaveiro do macOS a cada execução e trava o worker.
COOKIES_FILE = Path(os.environ.get(
    'TRANSCRICAO_COOKIES', '~/.config/canaldecortes/cookies.txt',
)).expanduser()

PROGRESS_MARK = '[progresso]'

_LOGIN_HINTS = ('logged-in', 'login', 'sign in', 'log in', 'cookies', 'members only',
                'registered users', 'http error 401', 'http error 403')


# ---------------------------------------------------------------- formatos

def format_srt_time(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    h, rest = divmod(total_ms, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def segments_to_srt(segments: list[dict]) -> str:
    blocks = []
    for seg in segments:
        text = (seg.get('text') or '').strip()
        if not text:
            continue
        n = len(blocks) + 1
        blocks.append(f"{n}\n{format_srt_time(seg['start'])} --> {format_srt_time(seg['end'])}\n{text}\n")
    return '\n'.join(blocks)


def segments_to_text(segments: list[dict]) -> str:
    """Texto corrido para leitura: frases juntas, parágrafo novo a cada pausa longa."""
    paragraphs: list[list[str]] = []
    last_end = None
    for seg in segments:
        text = (seg.get('text') or '').strip()
        if not text:
            continue
        if last_end is None or seg['start'] - last_end > PARAGRAPH_GAP_SECONDS:
            paragraphs.append([])
        paragraphs[-1].append(text)
        last_end = seg['end']
    return '\n\n'.join(' '.join(p) for p in paragraphs)


def merge_chunks(chunks: list[tuple[float, list[dict]]]) -> list[dict]:
    """Junta os segmentos de cada pedaço deslocando pelo início real do pedaço."""
    merged = []
    for offset, segments in chunks:
        for seg in segments:
            merged.append({
                'start': seg['start'] + offset,
                'end': seg['end'] + offset,
                'text': seg['text'],
            })
    return merged


def dollar_quote(text: str) -> str:
    """Literal SQL do PostgreSQL que dispensa escapar aspas: $tag$...$tag$.

    A tag é aleatória e conferida contra o texto — transcrição é texto livre,
    vindo de qualquer site, e nunca pode fechar o literal antes da hora.
    """
    while True:
        tag = f'$t{secrets.token_hex(6)}$'
        if tag not in text:
            return f'{tag}{text}{tag}'


# ---------------------------------------------------------------- chave

def load_groq_key(env_file: Path = PROJECT_ENV) -> str | None:
    """GROQ_API_KEY do ambiente ou do .env do projeto (que nunca vai ao git)."""
    key = os.environ.get('GROQ_API_KEY')
    if key:
        return key
    try:
        for line in Path(env_file).read_text().splitlines():
            if line.startswith('GROQ_API_KEY='):
                value = line.split('=', 1)[1].strip().strip('"').strip("'")
                return value or None
    except OSError:
        return None
    return None


# ---------------------------------------------------------------- etapas reais

def yt_dlp_args(url: str, template, cookies_file: Path = COOKIES_FILE) -> list[str]:
    """Linha de comando do yt-dlp para baixar a aula (vídeo até 720p, em mp4).

    `generic:impersonate` se passa por Chrome (via curl_cffi) no extractor genérico,
    que é por onde entram as plataformas de curso — sem isso a Asimov devolve
    HTTP 403 do Cloudflare anti-bot antes mesmo de pedir login.
    """
    args = ['yt-dlp', '--no-update', '--no-playlist', '--newline',
            # "download:" é o seletor de tipo do yt-dlp ([TIPO:]MODELO), não sai na
            # linha; o marcador literal é o PROGRESS_MARK.
            '--progress', '--progress-template', f'download:{PROGRESS_MARK} %(progress._percent_str)s',
            '-f', MEDIA_FORMAT, '--merge-output-format', 'mp4', '--write-info-json',
            '--extractor-args', 'generic:impersonate', '-o', str(template)]
    if Path(cookies_file).is_file():
        args += ['--cookies', str(cookies_file)]
    return args + [url]


def parse_progress(line: str) -> float | None:
    """'[progresso]  42.3%' -> 42.3. Qualquer outra linha do yt-dlp -> None."""
    if not line.startswith(PROGRESS_MARK):
        return None
    try:
        return float(line[len(PROGRESS_MARK):].strip().rstrip('%'))
    except ValueError:
        return None


def explain_error(message: str, cookies_file: Path = COOKIES_FILE) -> str:
    """Erro de login vira instrução do que fazer; qualquer outro passa intacto."""
    lower = message.lower()
    if not any(hint in lower for hint in _LOGIN_HINTS):
        return message
    if Path(cookies_file).is_file():
        return (f'{message}\n\nO site pediu login e o cookies.txt não bastou: provavelmente '
                f'expirou. Entre de novo no site pelo Chrome e exporte outra vez para {cookies_file}.')
    return (f'{message}\n\nEste site exige login. Entre nele pelo Chrome, exporte os cookies com a '
            f'extensão "Get cookies.txt LOCALLY" e salve em {cookies_file}.')


def _arquivo_baixado(workdir: Path) -> Path | None:
    """O `aula.<ext>` final: ignora info.json, pedaço .part e as faixas separadas
    (`aula.f137.mp4`) que o yt-dlp junta e apaga."""
    for p in sorted(workdir.glob('aula.*')):
        if p.name.count('.') == 1 and p.suffix not in ('.json', '.part', '.ytdl'):
            return p
    return None


def download_media(url: str, workdir: Path, on_progress=None) -> tuple[Path, dict]:
    """Baixa a aula e os metadados. Levanta RuntimeError com a mensagem do yt-dlp.

    `on_progress(percent)` recebe o avanço do download; se ele levantar (job pausado
    ou apagado), o yt-dlp é encerrado na hora.
    """
    proc = subprocess.Popen(yt_dlp_args(url, workdir / 'aula.%(ext)s'), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, errors='replace')
    try:
        for line in proc.stdout:
            percent = parse_progress(line.strip())
            if percent is not None and on_progress:
                on_progress(percent)
        stderr = proc.stderr.read()
        proc.wait(timeout=1800)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()

    if proc.returncode != 0:
        erro = [l for l in stderr.splitlines() if 'ERROR' in l] or stderr.splitlines()[-1:]
        raise RuntimeError(explain_error((erro[-1] if erro else 'yt-dlp falhou sem mensagem')[:500]))

    info_files = list(workdir.glob('aula*.info.json'))
    info = json.loads(info_files[0].read_text()) if info_files else {}
    media = _arquivo_baixado(workdir)
    if not media:
        raise RuntimeError('yt-dlp terminou sem gerar o arquivo da aula')
    return media, info


def guardar_aula(job_id: int, media: Path, local_root: Path = LOCAL_CURSOS_DIR,
                 upload=None) -> tuple[str, int]:
    """Move o arquivo baixado para `conteudo-cursos/aulas/<id>.<ext>` no Mac e, com
    `upload(arquivo, caminho_relativo)`, manda a mesma árvore para a A1.

    Chave é o id do job, não o título: título tem acento, barra e muda; o nome
    bonito sai na hora do download. Devolve (caminho relativo, bytes).
    """
    relativo = f'aulas/{int(job_id)}{media.suffix.lower()}'
    destino = Path(local_root) / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(media), destino)
    if upload:
        upload(destino, relativo)
    return relativo, destino.stat().st_size


def _probe_duration(path: Path) -> float:
    res = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
        capture_output=True, text=True, timeout=60,
    )
    try:
        return float(res.stdout.strip())
    except ValueError:
        return 0.0


def split_audio(audio: Path, workdir: Path) -> list[tuple[float, Path]]:
    """Mono 16 kHz 32 kbps em pedaços de CHUNK_SECONDS. Devolve (início real, arquivo)."""
    pattern = workdir / 'parte_%03d.mp3'
    res = subprocess.run(
        ['ffmpeg', '-v', 'error', '-y', '-i', str(audio), '-vn', '-ac', '1', '-ar', '16000',
         '-b:a', '32k', '-f', 'segment', '-segment_time', str(CHUNK_SECONDS), str(pattern)],
        capture_output=True, text=True, errors='replace', timeout=1800,
    )
    if res.returncode != 0:
        raise RuntimeError(f'ffmpeg falhou: {res.stderr.strip()[-300:]}')

    chunks, offset = [], 0.0
    for part in sorted(workdir.glob('parte_*.mp3')):
        chunks.append((offset, part))
        offset += _probe_duration(part)  # soma a duração real, não CHUNK_SECONDS
    if not chunks:
        raise RuntimeError('ffmpeg não gerou nenhum pedaço de áudio')
    return chunks


def groq_transcribe(chunk: Path, api_key: str | None = None) -> list[dict]:
    """Um pedaço no Groq Whisper. Multipart na mão: a chave fica só em memória,
    nunca em argumento de processo (que aparece no `ps`)."""
    api_key = api_key or load_groq_key()
    if not api_key:
        raise RuntimeError('GROQ_API_KEY ausente no ambiente e no .env do projeto')

    boundary = uuid.uuid4().hex
    fields = {'model': GROQ_MODEL, 'response_format': 'verbose_json', 'temperature': '0'}
    body = b''
    for name, value in fields.items():
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
                 f'{value}\r\n').encode()
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
             f'filename="{chunk.name}"\r\nContent-Type: audio/mpeg\r\n\r\n').encode()
    body += chunk.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()

    req = urllib.request.Request(GROQ_URL, data=body, method='POST', headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'User-Agent': USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors='replace')[:300]
        raise RuntimeError(f'Groq HTTP {e.code}: {detail}') from None

    return [{'start': float(s['start']), 'end': float(s['end']), 'text': s['text']}
            for s in payload.get('segments', [])]


# ---------------------------------------------------------------- orquestração

CLAIM_SQL = (
    "UPDATE transcription_jobs SET status = 'downloading', progress_percent = 5, "
    "error_message = NULL, updated_at = NOW() "
    "WHERE id = (SELECT id FROM transcription_jobs WHERE status = 'pending' "
    "ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED) "
    "RETURNING id, source_url;"
)

# Worker que morreu no meio (Mac desligado, reboot) deixaria o job andando para
# sempre na tela. Devolve como falha visível em vez de reprocessar às cegas.
RELEASE_STUCK_SQL = (
    "UPDATE transcription_jobs SET status = 'failed', "
    "error_message = 'Interrompido: o worker do Mac parou no meio. Envie de novo.', "
    "updated_at = NOW() WHERE status IN ('downloading', 'transcribing') "
    f"AND updated_at < NOW() - INTERVAL '{STUCK_MINUTES} minutes';"
)


class Cancelado(Exception):
    """O job foi pausado ou apagado no painel enquanto rodava."""


def _progress_sql(job_id: int, status: str, percent: int) -> str:
    """Só avança job que ainda está andando: pausado ou apagado não volta a correr.
    Sem linha no RETURNING = o operador parou o job."""
    return (f"UPDATE transcription_jobs SET status = '{status}', progress_percent = {int(percent)}, "
            f"updated_at = NOW() WHERE id = {int(job_id)} "
            f"AND status IN ('downloading', 'transcribing') RETURNING id;")


def _done_sql(job_id: int, info: dict, text: str, srt: str,
             media_path: str | None = None, media_bytes: int | None = None,
             aviso: str | None = None) -> str:
    title = (info.get('title') or '')[:500]
    platform = (info.get('extractor_key') or info.get('extractor') or '')[:50]
    duration = info.get('duration')
    duration_sql = str(int(duration)) if isinstance(duration, (int, float)) else 'NULL'
    return (
        "UPDATE transcription_jobs SET status = 'done', progress_percent = 100, "
        f"title = {dollar_quote(title)}, platform = {dollar_quote(platform)}, "
        f"duration_seconds = {duration_sql}, "
        f"transcript_text = {dollar_quote(text)}, transcript_srt = {dollar_quote(srt)}, "
        f"media_path = {dollar_quote(media_path) if media_path else 'NULL'}, "
        f"media_bytes = {int(media_bytes) if media_bytes else 'NULL'}, "
        f"error_message = {dollar_quote(aviso[:1000]) if aviso else 'NULL'}, "
        f"updated_at = NOW() WHERE id = {int(job_id)};"
    )


def _failed_sql(job_id: int, message: str) -> str:
    return (f"UPDATE transcription_jobs SET status = 'failed', "
            f"error_message = {dollar_quote(message[:1000])}, updated_at = NOW() "
            f"WHERE id = {int(job_id)};")


def process_one_job(run_sql, run_sql_stdin, workdir_root: Path | None = None,
                    download=download_media, split=split_audio, transcribe=groq_transcribe,
                    guardar=None) -> bool:
    """Processa no máximo um job. Devolve True se pegou algum (concluído, falho ou parado).

    Barra de progresso: 5 → 30 % no download (real, do yt-dlp), 30 → 95 % na
    transcrição (por pedaço), 95 % enquanto guarda o arquivo da aula, 100 % ao gravar. Cada aviso também é a checagem de
    pausa: se o painel pausou ou apagou, o job para ali sem gravar nada.
    """
    run_sql(RELEASE_STUCK_SQL)
    row = (run_sql(CLAIM_SQL) or '').strip()
    if not row:
        return False

    job_id_raw, url = row.splitlines()[0].split('\t', 1)
    job_id = int(job_id_raw)
    enviado = {'percent': 5}

    def avisa(status: str, percent: int, forcar: bool = False) -> None:
        percent = max(enviado['percent'], min(int(percent), 99))  # nunca anda para trás
        # Cada aviso é uma ida ao servidor por ssh: só manda de 5 em 5 pontos.
        if not forcar and percent - enviado['percent'] < 5:
            return
        enviado['percent'] = percent
        if not (run_sql(_progress_sql(job_id, status, percent)) or '').strip():
            raise Cancelado()

    workdir = Path(tempfile.mkdtemp(prefix=f'transcricao_{job_id}_', dir=workdir_root))
    try:
        media, info = download(url, workdir,
                               on_progress=lambda p: avisa('downloading', 5 + p * 25 / 100))
        avisa('transcribing', 30, forcar=True)

        chunks = split(media, workdir)
        results = []
        for i, (offset, part) in enumerate(chunks, start=1):
            results.append((offset, transcribe(part)))
            avisa('transcribing', 30 + 65 * i / len(chunks), forcar=True)
        segments = merge_chunks(results)

        # O texto já custou download e Groq: arquivo que não subiu não derruba a
        # transcrição, só fica sem o botão da aula e com o motivo na tela.
        media_path = media_bytes = aviso = None
        if guardar:
            try:
                media_path, media_bytes = guardar(job_id, media)
            except Exception as e:
                aviso = f'Transcrição salva, mas o arquivo da aula não foi guardado: {e}'

        run_sql_stdin(_done_sql(job_id, info, segments_to_text(segments), segments_to_srt(segments),
                                media_path, media_bytes, aviso))
    except Cancelado:
        pass  # pausado ou apagado no painel: o estado já é o que o operador escolheu
    except Exception as e:  # qualquer falha vira mensagem legível na tela, nunca job preso
        run_sql_stdin(_failed_sql(job_id, str(e) or e.__class__.__name__))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return True
