"""
video_processor.py — Corte, legendas, thumbnail e processamento de clips.

Exporta:
  - cut_clip(source_path, start_time, end_time, output_path) -> str
  - render_short_clip(source_path, start_time, end_time, output_path, ...) -> str
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

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Any

from src.media_assets import resolve_media_assets
from src.media_composer import compose_media, content_start_offset
from src.media_contract import (
    SHORTS_DURATION_TOLERANCE_SECONDS,
    SHORTS_MAX_DURATION_SECONDS,
    SHORTS_MIN_DURATION_SECONDS,
)
from src.meme_editor import build_panico_face_bulge_filter, detect_meme_moments
from src.metadata_generator import generate_metadata, generate_thumbnail_text, update_clip_metadata
from src.paths import BRANDING_DIR, VIDEOS_DIR, resolve_stored_video_path
from src.prompt_profiles import PROMPT_PROFILE_SQL_COLUMNS, profile_from_row, profile_matches_niche
from src.related_video import related_video_from_clip
from src.selector import complete_moment_boundaries, normalize_shortform_moment
from src.subtitle_detector import has_burned_subtitles
from src.video_quality import AUDIO_ENCODER_OPTIONS, VIDEO_ENCODER_OPTIONS, YOUTUBE_LOUDNORM_FILTER

CLIPS_DIR = os.path.join(VIDEOS_DIR, 'clips')
THUMBNAILS_DIR = os.path.join(VIDEOS_DIR, 'thumbnails')
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


def _subtitle_filter(srt_path: str) -> str:
    return (
        f'subtitles={srt_path}:'
        "force_style='Fontname=DejaVu Sans,Bold=1,Fontsize=38,"
        'PlayResX=1080,PlayResY=1920,'
        'PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,'
        'BackColour=&H60000000,'
        "BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginV=180'"
    )


def _thumbnail_sample_time(
    video_format: str,
    media_assets: dict[str, Any] | None,
    content_duration: float,
) -> float:
    """Sample an in-content frame, skipping the long-form intro when present."""
    duration = max(0.0, float(content_duration))
    if video_format == 'longo':
        offset = content_start_offset(media_assets or {}, duration)
        in_content_offset = min(2.0, duration / 2.0)
        return offset + in_content_offset
    return min(1.0, duration / 2.0)


def _meme_effects_enabled(destination_channel_slug: str | None) -> bool:
    configured = {
        slug.strip()
        for slug in os.environ.get('MEME_EFFECTS_CHANNELS', '').split(',')
        if slug.strip()
    }
    return bool(destination_channel_slug and destination_channel_slug in configured)


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def cut_clip(
    source_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
    fmt: str = 'curto',
    meme_filter: str | None = None,
) -> str:
    """Corta um trecho do vídeo fonte.

    fmt='curto' (padrão): converte pra vertical 1080x1920 (Shorts).
    O quadro horizontal completo é preservado no centro, com uma cópia
    desfocada e escurecida preenchendo o fundo vertical.
    fmt='longo': mantém aspecto horizontal original, só normaliza a altura pra
    1080p — vídeo longo de 7-20min não faz sentido em formato vertical.
    meme_filter: filtro FFmpeg opcional para efeitos cômicos/inchar a cara estilo Pânico na TV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    duration = max(float(end_time) - float(start_time), 1.0)
    fade_out_start = max(0.0, duration - 0.20)
    afade_filter = f'afade=t=in:ss=0:d=0.08,afade=t=out:st={fade_out_start:.2f}:d=0.20'

    audio_filter = f'{YOUTUBE_LOUDNORM_FILTER},{afade_filter}'
    if fmt == 'longo':
        vf = 'scale=-2:1080,setsar=1'
        if meme_filter:
            vf = f'{vf},{meme_filter}'
        video_args = ['-vf', vf]
        audio_args = ['-af', audio_filter]
    else:
        video_args = [
            '-filter_complex',
            SHORTS_VERTICAL_FILTER,
            '-map',
            '[v]',
            '-map',
            '0:a?',
        ]
        audio_args = ['-af', audio_filter]
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
            *VIDEO_ENCODER_OPTIONS,
            *AUDIO_ENCODER_OPTIONS,
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


