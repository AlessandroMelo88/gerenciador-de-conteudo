"""
internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.

Endpoints:
  - POST /internal/resolve-channel  {url}      -> {channel_id, channel_name, channel_handle}
  - POST /internal/reject-clip      {clip_id}  -> {exit_code}

Auth: header X-Internal-Token verificado contra CLIP_PROCESSOR_INTERNAL_TOKEN.
Rede: bind 0.0.0.0:8090 dentro do container `clip-processor`, rede docker `internal`
      — sem publicação de porta no host.
"""
import json
import os
import subprocess

from flask import Flask, jsonify, request

from src.rejeitar import rejeitar

INTERNAL_TOKEN = os.environ.get('CLIP_PROCESSOR_INTERNAL_TOKEN')

app = Flask(__name__)


def _check_auth() -> bool:
    return bool(INTERNAL_TOKEN) and request.headers.get('X-Internal-Token') == INTERNAL_TOKEN


def resolve_channel(url: str) -> dict:
    """Roda yt-dlp em modo metadata-only e extrai id/name/handle.

    Padrão yt-dlp: --flat-playlist --skip-download --dump-single-json {url}
    (Zero cota YouTube Data API — mesma tática do /processar da Phase 6.)

    Raises:
        RuntimeError: yt-dlp retornou exit code != 0.
    """
    result = subprocess.run(
        ['yt-dlp', '--flat-playlist', '--skip-download', '--dump-single-json', url],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or 'yt-dlp failed')

    payload = json.loads(result.stdout)
    channel_id = payload.get('id') or payload.get('channel_id') or ''
    channel_name = payload.get('channel') or payload.get('title') or channel_id
    channel_handle = payload.get('uploader_id') or payload.get('channel_id') or ''
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
