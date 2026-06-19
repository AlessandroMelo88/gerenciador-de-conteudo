"""
pipeline_runner.py — Uma execucao completa do pipeline.

Usado pelo daemon e pelo workflow n8n.
"""
import os
from datetime import datetime

import redis as redis_lib

from src.db import get_db_connection, update_status
from src.downloader import download_video
from src.publisher import publish_pending_clips
from src.rss_poller import poll_all_channels
from src.uploader import YouTubeUploader


REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [RUN] {msg}', flush=True)


def _download_pending_videos(db_conn) -> None:
    """Baixa vídeos com status 'pending', um por vez, atualizando status no DB."""
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT youtube_video_id FROM source_videos WHERE status = 'pending' LIMIT 5"
        )
        pending = [row[0] for row in cur.fetchall()]

    for video_id in pending:
        _log(f'Baixando vídeo: {video_id}')
        update_status(db_conn, video_id, 'downloading')
        success = download_video(video_id)
        if success:
            local_path = f'/app/videos/{video_id}.mp4'
            update_status(db_conn, video_id, 'downloaded', local_path=local_path)
            _log(f'Download OK: {video_id}')
        else:
            update_status(db_conn, video_id, 'failed')
            _log(f'Download FALHOU: {video_id}')


def run_pipeline_once(db_conn=None, redis_client=None):
    """Executa RSS/download/AI/video e depois publicacao.

    Falhas isoladas sao logadas, mas nao propagadas para manter o scheduler vivo.
    """
    own_db = db_conn is None
    own_redis = redis_client is None

    if own_db:
        db_conn = get_db_connection()
    if own_redis:
        redis_client = redis_lib.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
        )

    publish_result = None
    try:
        _log('Iniciando ciclo completo')
        try:
            poll_all_channels(db_conn=db_conn, redis_client=redis_client)
        except Exception as exc:
            _log(f'ERRO em poll_all_channels: {exc}')

        try:
            _download_pending_videos(db_conn)
        except Exception as exc:
            _log(f'ERRO em _download_pending_videos: {exc}')

        try:
            publish_result = publish_pending_clips(
                db_conn,
                redis_client,
                uploader=YouTubeUploader(),
            )
        except Exception as exc:
            _log(f'ERRO em publish_pending_clips: {exc}')

        _log(f'Ciclo completo finalizado: {publish_result}')
        return publish_result
    finally:
        if own_db:
            db_conn.close()


if __name__ == '__main__':
    run_pipeline_once()
