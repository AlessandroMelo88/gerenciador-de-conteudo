"""
publisher.py — Publica clips pending no YouTube e atualiza o banco.

Exporta:
  - publish_pending_clips(conn, redis_client, uploader=None, now=None)
"""
import os
from datetime import datetime, timezone

from src.quota_manager import QuotaManager
from src.uploader import YouTubeUploader


NON_TERMINAL_CLIP_STATUSES = ('pending_cut', 'cutting', 'pending', 'publishing')


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [PUB] {msg}')


def publish_pending_clips(
    conn,
    redis_client,
    uploader: YouTubeUploader | None = None,
    quota_manager: QuotaManager | None = None,
    now: datetime | None = None,
) -> int:
    """Publica clips prontos e retorna quantidade publicada."""
    uploader = uploader or YouTubeUploader()
    quota_manager = quota_manager or QuotaManager(redis_client)
    published_count = 0

    for clip in _fetch_pending_clips(conn):
        clip_id = clip['id']

        if not quota_manager.can_upload(now=now):
            _log(f'Clip {clip_id} mantido approved por quota/janela')
            break

        _log(f'Próximo clip approved: id={clip_id}')

        # Phase 6: guard de status — defesa contra race com /rejeitar concorrente.
        # Se 0 rows afetadas, o clip foi rejeitado em paralelo: skip silencioso.
        if not _transition_approved_to_publishing(conn, clip_id):
            _log(f'Clip {clip_id} pulado: status mudou durante seleção')
            continue

        try:
            youtube_video_id = uploader.upload_clip(clip)
            _mark_clip_published(conn, clip_id, youtube_video_id)
            quota_manager.record_upload(now=now)
            _maybe_finalize_source_video(conn, clip['source_video_id'], clip.get('source_local_path'))
            published_count += 1
            _log(f'Clip {clip_id} publicado no YouTube: {youtube_video_id}')
        except Exception as exc:
            _mark_clip_failed(conn, clip_id, str(exc))
            _log(f'Falha ao publicar clip {clip_id}: {exc}')

    return published_count


def _fetch_pending_clips(conn) -> list[dict]:
    # Phase 6: seleciona apenas 'approved' (mudança de pending). Bot Telegram aprova via /aprovar.
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'gc.id, gc.source_video_id, gc.clip_path, gc.thumbnail_path, '
            'gc.title, gc.description, gc.tags, sv.local_path AS source_local_path '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            "WHERE gc.status = 'approved' "
            'AND gc.clip_path IS NOT NULL '
            'AND gc.title IS NOT NULL '
            'ORDER BY gc.created_at ASC'
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


def _transition_approved_to_publishing(conn, clip_id: int) -> bool:
    """Phase 6: move clip approved → publishing com guard de status.

    Retorna True se a transição ocorreu (1 row afetada), False se o clip já
    saiu de approved (race com /rejeitar). Em ambos os casos, faz commit.
    """
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE generated_clips SET status='publishing' "
            "WHERE id=%s AND status='approved'",
            (clip_id,),
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
