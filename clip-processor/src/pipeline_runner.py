"""Execução dos ciclos de ingestão e publicação do pipeline."""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import redis as redis_lib

from src.db import get_db_connection, update_status
from src.downloader import VIDEOS_DIR, cleanup_stale_downloads, download_video
from src.publisher import publish_pending_clips
from src.queue_controls import _CLIP_STATUSES_NEED_RAW, _cleanup_partial
from src.rss_poller import poll_all_channels
from src.telegram_notifier import notify

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
DOWNLOAD_WINDOW_CURTO = int(os.environ.get('DOWNLOAD_WINDOW_CURTO', 6))
DOWNLOAD_WINDOW_LONGO = int(os.environ.get('DOWNLOAD_WINDOW_LONGO', 4))

# A composição em qualidade alta usa preset=slow e pode ultrapassar 30 minutos
# em vídeos longos. O TTL precisa cobrir esse trabalho para que uma segunda
# rodada não entre enquanto a primeira ainda publica.
PIPELINE_LOCK_TIMEOUT_SECONDS = int(os.environ.get('PIPELINE_LOCK_TIMEOUT_SECONDS', 7200))
PUBLISH_LOCK_TIMEOUT_SECONDS = int(os.environ.get('PUBLISH_LOCK_TIMEOUT_SECONDS', 7200))

# Janela de frescor (em dias) para considerar vídeos na fila de download automático.
FRESHNESS_DAYS = int(os.environ.get('FRESHNESS_DAYS', 365))


def _select_pending_videos(db_conn) -> list:
    """Seleciona vídeos pendentes pra repor a janela de download ativo.

    Para cada formato: conta quantos vídeos já ocupam a janela (com arquivo bruto
    em disco, status em processamento ativo ou clips pendentes/aprovados que ainda
    estão sendo trabalhados), calcula o déficit até o teto (DOWNLOAD_WINDOW_LONGO/CURTO)
    e busca só esse tanto, restrito a published_at de hoje ou ontem (FRESHNESS_DAYS),
    ordenado por prioridade e publicado_at DESC. Se um formato já está na janela
    cheia, não baixa nada dele nesta rodada.
    """
    cutoff_date = (datetime.now(SAO_PAULO_TZ) - timedelta(days=FRESHNESS_DAYS)).date()

    result: list[str] = []
    for fmt, window in (('longo', DOWNLOAD_WINDOW_LONGO), ('curto', DOWNLOAD_WINDOW_CURTO)):
        with db_conn.cursor() as cur:
            cur.execute(
                'SELECT COUNT(DISTINCT sv.id) AS c FROM source_videos sv '
                'LEFT JOIN generated_clips gc ON gc.source_video_id = sv.id '
                'WHERE sv.format = %s AND ('
                '  sv.local_path IS NOT NULL '
                "  OR sv.status IN ('downloading', 'downloaded', 'transcribing', 'selecting', 'cutting', 'publishing') "
                "  OR (gc.id IS NOT NULL AND gc.status IN ('pending_cut', 'pending', 'cutting', 'approved'))"
                ')',
                (fmt,),
            )
            occupied = cur.fetchone()['c']

        deficit = max(0, window - occupied)
        if deficit == 0:
            continue

        with db_conn.cursor() as cur:
            cur.execute(
                'SELECT youtube_video_id FROM source_videos '
                "WHERE status = 'pending' AND paused = FALSE AND format = %s "
                'AND DATE(published_at) >= %s '
                'ORDER BY EXISTS ('
                '  SELECT 1 FROM generated_clips gc '
                '  WHERE gc.source_video_id = source_videos.id '
                "  AND gc.status IN ('pending_cut', 'cutting')"
                ') DESC, '
                'priority DESC, '
                'queue_position IS NULL, queue_position ASC, '
                'published_at DESC LIMIT %s',
                (fmt, cutoff_date, deficit),
            )
            result.extend(row['youtube_video_id'] for row in cur.fetchall())

    return result


