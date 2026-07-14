"""
publisher.py — Publica clips pending no YouTube e atualiza o banco.

Exporta:
  - publish_pending_clips(conn, redis_client, uploader=None, quota_manager=None, now=None)
  - _fetch_destination_channels(conn)
  - _fetch_pending_clips_for_channel(conn, destination_channel_id)
"""
import os
from datetime import datetime, timezone

from src.metadata_generator import append_credits, resolve_credit_handle
from src.quota_manager import QuotaManager
from src.telegram_notifier import notify
from src.uploader import YouTubeUploader


NON_TERMINAL_CLIP_STATUSES = ('pending_cut', 'cutting', 'pending', 'approved', 'publishing')


def _publishable_status() -> str:
    """'approved' quando operador deve aprovar via Telegram, 'pending' para auto-publicar.

    Controlado por MANUAL_APPROVAL_REQUIRED (default 'false' = 100% auto).
    """
    return 'approved' if os.environ.get('MANUAL_APPROVAL_REQUIRED', 'false').lower() == 'true' else 'pending'


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [PUB] {msg}')


def publish_pending_clips(
    conn,
    redis_client,
    uploader: YouTubeUploader | None = None,
    quota_manager: QuotaManager | None = None,
    now: datetime | None = None,
) -> int:
    """Publica clips prontos e retorna quantidade publicada.

    Fluxo multi-canal (Phase 7):
    - Busca canais-destino ativos em destination_channels
    - Para cada canal: instancia QuotaManager e YouTubeUploader independentes
    - Appenda créditos na descrição antes do upload quando template disponível

    Fallback legado (sem canais-destino configurados):
    - Usa _fetch_pending_clips() original com um único uploader/quota_manager
    """
    dest_channels = _fetch_destination_channels(conn)

    if not dest_channels:
        # Fallback: sem canais-destino configurados — usa fluxo legado
        _log('[PUBLISHER] Nenhum canal-destino ativo — usando fluxo legado')
        ch_uploader = uploader or YouTubeUploader()
        ch_quota = quota_manager or QuotaManager(redis_client)
        return _publish_clips_for(conn, _fetch_pending_clips(conn), ch_uploader, ch_quota, now)

    total = 0
    for dest in dest_channels:
        ch_uploader = uploader or YouTubeUploader(channel_slug=dest['slug'])
        ch_quota = quota_manager or QuotaManager(redis_client, channel_id=dest['youtube_channel_id'])
        clips = _fetch_pending_clips_for_channel(conn, dest['id'])

        for clip in clips:
            credit_handle = resolve_credit_handle(clip.get('channel_handle'), clip.get('channel_name'))
            if dest.get('credit_template') and credit_handle:
                clip = dict(clip)  # não mutar original
                clip['description'] = append_credits(
                    clip.get('description') or '',
                    dest['credit_template'],
                    credit_handle,
                )
            total += _publish_one(conn, clip, ch_uploader, ch_quota, now)

    return total


