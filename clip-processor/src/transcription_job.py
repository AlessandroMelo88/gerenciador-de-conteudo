"""
transcription_job.py — Worker de "Transcrição Local" (QUICK-1).

Feature isolada do pipeline principal: o operador cola uma URL do YouTube no painel,
o clip-processor baixa o áudio (yt-dlp) e roda whisper-cpp local (sem custo, sem
YouTube, sem cota da Groq API) em background numa thread daemon. Progresso persistido
na tabela `transcription_jobs` (MySQL) — nunca em memória — para sobreviver a
reload/saída da página do operador.

NÃO toca em source_videos/generated_clips: nenhum job de transcrição local entra na
fila de aprovação de clips nem é enviado ao YouTube.

LIMITAÇÃO DOCUMENTADA: whisper-cpp não expõe progresso incremental fácil de parsear
via stdout/stderr entre versões — usamos milestones grosseiros de progresso (10% ao
iniciar download, 50% ao iniciar transcrição, 100% ao terminar), não % real do whisper.
"""
import math
import os
import re
import subprocess
import threading

from src.db import get_db_connection

VIDEOS_DIR = '/app/videos'
TRANSCRIPTS_DIR = os.path.join(VIDEOS_DIR, 'transcripts')

WHISPER_BIN = os.environ.get('WHISPER_CPP_BIN', '/opt/whisper.cpp/build/bin/whisper-cli')
WHISPER_MODEL = os.environ.get('WHISPER_MODEL_PATH', '/opt/whisper.cpp/models/ggml-small.bin')

# Acima desse tanto de áudio, quebra em pedaços pro whisper-cpp não estourar o
# timeout de 1800s por chamada (vídeo de 112min travou inteiro numa passada só).
# Nunca mais que 3 pedaços — pedido explícito do operador, mesmo que cada pedaço
# ainda fique longo pra vídeos muito extensos.
CHUNK_THRESHOLD_SECONDS = 1500
MAX_CHUNKS = 3
WHISPER_TIMEOUT_SECONDS = 3600

SRT_TIME_RE = re.compile(r'(\d\d):(\d\d):(\d\d),(\d\d\d)')


def create_transcription_job(conn, youtube_url: str) -> int:
    """Insere um novo job em transcription_jobs com status='pending' e retorna o id gerado."""
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO transcription_jobs '
            '(youtube_url, status, progress_percent, created_at, updated_at) '
            "VALUES (%s, 'pending', 0, NOW(), NOW())",
            (youtube_url,),
        )
        job_id = cur.lastrowid
    conn.commit()
    return job_id


def update_job(conn, job_id, status=None, progress_percent=None, srt_path=None, error_message=None):
    """Monta um UPDATE dinâmico só com os campos passados (não sobrescreve os demais)."""
    fields = []
    params = []

    if status is not None:
        fields.append('status=%s')
        params.append(status)
    if progress_percent is not None:
        fields.append('progress_percent=%s')
        params.append(progress_percent)
    if srt_path is not None:
        fields.append('srt_path=%s')
        params.append(srt_path)
    if error_message is not None:
        fields.append('error_message=%s')
        params.append(error_message)

    fields.append('updated_at=NOW()')

    sql = f"UPDATE transcription_jobs SET {', '.join(fields)} WHERE id=%s"
    params.append(job_id)

    with conn.cursor() as cur:
        cur.execute(sql, tuple(params))
    conn.commit()


def _download_audio(job_id, youtube_url: str) -> str:
    """Baixa o áudio da URL via yt-dlp em formato wav para TRANSCRIPTS_DIR.

    Raises:
        subprocess.CalledProcessError: yt-dlp falhou (check=True).
    """
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    subprocess.run(
        [
            'yt-dlp', '-x', '--audio-format', 'wav',
            '-o', f'{TRANSCRIPTS_DIR}/{job_id}_audio.%(ext)s',
            youtube_url,
        ],
        check=True, capture_output=True, timeout=600,
    )
    return f'{TRANSCRIPTS_DIR}/{job_id}_audio.wav'


def _audio_duration_seconds(audio_path: str) -> float:
    result = subprocess.run(
        [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_path,
        ],
        check=True, capture_output=True, timeout=60, text=True,
    )
    return float(result.stdout.strip())


def _split_audio(job_id, audio_path: str, num_chunks: int, duration: float) -> list[str]:
    """Divide o wav em `num_chunks` pedaços de duração igual via ffmpeg (recorte por tempo,
    sem recodificar). Retorna os paths dos pedaços, na ordem.
    """
    chunk_duration = duration / num_chunks
    chunk_paths = []
    for i in range(num_chunks):
        start = i * chunk_duration
        chunk_path = f'{TRANSCRIPTS_DIR}/{job_id}_part{i}.wav'
        subprocess.run(
            [
                'ffmpeg', '-y', '-ss', str(start), '-i', audio_path,
                '-t', str(chunk_duration), '-c', 'copy', chunk_path,
            ],
            check=True, capture_output=True, timeout=300,
        )
        chunk_paths.append(chunk_path)
    return chunk_paths


