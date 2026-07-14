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
from src.telegram_notifier import notify
from src.uploader import YouTubeUploader


REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [RUN] {msg}', flush=True)


LONGO_PER_CYCLE = 2
CURTO_PER_CYCLE = 3


def _select_pending_videos(db_conn) -> list:
    """Seleciona vídeos pendentes pra baixar nesta rodada, na sequência fixa
    LONGO_PER_CYCLE longos seguidos de CURTO_PER_CYCLE curtos.

    Ordena por published_at DESC (notícia mais recente primeiro), não por
    created_at — com um backlog grande de vídeos represados, ordenar pela
    ordem de descoberta faria notícia de meses atrás furar na frente de
    notícia de hoje só por ter sido enfileirada primeiro. Se não houver o
    suficiente de um formato, baixa só os disponíveis — não puxa do outro
    formato pra completar a cota.
    """
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT youtube_video_id FROM source_videos "
            "WHERE status = 'pending' AND format = 'longo' "
            "ORDER BY published_at DESC LIMIT %s",
            (LONGO_PER_CYCLE,),
        )
        longos = [row['youtube_video_id'] for row in cur.fetchall()]

        cur.execute(
            "SELECT youtube_video_id FROM source_videos "
            "WHERE status = 'pending' AND format = 'curto' "
            "ORDER BY published_at DESC LIMIT %s",
            (CURTO_PER_CYCLE,),
        )
        curtos = [row['youtube_video_id'] for row in cur.fetchall()]

    return longos + curtos


def _download_pending_videos(db_conn) -> None:
    """Baixa vídeos com status 'pending', um por vez, atualizando status no DB."""
    pending = _select_pending_videos(db_conn)

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
            # Phase 6 (CTRL-06): notifica Telegram em falha crítica de estágio.
            notify('pipeline_failure', {
                'stage': 'poll_all_channels',
                'error_msg': str(exc)[:500],
            })

        try:
            _download_pending_videos(db_conn)
        except Exception as exc:
            _log(f'ERRO em _download_pending_videos: {exc}')
            notify('pipeline_failure', {
                'stage': 'download_pending_videos',
                'error_msg': str(exc)[:500],
            })

        try:
            publish_result = publish_pending_clips(
                db_conn,
                redis_client,
            )
        except Exception as exc:
            _log(f'ERRO em publish_pending_clips: {exc}')
            notify('pipeline_failure', {
                'stage': 'publish_pending_clips',
                'error_msg': str(exc)[:500],
            })

        _log(f'Ciclo completo finalizado: {publish_result}')
        return publish_result
    finally:
        if own_db:
            db_conn.close()


def run_publish_only(db_conn=None, redis_client=None):
    """Roda só a publicação de clips aprovados, sem RSS/download/AI.

    Existe pra drenar a fila de aprovados com frequência bem maior que o
    ciclo completo (6h) — assim, quando a cota diária reseta à meia-noite,
    os aprovados não ficam represados esperando o próximo ciclo completo.
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

    try:
        result = publish_pending_clips(db_conn, redis_client)
        _log(f'Publicação isolada finalizada: {result}')
        return result
    except Exception as exc:
        _log(f'ERRO em publish_pending_clips (ciclo isolado): {exc}')
        notify('pipeline_failure', {
            'stage': 'publish_pending_clips_standalone',
            'error_msg': str(exc)[:500],
        })
        return None
    finally:
        if own_db:
            db_conn.close()


if __name__ == '__main__':
    run_pipeline_once()
