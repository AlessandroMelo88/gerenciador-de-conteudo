"""Opções de encode usadas em todos os vídeos publicados.

O YouTube reprocessa os arquivos enviados, mas a qualidade da primeira cópia
depende do arquivo de origem. Manter um conjunto único de opções evita que
uma etapa posterior (watermark, composição ou legenda) reduza a qualidade.
"""

import os

FFMPEG_PRESET = os.environ.get('FFMPEG_PRESET_OVERRIDE') or os.environ.get('FFMPEG_PRESET') or 'veryfast'
if FFMPEG_PRESET in ('slow', 'fast'):
    FFMPEG_PRESET = 'veryfast'
FFMPEG_CRF = os.environ.get('FFMPEG_CRF_OVERRIDE') or os.environ.get('FFMPEG_CRF') or '20'
if FFMPEG_CRF in ('14', '18'):
    FFMPEG_CRF = '20'

VIDEO_ENCODER_OPTIONS = (
    '-c:v',
    'libx264',
    '-preset',
    FFMPEG_PRESET,
    '-crf',
    FFMPEG_CRF,
    '-profile:v',
    'high',
    '-level:v',
    '4.2',
    '-pix_fmt',
    'yuv420p',
)

AUDIO_ENCODER_OPTIONS = (
    '-c:a',
    'aac',
    '-b:a',
    '320k',
    '-ar',
    '48000',
    '-ac',
    '2',
)