def render_short_clip(
    source_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
    subtitle_path: str | None = None,
    watermark_path: str | None = None,
    meme_filter: str | None = None,
) -> str:
    """Renderiza um Short completo em uma única recodificação de vídeo.

    Cortar, queimar legenda e aplicar watermark em chamadas FFmpeg separadas
    acumulava perdas de qualidade. Esta função compõe todas as camadas no mesmo
    filtro e mantém a duração selecionada, entre 30 e 45 segundos por padrão,
    em 1080x1920.
    """
    duration = float(end_time) - float(start_time)
    if (
        duration < SHORTS_MIN_DURATION_SECONDS - SHORTS_DURATION_TOLERANCE_SECONDS
        or duration > SHORTS_MAX_DURATION_SECONDS + SHORTS_DURATION_TOLERANCE_SECONDS
    ):
        raise ValueError(
            f'Short precisa ter entre {SHORTS_MIN_DURATION_SECONDS:.0f} e '
            f'{SHORTS_MAX_DURATION_SECONDS:.0f}s, recebeu {duration:.2f}s'
        )
    render_duration = min(max(duration, SHORTS_MIN_DURATION_SECONDS), SHORTS_MAX_DURATION_SECONDS)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    filter_graph = SHORTS_VERTICAL_FILTER.replace('[v]', '[short_base]')
    current_label = '[short_base]'
    if meme_filter:
        filter_graph += f';{current_label}{meme_filter}[short_meme]'
        current_label = '[short_meme]'
    if subtitle_path:
        filter_graph += f';{current_label}{_subtitle_filter(subtitle_path)}[short_captioned]'
        current_label = '[short_captioned]'

    effective_watermark_path = (
        watermark_path if watermark_path and os.path.exists(watermark_path) else None
    )
    if effective_watermark_path:
        filter_graph += (
            ';[1:v]format=rgba[short_watermark];'
            f'{current_label}[short_watermark]'
            'overlay=W-w-20:20:eof_action=repeat:format=auto[short_final]'
        )
        output_label = '[short_final]'
    else:
        output_label = current_label
        if watermark_path:
            _log(f'[WATERMARK] Arquivo não encontrado: {watermark_path} — pulo overlay')

    fade_out_start = max(0.0, render_duration - 0.20)
    afade_filter = f'{YOUTUBE_LOUDNORM_FILTER},afade=t=in:ss=0:d=0.08,afade=t=out:st={fade_out_start:.2f}:d=0.20'
    command = [
        'ffmpeg',
        '-ss',
        str(start_time),
        '-i',
        source_path,
    ]
    if effective_watermark_path:
        command.extend(['-loop', '1', '-i', effective_watermark_path])
    command.extend(
        [
            '-t',
            f'{render_duration:.2f}',
            '-filter_complex',
            filter_graph,
            '-map',
            output_label,
            '-map',
            '0:a?',
            *VIDEO_ENCODER_OPTIONS,
            *AUDIO_ENCODER_OPTIONS,
            '-af',
            afade_filter,
            '-movflags',
            '+faststart',
            output_path,
            '-y',
        ]
    )
    subprocess.run(command, check=True, capture_output=True)
    return output_path


