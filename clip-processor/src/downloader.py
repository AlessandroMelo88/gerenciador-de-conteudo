"""
downloader.py — Download de vídeos YouTube via yt-dlp com disk guard e retry.

Exporta:
  - download_video(video_id, output_path=None) -> bool

Comportamento:
  - Verifica espaço em disco (mínimo 2GB) antes de baixar
  - Usa formato 720p (bestvideo[height<=720]+bestaudio/best) em mp4
  - Tenta até 3 vezes para erros transientes
  - Retorna False imediatamente para erros permanentes (private, removed, unavailable, geo)
  - Aborta se o vídeo foi pausado via painel (progress_hook + check entre retries)
  - Limpa arquivos .part após cada falha
"""
import glob
import os
import shutil
import time
from datetime import datetime

import yt_dlp
from yt_dlp.utils import DownloadError

from src.queue_controls import PauseAborted

VIDEOS_DIR = '/app/videos'
MIN_FREE_BYTES = 2 * 1024 ** 3  # 2 GB
PERMANENT_ERRORS = ('private', 'removed', 'unavailable', 'geo')


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [ACQU] {msg}')


def _cleanup_partial(path: str) -> None:
    """Deleta arquivos .part gerados por download incompleto."""
    part_files = glob.glob(path + '*.part')
    for part_file in part_files:
        try:
            os.remove(part_file)
            _log(f'Arquivo parcial removido: {part_file}')
        except OSError as exc:
            _log(f'AVISO: falha ao remover {part_file}: {exc}')


def download_video(video_id: str, output_path: str = None) -> bool:
    """Baixa um vídeo do YouTube em formato 720p mp4.

    Returns:
        True se download bem-sucedido, False caso contrário (inclui pause).
    """
    if output_path is None:
        output_path = f'{VIDEOS_DIR}/{video_id}.mp4'

    disk = shutil.disk_usage(VIDEOS_DIR)
    if disk.free < MIN_FREE_BYTES:
        free_gb = disk.free / (1024 ** 3)
        _log(f'Espaço insuficiente em disco: {free_gb:.1f}GB livre (mínimo 2GB). Abortando download.')
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
        'format': 'bestvideo[height<=720]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'no_color': True,
        'noprogress': True,
        'progress_hooks': [_abort_if_paused],
    }

    for attempt in range(1, 4):
        try:
            _abort_if_paused()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
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
