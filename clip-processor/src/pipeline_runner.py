"""
pipeline_runner.py — Uma execucao completa do pipeline.

Usado pelo daemon e pelo workflow n8n.
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import redis as redis_lib

from src.db import get_db_connection, update_status
from src.downloader import VIDEOS_DIR, cleanup_stale_downloads, download_video
from src.queue_controls import _CLIP_STATUSES_NEED_RAW, _cleanup_partial
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
DOWNLOAD_WINDOW_CURTO = int(os.environ.get('DOWNLOAD_WINDOW_CURTO', 6))
DOWNLOAD_WINDOW_LONGO = int(os.environ.get('DOWNLOAD_WINDOW_LONGO', 4))

# Só entra na janela vídeo publicado há no máximo esse tanto de dias — mesmo
# com vaga livre e backlog represado, notícia velha nunca é baixada; evita
# gastar disco/banda com conteúdo que não vai mais fazer sentido postar.
FRESHNESS_DAYS = int(os.environ.get('FRESHNESS_DAYS', 3))


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

    result = []
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
                "SELECT sv.youtube_video_id FROM source_videos sv "
                "LEFT JOIN source_channels sc ON sc.id = sv.channel_id "
                "WHERE sv.status = 'pending' AND sv.paused = 0 AND sv.format = %s "
                "AND DATE(sv.published_at) >= %s "
                "ORDER BY sv.priority DESC, "
                "CASE WHEN LOWER(COALESCE(sc.target_niche, '')) = 'futebol' THEN 0 ELSE 1 END, "
                "sv.queue_position IS NULL, sv.queue_position ASC, "
                "sv.published_at DESC LIMIT %s",
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


def reconcile_active_window(db_conn) -> None:
    """Verifica vídeos na janela ativa cujo arquivo não existe mais em disco e limpa."""
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT id, youtube_video_id, local_path, status FROM source_videos "
            "WHERE local_path IS NOT NULL OR status IN ('selecting', 'downloading', 'transcribing')"
        )
        rows = cur.fetchall()

    for row in rows:
        vid_id = row['youtube_video_id']
        local_path = row.get('local_path')
        if not local_path or not os.path.exists(local_path):
            if not _clips_need_raw(db_conn, vid_id):
                update_status(db_conn, vid_id, 'failed', clear_local_path=True)
                _log(f'Reconciliação: vídeo {vid_id} sem arquivo em disco — local_path limpo e status failed')


def _download_pending_videos(db_conn) -> None:
    """Baixa vídeos com status 'pending', um por vez, atualizando status no DB."""
    # Antes de ocupar disco novo, devolve o que ficou preso em download morto —
    # o disk guard de 2GB do downloader mede o disco real, então órfão não
    # limpo vira bloqueio de download.
    cleanup_stale_downloads()
    reconcile_active_window(db_conn)

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

        allow_local = os.getenv('ALLOW_LOCAL_DOWNLOAD', 'true').lower() in ('true', '1', 'yes')
        if not allow_local:
            try:
                _download_pending_videos(db_conn)
            except Exception as exc:
                _log(f'ERRO em _download_pending_videos: {exc}')
                notify('pipeline_failure', {
                    'stage': 'download_pending_videos',
                    'error_msg': str(exc)[:500],
                })
        else:
            _log('ALLOW_LOCAL_DOWNLOAD=true: downloads gerenciados pelo worker local (IP residencial)')

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

        allow_local = os.getenv('ALLOW_LOCAL_DOWNLOAD', 'true').lower() in ('true', '1', 'yes')
        if not allow_local:
            try:
                _download_pending_videos(db_conn)
            except Exception as exc:
                _log(f'ERRO em _download_pending_videos (ciclo ingest): {exc}')
                notify('pipeline_failure', {
                    'stage': 'download_pending_videos',
                    'error_msg': str(exc)[:500],
                })
        else:
            _log('ALLOW_LOCAL_DOWNLOAD=true: downloads gerenciados pelo worker local (IP residencial)')

        _log('Ciclo de ingestão finalizado')
    finally:
        if own_db:
            db_conn.close()


if __name__ == '__main__':
    run_pipeline_once()