def generate_srt(
    transcript: dict,
    start_time: float,
    end_time: float,
    srt_path: str,
    time_offset: float = 0.0,
) -> str:
    """Gera SRT relativo ao clip, com offset opcional da composição final."""
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
        cues.append((cue_start + time_offset, cue_end + time_offset, text))

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

    subprocess.run(
        [
            'ffmpeg',
            '-i',
            input_clip_path,
            '-vf',
            _subtitle_filter(srt_path),
            *VIDEO_ENCODER_OPTIONS,
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
            *VIDEO_ENCODER_OPTIONS,
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

    Pipeline de Shorts: render único (quadro vertical + legenda + watermark) →
    metadata → thumbnail com chamada. Shorts são verticais e não recebem intro,
    encerramento ou música. Pipeline longo: cut → generate_srt → watermark →
    intro + conteúdo + encerramento com trecho musical → metadata → thumbnail
    com chamada. Vídeos longos recebem o SRT para publicação como legenda
    oficial, mas não têm a legenda queimada no quadro. Em Shorts cujo vídeo fonte
    já traz legenda gravada, burn_subtitles é pulado: o clip sai só com a legenda
    que já vinha do vídeo original, mais o SRT como legenda oficial.
    """
    try:
        # Trava atômica: garante que apenas um worker processe o clip em pending_cut
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE generated_clips SET status = 'cutting' WHERE id = %s AND status = 'pending_cut'",
                (clip_id,),
            )
            if cur.rowcount == 0:
                _log(
                    f'Clip {clip_id} já está em processamento ou não está em pending_cut — pulando'
                )
                return False
        conn.commit()

        clip = _fetch_clip(conn, clip_id)
        if clip is None:
            _log(f'Clip {clip_id} não encontrado')
            return False

        transcript_path = resolve_stored_video_path(clip.get('transcript_path'))
        transcript_data = clip.get('transcript_data')
        local_path = resolve_stored_video_path(clip.get('local_path'))

        if not transcript_path and not transcript_data:
            err = f'Clip {clip_id} sem transcrição arquivada'
            _log(err)
            _update_clip_failure(conn, clip_id, err)
            return False

        if not local_path:
            err = f'Clip {clip_id} sem local_path cadastrado'
            _log(err)
            _update_clip_failure(conn, clip_id, err)
            return False

        if clip.get('start_time') is None or clip.get('end_time') is None:
            err = f'Clip {clip_id} com start_time ou end_time nulos'
            _log(err)
            _update_clip_failure(conn, clip_id, err)
            return False

        if float(clip['end_time']) <= float(clip['start_time']):
            err = f'Clip {clip_id} com end_time ({clip["end_time"]}) <= start_time ({clip["start_time"]})'
            _log(err)
            _update_clip_failure(conn, clip_id, err)
            return False

        if transcript_path and os.path.isfile(transcript_path):
            with open(transcript_path, encoding='utf-8') as f:
                transcript = json.load(f)
        else:
            transcript = (
                json.loads(transcript_data) if isinstance(transcript_data, str) else transcript_data
            )
        if not isinstance(transcript, dict) or not isinstance(transcript.get('segments'), list):
            raise ValueError(f'Clip {clip_id} tem transcrição inválida ou vazia')

        # Proteção adicional para clips inseridos antes do ajuste do selector
        # ou criados manualmente: nunca entregar ao FFmpeg um fim no meio da fala.
        video_format = clip.get('format') or 'curto'
        adjusted_timing = complete_moment_boundaries(
            [
                {
                    'start_time': clip['start_time'],
                    'end_time': clip['end_time'],
                }
            ],
            transcript.get('segments', []),
        )[0]
        if video_format == 'curto':
            transcript_duration = max(
                (float(segment.get('end', 0)) for segment in transcript.get('segments', [])),
                default=0.0,
            )
            normalized_timing = normalize_shortform_moment(
                adjusted_timing,
                transcript_duration=transcript_duration or None,
            )
            if normalized_timing is None:
                raise ValueError(f'Clip curto {clip_id} não possui uma janela válida de 30s')
            adjusted_timing = normalized_timing
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
        final_clip_path = os.path.join(CLIPS_DIR, f'{clip_id}.mp4')
        thumbnail_path = os.path.join(THUMBNAILS_DIR, f'{clip_id}.jpg')

        # Distorção cômica é opcional por canal para não alterar conteúdo técnico
        # ou jornalístico por coincidência de palavras como "falhou" e "quebrou".
        meme_events = (
            detect_meme_moments(
                transcript.get('segments', []),
                clip['start_time'],
                clip['end_time'],
                max_effects=3 if video_format == 'curto' else 6,
            )
            if _meme_effects_enabled(clip.get('destination_channel_slug'))
            else []
        )
        meme_filter = build_panico_face_bulge_filter(meme_events) if meme_events else None
        if meme_filter:
            keywords = [e['keyword'] for e in meme_events]
            _log(
                f'Clip {clip_id}: {len(meme_events)} momentos meme estilo Pânico na TV detectados {keywords}'
            )

        if video_format == 'curto':
            # No Shorts a faixa acompanha o clip sem composição adicional e
            # também é queimada no quadro — exceto quando o próprio vídeo fonte
            # já traz a legenda gravada, caso em que queimar de novo deixaria
            # dois textos na tela. O SRT continua sendo gerado nos dois casos
            # porque a legenda oficial do YouTube vem dele.
            generate_srt(transcript, clip['start_time'], clip['end_time'], srt_path)
            source_has_burned_subtitles = has_burned_subtitles(
                clip['local_path'], transcript, clip['start_time'], clip['end_time']
            )
            if source_has_burned_subtitles:
                _log(
                    f'Clip {clip_id}: fonte já tem legenda queimada — mantendo só a legenda oficial'
                )
            watermark_path = None
            if clip.get('destination_channel_slug'):
                watermark_path = os.path.join(
                    BRANDING_DIR,
                    f'watermark-{clip["destination_channel_slug"]}.png',
                )
            short_kwargs: dict[str, Any] = {
                'subtitle_path': None if source_has_burned_subtitles else srt_path,
                'watermark_path': watermark_path,
            }
            if meme_filter:
                short_kwargs['meme_filter'] = meme_filter
            render_short_clip(
                clip['local_path'],
                clip['start_time'],
                clip['end_time'],
                final_clip_path,
                **short_kwargs,
            )
        else:
            cut_kwargs: dict[str, Any] = {'fmt': video_format}
            if meme_filter:
                cut_kwargs['meme_filter'] = meme_filter
            cut_clip(
                clip['local_path'],
                clip['start_time'],
                clip['end_time'],
                raw_clip_path,
                **cut_kwargs,
            )
            _log('Clip longo: SRT será alinhado após a composição da intro')
            processed_clip_path = raw_clip_path

            # Aplicar watermark ao vídeo longo, que não participa do render
            # único dos Shorts.
            slug = clip.get('destination_channel_slug')
            if slug:
                watermark_path = os.path.join(BRANDING_DIR, f'watermark-{slug}.png')
                result_path = overlay_watermark(
                    processed_clip_path, watermark_path, final_clip_path
                )
                if result_path == processed_clip_path:
                    os.rename(processed_clip_path, final_clip_path)
                elif os.path.exists(processed_clip_path):
                    os.remove(processed_clip_path)
            else:
                os.rename(processed_clip_path, final_clip_path)

        media_assets: dict[str, Any] = {}
        if video_format == 'longo':
            # Assets do canal vêm de assets/channels/<canal>, incluindo a
            # música em audio/. O banco mantém assets legados já associados a
            # um destino. Shorts não passam por esta etapa.
            channel_slug = clip.get('destination_channel_slug') or clip.get('source_niche')
            media_assets = resolve_media_assets(
                conn,
                destination_channel_id=clip.get('destination_channel_id'),
                video_format=video_format,
                clip_id=clip_id,
                channel_slug=channel_slug,
            )

            # O encerramento tem uma área reservada para o próximo vídeo. A
            # escolha prioriza outro vídeo publicado no canal-destino e cai no
            # vídeo fonte quando ainda não há histórico próprio.
            related_video = related_video_from_clip(clip)
            if related_video and 'outro' in media_assets:
                media_assets['related_video'] = related_video

            missing_assets = [kind for kind in REQUIRED_LONGFORM_ASSETS if kind not in media_assets]
            if missing_assets:
                missing = ', '.join(missing_assets)
                raise RuntimeError(
                    f'Clip longo {clip_id} sem assets obrigatórios: {missing}. '
                    'Configure assets/channels/<canal>/ e associe os assets do painel ao canal.'
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
                    raise

            # Intro/outro e crossfade alteram a linha do tempo do conteúdo.
            # Só gerar o SRT depois da composição garante que a legenda oficial
            # acompanhe a fala na posição correta do vídeo final.
            generate_srt(
                transcript,
                clip['start_time'],
                clip['end_time'],
                srt_path,
                time_offset=content_start_offset(
                    media_assets,
                    clip['end_time'] - clip['start_time'],
                ),
            )

        clip_context = _build_clip_context(clip, transcript)
        metadata = generate_metadata(clip_context, anthropic_client=anthropic_client)
        thumbnail_text = generate_thumbnail_text(clip_context, anthropic_client=anthropic_client)

        thumbnail_at = _thumbnail_sample_time(
            video_format,
            media_assets,
            clip['end_time'] - clip['start_time'],
        )
        extract_thumbnail(final_clip_path, thumbnail_path, at_seconds=thumbnail_at)
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
            _update_clip_failure(conn, clip_id, str(exc))
        except Exception:
            pass
        return False


def _fetch_clip(conn, clip_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT '
            'gc.id, gc.source_video_id, gc.start_time, gc.end_time, gc.score, gc.reason, '
            'sv.youtube_video_id AS source_youtube_video_id, sv.title AS source_title, '
            'sv.local_path, sv.transcript_path, sv.transcript_data, '
            'COALESCE(gc.format, sv.format) AS format, '
            'sc.target_niche AS source_niche, ' + PROMPT_PROFILE_SQL_COLUMNS + ', '
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
            'LEFT JOIN prompt_profiles pp '
            'ON pp.id = COALESCE(dc.prompt_profile_id, sc.prompt_profile_id) '
            'AND pp.active = TRUE '
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


def _update_clip_failure(conn, clip_id: int, error: str) -> None:
    """Marca a falha do corte e persiste o motivo para diagnóstico no painel."""
    with conn.cursor() as cur:
        cur.execute(
            'UPDATE generated_clips SET status=%s, upload_error=%s WHERE id=%s',
            ('failed', error[:2000], clip_id),
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

    niche = clip.get('destination_niche') or clip.get('target_niche') or ''
    prompt_profile = profile_from_row(clip)
    if prompt_profile and not profile_matches_niche(prompt_profile, niche):
        prompt_profile = None

    return {
        'source_title': clip.get('source_title') or '',
        'reason': clip.get('reason') or '',
        'score': clip.get('score'),
        'start_time': start_time,
        'end_time': end_time,
        'format': clip.get('format') or 'curto',
        'niche': niche,
        'prompt_profile': prompt_profile,
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
