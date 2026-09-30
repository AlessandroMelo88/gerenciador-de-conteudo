"""Composição FFmpeg dos assets configuráveis de cada clip."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from src.related_video import download_related_thumbnail, normalize_video_id
from src.video_quality import AUDIO_ENCODER_OPTIONS, VIDEO_ENCODER_OPTIONS, YOUTUBE_LOUDNORM_FILTER

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
DEFAULT_STILL_DURATION_SECONDS = 3
DEFAULT_MUSIC_VOLUME = 0.24
MUSIC_DURATION_SECONDS = 15
MUSIC_FINAL_VOLUME_SECONDS = 8
DEFAULT_TRANSITION_SECONDS = 0.35
RELATED_CARD_FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


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
    if isinstance(value, (int, float)):
        return float(value)
    return DEFAULT_MUSIC_VOLUME


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


def content_start_offset(
    assets: Mapping[str, Mapping[str, object]], content_duration: float
) -> float:
    """Calcula onde o conteúdo começa depois da intro com crossfade.

    O SRT de um vídeo longo precisa acompanhar a linha do tempo final, que
    inclui a intro. A composição usa a mesma transição de até 350 ms de
    ``_concat_segments``; repetir esse cálculo evita deslocar a legenda.
    """
    intro = assets.get('intro')
    if not intro:
        return 0.0
    intro_path = Path(str(intro.get('absolute_path')))
    if not intro_path or not intro_path.is_file():
        return 0.0

    intro_duration = _probe_duration(intro_path)
    if intro_duration is None:
        intro_duration = float(_duration(intro.get('duration_seconds')))

    known_durations = [intro_duration, max(float(content_duration), 1.0)]
    outro = assets.get('outro')
    if outro and outro.get('absolute_path'):
        outro_path = Path(str(outro['absolute_path']))
        if outro_path.is_file():
            outro_duration = _probe_duration(outro_path)
            if outro_duration is None:
                outro_duration = float(_duration(outro.get('duration_seconds')))
            known_durations.append(outro_duration)

    transition = min(DEFAULT_TRANSITION_SECONDS, min(known_durations) / 2)
    transition = max(0.05, transition)
    return max(0.05, intro_duration - transition)


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


def _escape_filter_path(path: str | Path) -> str:
    return str(path).replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")


def _related_card_geometry(video_format: str) -> tuple[int, int, int, int, int, int, int]:
    """Retorna painel, miniatura e posição para as duas telas suportadas."""
    if video_format == 'curto':
        return 60, 1280, 960, 600, 820, 1330, 34
    return 1340, 270, 540, 430, 420, 320, 32


def _apply_related_video_card(
    input_path: str,
    output_path: str,
    video_format: str,
    related_video: Mapping[str, object],
    temp_root: Path,
) -> bool:
    """Preenche a área reservada do encerramento com a miniatura relacionada."""
    video_id = normalize_video_id(related_video.get('video_id'))
    if not video_id:
        return False

    thumbnail_path = temp_root / 'related_thumbnail.jpg'
    has_thumbnail = download_related_thumbnail(video_id, thumbnail_path)

    panel_x, panel_y, panel_width, panel_height, thumb_width, thumb_y, font_size = (
        _related_card_geometry(video_format)
    )
    thumb_height = round(thumb_width * 9 / 16)
    thumb_x = panel_x + (panel_width - thumb_width) // 2
    title_path = temp_root / 'related_title.txt'
    title = str(related_video.get('title') or 'Vídeo relacionado')
    title_path.write_text(' '.join(title.split())[:72], encoding='utf-8')

    panel_bottom = panel_y + panel_height
    title_y = min(panel_bottom - font_size - 18, thumb_y + thumb_height + 28)
    filter_graph = (
        f'[0:v]drawbox=x={panel_x}:y={panel_y}:w={panel_width}:h={panel_height}:'
        'color=black@0.86:t=fill[panel];'
    )
    if has_thumbnail:
        filter_graph += (
            f'[1:v]scale={thumb_width}:{thumb_height}:force_original_aspect_ratio=decrease,'
            f'pad={thumb_width}:{thumb_height}:(ow-iw)/2:(oh-ih)/2:color=black[related_thumb];'
            f'[panel][related_thumb]overlay={thumb_x}:{thumb_y}[with_thumb];'
        )
        related_label = 'with_thumb'
    else:
        # A URL válida continua sendo apresentada mesmo se o YouTube não
        # responder a tempo com a miniatura; a publicação ainda terá o link.
        related_label = 'panel'
    filter_graph += (
        f'[{related_label}]drawtext=fontfile={_escape_filter_path(RELATED_CARD_FONT_PATH)}:'
        f'textfile={_escape_filter_path(title_path)}:fontcolor=white:fontsize={font_size}:'
        'box=1:boxcolor=black@0.55:boxborderw=10:'
        f'x={panel_x + 18}:y={title_y}[v]'
    )
    command = ['ffmpeg', '-y', '-i', input_path]
    if has_thumbnail:
        command.extend(['-loop', '1', '-i', str(thumbnail_path)])
    command.extend(
        [
            '-filter_complex',
            filter_graph,
            '-map',
            '[v]',
            '-map',
            '0:a:0',
            *VIDEO_ENCODER_OPTIONS,
            '-c:a',
            'copy',
            '-shortest',
            '-movflags',
            '+faststart',
            output_path,
        ]
    )
    try:
        _run_ffmpeg(command)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f'[MEDIA] Card relacionado não aplicado: {exc}', flush=True)
        return False
    return True


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

    Shorts são vídeos verticais curtos e devem permanecer apenas com o conteúdo
    principal, mesmo que um caller antigo forneça assets.
    """
    if video_format != 'longo':
        return input_path

    related_video = assets.get('related_video')
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

            outro_visual_path = outro_path
            if related_video:
                outro_with_related_path = temp_root / 'outro_com_relacionado.mp4'
                if _apply_related_video_card(
                    str(outro_path),
                    str(outro_with_related_path),
                    video_format,
                    related_video,
                    temp_root,
                ):
                    outro_visual_path = outro_with_related_path

            segments.append(outro_visual_path)

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
