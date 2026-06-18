"""
metadata_generator.py — Geração de título, descrição e tags para YouTube.

Exporta:
  - generate_metadata(clip_context, anthropic_client=None) -> dict
  - update_clip_metadata(conn, clip_id, metadata) -> None

Convenções:
  - anthropic_client=None cria cliente de produção; injetado em testes
  - title deve respeitar o limite de 100 caracteres do YouTube
  - tags são persistidas em generated_clips.tags como texto
"""
from datetime import datetime


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def generate_metadata(clip_context: dict, anthropic_client=None) -> dict:
    """Gera {'title', 'description', 'tags'} para um clip."""
    raise NotImplementedError


def update_clip_metadata(conn, clip_id: int, metadata: dict) -> None:
    """Persiste metadata em generated_clips."""
    raise NotImplementedError
