"""Composição FFmpeg dos assets configuráveis de cada clip."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
DEFAULT_STILL_DURATION_SECONDS = 3
DEFAULT_MUSIC_VOLUME = 0.12


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
            '-c:v',
            'libx264',
            '-preset',
            'veryfast',
            '-crf',
            '23',
            '-pix_fmt',
            'yuv420p',
        ]
    )
    if has_audio:
        command.extend(['-map', '0:a:0', '-c:a', 'aac', '-ar', '48000', '-ac', '2'])
    else:
        command.extend(['-map', '1:a:0', '-c:a', 'aac', '-ar', '48000', '-ac', '2'])

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


def _mix_music(input_path: str, music_path: str, output_path: str, volume: float) -> None:
    safe_volume = min(max(float(volume), 0.01), 1.0)
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
                f'[1:a]volume={safe_volume:.3f}[music];'
                '[0:a][music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[a]'
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
    """Aplica intro, encerramento e música; sem assets, mantém o caminho original."""
    usable_assets = {
        kind: asset
        for kind, asset in assets.items()
        if asset.get('absolute_path') and os.path.isfile(str(asset['absolute_path']))
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

        music = usable_assets.get('music')
        if music:
            _mix_music(
                str(concatenated_path),
                str(music['absolute_path']),
                output_path,
                _volume(music.get('music_volume')),
            )
        else:
            shutil.copyfile(concatenated_path, output_path)

    return output_path
