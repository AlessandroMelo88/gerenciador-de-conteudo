"""
internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.

Endpoints (implementação GREEN no Plan 08-07):
  - POST /internal/resolve-channel  {url}      -> {channel_id, channel_name, channel_handle}
  - POST /internal/reject-clip      {clip_id}  -> {exit_code}

Auth: header X-Internal-Token verificado contra CLIP_PROCESSOR_INTERNAL_TOKEN.
Rede: bind 0.0.0.0:8090 dentro do container `clip-processor`, rede docker `internal`
      — sem publicação de porta no host.
"""
import os
from flask import Flask, jsonify, request

# Imports que a implementação GREEN vai usar (mantidos aqui para expor à collect
# dos testes; NotImplementedError vem do corpo das funções, não do import).
from src.rejeitar import rejeitar  # noqa: F401  # usado por reject_clip()

INTERNAL_TOKEN = os.environ.get('CLIP_PROCESSOR_INTERNAL_TOKEN')

app = Flask(__name__)


def _check_auth() -> bool:
    return bool(INTERNAL_TOKEN) and request.headers.get('X-Internal-Token') == INTERNAL_TOKEN


def resolve_channel(url: str) -> dict:
    """RED skeleton — implementação em Plan 08-07."""
    raise NotImplementedError('resolve_channel — Plan 08-07 GREEN pendente')


def reject_clip(clip_id: int) -> int:
    """RED skeleton — implementação em Plan 08-07."""
    raise NotImplementedError('reject_clip — Plan 08-07 GREEN pendente')


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
        return jsonify(data), 200
    except NotImplementedError as e:
        return jsonify(error=str(e)), 501
    except RuntimeError as e:
        return jsonify(error='yt-dlp failed', stderr=str(e)), 422


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
        return jsonify(exit_code=exit_code), 200
    except NotImplementedError as e:
        return jsonify(error=str(e)), 501
