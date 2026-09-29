"""
downloader.py — Download de vídeos YouTube via yt-dlp com disk guard e retry.

Exporta:
  - download_video(video_id, output_path=None) -> bool
  - cleanup_stale_downloads(max_age_hours=STALE_AFTER_HOURS) -> dict

Comportamento:
  - Verifica espaço em disco (mínimo 2GB) antes de baixar
  - Usa a melhor fonte disponível até 1080p em mp4
  - Tenta até 3 vezes para erros transientes
  - Retorna False imediatamente para erros permanentes (private, removed, unavailable, geo)
  - Aborta se o vídeo foi pausado via painel (progress_hook + check entre retries)
  - Limpa artefatos de download incompleto após cada falha e varre os órfãos de
    crash (processo morto sem passar pelo except) a cada ciclo do pipeline
"""

from __future__ import annotations

import glob
import os
import re
import shutil
import time
from datetime import datetime

import yt_dlp
from yt_dlp.utils import DownloadError

from src.paths import VIDEOS_DIR, YOUTUBE_COOKIES_FILE
from src.queue_controls import PauseAborted

MIN_FREE_BYTES = 2 * 1024**3  # 2 GB
# Respostas definitivas para o ciclo atual. Estreias futuras e lives ainda não
# iniciadas não são falhas transitórias: repetir em intervalos de 60s só segura
# a fila. O item permanece registrado como falho para revisão/reprocessamento
# explícito quando o conteúdo ficar disponível.
PERMANENT_ERRORS = (
    'private',
    'removed',
    'unavailable',
    'geo',
    'premieres in',
    'is a live event',
    'live event',
    'has not started',
    'not currently available',
)

# Sufixos de trabalho do yt-dlp. Nenhum deles é artefato final — o download
# bem-sucedido sempre termina em `<video_id>.mp4` sem sufixo intermediário.
#   .part / .part-FragN.part → download em andamento (ou morto)
#   .ytdl                    → estado do downloader fragmentado (DASH)
#   .fNNN.mp4 / .fNNN.webm   → streams de vídeo/áudio separados, pré-merge
#   .temp.mp4                → saída do merge, antes do rename final
_WORK_ARTIFACT_RE = re.compile(
    r'(\.part(-Frag\d+\.part)?|\.ytdl|\.temp\.(mp4|mkv|webm)|\.f\d+\.(mp4|webm|m4a))$'
)

# Um download de 720p leva minutos, não horas. Passou de 1 hora sem terminar,
# o processo que o segurava morreu ou foi abortado — limpa pra liberar disco.
STALE_AFTER_HOURS = 1
DOWNLOAD_SOCKET_TIMEOUT_SECONDS = int(os.environ.get('DOWNLOAD_SOCKET_TIMEOUT_SECONDS', 60))


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [ACQU] {msg}')


def _cleanup_partial(path: str) -> None:
    """Deleta artefatos de trabalho do yt-dlp gerados por download incompleto.

    O glob é sobre o prefixo sem extensão (`/app/videos/<video_id>`), não sobre
    `output_path`: os streams separados entram como `<video_id>.f298.mp4.part`,
    ou seja, com sufixo ANTES do `.mp4`. Globar `output_path + '*.part'` só
    pegava `<video_id>.mp4.part` e deixava todo o resto no disco.
    """
    prefix = path[:-4] if path.endswith('.mp4') else path
    for candidate in glob.glob(glob.escape(prefix) + '.*'):
        if not _WORK_ARTIFACT_RE.search(candidate):
            continue
        try:
            os.remove(candidate)
            _log(f'Arquivo parcial removido: {candidate}')
        except OSError as exc:
            _log(f'AVISO: falha ao remover {candidate}: {exc}')


