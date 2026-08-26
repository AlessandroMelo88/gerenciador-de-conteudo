"""
video_processor.py — Corte, legendas, thumbnail e processamento de clips.

Exporta:
  - cut_clip(source_path, start_time, end_time, output_path) -> str
  - generate_srt(transcript, start_time, end_time, srt_path) -> str
  - burn_subtitles(input_clip_path, srt_path, output_path, fmt='curto') -> str
  - extract_thumbnail(clip_path, thumbnail_path, at_seconds=None) -> str
  - overlay_thumbnail_text(input_path, text, output_path) -> str
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
import tempfile
from datetime import datetime

from src.media_assets import resolve_media_assets
from src.media_composer import compose_media
from src.metadata_generator import generate_metadata, generate_thumbnail_text, update_clip_metadata
from src.related_video import related_video_from_clip
from src.selector import complete_moment_boundaries

VIDEOS_DIR = '/app/videos'
CLIPS_DIR = '/app/videos/clips'
THUMBNAILS_DIR = '/app/videos/thumbnails'
THUMBNAIL_FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REQUIRED_LONGFORM_ASSETS = ('intro', 'outro', 'music')

# Shorts: preserve the complete horizontal source in the foreground and use a
# blurred/dimmed copy behind it to fill the 9:16 canvas. A center crop loses
# speakers, screen recordings and on-screen text from 16:9 source videos.
SHORTS_VERTICAL_FILTER = (
    '[0:v]split=2[bg][fg];'
    '[bg]scale=1080:1920:force_original_aspect_ratio=increase,'
    'crop=1080:1920,boxblur=20:10,eq=brightness=-0.30:saturation=0.85[bgblur];'
    '[fg]scale=1080:1920:force_original_aspect_ratio=decrease,setsar=1[fgfit];'
    '[bgblur][fgfit]overlay=(W-w)/2:(H-h)/2:format=auto,setsar=1,format=yuv420p[v]'
)


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def cut_clip(
    source_path: str, start_time: float, end_time: float, output_path: str, fmt: str = 'curto'
) -> str:
    """Corta um trecho do vídeo fonte.

    fmt='curto' (padrão): converte pra vertical 1080x1920 (Shorts).
    O quadro horizontal completo é preservado no centro, com uma cópia
    desfocada e escurecida preenchendo o fundo vertical.
    fmt='longo': mantém aspecto horizontal original, só normaliza a altura pra
    1080p — vídeo longo de 7-20min não faz sentido em formato vertical.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    duration = max(float(end_time) - float(start_time), 1.0)
    fade_out_start = max(0.0, duration - 0.20)
    afade_filter = f'afade=t=in:ss=0:d=0.08,afade=t=out:st={fade_out_start:.2f}:d=0.20'

    if fmt == 'longo':
        video_args = ['-vf', 'scale=-2:1080,setsar=1']
        audio_args = ['-af', afade_filter]
    else:
        video_args = [
            '-filter_complex',
            SHORTS_VERTICAL_FILTER,
            '-map',
            '[v]',
            '-map',
            '0:a?',
        ]
        audio_args = ['-af', afade_filter]
    subprocess.run(
        [
            'ffmpeg',
            '-ss',
            str(start_time),
            '-to',
            str(end_time),
            '-i',
            source_path,
            *video_args,
            '-c:v',
            'libx264',
            '-preset',
            'veryfast',
            '-crf',
            '23',
            '-c:a',
            'aac',
            '-b:a',
            '128k',
            *audio_args,
            '-shortest',
            '-movflags',
            '+faststart',
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
        if seg_start >= end_time - 0.35:
            continue

        cue_start = max(seg_start, start_time) - start_time
        cue_end = min(seg_end, end_time) - start_time
        text = str(seg.get('text', '')).strip()
        if not text or cue_end <= cue_start:
            continue
        cues.append((cue_start, cue_end, text))

    with open(srt_path, 'w', encoding='utf-8') as f:
        for index, (cue_start, cue_end, text) in enumerate(cues, start=1):
            f.write(f'{index}\n')
            f.write(f'{_format_srt_time(cue_start)} --> {_format_srt_time(cue_end)}\n')
            f.write(f'{text}\n\n')

    return srt_path


def burn_subtitles(
    input_clip_path: str, srt_path: str, output_path: str, fmt: str = 'curto'
) -> str:
    """Queima legendas SRT no clip usando FFmpeg.

    A legenda queimada é um recurso exclusivo de Shorts. Manter essa guarda
    também na função, além do orquestrador, evita que um novo caller coloque
    legendas acidentalmente em um vídeo longo.

    Alignment=2 (rodapé-centro), estilo próximo do closed caption nativo do
    YouTube: fonte menor, caixa semi-transparente e fina em vez do bloco opaco
    grande. MarginV afasta o texto da barra de interações/UI do player. PlayResX/Y
    fixam a referência de escala do libass no tamanho real do clip. DejaVu Sans
    Bold: única família disponível no container (fc-list).
    """
    if fmt != 'curto':
        raise ValueError('Legendas queimadas são permitidas somente em Shorts (format=curto)')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    subtitle_filter = (
        f'subtitles={srt_path}:'
        "force_style='Fontname=DejaVu Sans,Bold=1,Fontsize=38,"
        'PlayResX=1080,PlayResY=1920,'
        'PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,'
        'BackColour=&H60000000,'
        "BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginV=180'"
    )
    subprocess.run(
        [
            'ffmpeg',
            '-i',
            input_clip_path,
            '-vf',
            subtitle_filter,
            '-c:v',
            'libx264',
            '-preset',
            'veryfast',
            '-crf',
            '23',
            '-c:a',
            'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def extract_thumbnail(clip_path: str, thumbnail_path: str, at_seconds: float | None = None) -> str:
    """Extrai um frame do clip como thumbnail JPG."""
    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
    if at_seconds is None:
        at_seconds = 1.0
    subprocess.run(
        [
            'ffmpeg',
            '-ss',
            str(at_seconds),
            '-i',
            clip_path,
            '-frames:v',
            '1',
            '-q:v',
            '2',
            thumbnail_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return thumbnail_path


def _escape_drawtext_value(value: str) -> str:
    """Escapa um valor de caminho no parser de filtros do FFmpeg."""
    return (
        str(value)
        .replace('\\', '\\\\')
        .replace("'", "\\'")
        .replace(':', '\\:')
        .replace(',', '\\,')
        .replace(';', '\\;')
        .replace('%', '\\%')
        .replace('[', '\\[')
        .replace(']', '\\]')
    )


def overlay_thumbnail_text(input_path: str, text: str | None, output_path: str) -> str:
    """Aplica a chamada obrigatória sobre a thumbnail usando FFmpeg."""
    text = str(text or '').strip()
    if not text:
        raise ValueError('Não é possível gerar thumbnail sem thumbnail_text')
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f'Thumbnail de entrada não encontrada: {input_path}')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    text_file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            suffix='.txt',
            dir=os.path.dirname(output_path),
            delete=False,
        ) as text_file:
            text_file.write(text)
            text_file_path = text_file.name

        drawtext_filter = (
            f'drawtext=fontfile={THUMBNAIL_FONT_PATH}:'
            f'textfile={_escape_drawtext_value(text_file_path)}:'
            'fontcolor=white:fontsize=78:'
            'borderw=4:bordercolor=black:'
            'box=1:boxcolor=black@0.70:boxborderw=24:'
            'x=(w-text_w)/2:y=48:fix_bounds=1'
        )
        subprocess.run(
            [
                'ffmpeg',
                '-i',
                input_path,
                '-vf',
                drawtext_filter,
                '-frames:v',
                '1',
                '-q:v',
                '2',
                output_path,
                '-y',
            ],
            check=True,
            capture_output=True,
        )
    except Exception:
        try:
            os.remove(output_path)
        except FileNotFoundError:
            pass
        raise
    finally:
        if text_file_path:
            try:
                os.remove(text_file_path)
            except FileNotFoundError:
                pass
    return output_path


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
            '-i',
            input_path,  # [0] = clip vídeo
            '-i',
            watermark_path,  # [1] = PNG watermark
            '-filter_complex',
            'overlay=W-w-20:20',  # canto sup direito, margem 20px
            '-c:v',
            'libx264',
            '-preset',
            'veryfast',
            '-crf',
            '23',
            '-c:a',
            'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path


def process_clip(conn, clip_id: int, anthropic_client=None) -> bool:
    """Processa um registro de generated_clips com status pending_cut.

    Pipeline de Shorts: cut → generate_srt → burn_subtitles → watermark → mídia →
    metadata → thumbnail com chamada. Pipeline longo: cut → watermark → intro +
    conteúdo + encerramento com trecho musical → metadata → thumbnail com chamada;
    vídeos longos não recebem SRT nem legendas queimadas.
    """
    try:
        clip = _fetch_clip(conn, clip_id)
        if clip is None:
            _log(f'Clip {clip_id} não encontrado')
            return False

        _update_clip_status(conn, clip_id, 'cutting')

        with open(clip['transcript_path'], encoding='utf-8') as f:
            transcript = json.load(f)

        # Proteção adicional para clips inseridos antes do ajuste do selector
        # ou criados manualmente: nunca entregar ao FFmpeg um fim no meio da fala.
        adjusted_timing = complete_moment_boundaries(
            [
                {
                    'start_time': clip['start_time'],
                    'end_time': clip['end_time'],
                }
            ],
            transcript.get('segments', []),
        )[0]
        if (
            adjusted_timing['start_time'] != clip['start_time']
            or adjusted_timing['end_time'] != clip['end_time']
        ):
            clip['start_time'] = adjusted_timing['start_time']
            clip['end_time'] = adjusted_timing['end_time']
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE generated_clips SET start_time=%s, end_time=%s WHERE id=%s',
                    (clip['start_time'], clip['end_time'], clip_id),
                )
            conn.commit()

        raw_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}_raw.mp4')
        srt_path = os.path.join(CLIPS_DIR, f'{clip_id}.srt')
        subtitled_path = os.path.join(CLIPS_DIR, f'{clip_id}_subtitled.mp4')
        final_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}.mp4')
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f'{clip_id}.jpg')
        video_format = clip.get('format') or 'curto'

        cut_clip(
            clip['local_path'],
            clip['start_time'],
            clip['end_time'],
            raw_clip_path,
            fmt=video_format,
        )

        if video_format == 'curto':
            generate_srt(transcript, clip['start_time'], clip['end_time'], srt_path)
            processed_clip_path = burn_subtitles(raw_clip_path, srt_path, subtitled_path)
        else:
            _log(f'Clip {clip_id} longo: legendas desativadas')
            processed_clip_path = raw_clip_path

        # Aplicar watermark se canal-destino tem slug configurado
        slug = clip.get('destination_channel_slug')
        if slug:
            watermark_path = f'/app/branding/watermark-{slug}.png'
            # overlay_watermark retorna o input se o arquivo não existir (graceful)
            result_path = overlay_watermark(processed_clip_path, watermark_path, final_clip_path)
            if result_path == processed_clip_path:
                # Watermark ausente: renomear para path final
                os.rename(processed_clip_path, final_clip_path)
            else:
                # Watermark aplicado: remover intermediário
                if os.path.exists(processed_clip_path):
                    os.remove(processed_clip_path)
        else:
            # Sem canal-destino: renomear o resultado de pós-produção para o final
            os.rename(processed_clip_path, final_clip_path)

        # Assets visuais vêm de assets/channels/<canal> e a música de assets/audio.
        # O banco de media_assets continua sendo fallback para instalações antigas.
        channel_slug = clip.get('destination_channel_slug') or clip.get('source_niche')
        media_assets = resolve_media_assets(
            conn,
            destination_channel_id=clip.get('destination_channel_id'),
            video_format=video_format,
            clip_id=clip_id,
            channel_slug=channel_slug,
        )

        # O encerramento tem uma área reservada para o próximo vídeo. A escolha
        # prioriza outro vídeo publicado no canal-destino e cai no vídeo fonte
        # quando ainda não há histórico próprio.
        related_video = related_video_from_clip(clip)
        if related_video and 'outro' in media_assets:
            media_assets['related_video'] = related_video

        if video_format == 'longo':
            missing_assets = [kind for kind in REQUIRED_LONGFORM_ASSETS if kind not in media_assets]
            if missing_assets:
                missing = ', '.join(missing_assets)
                raise RuntimeError(
                    f'Clip longo {clip_id} sem assets obrigatórios: {missing}. '
                    'Configure assets/channels/<canal> e assets/audio.'
                )

        if media_assets:
            branded_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}_branded.mp4')
            try:
                composed_path = compose_media(
                    final_clip_path,
                    branded_clip_path,
                    video_format,
                    media_assets,
                )
                if composed_path != final_clip_path:
                    os.replace(composed_path, final_clip_path)
            except Exception as exc:
                _log(f'Clip {clip_id}: mídia configurada não aplicada — {exc}')
                if os.path.exists(branded_clip_path):
                    os.remove(branded_clip_path)
                if video_format == 'longo':
                    raise

        clip_context = _build_clip_context(clip, transcript)
        metadata = generate_metadata(clip_context, anthropic_client=anthropic_client)
        thumbnail_text = generate_thumbnail_text(clip_context, anthropic_client=anthropic_client)

        extract_thumbnail(final_clip_path, thumbnail_path, at_seconds=1.0)
        thumbnail_with_text_path = os.path.join(THUMBNAILS_DIR, f'{clip_id}_with_text.jpg')
        enriched_thumbnail_path = overlay_thumbnail_text(
            thumbnail_path,
            thumbnail_text,
            thumbnail_with_text_path,
        )
        os.replace(enriched_thumbnail_path, thumbnail_path)

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE generated_clips SET clip_path=%s, thumbnail_path=%s WHERE id=%s',
                (final_clip_path, thumbnail_path, clip_id),
            )
        conn.commit()

        update_clip_metadata(conn, clip_id, metadata, clip_context=clip_context)
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
            'sv.youtube_video_id AS source_youtube_video_id, sv.title AS source_title, '
            'sv.local_path, sv.transcript_path, sv.format, '
            'sc.target_niche AS source_niche, '
            'dc.id AS destination_channel_id, dc.slug AS destination_channel_slug, '
            'dc.niche AS destination_niche, '
            '(SELECT rgc.youtube_video_id FROM generated_clips rgc '
            "WHERE rgc.status = 'published' "
            'AND rgc.youtube_video_id IS NOT NULL '
            'AND rgc.id <> gc.id '
            'AND rgc.destination_channel_id IS NOT DISTINCT FROM gc.destination_channel_id '
            'ORDER BY rgc.published_at DESC NULLS LAST, rgc.id DESC LIMIT 1) '
            'AS related_video_id, '
            '(SELECT rgc.title FROM generated_clips rgc '
            "WHERE rgc.status = 'published' "
            'AND rgc.youtube_video_id IS NOT NULL '
            'AND rgc.id <> gc.id '
            'AND rgc.destination_channel_id IS NOT DISTINCT FROM gc.destination_channel_id '
            'ORDER BY rgc.published_at DESC NULLS LAST, rgc.id DESC LIMIT 1) '
            'AS related_video_title '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            'LEFT JOIN source_channels sc ON sc.id = sv.channel_id '
            'LEFT JOIN destination_channels dc ON dc.id = gc.destination_channel_id '
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
        'format': clip.get('format') or 'curto',
        'niche': clip.get('destination_niche') or clip.get('target_niche') or '',
        'transcript_excerpt': ' '.join(line for line in excerpt_lines if line),
    }


def _format_srt_time(seconds: float) -> str:
    milliseconds_total = round(seconds * 1000)
    hours = milliseconds_total // 3_600_000
    remainder = milliseconds_total % 3_600_000
    minutes = remainder // 60_000
    remainder %= 60_000
    secs = remainder // 1000
    millis = remainder % 1000
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}'
