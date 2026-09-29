"""Contrato técnico para a mídia que pode ser publicada como YouTube Short."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any

SHORTS_DURATION_SECONDS = 30.0
SHORTS_DURATION_TOLERANCE_SECONDS = 0.35
SHORTS_MIN_DURATION_SECONDS = 30.0
SHORTS_MAX_DURATION_SECONDS = max(
    SHORTS_MIN_DURATION_SECONDS,
    float(os.environ.get('SHORTS_MAX_DURATION_SECONDS', '45')),
)
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920


class MediaContractError(ValueError):
    """Arquivo de mídia não atende ao contrato de publicação."""


def probe_media(path: str) -> dict[str, Any]:
    """Lê duração e dimensões do arquivo usando o ffprobe disponível no worker."""
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v',
                'error',
                '-show_entries',
                'stream=codec_type,width,height:format=duration',
                '-of',
                'json',
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise MediaContractError('ffprobe não está disponível no clip-processor') from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or '').strip().splitlines()[-1:] or ['erro desconhecido']
        raise MediaContractError(f'Não foi possível inspecionar a mídia: {detail[0]}') from exc

    try:
        payload = json.loads(result.stdout or '{}')
        video_stream = next(
            stream for stream in payload.get('streams', []) if stream.get('codec_type') == 'video'
        )
        duration = float(payload.get('format', {}).get('duration'))
        width = int(video_stream.get('width'))
        height = int(video_stream.get('height'))
    except (KeyError, TypeError, ValueError, StopIteration) as exc:
        raise MediaContractError(
            f'ffprobe retornou dados incompletos para a mídia: {path}'
        ) from exc

    return {
        'duration': duration,
        'width': width,
        'height': height,
        'is_vertical': width * 16 == height * 9,
    }


def validate_short_media(path: str) -> dict[str, Any]:
    """Valida o arquivo final de um Short antes de qualquer upload.

    A tolerância cobre diferenças residuais de container/encodificação. Por
    padrão, o corte pode durar de 30 a 45 segundos; SHORTS_MAX_DURATION_SECONDS
    permite experimentar com durações maiores quando isso for configurado.
    """
    info = probe_media(path)
    if not info['is_vertical']:
        raise MediaContractError(
            f'Short precisa ser vertical 9:16, mas recebeu {info["width"]}x{info["height"]}'
        )
    if (
        info['duration'] < SHORTS_MIN_DURATION_SECONDS - SHORTS_DURATION_TOLERANCE_SECONDS
        or info['duration'] > SHORTS_MAX_DURATION_SECONDS + SHORTS_DURATION_TOLERANCE_SECONDS
    ):
        raise MediaContractError(
            f'Short precisa ter entre {SHORTS_MIN_DURATION_SECONDS:.0f} e '
            f'{SHORTS_MAX_DURATION_SECONDS:.0f}s, mas recebeu {info["duration"]:.2f}s'
        )
    return info
