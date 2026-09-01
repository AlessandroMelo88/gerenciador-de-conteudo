"""Opções de encode usadas em todos os vídeos publicados.

O YouTube reprocessa os arquivos enviados, mas a qualidade da primeira cópia
depende do arquivo de origem. Manter um conjunto único de opções evita que
uma etapa posterior (watermark, composição ou legenda) reduza a qualidade.
"""

import os

FFMPEG_PRESET = os.environ.get('FFMPEG_PRESET', 'slow')
FFMPEG_CRF = os.environ.get('FFMPEG_CRF', '14')

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