def _clips_need_raw(db_conn, video_id: str) -> bool:
    """Diz se algum clip desse vídeo ainda precisa do arquivo bruto em disco.

    `process_clip` lê o .mp4 original na hora de cortar, então clip em
    'pending_cut'/'cutting' segura o raw. O guard do sidecar
    (`can_delete_raw`) só olha `source_videos.status`, que nunca recebe
    'cutting' — aqui a checagem é direto em `generated_clips.status`.
    """
    placeholders = ', '.join(['%s'] * len(_CLIP_STATUSES_NEED_RAW))
    with db_conn.cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) AS c FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            f'WHERE sv.youtube_video_id = %s AND gc.status IN ({placeholders})',
            (video_id, *_CLIP_STATUSES_NEED_RAW),
        )
        row = cur.fetchone()
    return bool(row and row.get('c'))


def _discard_failed_download(db_conn, video_id: str) -> None:
    """Marca o download como 'failed' e libera a vaga que ele ocupava na janela.

    Antes só rodava `update_status(..., 'failed')`: o .mp4 meio baixado ficava no
    disco e `local_path` continuava preenchido, então a contagem da janela
    (`local_path IS NOT NULL`) considerava o vídeo ocupando slot PARA SEMPRE —
    com 58 'failed' acumulados o déficit virou 0 e o pipeline parou de baixar.

    Ordem obrigatória (CLAUDE.md, operações destrutivas item 2): apaga o arquivo
    em disco primeiro, com caminho absoluto, confere que ele realmente saiu e só
    então zera `local_path`. Se a remoção falhar, mantém `local_path` — banco e
    disco divergentes são pior que uma vaga presa.
    """
    if _clips_need_raw(db_conn, video_id):
        # Caso raro (falha de re-download com clips já gerados): o raw ainda é
        # insumo do corte, então não apaga nem zera a coluna.
        update_status(db_conn, video_id, 'failed')
        _log(f'Download FALHOU: {video_id} — raw preservado (clips em pending_cut/cutting)')
        return

    raw_path = f'{VIDEOS_DIR}/{video_id}.mp4'
    # Reaproveita o cleanup do queue_controls: apaga <id>.mp4, .part e .ytdl com
    # caminho absoluto, tolerando arquivo inexistente e logando OSError.
    _cleanup_partial(video_id, videos_dir=VIDEOS_DIR)

    if os.path.exists(raw_path):
        update_status(db_conn, video_id, 'failed')
        _log(
            f'Download FALHOU: {video_id} — AVISO: {raw_path} ainda existe, '
            'local_path mantido pra não divergir de disco'
        )
        return

    update_status(db_conn, video_id, 'failed', clear_local_path=True)
    _log(f'Download FALHOU: {video_id} — arquivo removido e local_path limpo')


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
            local_path = f'{VIDEOS_DIR}/{video_id}.mp4'
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
                _discard_failed_download(db_conn, video_id)


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

    if not _acquire_redis_lock(
        redis_client,
        'lock:pipeline_ingest',
        timeout_seconds=PIPELINE_LOCK_TIMEOUT_SECONDS,
    ):
        _log('Ciclo completo já está em execução em outro processo — pulando esta rodada')
        if own_db:
            db_conn.close()
        return None

    publish_result = None
    publish_lock_acquired = False
    try:
        _log('Iniciando ciclo completo')
        try:
            poll_all_channels(db_conn=db_conn, redis_client=redis_client)
        except Exception as exc:
            _log(f'ERRO em poll_all_channels: {exc}')
            # Phase 6 (CTRL-06): notifica Telegram em falha crítica de estágio.
            notify(
                'pipeline_failure',
                {
                    'stage': 'poll_all_channels',
                    'error_msg': str(exc)[:500],
                },
            )

        try:
            _download_pending_videos(db_conn)
        except Exception as exc:
            _log(f'ERRO em _download_pending_videos: {exc}')
            notify(
                'pipeline_failure',
                {
                    'stage': 'download_pending_videos',
                    'error_msg': str(exc)[:500],
                },
            )

        if _acquire_redis_lock(
            redis_client,
            'lock:pipeline_publish',
            timeout_seconds=PUBLISH_LOCK_TIMEOUT_SECONDS,
        ):
            publish_lock_acquired = True
            try:
                publish_result = publish_pending_clips(
                    db_conn,
                    redis_client,
                )
            except Exception as exc:
                _log(f'ERRO em publish_pending_clips: {exc}')
                notify(
                    'pipeline_failure',
                    {
                        'stage': 'publish_pending_clips',
                        'error_msg': str(exc)[:500],
                    },
                )
        else:
            _log(
                'Publicação do ciclo completo já está em execução em outro processo — pulando esta rodada'
            )

        _log(f'Ciclo completo finalizado: {publish_result}')
        return publish_result
    finally:
        if publish_lock_acquired:
            _release_redis_lock(redis_client, 'lock:pipeline_publish')
        _release_redis_lock(redis_client, 'lock:pipeline_ingest')
        if own_db:
            db_conn.close()