def _run_whisper_on(audio_path: str, out_prefix: str) -> str:
    """Roda whisper-cpp local sobre um wav, gerando `<out_prefix>.srt`.

    Raises:
        subprocess.CalledProcessError: whisper-cpp falhou (check=True).
        subprocess.TimeoutExpired: passou de WHISPER_TIMEOUT_SECONDS.
    """
    subprocess.run(
        [
            WHISPER_BIN, '-m', WHISPER_MODEL, '-f', audio_path,
            '-l', 'pt', '-osrt', '-of', out_prefix,
        ],
        check=True, capture_output=True, timeout=WHISPER_TIMEOUT_SECONDS,
    )
    return f'{out_prefix}.srt'


def _shift_srt_timestamps(srt_text: str, offset_seconds: float) -> str:
    """Soma `offset_seconds` a cada timestamp de um bloco .srt (não renumera — quem
    concatena os blocos cuida da renumeração sequencial).
    """
    def _shift(match):
        h, m, s, ms = (int(g) for g in match.groups())
        total_ms = ((h * 3600 + m * 60 + s) * 1000 + ms) + round(offset_seconds * 1000)
        h, rem = divmod(total_ms, 3600_000)
        m, rem = divmod(rem, 60_000)
        s, ms = divmod(rem, 1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

    return SRT_TIME_RE.sub(_shift, srt_text)


def _merge_srt_chunks(chunk_srt_paths: list[str], chunk_duration: float, final_path: str) -> None:
    """Concatena os .srt de cada pedaço, deslocando os timestamps pelo offset acumulado
    (índice do pedaço * duração do pedaço) e renumerando os blocos sequencialmente.
    """
    merged_blocks = []
    next_index = 1
    for i, srt_path in enumerate(chunk_srt_paths):
        with open(srt_path, encoding='utf-8') as f:
            text = f.read()
        shifted = _shift_srt_timestamps(text, offset_seconds=i * chunk_duration)
        for block in re.split(r'\n\s*\n', shifted.strip()):
            lines = block.split('\n')
            if len(lines) < 2:
                continue
            lines[0] = str(next_index)
            next_index += 1
            merged_blocks.append('\n'.join(lines))

    with open(final_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(merged_blocks) + '\n')


def _run_whisper(job_id, audio_path: str) -> str:
    """Roda whisper-cpp sobre o áudio baixado, gerando `<job_id>.srt` em TRANSCRIPTS_DIR.

    Áudio curto (<= CHUNK_THRESHOLD_SECONDS): passada única, igual antes.
    Áudio longo: quebra em até MAX_CHUNKS pedaços (ffmpeg, recorte sem recodificar),
    roda whisper-cpp em cada um (timeout maior por pedaço), e funde os .srt com
    timestamps ajustados — evita o timeout de 1800s que vídeo inteiro longo batia.
    Pedaços intermediários (.wav e .srt) são apagados ao final, sobra só o .srt final.
    """
    duration = _audio_duration_seconds(audio_path)
    final_srt = f'{TRANSCRIPTS_DIR}/{job_id}.srt'

    if duration <= CHUNK_THRESHOLD_SECONDS:
        return _run_whisper_on(audio_path, f'{TRANSCRIPTS_DIR}/{job_id}')

    num_chunks = min(MAX_CHUNKS, math.ceil(duration / CHUNK_THRESHOLD_SECONDS))
    chunk_duration = duration / num_chunks
    chunk_wavs = _split_audio(job_id, audio_path, num_chunks, duration)

    chunk_srts = []
    try:
        for i, chunk_wav in enumerate(chunk_wavs):
            chunk_srts.append(_run_whisper_on(chunk_wav, f'{TRANSCRIPTS_DIR}/{job_id}_part{i}'))
        _merge_srt_chunks(chunk_srts, chunk_duration, final_srt)
    finally:
        for path in chunk_wavs + chunk_srts:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    return final_srt


def process_transcription_job(job_id: int) -> None:
    """Executa o ciclo completo de uma transcrição local (roda em thread de background).

    Caminho feliz: downloading(10%) -> _download_audio -> transcribing(50%) ->
    _run_whisper -> done(100%, srt_path).

    Erro: qualquer exceção marca status='failed' com error_message preenchido —
    NUNCA propaga (thread de background não pode matar o processo).
    """
    conn = get_db_connection()
    audio_path = None
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT youtube_url FROM transcription_jobs WHERE id=%s', (job_id,))
            row = cur.fetchone()
        youtube_url = row['youtube_url']

        update_job(conn, job_id, status='downloading', progress_percent=10)
        audio_path = _download_audio(job_id, youtube_url)

        update_job(conn, job_id, status='transcribing', progress_percent=50)
        srt_path = _run_whisper(job_id, audio_path)

        update_job(conn, job_id, status='done', progress_percent=100, srt_path=srt_path)
    except Exception as e:  # noqa: BLE001 — thread de background não pode propagar
        update_job(conn, job_id, status='failed', error_message=str(e))
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass
        conn.close()


def start_transcription_job(youtube_url: str) -> int:
    """Cria o job no banco e dispara a thread de background que processa a transcrição.

    Retorna imediatamente com o job_id — o endpoint HTTP não espera o whisper terminar.
    Nunca compartilha conexão pymysql entre threads: esta função fecha sua própria
    conexão, a thread abre a sua via get_db_connection() dentro de process_transcription_job.
    """
    conn = get_db_connection()
    job_id = create_transcription_job(conn, youtube_url)
    conn.close()

    thread = threading.Thread(target=process_transcription_job, args=(job_id,), daemon=True)
    thread.start()

    return job_id
