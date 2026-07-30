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
import os
import subprocess
import threading

from src.db import get_db_connection

VIDEOS_DIR = '/app/videos'
TRANSCRIPTS_DIR = os.path.join(VIDEOS_DIR, 'transcripts')

WHISPER_BIN = os.environ.get('WHISPER_CPP_BIN', '/opt/whisper.cpp/build/bin/whisper-cli')
WHISPER_MODEL = os.environ.get('WHISPER_MODEL_PATH', '/opt/whisper.cpp/models/ggml-small.bin')


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


def _run_whisper(job_id, audio_path: str) -> str:
    """Roda whisper-cpp local sobre o wav baixado, gerando um .srt em TRANSCRIPTS_DIR.

    O whisper-cpp com `-osrt -of <prefix>` gera `<prefix>.srt`.

    Raises:
        subprocess.CalledProcessError: whisper-cpp falhou (check=True).
    """
    subprocess.run(
        [
            WHISPER_BIN, '-m', WHISPER_MODEL, '-f', audio_path,
            '-l', 'pt', '-osrt', '-of', f'{TRANSCRIPTS_DIR}/{job_id}',
        ],
        check=True, capture_output=True, timeout=1800,
    )
    return f'{TRANSCRIPTS_DIR}/{job_id}.srt'


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
