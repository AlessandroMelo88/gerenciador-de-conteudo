"""Opções de encode usadas em todos os vídeos publicados.

O YouTube reprocessa os arquivos enviados, mas a qualidade da primeira cópia
depende do arquivo de origem. Manter um conjunto único de opções evita que
uma etapa posterior (watermark, composição ou legenda) reduza a qualidade.
"""

import os

def video_render_mode() -> str:
    mode = (os.environ.get('VIDEO_RENDER_MODE') or '').strip().lower()
    if mode in ('fast', 'ultra'):
        return mode
    return 'quality'


def ffmpeg_global_options() -> tuple[str, ...]:
    filter_threads = os.environ.get('FFMPEG_FILTER_THREADS', '0')
    return (
        '-filter_threads',
        filter_threads,
        '-filter_complex_threads',
        filter_threads,
    )


def video_encoder_options() -> tuple[str, ...]:
    mode = video_render_mode()
    threads = os.environ.get('FFMPEG_THREADS', '0')

    if mode == 'ultra':
        preset = 'ultrafast'
        default_crf = '18'
    elif mode == 'fast':
        preset = 'veryfast'
        default_crf = '16'
    else:
        # Modo padrão: qualidade máxima
        preset = os.environ.get('FFMPEG_PRESET', 'slow')
        default_crf = '14'

    crf = os.environ.get('FFMPEG_CRF', default_crf)

    return (
        '-c:v',
        'libx264',
        '-preset',
        preset,
        '-crf',
        crf,
        '-threads',
        threads,
        '-profile:v',
        'high',
        '-level:v',
        '4.2',
        '-pix_fmt',
        'yuv420p',
    )


FFMPEG_PRESET = os.environ.get('FFMPEG_PRESET', 'slow')
FFMPEG_CRF = os.environ.get('FFMPEG_CRF', '14')

VIDEO_ENCODER_OPTIONS = video_encoder_options()

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
