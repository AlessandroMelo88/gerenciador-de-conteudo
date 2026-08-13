"""
queue_controls.py — Pause / resume / reorder / prioritize da fila de source_videos.
"""
import os
import subprocess
from datetime import datetime

from src.db import get_db_connection

_CLIP_STATUSES_NEED_RAW = ('pending_cut', 'cutting')


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [QUEUE] {msg}', flush=True)


class PauseAborted(Exception):
    """Download/processo abortado porque o vídeo foi pausado."""


def is_paused(conn, *, source_video_id: int | None = None, youtube_video_id: str | None = None) -> bool:
    with conn.cursor() as cur:
        if source_video_id is not None:
            cur.execute('SELECT paused FROM source_videos WHERE id = %s', (source_video_id,))
        else:
            cur.execute(
                'SELECT paused FROM source_videos WHERE youtube_video_id = %s',
                (youtube_video_id,),
            )
        row = cur.fetchone()
    return bool(row and row.get('paused'))


def pause_video(source_video_id: int) -> dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, youtube_video_id, status, local_path, paused '
                'FROM source_videos WHERE id = %s',
                (source_video_id,),
            )
            row = cur.fetchone()
        if not row:
            raise RuntimeError('source_video não encontrado')

        with conn.cursor() as cur:
            cur.execute('UPDATE source_videos SET paused = 1 WHERE id = %s', (source_video_id,))
        conn.commit()

        status = row['status']
        youtube_video_id = row['youtube_video_id']
        actions: list[str] = ['paused']

        if status == 'downloading':
            _kill_ytdlp_for(youtube_video_id)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE source_videos SET status = 'pending', local_path = NULL WHERE id = %s",
                    (source_video_id,),
                )
            conn.commit()
            _cleanup_partial(youtube_video_id)
            actions.append('download_aborted')

        elif status in ('transcribing', 'selecting'):
            # Worker checa paused entre etapas; se já terminou a IA sem clips,
            # recover_stuck_selecting / failed path libera. Aqui só marca.
            actions.append('cooperative_hold')

        # Clips em cutting: aborta FFmpeg e devolve pra pending_cut
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM generated_clips "
                "WHERE source_video_id = %s AND status = 'cutting'",
                (source_video_id,),
            )
            cutting = cur.fetchall() or []
        for clip in cutting:
            _kill_ffmpeg_for_clip(clip['id'])
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE generated_clips SET status = 'pending_cut' WHERE id = %s AND status = 'cutting'",
                    (clip['id'],),
                )
            actions.append(f"clip_{clip['id']}_cut_aborted")
        if cutting:
            conn.commit()

        _log(f'pause video={source_video_id} status={status} actions={actions}')
        return {'paused': True, 'status': status, 'actions': actions}
    finally:
        conn.close()


def resume_video(source_video_id: int) -> dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, status FROM source_videos WHERE id = %s', (source_video_id,))
            row = cur.fetchone()
        if not row:
            raise RuntimeError('source_video não encontrado')

        with conn.cursor() as cur:
            cur.execute('UPDATE source_videos SET paused = 0 WHERE id = %s', (source_video_id,))
        conn.commit()
        _log(f'resume video={source_video_id}')
        return {'paused': False, 'status': row['status']}
    finally:
        conn.close()


def reorder_videos(ids: list[int]) -> dict:
    if not ids:
        raise RuntimeError('ids vazio')
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for position, video_id in enumerate(ids):
                cur.execute(
                    'UPDATE source_videos SET queue_position = %s WHERE id = %s',
                    (position, video_id),
                )
        conn.commit()
        _log(f'reorder {len(ids)} vídeo(s)')
        return {'reordered': len(ids)}
    finally:
        conn.close()


def prioritize_video(source_video_id: int) -> dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COALESCE(MAX(priority), 0) AS m FROM source_videos')
            max_priority = int(cur.fetchone()['m'] or 0)
            cur.execute(
                'UPDATE source_videos SET priority = %s WHERE id = %s',
                (max_priority + 1, source_video_id),
            )
            affected = cur.rowcount
        conn.commit()
        if affected == 0:
            raise RuntimeError('source_video não encontrado')
        _log(f'prioritize video={source_video_id} priority={max_priority + 1}')
        return {'priority': max_priority + 1}
    finally:
        conn.close()


def can_delete_raw(conn, source_video_id: int) -> tuple[bool, str]:
    with conn.cursor() as cur:
        cur.execute('SELECT status FROM source_videos WHERE id = %s', (source_video_id,))
        row = cur.fetchone()
    if not row:
        return False, 'source_video não encontrado'
    if row['status'] in ('downloading', 'cutting'):
        return False, f"vídeo em uso agora (status={row['status']})"
    with conn.cursor() as cur:
        placeholders = ', '.join(['%s'] * len(_CLIP_STATUSES_NEED_RAW))
        cur.execute(
            f'SELECT COUNT(*) AS c FROM generated_clips '
            f'WHERE source_video_id = %s AND status IN ({placeholders})',
            (source_video_id, *_CLIP_STATUSES_NEED_RAW),
        )
        if cur.fetchone()['c'] > 0:
            return False, 'clips ainda precisam do arquivo bruto (pending_cut/cutting)'
    return True, ''


def _cleanup_partial(youtube_video_id: str, videos_dir: str = '/app/videos') -> None:
    """Apaga o raw e os temporários de download de um vídeo (best-effort).

    `videos_dir` existe só pra quem já tem o diretório em mão (e pros testes);
    o default segue o caminho de produção dentro do container.
    """
    base = f'{videos_dir}/{youtube_video_id}'
    for path in (f'{base}.mp4', f'{base}.mp4.part', f'{base}.mp4.ytdl'):
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as exc:
                _log(f'AVISO: falha ao remover {path}: {exc}')


def _kill_ytdlp_for(youtube_video_id: str) -> None:
    """Best-effort: mata processos yt-dlp cujo cmdline menciona o video_id."""
    try:
        subprocess.run(
            ['pkill', '-f', f'yt-dlp.*{youtube_video_id}'],
            check=False,
            capture_output=True,
        )
    except Exception as exc:  # noqa: BLE001
        _log(f'AVISO: pkill yt-dlp falhou: {exc}')
    # YoutubeDL roda in-process — o progress_hook / retry check aborta o download.


def _kill_ffmpeg_for_clip(clip_id: int) -> None:
    try:
        subprocess.run(
            ['pkill', '-f', f'ffmpeg.*clips/{clip_id}'],
            check=False,
            capture_output=True,
        )
        # também tenta pelo path completo
        subprocess.run(
            ['pkill', '-f', f'/{clip_id}\\.mp4'],
            check=False,
            capture_output=True,
        )
    except Exception as exc:  # noqa: BLE001
        _log(f'AVISO: pkill ffmpeg falhou: {exc}')