def _fetch_destination_channels(conn) -> list[dict]:
    """Retorna canais-destino ativos de destination_channels."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT id, slug, name, niche, youtube_channel_id, credit_template '
            'FROM destination_channels WHERE active = TRUE'
        )
        return cur.fetchall() or []


def _fetch_pending_clips_for_channel(conn, destination_channel_id: int) -> list[dict]:
    """Retorna clips prontos para publicar filtrados por canal-destino.

    Faz fairness round-robin por canal fonte (sc.id): sem isso, uma leva de
    clips represada (ex.: dezenas de vídeos presos em 'selecting' por semanas
    que destravam de uma vez) fura a fila FIFO por created_at e monopoliza a
    cota diária por dias seguidos, enquanto outros canais fonte com volume
    maior ficam represados atrás. Round-robin garante que, a cada ciclo de
    publicação, nenhum canal fonte publique dois clips seguidos enquanto
    houver clip pendente de outro canal.
    """
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.source_video_id, gc.clip_path, gc.thumbnail_path, '
            'gc.title, gc.description, gc.tags, '
            'sv.local_path AS source_local_path, '
            'sc.id AS source_channel_id, sc.channel_handle, sc.channel_name '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            'JOIN source_channels sc ON sc.id = sv.channel_id '
            'WHERE gc.status = %s '
            'AND gc.destination_channel_id = %s '
            'AND gc.clip_path IS NOT NULL '
            'AND gc.title IS NOT NULL '
            'ORDER BY gc.created_at ASC',
            (_publishable_status(), destination_channel_id),
        )
        clips = cur.fetchall() or []
    return _round_robin_by_source_channel(clips)


def _round_robin_by_source_channel(clips: list[dict]) -> list[dict]:
    """Reordena clips (já em ordem created_at ASC) intercalando por source_channel_id,
    preservando a ordem relativa dentro de cada canal."""
    queues: dict = {}
    order: list = []
    for clip in clips:
        key = clip.get('source_channel_id')
        if key not in queues:
            queues[key] = []
            order.append(key)
        queues[key].append(clip)

    result = []
    while order:
        for key in list(order):
            result.append(queues[key].pop(0))
            if not queues[key]:
                order.remove(key)
    return result


def _publish_clips_for(conn, clips, uploader, quota_manager, now) -> int:
    """Publica uma sequência de clips com um uploader/quota_manager dado."""
    current_status = _publishable_status()
    published_count = 0

    for clip in clips:
        clip_id = clip['id']

        if not quota_manager.can_upload(now=now):
            _log(f'Clip {clip_id} mantido {current_status} por quota/janela')
            break

        _log(f'Próximo clip {current_status}: id={clip_id}')

        if not _transition_to_publishing(conn, clip_id):
            _log(f'Clip {clip_id} pulado: status mudou durante seleção')
            continue

        try:
            youtube_video_id = uploader.upload_clip(clip)
            _mark_clip_published(conn, clip_id, youtube_video_id)
            quota_manager.record_upload(now=now)
            _maybe_finalize_source_video(conn, clip['source_video_id'], clip.get('source_local_path'))
            published_count += 1
            _log(f'Clip {clip_id} publicado no YouTube: {youtube_video_id}')
            notify('upload_published', {
                'clip_id': clip_id,
                'youtube_video_id': youtube_video_id,
                'youtube_url': f'https://www.youtube.com/watch?v={youtube_video_id}',
                'title': clip.get('title'),
            })
        except Exception as exc:
            _mark_clip_failed(conn, clip_id, str(exc))
            _log(f'Falha ao publicar clip {clip_id}: {exc}')

    return published_count


def _publish_one(conn, clip, uploader, quota_manager, now) -> int:
    """Publica um único clip. Retorna 1 se publicado, 0 caso contrário."""
    current_status = _publishable_status()
    clip_id = clip['id']

    if not quota_manager.can_upload(now=now):
        _log(f'Clip {clip_id} mantido {current_status} por quota/janela')
        return 0

    _log(f'Próximo clip {current_status}: id={clip_id}')

    if not _transition_to_publishing(conn, clip_id):
        _log(f'Clip {clip_id} pulado: status mudou durante seleção')
        return 0

    try:
        youtube_video_id = uploader.upload_clip(clip)
        _mark_clip_published(conn, clip_id, youtube_video_id)
        quota_manager.record_upload(now=now)
        _maybe_finalize_source_video(conn, clip['source_video_id'], clip.get('source_local_path'))
        _log(f'Clip {clip_id} publicado no YouTube: {youtube_video_id}')
        notify('upload_published', {
            'clip_id': clip_id,
            'youtube_video_id': youtube_video_id,
            'youtube_url': f'https://www.youtube.com/watch?v={youtube_video_id}',
            'title': clip.get('title'),
        })
        return 1
    except Exception as exc:
        _mark_clip_failed(conn, clip_id, str(exc))
        _log(f'Falha ao publicar clip {clip_id}: {exc}')
        return 0


def _fetch_pending_clips(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'gc.id, gc.source_video_id, gc.clip_path, gc.thumbnail_path, '
            'gc.title, gc.description, gc.tags, sv.local_path AS source_local_path '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            'WHERE gc.status = %s '
            'AND gc.clip_path IS NOT NULL '
            'AND gc.title IS NOT NULL '
            'ORDER BY gc.created_at ASC',
            (_publishable_status(),),
        )
        return cur.fetchall()


def _ensure_publishable_files(clip: dict) -> None:
    clip_path = clip.get('clip_path')
    if not clip_path or not os.path.exists(clip_path):
        raise FileNotFoundError(f'clip_path not found: {clip_path}')

    thumbnail_path = clip.get('thumbnail_path')
    if thumbnail_path and not os.path.exists(thumbnail_path):
        raise FileNotFoundError(f'thumbnail_path not found: {thumbnail_path}')


def _update_clip_status(conn, clip_id: int, status: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE generated_clips SET status=%s WHERE id=%s',
            (status, clip_id),
        )
    conn.commit()


def _transition_to_publishing(conn, clip_id: int) -> bool:
    """Move clip do status publicável → publishing com guard.

    Retorna True se a transição ocorreu (1 row afetada), False se o clip já
    saiu do status publicável (race com /rejeitar). Em ambos os casos, faz commit.
    """
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE generated_clips SET status='publishing' "
            'WHERE id=%s AND status=%s',
            (clip_id, _publishable_status()),
        )
        rowcount = cur.rowcount
    conn.commit()
    return rowcount > 0


def _mark_clip_published(conn, clip_id: int, youtube_video_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE generated_clips '
            "SET status='published', youtube_video_id=%s, published_at=%s, upload_error=NULL "
            'WHERE id=%s',
            (youtube_video_id, datetime.now(timezone.utc), clip_id),
        )
    conn.commit()


def _mark_clip_failed(conn, clip_id: int, error: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE generated_clips '
            "SET status='failed', upload_error=%s "
            'WHERE id=%s',
            (error[:2000], clip_id),
        )
    conn.commit()


def _maybe_finalize_source_video(conn, source_video_id: int, source_local_path: str | None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'SUM(status IN %s) AS non_terminal_count, '
            "SUM(status = 'published') AS published_count "
            'FROM generated_clips '
            'WHERE source_video_id = %s',
            (NON_TERMINAL_CLIP_STATUSES, source_video_id),
        )
        row = cur.fetchone() or {}

    non_terminal_count = int(row.get('non_terminal_count') or 0)
    published_count = int(row.get('published_count') or 0)
    if non_terminal_count != 0 or published_count == 0:
        return

    if source_local_path and os.path.exists(source_local_path):
        os.remove(source_local_path)

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE source_videos SET status='published', local_path=NULL WHERE id=%s",
            (source_video_id,),
        )
    conn.commit()
