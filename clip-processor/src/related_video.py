"""Destinos relacionados usados no encerramento e na publicação.

O YouTube Data API não expõe a edição de telas finais. O pipeline mantém o
encerramento preparado para o card visual e também publica um link clicável na
descrição, escolhendo primeiro outro vídeo já publicado no mesmo canal-destino
e usando o vídeo fonte como fallback.
"""

from __future__ import annotations

import re
import urllib.request
from collections.abc import Mapping
from pathlib import Path

YOUTUBE_ID_RE = re.compile(r'^[A-Za-z0-9_-]{6,64}$')
RELATED_VIDEO_LABEL = 'Assista também'
RELATED_THUMBNAIL_MAX_BYTES = 8 * 1024 * 1024


def normalize_video_id(value: object) -> str | None:
    """Valida um identificador antes de usá-lo em URL ou filtro FFmpeg."""
    if value is None:
        return None
    video_id = str(value).strip()
    return video_id if YOUTUBE_ID_RE.fullmatch(video_id) else None


def related_video_from_clip(clip: Mapping[str, object]) -> dict[str, object] | None:
    """Retorna o vídeo relacionado escolhido para um clip.

    ``related_video_id`` vem da consulta de publicação e representa o último
    clip publicado no mesmo canal-destino. Antes de existir um vídeo próprio,
    ``source_youtube_video_id`` (o vídeo de origem) garante que o encerramento
    nunca fique sem um destino válido.
    """
    video_id = next(
        (
            normalize_video_id(candidate)
            for candidate in (
                clip.get('related_video_id'),
                clip.get('source_youtube_video_id'),
                clip.get('youtube_video_id'),
            )
            if normalize_video_id(candidate)
        ),
        None,
    )
    if not video_id:
        return None

    title = str(
        clip.get('related_video_title')
        or clip.get('source_title')
        or clip.get('title')
        or 'Vídeo relacionado'
    ).strip()
    return {
        'video_id': video_id,
        'title': title or 'Vídeo relacionado',
        'url': f'https://www.youtube.com/watch?v={video_id}',
        'thumbnail_url': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
    }


def append_related_video(description: object, related_video: Mapping[str, object] | None) -> str:
    """Acrescenta um destino relacionado sem duplicar links já publicados."""
    base = str(description or '').strip()
    if not related_video:
        return base

    video_id = normalize_video_id(related_video.get('video_id'))
    if not video_id:
        return base

    url = f'https://www.youtube.com/watch?v={video_id}'
    if url in base or f'https://youtu.be/{video_id}' in base:
        return base

    title = str(related_video.get('title') or 'Vídeo relacionado').strip()
    suffix = f'{RELATED_VIDEO_LABEL}: {title}\n{url}'
    return f'{base}\n\n{suffix}' if base else suffix


def download_related_thumbnail(video_id: object, output_path: str | Path) -> bool:
    """Baixa a miniatura pública do vídeo para compor o card final.

    A miniatura é um enriquecimento opcional: uma falha de rede não impede o
    clip de ser produzido nem a URL relacionada de ir para a descrição.
    """
    normalized_id = normalize_video_id(video_id)
    if not normalized_id:
        return False

    request = urllib.request.Request(
        f'https://i.ytimg.com/vi/{normalized_id}/hqdefault.jpg',
        headers={'User-Agent': 'clip-processor/1.0'},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read(RELATED_THUMBNAIL_MAX_BYTES + 1)
    except (OSError, TimeoutError, ValueError):
        return False

    if not data or len(data) > RELATED_THUMBNAIL_MAX_BYTES:
        return False

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return True
