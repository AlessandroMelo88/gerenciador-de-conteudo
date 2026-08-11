"""
pipeline_runner.py — Uma execucao completa do pipeline.

Usado pelo daemon e pelo workflow n8n.
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import redis as redis_lib

from src.db import get_db_connection, update_status
from src.downloader import cleanup_stale_downloads, download_video
from src.publisher import publish_pending_clips
from src.rss_poller import poll_all_channels
from src.telegram_notifier import notify
from src.uploader import YouTubeUploader


REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
SAO_PAULO_TZ = ZoneInfo('America/Sao_Paulo')


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [RUN] {msg}', flush=True)


# Janela: no máximo esses tantos vídeos com arquivo em disco (local_path IS NOT
# NULL) ao mesmo tempo, por formato — não baixa mais que isso independente do
# tamanho do backlog. Repõe só o déficit (janela - ocupação atual) a cada rodada,
# então vaga aberta (por publicação concluída ou por exclusão manual no painel)
# é reposta na rodada seguinte, mantendo a janela sempre perto de cheia.
DOWNLOAD_WINDOW_CURTO = 6
DOWNLOAD_WINDOW_LONGO = 4

# Só entra na janela vídeo publicado há no máximo esse tanto de dias — mesmo
# com vaga livre e backlog represado, notícia velha nunca é baixada; evita
# gastar disco/banda com conteúdo que não vai mais fazer sentido postar.
FRESHNESS_DAYS = 1


def _select_pending_videos(db_conn) -> list:
    """Seleciona vídeos pendentes pra repor a janela de download ativo.

    Para cada formato: conta quantos vídeos já ocupam a janela (local_path
    setado E status ainda em andamento — linha morta com arquivo em disco não
    ocupa slot), calcula o déficit até o teto (DOWNLOAD_WINDOW_LONGO/CURTO) e busca
    só esse tanto, restrito a published_at de hoje ou ontem (FRESHNESS_DAYS),
    ordenado por published_at DESC (notícia mais recente primeiro). Se um
    formato já está na janela cheia, não baixa nada dele nesta rodada — não
    puxa do outro formato pra completar.
    """
    cutoff_date = (datetime.now(SAO_PAULO_TZ) - timedelta(days=FRESHNESS_DAYS)).date()

    result = []
    for fmt, window in (('longo', DOWNLOAD_WINDOW_LONGO), ('curto', DOWNLOAD_WINDOW_CURTO)):
        with db_conn.cursor() as cur:
            cur.execute(
                'SELECT COUNT(*) AS c FROM source_videos '
                'WHERE format=%s AND local_path IS NOT NULL '
                "AND status IN ('downloading', 'downloaded', 'selecting')",
                (fmt,),
            )
            occupied = cur.fetchone()['c']

        deficit = max(0, window - occupied)
        if deficit == 0:
            continue

        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT youtube_video_id FROM source_videos "
                "WHERE status = 'pending' AND paused = 0 AND format = %s "
                "AND DATE(published_at) >= %s "
                'ORDER BY priority DESC, '
                'queue_position IS NULL, queue_position ASC, '
                'published_at DESC LIMIT %s',
                (fmt, cutoff_date, deficit),
            )
            result.extend(row['youtube_video_id'] for row in cur.fetchall())

    return result


def _download_pending_videos(db_conn) -> None:
    """Baixa vídeos com status 'pending', um por vez, atualizando status no DB."""
    # Antes de ocupar disco novo, devolve o que ficou preso em download morto —
    # o disk guard de 2GB do downloader mede o disco real, então órfão não
    # limpo vira bloqueio de download.
    cleanup_stale_downloads()

    pending = _select_pending_videos(db_conn)

    for video_id in pending:
        # Pausa pode ter sido aplicada entre a seleção e o início do download.
        with db_conn.cursor() as cur:
            cur.execute(
                'SELECT paused FROM source_videos WHERE youtube_video_id = %s',
                (video_id,),
            )
            row = cur.fetchone()
        if row and row.get('paused'):
            _log(f'Download pulado (pausado): {video_id}')
            continue

        _log(f'Baixando vídeo: {video_id}')
        update_status(db_conn, video_id, 'downloading')
        success = download_video(video_id)
        if success:
            local_path = f'/app/videos/{video_id}.mp4'
            update_status(db_conn, video_id, 'downloaded', local_path=local_path)
            _log(f'Download OK: {video_id}')
        else:
            with db_conn.cursor() as cur:
                cur.execute(
                    'SELECT paused FROM source_videos WHERE youtube_video_id = %s',
                    (video_id,),
                )
                paused_row = cur.fetchone()
            if paused_row and paused_row.get('paused'):
                update_status(db_conn, video_id, 'pending')
                _log(f'Download abortado por pause — volta pra pending: {video_id}')
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


def run_ingest_cycle(db_conn=None, redis_client=None):
    """Roda RSS/download/AI (poll_all_channels + _download_pending_videos), sem publish.

    Substitui o ciclo completo de 6h como job principal — poll_all_channels já
    processa vídeos 'downloaded' (transcrição/seleção IA) e clips 'pending_cut'
    (corte), então rodar isso a cada 20min (mesma cadência de run_publish_only)
    faz a janela de download (DOWNLOAD_WINDOW_*) repor vaga logo após um vídeo
    ser excluído manualmente no painel, em vez de esperar até 6h.
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
        try:
            poll_all_channels(db_conn=db_conn, redis_client=redis_client)
        except Exception as exc:
            _log(f'ERRO em poll_all_channels (ciclo ingest): {exc}')
            notify('pipeline_failure', {
                'stage': 'poll_all_channels',
                'error_msg': str(exc)[:500],
            })

        try:
            _download_pending_videos(db_conn)
        except Exception as exc:
            _log(f'ERRO em _download_pending_videos (ciclo ingest): {exc}')
            notify('pipeline_failure', {
                'stage': 'download_pending_videos',
                'error_msg': str(exc)[:500],
            })

        _log('Ciclo de ingestão finalizado')
    finally:
        if own_db:
            db_conn.close()


if __name__ == '__main__':
    run_pipeline_once()