def _acquire_redis_lock(redis_client, lock_key: str, timeout_seconds: int = 1800) -> bool:
    if redis_client is None:
        return True
    try:
        return bool(redis_client.set(lock_key, '1', nx=True, ex=timeout_seconds))
    except Exception:
        return True


def _release_redis_lock(redis_client, lock_key: str) -> None:
    if redis_client is None:
        return
    try:
        redis_client.delete(lock_key)
    except Exception:
        pass


def run_publish_only(db_conn=None, redis_client=None):
    """Roda só a publicação de clips aprovados, sem RSS/download/AI."""
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

    if not _acquire_redis_lock(
        redis_client,
        'lock:pipeline_publish',
        timeout_seconds=PUBLISH_LOCK_TIMEOUT_SECONDS,
    ):
        _log('Publicação isolada já em execução em outro processo — pulando esta rodada')
        if own_db:
            db_conn.close()
        return None

    try:
        result = publish_pending_clips(db_conn, redis_client)
        _log(f'Publicação isolada finalizada: {result}')
        return result
    except Exception as exc:
        _log(f'ERRO em publish_pending_clips (ciclo isolado): {exc}')
        notify(
            'pipeline_failure',
            {
                'stage': 'publish_pending_clips_standalone',
                'error_msg': str(exc)[:500],
            },
        )
        return None
    finally:
        _release_redis_lock(redis_client, 'lock:pipeline_publish')
        if own_db:
            db_conn.close()


def run_ingest_cycle(db_conn=None, redis_client=None):
    """Roda RSS/download/AI (poll_all_channels + _download_pending_videos), sem publish."""
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

    if not _acquire_redis_lock(
        redis_client,
        'lock:pipeline_ingest',
        timeout_seconds=PIPELINE_LOCK_TIMEOUT_SECONDS,
    ):
        _log('Ciclo de ingestão já em execução em outro processo — pulando esta rodada')
        if own_db:
            db_conn.close()
        return

    try:
        try:
            poll_all_channels(db_conn=db_conn, redis_client=redis_client)
        except Exception as exc:
            _log(f'ERRO em poll_all_channels (ciclo ingest): {exc}')
            notify(
                'pipeline_failure',
                {
                    'stage': 'poll_all_channels',
                    'error_msg': str(exc)[:500],
                },
            )

        try:
            _download_pending_videos(db_conn)
        except Exception as exc:
            _log(f'ERRO em _download_pending_videos (ciclo ingest): {exc}')
            notify(
                'pipeline_failure',
                {
                    'stage': 'download_pending_videos',
                    'error_msg': str(exc)[:500],
                },
            )

        _log('Ciclo de ingestão finalizado')
    finally:
        _release_redis_lock(redis_client, 'lock:pipeline_ingest')
        if own_db:
            db_conn.close()


if __name__ == '__main__':
    run_pipeline_once()