def cleanup_stale_downloads(
    max_age_hours: int = STALE_AFTER_HOURS, videos_dir: str = VIDEOS_DIR
) -> dict:
    """Remove artefatos de download parados há mais de `max_age_hours`.

    Rede de segurança pro caso em que `_cleanup_partial` nunca roda: container
    morto, OOM, PostgreSQL fora do ar derrubando o processo. Aí o `except` não
    executa e o `.part` de 1.4GB fica órfão indefinidamente.

    Só olha o primeiro nível de `videos_dir` (clips/ e thumbnails/ têm outro
    ciclo de vida) e só toca em nomes que casam com `_WORK_ARTIFACT_RE` — um
    `<video_id>.mp4` completo nunca casa, então não há risco de apagar raw vivo.

    Returns:
        dict com removed (contagem) e freed_bytes.
    """
    cutoff = time.time() - max_age_hours * 3600
    removed = 0
    freed_bytes = 0

    try:
        entries = os.listdir(videos_dir)
    except OSError as exc:
        _log(f'AVISO: não consegui listar {videos_dir}: {exc}')
        return {'removed': 0, 'freed_bytes': 0}

    for name in entries:
        if not _WORK_ARTIFACT_RE.search(name):
            continue
        path = os.path.join(videos_dir, name)
        try:
            stat = os.stat(path)
            if not os.path.isfile(path) or stat.st_mtime > cutoff:
                continue
            size = stat.st_size
            os.remove(path)
        except OSError as exc:
            _log(f'AVISO: falha ao remover órfão {path}: {exc}')
            continue
        removed += 1
        freed_bytes += size
        _log(f'Órfão de download removido: {name} ({size / 1024**2:.0f} MB)')

    if removed:
        _log(f'Limpeza de órfãos: {removed} arquivo(s), {freed_bytes / 1024**3:.2f} GB liberados')

    return {'removed': removed, 'freed_bytes': freed_bytes}


def download_video(video_id: str, output_path: str | None = None) -> bool:
    """Baixa um vídeo do YouTube em até 1080p mp4.

    Returns:
        True se download bem-sucedido, False caso contrário (inclui pause).
    """
    if output_path is None:
        output_path = f'{VIDEOS_DIR}/{video_id}.mp4'

    disk = shutil.disk_usage(VIDEOS_DIR)
    if disk.free < MIN_FREE_BYTES:
        free_gb = disk.free / (1024**3)
        _log(
            f'Espaço insuficiente em disco: {free_gb:.1f}GB livre (mínimo 2GB). Abortando download.'
        )
        return False

    url = f'https://www.youtube.com/watch?v={video_id}'

    def _abort_if_paused(_status=None):
        try:
            from src.db import get_db_connection
            from src.queue_controls import is_paused

            conn = get_db_connection()
            try:
                if is_paused(conn, youtube_video_id=video_id):
                    raise PauseAborted(f'download pausado: {video_id}')
            finally:
                conn.close()
        except PauseAborted:
            raise
        except Exception:
            pass

    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'no_color': True,
        'noprogress': True,
        # Evita que uma live/estreia futura ou uma conexão pendurada segure o
        # lock de ingestão por horas. Retries transientes continuam controlados
        # pelo loop externo abaixo.
        'socket_timeout': DOWNLOAD_SOCKET_TIMEOUT_SECONDS,
        'retries': 0,
        'fragment_retries': 0,
        'progress_hooks': [_abort_if_paused],
        'remote_components': ['ejs:github'],
        'extractor_args': {'youtube': {'player_client': ['mweb', 'tv', 'ios', 'android']}},
    }

    cookie_file = YOUTUBE_COOKIES_FILE
    if os.path.exists(cookie_file):
        ydl_opts['cookiefile'] = cookie_file
        ydl_opts.pop('extractor_args', None)

    for attempt in range(1, 4):
        try:
            _abort_if_paused()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if not os.path.isfile(output_path):
                _log(f'Download sem arquivo de saída para {video_id}: {output_path}')
                _cleanup_partial(output_path)
                return False
            _log(f'Download concluído: {video_id} → {output_path}')
            return True

        except PauseAborted:
            _log(f'Download abortado (pausado): {video_id}')
            _cleanup_partial(output_path)
            return False

        except DownloadError as exc:
            error_msg = str(exc).lower()
            if any(keyword in error_msg for keyword in PERMANENT_ERRORS):
                _log(f'Erro permanente para {video_id}: {exc}. Sem retry.')
                _cleanup_partial(output_path)
                return False

            _log(f'Tentativa {attempt}/3 falhou para {video_id}: {exc}')
            if attempt < 3:
                _log('Aguardando 60s antes da próxima tentativa...')
                time.sleep(60)

    _cleanup_partial(output_path)
    _log(f'Download falhou após 3 tentativas: {video_id}')
    return False
