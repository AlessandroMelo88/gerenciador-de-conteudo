"""Contrato técnico da mídia publicada como YouTube Short.

Reconciliação com a regra de duração da master (decisão de 30/09/2026):
a POLÍTICA editorial continua no ``selector`` — descarta momento abaixo de 15 s,
estica 15-30 s até 30 s quando a transcrição permite, teto de 180 s. Este módulo
só verifica o que é TÉCNICO no arquivo já renderizado: vertical 9:16 e duração
entre um piso absoluto e o teto. A faixa rígida 30-45 s da release/rico NÃO foi
adotada por padrão; quem quiser o teto de 45 s define
``SHORTS_MAX_DURATION_SECONDS=45`` (o render corta o excedente e o contrato o
respeita).
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any

SHORTS_DURATION_TOLERANCE_SECONDS = 0.35
# Piso absoluto: o selector aceita clip curto só quando a transcrição inteira é
# menor que 30 s (nunca abaixo de 5 s).
SHORTS_MIN_DURATION_SECONDS = 5.0
SHORTS_DEFAULT_MAX_DURATION_SECONDS = 180.0
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920


def shorts_max_duration() -> float:
    """Teto de duração do Short (env ``SHORTS_MAX_DURATION_SECONDS``, padrão 180)."""
    raw = os.environ.get('SHORTS_MAX_DURATION_SECONDS', '').strip()
    try:
        value = float(raw) if raw else SHORTS_DEFAULT_MAX_DURATION_SECONDS
    except ValueError:
        value = SHORTS_DEFAULT_MAX_DURATION_SECONDS
    return max(value, SHORTS_MIN_DURATION_SECONDS)


class MediaContractError(ValueError):
    """Arquivo de mídia não atende ao contrato de publicação."""


def probe_media(path: str) -> dict[str, Any]:
    """Lê duração e dimensões do arquivo usando o ffprobe disponível no worker."""
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'error',
                '-show_entries', 'stream=codec_type,width,height:format=duration',
                '-of', 'json', path,
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
            s for s in payload.get('streams', []) if s.get('codec_type') == 'video'
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
    """Valida o arquivo final de um Short: vertical 9:16 e duração dentro dos limites."""
    info = probe_media(path)
    if not info['is_vertical']:
        raise MediaContractError(
            f'Short precisa ser vertical 9:16, mas recebeu {info["width"]}x{info["height"]}'
        )
    max_duration = shorts_max_duration()
    if (
        info['duration'] < SHORTS_MIN_DURATION_SECONDS - SHORTS_DURATION_TOLERANCE_SECONDS
        or info['duration'] > max_duration + SHORTS_DURATION_TOLERANCE_SECONDS
    ):
        raise MediaContractError(
            f'Short precisa ter entre {SHORTS_MIN_DURATION_SECONDS:.0f} e '
            f'{max_duration:.0f}s, mas recebeu {info["duration"]:.2f}s'
        )
    return info
