"""Opções de encode dos vídeos publicados (modos de render).

O YouTube reprocessa o arquivo enviado, mas a qualidade da primeira cópia depende
do arquivo de origem. Este módulo concentra as opções de x264/AAC para que todas
as etapas (corte, legenda, watermark) usem o mesmo conjunto.

Modo escolhido por ``VIDEO_RENDER_MODE`` (lido a cada chamada, sem rebuild):

  padrao   (padrão) ultrafast, CRF 24, 1 thread, AAC 128k — comportamento da
           master antes deste módulo; é o que a A1 (2 OCPU) sustenta sem folga
           extra de CPU.
  economia veryfast, CRF 16 (alias: ``fast``) — meio-termo opt-in.
  quality  slow, CRF 14, AAC 320k (alias: ``maximo``) — qualidade máxima
           (portado de release/rico); custo de CPU alto, opt-in.
  ultra    ultrafast, CRF 18.

Ajustes finos: ``FFMPEG_PRESET``, ``FFMPEG_CRF`` e ``FFMPEG_THREADS`` sobrescrevem
o modo. ``AUDIO_LOUDNORM=0`` desliga a normalização de áudio.
"""

from __future__ import annotations

import os

MODE_PADRAO = 'padrao'
MODE_ECONOMIA = 'economia'
MODE_QUALITY = 'quality'
MODE_ULTRA = 'ultra'

_ALIASES = {
    'padrao': MODE_PADRAO,
    'padrão': MODE_PADRAO,
    'legacy': MODE_PADRAO,
    'economia': MODE_ECONOMIA,
    'fast': MODE_ECONOMIA,
    'quality': MODE_QUALITY,
    'maximo': MODE_QUALITY,
    'máximo': MODE_QUALITY,
    'ultra': MODE_ULTRA,
}

# modo -> (preset, crf, threads, audio_bitrate)
_PROFILES = {
    MODE_PADRAO: ('ultrafast', '24', '1', '128k'),
    MODE_ECONOMIA: ('veryfast', '16', '2', '320k'),
    MODE_QUALITY: ('slow', '14', '2', '320k'),
    MODE_ULTRA: ('ultrafast', '18', '2', '320k'),
}

# Normalização de áudio para o padrão YouTube / EBU R128 (-14 LUFS, TP -1.5 dB, LRA 11)
YOUTUBE_LOUDNORM_FILTER = 'loudnorm=I=-14:LRA=11:TP=-1.5'


def video_render_mode() -> str:
    raw = (os.environ.get('VIDEO_RENDER_MODE') or '').strip().lower()
    return _ALIASES.get(raw, MODE_PADRAO)


def video_encoder_options() -> tuple[str, ...]:
    preset, crf, threads, _ = _PROFILES[video_render_mode()]
    preset = os.environ.get('FFMPEG_PRESET') or preset
    crf = os.environ.get('FFMPEG_CRF') or crf
    threads = os.environ.get('FFMPEG_THREADS') or threads
    return (
        '-threads', threads,
        '-c:v', 'libx264',
        '-preset', preset,
        '-crf', crf,
        '-profile:v', 'high',
        '-level:v', '4.2',
        '-pix_fmt', 'yuv420p',
    )


def audio_encoder_options() -> tuple[str, ...]:
    bitrate = _PROFILES[video_render_mode()][3]
    return ('-c:a', 'aac', '-b:a', bitrate, '-ar', '48000', '-ac', '2')


def loudnorm_enabled() -> bool:
    return (os.environ.get('AUDIO_LOUDNORM', '1').strip().lower()
            not in {'0', 'false', 'no', 'off'})


def dynamic_audio_filter(duration: float) -> str | None:
    """Filtro de áudio: loudnorm (-14 LUFS) + fade in/out curtos contra estalo de corte.

    Devolve None quando ``AUDIO_LOUDNORM`` está desligado (o áudio segue sem filtro).
    """
    if not loudnorm_enabled():
        return None
    fade_out_start = max(0.0, float(duration) - 0.20)
    return (
        f'{YOUTUBE_LOUDNORM_FILTER},'
        f'afade=t=in:ss=0:d=0.08,afade=t=out:st={fade_out_start:.2f}:d=0.20'
    )
