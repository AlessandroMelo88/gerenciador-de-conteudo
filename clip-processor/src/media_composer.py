"""Composição FFmpeg dos assets configuráveis de cada clip."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from src.media_assets import media_format_enabled


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
DEFAULT_STILL_DURATION_SECONDS = 3
DEFAULT_MUSIC_VOLUME = 0.24
MUSIC_DURATION_SECONDS = 15
MUSIC_FINAL_VOLUME_SECONDS = 8
DEFAULT_TRANSITION_SECONDS = 0.35

# Encode dos segmentos de intro/encerramento e da união final. Independe do
# render dos cortes: aqui vale equilíbrio entre tempo e qualidade (a mídia é
# curta e reencodada uma vez). Ajustável sem rebuild pelas variáveis abaixo.
MEDIA_FFMPEG_PRESET = os.environ.get('MEDIA_FFMPEG_PRESET', 'veryfast')
MEDIA_FFMPEG_CRF = os.environ.get('MEDIA_FFMPEG_CRF', '20')
VIDEO_ENCODER_OPTIONS = (
    '-c:v',
    'libx264',
    '-preset',
    MEDIA_FFMPEG_PRESET,
    '-crf',
    MEDIA_FFMPEG_CRF,
    '-profile:v',
    'high',
    '-pix_fmt',
    'yuv420p',
)
AUDIO_ENCODER_OPTIONS = ('-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2')
# Padrão YouTube / EBU R128 (-14 LUFS) no áudio da composição final.
YOUTUBE_LOUDNORM_FILTER = 'loudnorm=I=-14:LRA=11:TP=-1.5'


def _run_ffmpeg(command: Sequence[str]) -> None:
    subprocess.run(command, check=True, capture_output=True)


def _has_audio(path: str) -> bool:
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v',
                'error',
                '-select_streams',
                'a:0',
                '-show_entries',
                'stream=codec_type',
                '-of',
                'csv=p=0',
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        # O worker já depende do ffmpeg; se o ffprobe falhar em uma mídia de
        # vídeo, presumir que ela tem áudio evita remover trilha existente.
        return Path(path).suffix.lower() not in IMAGE_EXTENSIONS

    return bool(result.stdout.strip())


def _canvas(video_format: str) -> tuple[int, int]:
    return (1080, 1920) if video_format == 'curto' else (1920, 1080)


def _duration(value: object) -> int | float:
    if isinstance(value, (int, float)) and value > 0:
        return value
    return DEFAULT_STILL_DURATION_SECONDS


def _volume(value: object) -> float:
    # psycopg2 devolve NUMERIC como Decimal; aceita qualquer coisa convertível.
    try:
        volume = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return DEFAULT_MUSIC_VOLUME
    return volume if volume > 0 else DEFAULT_MUSIC_VOLUME


def _video_filter(video_format: str) -> str:
    width, height = _canvas(video_format)
    return (
        f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
        f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,'
        'setsar=1,fps=30,format=yuv420p'
    )


def _probe_duration(path: Path) -> float | None:
    """Lê a duração do segmento já normalizado para calcular o xfade."""
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v',
                'error',
                '-show_entries',
                'format=duration',
                '-of',
                'default=noprint_wrappers=1:nokey=1',
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        duration = float(result.stdout.strip())
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None
    return duration if duration > 0 else None


def _normalize_segment(
    source_path: str,
    output_path: str,
    video_format: str,
    *,
    duration_seconds: int | float | None = None,
) -> None:
    """Normaliza um segmento para permitir concatenação sem reencodar depois."""
    source = Path(source_path)
    is_image = source.suffix.lower() in IMAGE_EXTENSIONS
    command = ['ffmpeg', '-y']

    if is_image:
        command.extend(['-loop', '1', '-framerate', '30'])
    command.extend(['-i', source_path])

    has_audio = False if is_image else _has_audio(source_path)
    if not has_audio:
        command.extend(['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo'])

    command.extend(
        [
            '-vf',
            _video_filter(video_format),
            '-map',
            '0:v:0',
            *VIDEO_ENCODER_OPTIONS,
        ]
    )
    if has_audio:
        command.extend(['-map', '0:a:0', *AUDIO_ENCODER_OPTIONS])
    else:
        command.extend(['-map', '1:a:0', *AUDIO_ENCODER_OPTIONS])

    if is_image and duration_seconds is not None:
        command.extend(['-t', str(max(float(duration_seconds), 1.0))])
    if is_image or not has_audio:
        command.append('-shortest')
    command.extend(['-movflags', '+faststart', output_path])
    _run_ffmpeg(command)


def _concat_file_line(path: Path) -> str:
    # O formato concat aceita aspas simples escapadas com a mesma convenção do
    # shell. Os caminhos são gerados pelo sistema e não vêm diretamente da URL.
    escaped = str(path).replace("'", "'\\''")
    return f"file '{escaped}'"


def _concat_segments(segment_paths: Sequence[Path], list_path: Path, output_path: str) -> None:
    """Une segmentos com crossfade curto e sincronizado em áudio.

    O nome da função é mantido por compatibilidade com o pipeline e testes
    existentes. Os segmentos já foram normalizados para o mesmo canvas, FPS e
    áudio; por isso o xfade é aplicado somente nas fronteiras entre cenas.
    """
    if len(segment_paths) == 1:
        shutil.copyfile(segment_paths[0], output_path)
        return

    durations = [_probe_duration(path) for path in segment_paths]
    if any(duration is None for duration in durations):
        # Falha no ffprobe não deve eliminar uma composição válida. O fallback
        # preserva o comportamento anterior, com corte seco entre segmentos.
        list_path.write_text(
            '\n'.join(_concat_file_line(path) for path in segment_paths) + '\n',
            encoding='utf-8',
        )
        _run_ffmpeg(
            [
                'ffmpeg',
                '-y',
                '-f',
                'concat',
                '-safe',
                '0',
                '-i',
                str(list_path),
                '-c',
                'copy',
                '-movflags',
                '+faststart',
                output_path,
            ]
        )
        return

    known_durations = [float(duration) for duration in durations if duration is not None]
    transition = min(DEFAULT_TRANSITION_SECONDS, min(known_durations) / 2)
    transition = max(0.05, transition)

    filters: list[str] = []
    for index in range(len(segment_paths)):
        filters.append(
            f'[{index}:v:0]settb=AVTB,format=yuv420p[v{index}];'
            f'[{index}:a:0]aresample=48000,aformat=sample_fmts=fltp:'
            f'sample_rates=48000:channel_layouts=stereo[a{index}]'
        )

    current_video = 'v0'
    current_audio = 'a0'
    composed_duration = known_durations[0]
    for index in range(1, len(segment_paths)):
        offset = max(0.05, composed_duration - transition)
        next_video = f'vx{index}'
        next_audio = f'ax{index}'
        filters.append(
            f'[{current_video}][v{index}]xfade=transition=fade:'
            f'duration={transition:.3f}:offset={offset:.3f}[{next_video}]'
        )
        filters.append(
            f'[{current_audio}][a{index}]acrossfade=d={transition:.3f}:c1=tri:c2=tri[{next_audio}]'
        )
        current_video = next_video
        current_audio = next_audio
        composed_duration += known_durations[index] - transition

    # Aplica normalização padrão YouTube (-14 LUFS) no áudio mixado da composição
    filters.append(f'[{current_audio}]{YOUTUBE_LOUDNORM_FILTER}[anorm]')
    final_audio = 'anorm'

    command = ['ffmpeg', '-y']
    for path in segment_paths:
        command.extend(['-i', str(path)])
    command.extend(
        [
            '-filter_complex',
            ';'.join(filters),
            '-map',
            f'[{current_video}]',
            '-map',
            f'[{final_audio}]',
            *VIDEO_ENCODER_OPTIONS,
            *AUDIO_ENCODER_OPTIONS,
            '-movflags',
            '+faststart',
            output_path,
        ]
    )
    _run_ffmpeg(command)


def _mix_music(input_path: str, music_path: str, output_path: str, volume: float) -> None:
    input_duration = _probe_duration(Path(input_path))
    if input_duration is None:
        raise RuntimeError(f'Não foi possível determinar a duração de {input_path}')

    music_duration = min(float(MUSIC_DURATION_SECONDS), input_duration)
    music_start = max(input_duration - music_duration, 0.0)
    safe_volume = min(max(float(volume), 0.01), 1.0)
    ramp_duration = min(float(MUSIC_FINAL_VOLUME_SECONDS), music_duration)
    ramp_start = max(0.0, music_duration - ramp_duration)
    if ramp_duration > 0:
        volume_expression = (
            f'if(lt(t,{ramp_start:.3f}),'
            f'{safe_volume:.3f},'
            f'if(lt(t,{music_duration:.3f}),'
            f'{safe_volume:.3f}+(1-{safe_volume:.3f})*'
            f'(t-{ramp_start:.3f})/{ramp_duration:.3f},1))'
        )
    else:
        volume_expression = f'{safe_volume:.3f}'
    delay_ms = round(music_start * 1000)
    _run_ffmpeg(
        [
            'ffmpeg',
            '-y',
            '-i',
            input_path,
            '-stream_loop',
            '-1',
            '-i',
            music_path,
            '-filter_complex',
            (
                f'[1:a]atrim=duration={music_duration:.3f},'
                f"volume='{volume_expression}':eval=frame,"
                f'asetpts=PTS-STARTPTS,adelay={delay_ms}|{delay_ms}[music];'
                f'[0:a][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,{YOUTUBE_LOUDNORM_FILTER}[a]'
            ),
            '-map',
            '0:v:0',
            '-map',
            '[a]',
            '-c:v',
            'copy',
            '-c:a',
            'aac',
            '-b:a',
            '192k',
            '-shortest',
            '-movflags',
            '+faststart',
            output_path,
        ]
    )


def compose_media(
    input_path: str,
    output_path: str,
    video_format: str,
    assets: Mapping[str, Mapping[str, object]],
) -> str:
    """Aplica intro, encerramento e música somente a vídeos longos.

    A música cobre os 15 segundos finais do vídeo composto, com fade-in de
    7 segundos e volume final mantido nos 8 segundos finais.

    Por padrão só o formato longo recebe mídia (``MEDIA_FORMATS``, ver
    ``media_assets``). Um formato fora da lista devolve o arquivo de entrada
    sem tocar em nada, mesmo que o caller forneça assets.
    """
    if not media_format_enabled(video_format):
        return input_path

    usable_assets = {
        kind: asset
        for kind, asset in assets.items()
        if kind in {'intro', 'outro', 'music'}
        and asset.get('absolute_path')
        and os.path.isfile(str(asset['absolute_path']))
    }
    if not usable_assets:
        return input_path

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with tempfile.TemporaryDirectory(prefix='clip-media-') as temp_dir:
        temp_root = Path(temp_dir)
        segments: list[Path] = []

        intro = usable_assets.get('intro')
        if intro:
            intro_path = temp_root / 'intro.mp4'
            _normalize_segment(
                str(intro['absolute_path']),
                str(intro_path),
                video_format,
                duration_seconds=_duration(intro.get('duration_seconds')),
            )
            segments.append(intro_path)

        clip_path = temp_root / 'clip.mp4'
        _normalize_segment(input_path, str(clip_path), video_format)
        segments.append(clip_path)

        outro = usable_assets.get('outro')
        if outro:
            outro_path = temp_root / 'outro.mp4'
            _normalize_segment(
                str(outro['absolute_path']),
                str(outro_path),
                video_format,
                duration_seconds=_duration(outro.get('duration_seconds')),
            )

            segments.append(outro_path)

        concatenated_path = temp_root / 'concatenated.mp4'
        _concat_segments(segments, temp_root / 'segments.txt', str(concatenated_path))

        final_media_path = concatenated_path
        music = usable_assets.get('music')
        if music:
            concatenated_with_music_path = temp_root / 'concatenated_com_musica.mp4'
            _mix_music(
                str(concatenated_path),
                str(music['absolute_path']),
                str(concatenated_with_music_path),
                _volume(music.get('music_volume')),
            )
            final_media_path = concatenated_with_music_path

        shutil.copyfile(final_media_path, output_path)

    return output_path
