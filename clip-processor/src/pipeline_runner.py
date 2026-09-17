"""
pipeline_runner.py — Uma execucao completa do pipeline.

Usado pelo daemon e pelo workflow n8n.
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import redis as redis_lib

from src.db import get_db_connection, update_status
from src.fair_queue import channel_cap, fair_pick
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


# Janela: no máximo DOWNLOAD_WINDOW_PER_CHANNEL vídeos ocupando o servidor por
# canal destino ativo do nicho — arquivo em disco, em processamento ou com clip
# ainda na fila de aprovação. Hoje: Futebol em Cortes + Fatos & Debates = 20 no
# total. Cada canal destino novo soma mais 10 ao nicho dele. Repõe só o déficit
# (janela - ocupação atual) a cada rodada, independente do tamanho do backlog.
DOWNLOAD_WINDOW_PER_CHANNEL = int(os.environ.get('DOWNLOAD_WINDOW_PER_CHANNEL', 10))

# Fallback só se a consulta aos canais destino falhar.
DOWNLOAD_WINDOW_FUTEBOL = int(os.environ.get('DOWNLOAD_WINDOW_FUTEBOL', DOWNLOAD_WINDOW_PER_CHANNEL))
DOWNLOAD_WINDOW_POLITICA = int(os.environ.get('DOWNLOAD_WINDOW_POLITICA', DOWNLOAD_WINDOW_PER_CHANNEL))

# Aliases de compatibilidade
DOWNLOAD_WINDOW_CURTO = int(os.environ.get('DOWNLOAD_WINDOW_CURTO', 6))
DOWNLOAD_WINDOW_LONGO = int(os.environ.get('DOWNLOAD_WINDOW_LONGO', 4))

# Só entra na janela vídeo publicado há no máximo esse tanto de dias — mesmo
# com vaga livre e backlog represado, notícia velha nunca é baixada; evita
# gastar disco/banda com conteúdo que não vai mais fazer sentido postar.
FRESHNESS_DAYS = int(os.environ.get('FRESHNESS_DAYS', 3))

# Teto de vagas da janela por canal de origem. Vazio = calculado a cada rodada
# (janela do nicho ÷ canais de origem ativos), que é o que se quer no dia a dia:
# canal novo entra e o teto de todo mundo se ajusta sozinho.
DOWNLOAD_MAX_PER_SOURCE_CHANNEL = os.environ.get('DOWNLOAD_MAX_PER_SOURCE_CHANNEL') or None

# Quantos candidatos buscar por vaga livre. O round-robin precisa de mais de um
# canal na mão para intercalar; pedir só o déficit traria os N primeiros do
# mesmo canal prolífico e não haveria o que alternar.
CANDIDATES_PER_SLOT = int(os.environ.get('CANDIDATES_PER_SLOT', 5))


def _niche_windows(db_conn) -> list:
    """Teto da janela por nicho: DOWNLOAD_WINDOW_PER_CHANNEL × canais destino ativos.

    Futebol vem primeiro (prioridade de reposição). Nicho sem canal destino ativo
    não entra — não há para onde publicar, então não baixa. Se a consulta falhar,
    usa DOWNLOAD_WINDOW_FUTEBOL/POLITICA para não parar a ingestão.
    """
    try:
        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT LOWER(TRIM(niche)) AS niche, COUNT(*) AS n "
                "FROM destination_channels WHERE active = TRUE "
                "GROUP BY LOWER(TRIM(niche))"
            )
            rows = cur.fetchall() or []
    except Exception as e:
        _log(f'Falha ao ler canais destino ({e}) — usando janela padrão')
        return [('futebol', DOWNLOAD_WINDOW_FUTEBOL), ('politica', DOWNLOAD_WINDOW_POLITICA)]

    windows = [(row['niche'], int(row['n']) * DOWNLOAD_WINDOW_PER_CHANNEL) for row in rows if row.get('niche')]
    return sorted(windows, key=lambda w: (w[0] != 'futebol', w[0]))


def _active_source_channels(db_conn, niche: str) -> int:
    """Quantos canais de origem ativos o nicho tem — base do teto por canal."""
    with db_conn.cursor() as cur:
        cur.execute(
            'SELECT COUNT(*) AS c FROM source_channels sc '
            'WHERE sc.active = TRUE AND sc.blacklisted = FALSE AND ('
            "  (LOWER(COALESCE(sc.target_niche, 'futebol')) = %s) "
            "  OR (%s = 'futebol' AND (sc.target_niche IS NULL OR sc.target_niche = ''))"
            ')',
            (niche, niche),
        )
        return int(cur.fetchone()['c'])


def _select_pending_videos(db_conn) -> list:
    """Seleciona vídeos pendentes pra repor a janela de download ativo por nicho.

    Para cada nicho com canal destino ativo (10 por canal): conta a ocupação atual
    **por canal de origem** (arquivo bruto em disco, status em processamento ativo ou
    clips ainda sendo trabalhados), calcula o déficit até o teto do nicho
    (_niche_windows) e busca candidatos restritos a published_at de até
    FRESHNESS_DAYS dias atrás, na ordem de prioridade, posição na fila e
    published_at DESC.

    A escolha final é justa por canal (`fair_queue.fair_pick`): cada canal de
    origem só pode ocupar `channel_cap` vagas da janela, e quem ocupa menos vagas
    escolhe primeiro. Sem isso, um canal que publica 50 vídeos por dia toma a
    janela inteira e os outros nunca baixam. Nicho com a janela cheia não baixa nada.
    """
    cutoff_date = (datetime.now(SAO_PAULO_TZ) - timedelta(days=FRESHNESS_DAYS)).date()

    niche_windows = _niche_windows(db_conn)

    result = []
    for niche, window in niche_windows:
        with db_conn.cursor() as cur:
            cur.execute(
                'SELECT sv.channel_id AS channel_id, COUNT(DISTINCT sv.id) AS c '
                'FROM source_videos sv '
                'LEFT JOIN source_channels sc ON sc.id = sv.channel_id '
                'LEFT JOIN generated_clips gc ON gc.source_video_id = sv.id '
                'WHERE ('
                '  (LOWER(COALESCE(sc.target_niche, \'futebol\')) = %s) '
                "  OR (%s = 'futebol' AND (sc.target_niche IS NULL OR sc.target_niche = ''))"
                ') AND ('
                '  sv.local_path IS NOT NULL '
                "  OR sv.status IN ('downloading', 'downloaded', 'transcribing', 'selecting', 'cutting', 'publishing') "
                "  OR (gc.id IS NOT NULL AND gc.status IN ('pending_cut', 'pending', 'cutting', 'approved'))"
                ') GROUP BY sv.channel_id',
                (niche, niche),
            )
            rows = cur.fetchall() or []

        occupancy = {row['channel_id']: int(row['c']) for row in rows}
        occupied = sum(occupancy.values())

        deficit = max(0, window - occupied)
        if deficit == 0:
            continue

        cap = channel_cap(
            window=window,
            active_channels=_active_source_channels(db_conn, niche),
            override=DOWNLOAD_MAX_PER_SOURCE_CHANNEL,
        )

        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT sv.youtube_video_id, sv.channel_id FROM source_videos sv "
                "LEFT JOIN source_channels sc ON sc.id = sv.channel_id "
                "WHERE sv.status = 'pending' AND sv.paused = FALSE "
                "AND ("
                "  (LOWER(COALESCE(sc.target_niche, 'futebol')) = %s) "
                "  OR (%s = 'futebol' AND (sc.target_niche IS NULL OR sc.target_niche = ''))"
                ") "
                "AND DATE(sv.published_at) >= %s "
                "ORDER BY sv.priority DESC, "
                "sv.queue_position IS NULL, sv.queue_position ASC, "
                "sv.published_at DESC LIMIT %s",
                (niche, niche, cutoff_date, deficit * CANDIDATES_PER_SLOT),
            )
            candidates = [dict(row) for row in cur.fetchall()]

        escolhidos = fair_pick(candidates, occupancy=occupancy, deficit=deficit, cap=cap)
        result.extend(v['youtube_video_id'] for v in escolhidos)

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

        allow_local = os.getenv('ALLOW_LOCAL_DOWNLOAD', 'false').lower() in ('true', '1', 'yes')
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

        allow_local = os.getenv('ALLOW_LOCAL_DOWNLOAD', 'false').lower() in ('true', '1', 'yes')
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
