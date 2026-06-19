"""
processar.py — Ingestão manual de vídeo YouTube via comando /processar do Telegram.

Stub Phase 6 (Plan 06-01). Implementação real em Plan 06-04.

Exporta:
  - YOUTUBE_URL_RE: regex que extrai videoId de URLs do YouTube
  - parse_video_id(url) -> Optional[str]
  - fetch_metadata(video_id) -> dict
  - upsert_source_video(conn, meta) -> Tuple[str, bool]
  - main(url) -> int
"""
import re
import sys
from typing import Optional, Tuple

YOUTUBE_URL_RE = re.compile(
    r'(?:youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|embed\/|v\/)|youtu\.be\/)'
    r'(?P<id>[A-Za-z0-9_-]{11})'
)


def parse_video_id(url: str) -> Optional[str]:
    """Extrai videoId de 11 caracteres de uma URL YouTube. None se URL inválida."""
    raise NotImplementedError("Phase 6 — implementar em Plan 04")


def fetch_metadata(video_id: str) -> dict:
    """Busca metadados (title, channel, duration, published_at) via YouTube Data API."""
    raise NotImplementedError("Phase 6 — implementar em Plan 04")


def upsert_source_video(conn, meta: dict) -> Tuple[str, bool]:
    """Insere ou atualiza source_videos. Retorna (status_atual, created)."""
    raise NotImplementedError("Phase 6 — implementar em Plan 04")


def main(url: str) -> int:
    """Entry point CLI: ingesta vídeo a partir da URL. Retorna exit code."""
    raise NotImplementedError("Phase 6 — implementar em Plan 04")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ''))
