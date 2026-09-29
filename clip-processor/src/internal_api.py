"""
internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.

Endpoints:
  - POST /internal/resolve-channel      {url}              -> {channel_id, channel_name, channel_handle}
  - POST /internal/reject-clip          {clip_id}          -> {exit_code}
  - POST /internal/process-url          {url}              -> {exit_code}
  - POST /internal/delete-source-video  {source_video_id}  -> cleanup local, histórico preservado
  - POST /internal/transcribe           {url}              -> {job_id}

Auth: header X-Internal-Token verificado contra CLIP_PROCESSOR_INTERNAL_TOKEN.
Rede: bind 0.0.0.0:8090 dentro do container `clip-processor`, rede docker `internal`
      — sem publicação de porta no host.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading

import redis
from flask import Flask, jsonify, request

from src.db import get_db_connection
from src.paths import resolve_stored_video_path
from src.processar import main as processar_main
from src.publisher import publish_pending_clips
from src.rejeitar import rejeitar
from src.transcription_job import start_transcription_job

INTERNAL_TOKEN = os.environ.get('CLIP_PROCESSOR_INTERNAL_TOKEN')
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

app = Flask(__name__)


@app.get('/health')
def _route_health():
    return jsonify(status='ok'), 200


def _check_auth() -> bool:
    return bool(INTERNAL_TOKEN) and request.headers.get('X-Internal-Token') == INTERNAL_TOKEN


def resolve_channel(url: str) -> dict:
    """Roda yt-dlp em modo metadata-only e extrai id/name/handle.

    Padrão yt-dlp: --flat-playlist --skip-download --dump-single-json {url}
    (Zero cota YouTube Data API — mesma tática do /processar da Phase 6.)

    --playlist-items 1: sem isso, uma URL de canal (ex: /@Handle) faz o yt-dlp
    paginar todas as abas (videos/streams/shorts) do canal inteiro antes de
    retornar o JSON, o que estoura o timeout de 30s em canais grandes — mesmo
    precisando apenas dos metadados do canal (id/nome/handle), não da lista completa.

    Raises:
        RuntimeError: yt-dlp retornou exit code != 0.
    """
    result = subprocess.run(
        [
            'yt-dlp',
            '--flat-playlist',
            '--skip-download',
            '--playlist-items',
            '1',
            '--dump-single-json',
            url,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or 'yt-dlp failed')

    payload = json.loads(result.stdout)
    channel_id = payload.get('channel_id') or payload.get('id') or ''
    channel_name = payload.get('channel') or payload.get('title') or channel_id
    channel_handle = payload.get('uploader_id') or payload.get('id') or ''
    if channel_handle and not channel_handle.startswith('@'):
        channel_handle = '@' + channel_handle.lstrip('@')

    return {
        'channel_id': channel_id,
        'channel_name': channel_name,
        'channel_handle': channel_handle,
    }


def reject_clip(clip_id: int) -> int:
    """Chama src.rejeitar.rejeitar(clip_id) diretamente. Preserva exit codes 0/1/2."""
    return int(rejeitar(int(clip_id)))


def _archive_transcript_if_needed(conn, source_video_id: int, transcript_path: str | None) -> bool:
    """Garante que a transcrição antiga também esteja guardada no PostgreSQL."""
    transcript_path = resolve_stored_video_path(transcript_path)
    with conn.cursor() as cur:
        cur.execute(
            'SELECT transcript_data, transcript_text FROM source_videos WHERE id = %s',
            (source_video_id,),
        )
        row = cur.fetchone()
    existing_data = row.get('transcript_data') if row else None
    existing_text = str((row or {}).get('transcript_text') or '').strip()
    if existing_text:
        return True

    transcript = existing_data
    if isinstance(transcript, str):
        try:
            transcript = json.loads(transcript)
        except ValueError:
            transcript = None
    if isinstance(transcript, dict):
        text = str(
            transcript.get('text')
            or ' '.join(
                str(segment.get('text') or '')
                for segment in transcript.get('segments', [])
                if isinstance(segment, dict)
            )
        ).strip()
        if text:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE source_videos SET transcript_text=%s WHERE id=%s',
                    (text, source_video_id),
                )
            conn.commit()
            return True
    if not transcript_path or not os.path.isfile(transcript_path):
        return False

    try:
        with open(transcript_path, encoding='utf-8') as f:
            transcript = json.load(f)
    except (OSError, ValueError) as exc:
        print(f'[CLEANUP] Transcrição de {source_video_id} não foi arquivada: {exc}', flush=True)
        return False

    if not isinstance(transcript, dict):
        return False
    text = str(
        transcript.get('text')
        or ' '.join(
            str(segment.get('text') or '')
            for segment in transcript.get('segments', [])
            if isinstance(segment, dict)
        )
    ).strip()
    if not text:
        return False
    from src.db import get_db_driver

    json_assignment = (
        'transcript_data=%s::json' if get_db_driver(conn) == 'pgsql' else 'transcript_data=%s'
    )
    with conn.cursor() as cur:
        cur.execute(
            f'UPDATE source_videos SET {json_assignment}, transcript_text=%s WHERE id=%s',
            (json.dumps(transcript, ensure_ascii=False), text, source_video_id),
        )
    conn.commit()
    return True


def delete_source_video_file(source_video_id: int) -> dict:
    """Libera mídia local e preserva no banco a fonte, os metadados e a transcrição.

    Recusa apagar se o vídeo estiver em processamento. Clips ainda aguardando
    publicação mantêm seus próprios arquivos; os arquivos de clips terminais
    podem ser removidos com o raw.

    Raises:
        RuntimeError: vídeo não existe ou está em uso no momento.
    """
    from src.queue_controls import _cleanup_partial, can_delete_raw

    conn = get_db_connection()
    try:
        ok, reason = can_delete_raw(conn, source_video_id)
        if not ok:
            raise RuntimeError(reason)

        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, youtube_video_id, local_path, transcript_path FROM source_videos WHERE id = %s',
                (source_video_id,),
            )
            row = cur.fetchone()

        if not row:
            raise RuntimeError('source_video não encontrado')

        transcript_path = resolve_stored_video_path(row.get('transcript_path'))
        local_path = resolve_stored_video_path(row.get('local_path'))
        transcript_archived = _archive_transcript_if_needed(conn, source_video_id, transcript_path)
        if transcript_path and os.path.isfile(transcript_path) and not transcript_archived:
            raise RuntimeError(
                'Transcrição local não pôde ser arquivada no banco; os arquivos foram preservados.'
            )
        freed_bytes = 0

        # 1. Apagar clips gerados em disco (videos/clips/ e videos/thumbnails/)
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, status, clip_path, thumbnail_path FROM generated_clips '
                'WHERE source_video_id = %s',
                (source_video_id,),
            )
            clips = cur.fetchall() or []

        for clip in clips:
            if clip.get('status') not in ('published', 'rejected', 'failed'):
                continue
            clip_path = resolve_stored_video_path(clip.get('clip_path'))
            if clip_path:
                clip_stem = os.path.splitext(clip_path)[0]
                for candidate in (
                    clip_path,
                    f'{clip_stem}_raw.mp4',
                    f'{clip_stem}_subtitled.mp4',
                    f'{clip_stem}.srt',
                ):
                    if os.path.exists(candidate):
                        freed_bytes += os.path.getsize(candidate)
                        os.remove(candidate)

            thumb_path = resolve_stored_video_path(clip.get('thumbnail_path'))
            if thumb_path and os.path.exists(thumb_path):
                freed_bytes += os.path.getsize(thumb_path)
                os.remove(thumb_path)

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE generated_clips SET clip_path = NULL, thumbnail_path = NULL '
                "WHERE source_video_id = %s AND status IN ('published', 'rejected', 'failed')",
                (source_video_id,),
            )

        # 2. Apagar vídeo bruto
        if local_path and os.path.exists(local_path):
            freed_bytes += os.path.getsize(local_path)
            os.remove(local_path)

        # 3. Apagar transcrição
        if transcript_archived and transcript_path and os.path.exists(transcript_path):
            freed_bytes += os.path.getsize(transcript_path)
            os.remove(transcript_path)

        # 4. Apagar eventuais arquivos temporários de download (.part, .ytdl)
        yt_id = row.get('youtube_video_id')
        if yt_id:
            _cleanup_partial(yt_id)

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE source_videos SET local_path = NULL, '
                'transcript_path = CASE WHEN %s THEN NULL ELSE transcript_path END, '
                "status = CASE WHEN status IN ('pending', 'selecting', 'downloaded', 'transcribing', 'downloading') THEN 'failed' ELSE status END "
                'WHERE id = %s',
                (
                    transcript_archived
                    or not (transcript_path and os.path.exists(transcript_path)),
                    source_video_id,
                ),
            )
        conn.commit()

        return {
            'deleted': True,
            'transcript_archived': transcript_archived,
            'freed_bytes': freed_bytes,
        }
    finally:
        conn.close()


# Status de clip que ainda precisam do vídeo bruto em disco pra rodar o corte.
_CLIP_STATUSES_NEED_RAW_FILE = ('pending_cut', 'cutting')


def purge_old_videos(before_date: str) -> dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, local_path, transcript_path FROM source_videos '
                'WHERE published_at < %s ORDER BY published_at ASC, id ASC',
                (before_date,),
            )
            historical_rows = cur.fetchall()
        conn.close()

        rows_with_local_artifacts = [
            row for row in historical_rows if row.get('local_path') or row.get('transcript_path')
        ]

        # Históricos sem raw também não devem voltar para a fila de download
        # só porque a limpeza preservou o registro no banco.
        state_conn = get_db_connection()
        try:
            with state_conn.cursor() as cur:
                cur.execute(
                    "UPDATE source_videos SET status = 'failed' "
                    'WHERE published_at < %s AND local_path IS NULL '
                    "AND status IN ('pending', 'downloaded') "
                    'AND NOT EXISTS (SELECT 1 FROM generated_clips gc '
                    'WHERE gc.source_video_id = source_videos.id '
                    "AND gc.status IN ('pending_cut', 'cutting'))",
                    (before_date,),
                )
            state_conn.commit()
        finally:
            state_conn.close()

        freed_bytes = 0
        cleaned_videos = 0
        transcripts_archived = 0
        skipped_rows = 0
        for row in rows_with_local_artifacts:
            source_video_id = row['id']
            try:
                result = delete_source_video_file(int(source_video_id))
            except RuntimeError as exc:
                skipped_rows += 1
                print(
                    f'[CLEANUP] Vídeo antigo {source_video_id} preservado em disco por segurança: {exc}',
                    flush=True,
                )
                continue
            if result.get('deleted'):
                cleaned_videos += 1
                freed_bytes += int(result.get('freed_bytes') or 0)
            if result.get('transcript_archived'):
                transcripts_archived += 1

        return {
            'deleted_rows': 0,
            'retained_rows': len(historical_rows),
            'cleaned_videos': cleaned_videos,
            'transcripts_archived': transcripts_archived,
            'skipped_rows': skipped_rows,
            'freed_bytes': freed_bytes,
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post('/internal/purge-old-videos')
def _route_purge_old_videos():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    payload = request.get_json(silent=True) or {}
    before_date = payload.get('before_date')
    if not before_date:
        return jsonify(error='missing before_date'), 400
    try:
        result = purge_old_videos(before_date)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(result), 200


@app.post('/internal/resolve-channel')
def _route_resolve_channel():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    payload = request.get_json(silent=True) or {}
    url = payload.get('url')
    if not url:
        return jsonify(error='missing url'), 400
    try:
        data = resolve_channel(url)
    except RuntimeError as e:
        return jsonify(error='yt-dlp failed', stderr=str(e)), 422
    return jsonify(data), 200


@app.post('/internal/reject-clip')
def _route_reject_clip():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    payload = request.get_json(silent=True) or {}
    clip_id = payload.get('clip_id')
    if clip_id is None:
        return jsonify(error='missing clip_id'), 400
    try:
        exit_code = reject_clip(int(clip_id))
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(exit_code=exit_code), 200


@app.post('/internal/process-url')
def _route_process_url():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    payload = request.get_json(silent=True) or {}
    url = payload.get('url')
    fmt = payload.get('format', 'curto')
    if not url:
        return jsonify(error='missing url'), 400
    try:
        exit_code = processar_main(url, fmt=fmt)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(exit_code=exit_code), 200


@app.post('/internal/delete-source-video')
def _route_delete_source_video():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    payload = request.get_json(silent=True) or {}
    source_video_id = payload.get('source_video_id')
    if source_video_id is None:
        return jsonify(error='missing source_video_id'), 400
    try:
        result = delete_source_video_file(int(source_video_id))
    except RuntimeError as e:
        return jsonify(error=str(e)), 422
    return jsonify(result), 200


@app.post('/internal/transcribe')
def _route_transcribe():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    payload = request.get_json(silent=True) or {}
    url = payload.get('url')
    if not url:
        return jsonify(error='missing url'), 400
    try:
        job_id = start_transcription_job(url)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(job_id=job_id), 200


@app.post('/internal/videos/<int:source_video_id>/pause')
def _route_pause_video(source_video_id: int):
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    from src.queue_controls import pause_video

    try:
        return jsonify(pause_video(source_video_id)), 200
    except RuntimeError as e:
        return jsonify(error=str(e)), 422
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.post('/internal/videos/<int:source_video_id>/resume')
def _route_resume_video(source_video_id: int):
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    from src.queue_controls import resume_video

    try:
        return jsonify(resume_video(source_video_id)), 200
    except RuntimeError as e:
        return jsonify(error=str(e)), 422
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.post('/internal/videos/reorder')
def _route_reorder_videos():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    from src.queue_controls import reorder_videos

    payload = request.get_json(silent=True) or {}
    ids = payload.get('ids')
    if not isinstance(ids, list) or not ids:
        return jsonify(error='missing ids'), 400
    try:
        return jsonify(reorder_videos([int(i) for i in ids])), 200
    except RuntimeError as e:
        return jsonify(error=str(e)), 422
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.post('/internal/videos/<int:source_video_id>/prioritize')
def _route_prioritize_video(source_video_id: int):
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    from src.queue_controls import prioritize_video

    try:
        return jsonify(prioritize_video(source_video_id)), 200
    except RuntimeError as e:
        return jsonify(error=str(e)), 422
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.post('/internal/publish-now')
def _route_publish_now():
    """Dispara um ciclo imediato de publicação de clipes aprovados."""
    if not _check_auth():
        return jsonify(error='unauthorized'), 401

    def _run_publish():
        conn = None
        try:
            conn = get_db_connection()
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
            published = publish_pending_clips(conn, r, bypass_window=True)
            print(
                f'[INTERNAL_API] Publicação imediata finalizada: {published} clipe(s)', flush=True
            )
        except Exception as e:
            print(f'[INTERNAL_API] Erro durante publicação imediata: {e}', flush=True)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    t = threading.Thread(target=_run_publish, daemon=True)
    t.start()
    return jsonify(ok=True, message='Ciclo de publicação imediata iniciado'), 200
