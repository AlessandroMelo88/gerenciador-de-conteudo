"""
internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.

Endpoints:
  - POST /internal/resolve-channel      {url}              -> {channel_id, channel_name, channel_handle}
  - POST /internal/reject-clip          {clip_id}          -> {exit_code}
  - POST /internal/process-url          {url}              -> {exit_code}
  - POST /internal/delete-source-video  {source_video_id}  -> {deleted, freed_bytes}

Auth: header X-Internal-Token verificado contra CLIP_PROCESSOR_INTERNAL_TOKEN.
Rede: bind 0.0.0.0:8090 dentro do container `clip-processor`, rede docker `internal`
      — sem publicação de porta no host.
"""
import json
import os
import subprocess

import redis
from flask import Flask, jsonify, request

from src.db import get_db_connection
from src.processar import main as processar_main
from src.rejeitar import rejeitar

INTERNAL_TOKEN = os.environ.get('CLIP_PROCESSOR_INTERNAL_TOKEN')
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

app = Flask(__name__)


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
            'yt-dlp', '--flat-playlist', '--skip-download', '--playlist-items', '1',
            '--dump-single-json', url,
        ],
        capture_output=True, text=True, timeout=30,
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


def delete_source_video_file(source_video_id: int) -> dict:
    """Apaga o arquivo bruto (.mp4) de um source_video e zera local_path no banco.

    Não mexe no status do vídeo nem nos generated_clips — é só limpeza de disco,
    disparada manualmente pelo operador via painel (Vídeos > Apagar arquivo).
    Recusa apagar se o vídeo está em 'downloading' ou 'cutting' agora (arquivo em uso).

    Raises:
        RuntimeError: vídeo não existe, ou está em uso no momento.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, status, local_path FROM source_videos WHERE id = %s',
                (source_video_id,),
            )
            row = cur.fetchone()

        if not row:
            raise RuntimeError('source_video não encontrado')

        if row['status'] in ('downloading', 'cutting'):
            raise RuntimeError(f"vídeo em uso agora (status={row['status']}) — tente novamente em instantes")

        local_path = row['local_path']
        freed_bytes = 0
        if local_path and os.path.exists(local_path):
            freed_bytes = os.path.getsize(local_path)
            os.remove(local_path)

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE source_videos SET local_path = NULL WHERE id = %s',
                (source_video_id,),
            )
        conn.commit()

        return {'deleted': True, 'freed_bytes': freed_bytes}
    finally:
        conn.close()


# Status de clip que ainda precisam do vídeo bruto em disco pra rodar o corte.
_CLIP_STATUSES_NEED_RAW_FILE = ('pending_cut', 'cutting')


def purge_old_videos(before_date: str) -> dict:
    """Limpa vídeos fonte com published_at anterior a `before_date` (formato 'YYYY-MM-DD').

    Duas ações, pra manter o disco/banco enxutos sem quebrar nada em andamento:
      1. Vídeos que nunca passaram da ingestão (status pending/failed/downloaded)
         e não têm nenhum generated_clips — apaga a linha inteira (nunca vão ser
         processados de qualquer forma, já que o download prioriza notícia recente).
      2. Vídeos que já geraram clips (status selecting) mas cujo arquivo bruto
         (.mp4) ainda está no disco — apaga só o arquivo (libera espaço), mantendo
         a linha e os clips intactos. Pula qualquer vídeo com clip pending_cut/cutting
         (ainda precisa do bruto pra terminar o corte).

    Também remove do Redis a chave de deduplicação (video:{youtube_video_id}) das
    linhas apagadas — sem isso, a chave (TTL 30 dias) continua marcando o vídeo
    como "já visto" mesmo depois de removido do MySQL, e se o mesmo video_id
    voltar a aparecer num feed RSS o poller nunca mais o insere.

    Args:
        before_date: string 'YYYY-MM-DD' — vídeos publicados antes dessa data são alvo.

    Returns:
        dict com deleted_rows (linhas removidas) e freed_bytes (espaço liberado).
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sv.youtube_video_id FROM source_videos sv "
                "WHERE sv.published_at < %s "
                "AND sv.status IN ('pending', 'failed', 'downloaded') "
                "AND NOT EXISTS (SELECT 1 FROM generated_clips gc WHERE gc.source_video_id = sv.id)",
                (before_date,),
            )
            video_ids_to_purge = [row['youtube_video_id'] for row in cur.fetchall()]

        with conn.cursor() as cur:
            cur.execute(
                "DELETE sv FROM source_videos sv "
                "WHERE sv.published_at < %s "
                "AND sv.status IN ('pending', 'failed', 'downloaded') "
                "AND NOT EXISTS (SELECT 1 FROM generated_clips gc WHERE gc.source_video_id = sv.id)",
                (before_date,),
            )
            deleted_rows = cur.rowcount
        conn.commit()

        if video_ids_to_purge:
            try:
                r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
                r.delete(*[f'video:{vid}' for vid in video_ids_to_purge])
            except redis.RedisError:
                pass

        placeholders = ', '.join(['%s'] * len(_CLIP_STATUSES_NEED_RAW_FILE))
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT sv.id, sv.local_path FROM source_videos sv "
                f"WHERE sv.published_at < %s AND sv.local_path IS NOT NULL "
                f"AND sv.status NOT IN ('downloading', 'cutting') "
                f"AND NOT EXISTS ("
                f"  SELECT 1 FROM generated_clips gc "
                f"  WHERE gc.source_video_id = sv.id AND gc.status IN ({placeholders})"
                f")",
                (before_date, *_CLIP_STATUSES_NEED_RAW_FILE),
            )
            rows_with_file = cur.fetchall()

        freed_bytes = 0
        for row in rows_with_file:
            local_path = row['local_path']
            if local_path and os.path.exists(local_path):
                freed_bytes += os.path.getsize(local_path)
                os.remove(local_path)
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE source_videos SET local_path = NULL WHERE id = %s',
                    (row['id'],),
                )
        conn.commit()

        return {'deleted_rows': deleted_rows, 'freed_bytes': freed_bytes}
    finally:
        conn.close()


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
    except Exception as e:  # noqa: BLE001
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
