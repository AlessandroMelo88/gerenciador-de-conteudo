"""
video_processor.py — Corte, legendas, thumbnail e processamento de clips.

Exporta:
  - cut_clip(source_path, start_time, end_time, output_path) -> str
  - generate_srt(transcript, start_time, end_time, srt_path) -> str
  - burn_subtitles(input_clip_path, srt_path, output_path) -> str
  - extract_thumbnail(clip_path, thumbnail_path, at_seconds=None) -> str
  - overlay_watermark(input_path, watermark_path, output_path) -> str
  - process_clip(conn, clip_id, anthropic_client=None) -> bool

Convenções:
  - FFmpeg é chamado via subprocess.run(check=True, capture_output=True)
  - Diretórios são constantes patcháveis em testes
  - conn: quem chama é responsável por fechar
"""
import json
import os
import subprocess
from datetime import datetime

from src.metadata_generator import generate_metadata, update_clip_metadata


VIDEOS_DIR = '/app/videos'
CLIPS_DIR = '/app/videos/clips'
THUMBNAILS_DIR = '/app/videos/thumbnails'


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def cut_clip(source_path: str, start_time: float, end_time: float, output_path: str) -> str:
    """Corta um trecho do vídeo fonte e converte para 1080x1920."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    video_filter = (
        'scale=1080:1920:force_original_aspect_ratio=increase,'
        'crop=1080:1920,'
        'setsar=1'
    )
    subprocess.run(
        [
            'ffmpeg',
            '-ss', str(start_time),
            '-to', str(end_time),
            '-i', source_path,
            '-vf', video_filter,
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def generate_srt(transcript: dict, start_time: float, end_time: float, srt_path: str) -> str:
    """Gera arquivo SRT relativo ao início do clip a partir dos segmentos Whisper."""
    os.makedirs(os.path.dirname(srt_path), exist_ok=True)
    cues = []

    for seg in transcript.get('segments', []):
        seg_start = float(seg['start'])
        seg_end = float(seg['end'])
        if seg_end <= start_time or seg_start >= end_time:
            continue

        cue_start = max(seg_start, start_time) - start_time
        cue_end = min(seg_end, end_time) - start_time
        text = str(seg.get('text', '')).strip()
        if not text:
            continue
        cues.append((cue_start, cue_end, text))

    with open(srt_path, 'w', encoding='utf-8') as f:
        for index, (cue_start, cue_end, text) in enumerate(cues, start=1):
            f.write(f'{index}\n')
            f.write(f'{_format_srt_time(cue_start)} --> {_format_srt_time(cue_end)}\n')
            f.write(f'{text}\n\n')

    return srt_path


def burn_subtitles(input_clip_path: str, srt_path: str, output_path: str) -> str:
    """Queima legendas SRT no clip usando FFmpeg."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subtitle_filter = (
        f"subtitles={srt_path}:"
        "force_style='Fontname=Arial,Fontsize=12,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=160'"
    )
    subprocess.run(
        [
            'ffmpeg',
            '-i', input_clip_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-c:a', 'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def extract_thumbnail(clip_path: str, thumbnail_path: str, at_seconds: float = None) -> str:
    """Extrai um frame do clip como thumbnail JPG."""
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
    if at_seconds is None:
        at_seconds = 1.0
    subprocess.run(
        [
            'ffmpeg',
            '-ss', str(at_seconds),
            '-i', clip_path,
            '-frames:v', '1',
            '-q:v', '2',
            thumbnail_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return thumbnail_path


def overlay_watermark(input_path: str, watermark_path: str, output_path: str) -> str:
    """Aplica watermark PNG no canto superior direito do clip via FFmpeg.

    Usa -filter_complex overlay=W-w-20:20 com dois inputs (clip + PNG alpha).
    Retorna input_path sem chamar FFmpeg se o watermark não existir (graceful degradation).
    """
    if not os.path.exists(watermark_path):
        _log(f'[WATERMARK] Arquivo não encontrado: {watermark_path} — pulo overlay')
        return input_path

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subprocess.run(
        [
            'ffmpeg',
            '-i', input_path,        # [0] = clip vídeo
            '-i', watermark_path,    # [1] = PNG watermark
            '-filter_complex', 'overlay=W-w-20:20',  # canto sup direito, margem 20px
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-c:a', 'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def process_clip(conn, clip_id: int, anthropic_client=None) -> bool:
    """Processa um registro de generated_clips com status pending_cut."""
    try:
        clip = _fetch_clip(conn, clip_id)
        if clip is None:
            _log(f'Clip {clip_id} não encontrado')
            return False

        _update_clip_status(conn, clip_id, 'cutting')

        with open(clip['transcript_path'], 'r', encoding='utf-8') as f:
            transcript = json.load(f)

        raw_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}_raw.mp4')
        srt_path = os.path.join(CLIPS_DIR, f'{clip_id}.srt')
        final_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}.mp4')
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f'{clip_id}.jpg')

        cut_clip(clip['local_path'], clip['start_time'], clip['end_time'], raw_clip_path)
        generate_srt(transcript, clip['start_time'], clip['end_time'], srt_path)
        burn_subtitles(raw_clip_path, srt_path, final_clip_path)
        duration = max(float(clip['end_time']) - float(clip['start_time']), 1.0)
        extract_thumbnail(final_clip_path, thumbnail_path, at_seconds=duration / 2)

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE generated_clips '
                'SET clip_path=%s, thumbnail_path=%s '
                'WHERE id=%s',
                (final_clip_path, thumbnail_path, clip_id),
            )
        conn.commit()

        metadata = generate_metadata(_build_clip_context(clip, transcript), anthropic_client=anthropic_client)
        update_clip_metadata(conn, clip_id, metadata)
        _update_clip_status(conn, clip_id, 'pending')
        _log(f'Clip {clip_id} processado: {final_clip_path}')
        return True

    except Exception as exc:
        _log(f'Erro ao processar clip {clip_id}: {exc}')
        try:
            _update_clip_status(conn, clip_id, 'failed')
        except Exception:
            pass
        return False


def _fetch_clip(conn, clip_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'gc.id, gc.source_video_id, gc.start_time, gc.end_time, gc.score, gc.reason, '
            'sv.youtube_video_id, sv.title AS source_title, sv.local_path, sv.transcript_path '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            'WHERE gc.id = %s',
            (clip_id,),
        )
        return cur.fetchone()


def _update_clip_status(conn, clip_id: int, status: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE generated_clips SET status=%s WHERE id=%s',
            (status, clip_id),
        )
    conn.commit()


def _build_clip_context(clip: dict, transcript: dict) -> dict:
    start_time = float(clip['start_time'])
    end_time = float(clip['end_time'])
    excerpt_lines = []
    for seg in transcript.get('segments', []):
        seg_start = float(seg['start'])
        seg_end = float(seg['end'])
        if seg_end > start_time and seg_start < end_time:
            excerpt_lines.append(str(seg.get('text', '')).strip())

    return {
        'source_title': clip.get('source_title') or '',
        'reason': clip.get('reason') or '',
        'score': clip.get('score'),
        'start_time': start_time,
        'end_time': end_time,
        'transcript_excerpt': ' '.join(line for line in excerpt_lines if line),
    }


def _format_srt_time(seconds: float) -> str:
    milliseconds_total = int(round(seconds * 1000))
    hours = milliseconds_total // 3_600_000
    remainder = milliseconds_total % 3_600_000
    minutes = remainder // 60_000
    remainder %= 60_000
    secs = remainder // 1000
    millis = remainder % 1000
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}'
