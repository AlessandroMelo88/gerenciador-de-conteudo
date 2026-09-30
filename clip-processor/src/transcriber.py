"""
transcriber.py — Legendas do YouTube com fallback para Groq Whisper API.

Exporta:
  - transcribe_video(video_id, video_path, groq_client=None, db_conn=None, prompt=None) -> dict | None
  - save_transcript(conn, video_id, transcript) -> str

Convenções:
  - transcribe_video tenta primeiro as legendas manuais em português já disponíveis no YouTube;
    faixas ASR automáticas são ignoradas e Groq é usado quando nenhuma faixa manual é encontrada
  - groq_client=None cria cliente de produção; injetado em testes (padrão do projeto)
  - db_conn=None: save_transcript recebe conn explícito — quem chama fecha a conexão
  - Logging via _log() com tag [AI]
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TypedDict
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import yt_dlp

from src.db import get_db_driver
from src.paths import VIDEOS_DIR

YOUTUBE_CAPTION_LANGS = ('pt-BR', 'pt', 'pt.*')
YOUTUBE_PLAYER_CLIENT_VERSION = '20.10.38'
YOUTUBE_REQUEST_TIMEOUT_SECONDS = 20
# Groq rejects uploads around 25 MB. Keep a generous margin because the
# multipart request itself adds a small amount of overhead.
GROQ_SAFE_FILE_BYTES = 20_000_000
TRANSCRIPTION_CHUNK_SECONDS = 900
# Chave pública do cliente do YouTube (não é um segredo). A página pode fornecer
# uma chave atualizada; esta serve para o player continuar funcionando quando a
# página de watch responder 429.
YOUTUBE_FALLBACK_INNERTUBE_API_KEY = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
YOUTUBE_USER_AGENT = (
    f'com.google.android.youtube/{YOUTUBE_PLAYER_CLIENT_VERSION} (Linux; U; Android 11) gzip'
)

_VTT_TIMING_RE = re.compile(
    r'^\s*(?P<start>(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3})\s+-->\s+'
    r'(?P<end>(?:\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3})(?:\s|$)'
)
_VTT_TAG_RE = re.compile(r'<[^>]*>')

WHISPER_TECH_PROMPT = (
    'Tecnologia, Inteligência Artificial, LLMs, Machine Learning, Qwen 2.5, Claude Code, '
    'METR, Mano Deyvin, Lucas Montano, Gabriel Fróes, Vanessa Weber, Código Fonte TV, '
    'Hacker Libertário, SaaS, API, Docker, Linux, Git, Python, Prompt, Benchmark, Open Source.'
)


class TranscriptSegment(TypedDict):
    start: float
    end: float
    text: str


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [AI] {msg}')


def _parse_vtt_timestamp(value: str) -> float:
    """Converte timestamp WebVTT (com ou sem horas) para segundos."""
    parts = value.replace(',', '.').split(':')
    if len(parts) == 2:
        minutes, seconds = parts
        hours = '0'
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f'timestamp WebVTT inválido: {value}')
    return float(hours) * 3600 + float(minutes) * 60 + float(seconds)


def _clean_caption_text(value: str) -> str:
    """Remove marcações WebVTT/HTML e normaliza o texto de uma legenda."""
    value = html.unescape(value)
    value = _VTT_TAG_RE.sub('', value)
    return re.sub(r'\s+', ' ', value).strip()


def _normalize_segments(segments: list[TranscriptSegment]) -> list[TranscriptSegment]:
    """Garante que segmentos sejam estritamente sequenciais e sem sobreposições artificiais de display."""
    if not segments:
        return []

    normalized: list[TranscriptSegment] = []
    for seg in segments:
        start = seg['start']
        end = seg['end']
        text = seg['text']

        if normalized and normalized[-1]['end'] > start:
            if start > normalized[-1]['start']:
                normalized[-1]['end'] = start
            else:
                normalized[-1]['end'] = max(normalized[-1]['start'] + 0.1, start)

        if end <= start:
            continue
        normalized.append({'start': start, 'end': end, 'text': text})

    for i in range(len(normalized) - 1):
        if normalized[i]['end'] > normalized[i + 1]['start']:
            normalized[i]['end'] = normalized[i + 1]['start']

    return [s for s in normalized if s['end'] > s['start']]


def _parse_vtt(payload: str) -> dict | None:
    """Converte uma legenda WebVTT em transcrição com segmentos temporizados."""
    lines = payload.lstrip('\ufeff').splitlines()
    segments: list[TranscriptSegment] = []
    index = 0

    while index < len(lines):
        match = _VTT_TIMING_RE.match(lines[index])
        if not match:
            index += 1
            continue

        start = _parse_vtt_timestamp(match.group('start'))
        end = _parse_vtt_timestamp(match.group('end'))
        index += 1
        cue_lines = []
        while index < len(lines) and lines[index].strip():
            cue_lines.append(lines[index].strip())
            index += 1

        text = _clean_caption_text(' '.join(cue_lines))
        if end <= start or not text:
            continue

        segment: TranscriptSegment = {'start': start, 'end': end, 'text': text}
        if not (segments and segments[-1] == segment):
            segments.append(segment)

    segments = _normalize_segments(segments)
    if not segments:
        return None

    return {
        'text': '\n'.join(segment['text'] for segment in segments),
        'segments': segments,
    }


def _parse_youtube_timedtext(payload: str) -> dict | None:
    """Converte o XML timedtext oficial do player do YouTube em segmentos."""
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return _parse_vtt(payload)

    cues = root.findall('.//p')
    segments: list[TranscriptSegment] = []
    for index, cue in enumerate(cues):
        try:
            start = float(cue.attrib['t']) / 1000
        except (KeyError, TypeError, ValueError):
            continue

        text = _clean_caption_text(''.join(cue.itertext()))
        if not text:
            continue

        try:
            duration = float(cue.attrib['d']) / 1000
        except (KeyError, TypeError, ValueError):
            duration = 0
            for next_cue in cues[index + 1 :]:
                try:
                    next_start = float(next_cue.attrib['t']) / 1000
                except (KeyError, TypeError, ValueError):
                    continue
                if next_start > start:
                    duration = next_start - start
                    break
            if duration <= 0:
                duration = 5

        end = start + duration
        if end <= start:
            continue

        segment: TranscriptSegment = {'start': start, 'end': end, 'text': text}
        if not (segments and segments[-1] == segment):
            segments.append(segment)

    segments = _normalize_segments(segments)
    if not segments:
        return None

    return {
        'text': '\n'.join(segment['text'] for segment in segments),
        'segments': segments,
    }


def _caption_language_rank(language_code: str) -> int | None:
    """Retorna a prioridade de uma faixa de legenda em português."""
    normalized = language_code.lower()
    if normalized == 'pt-br':
        return 0
    if normalized == 'pt':
        return 1
    if normalized.startswith('pt-'):
        return 2
    return None


def _youtube_caption_tracks(player_response: dict, allow_automatic: bool = False) -> list[dict]:
    """Seleciona faixas pt publicadas/manualizadas (e automáticas se explicitamente permitido).

    Prioriza faixas manuais enviadas pelo criador. Se allow_automatic=True e não houver
    faixas manuais, aproveita a legenda oficial da plataforma para economizar recursos
    de transcrição.
    """
    captions = player_response.get('captions', {}).get('playerCaptionsTracklistRenderer', {})
    manual: list[tuple[int, dict]] = []
    auto: list[tuple[int, dict]] = []
    for track in captions.get('captionTracks', []):
        rank = _caption_language_rank(track.get('languageCode', ''))
        if rank is None or not track.get('baseUrl'):
            continue
        if track.get('kind') != 'asr':
            manual.append((rank, track))
        elif allow_automatic:
            auto.append((rank + 100, track))

    tracks = sorted(manual, key=lambda item: item[0])
    if not tracks and allow_automatic:
        tracks = sorted(auto, key=lambda item: item[0])

    return [track for _rank, track in tracks]


def _fetch_youtube_player_response(video_id: str, api_key: str) -> dict:
    """Consulta o endpoint Innertube do player sem baixar a mídia."""
    player_request = Request(
        'https://www.youtube.com/youtubei/v1/player?key=' + api_key,
        data=json.dumps(
            {
                'context': {
                    'client': {
                        'clientName': 'ANDROID',
                        'clientVersion': YOUTUBE_PLAYER_CLIENT_VERSION,
                    }
                },
                'videoId': video_id,
            }
        ).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'User-Agent': YOUTUBE_USER_AGENT,
            'X-YouTube-Client-Name': '3',
            'X-YouTube-Client-Version': YOUTUBE_PLAYER_CLIENT_VERSION,
        },
        method='POST',
    )
    with urlopen(player_request, timeout=YOUTUBE_REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode('utf-8'))


def _fetch_youtube_page_api_key(video_id: str) -> str:
    """Lê a chave pública atual do HTML do vídeo para renovar o fallback."""
    page_request = Request(
        f'https://www.youtube.com/watch?v={video_id}',
        headers={'User-Agent': 'Mozilla/5.0'},
    )
    with urlopen(page_request, timeout=YOUTUBE_REQUEST_TIMEOUT_SECONDS) as response:
        page = response.read().decode('utf-8', errors='replace')

    match = re.search(r'"INNERTUBE_API_KEY"\s*:\s*"([A-Za-z0-9_-]+)"', page)
    if not match:
        raise ValueError('INNERTUBE_API_KEY não encontrada na página do YouTube')
    return match.group(1)


def _download_youtube_player_transcript(
    video_id: str, allow_automatic: bool = False
) -> dict | None:
    """Obtém a faixa de legenda pelo player oficial, sem baixar a mídia."""
    try:
        try:
            player_response = _fetch_youtube_player_response(
                video_id, YOUTUBE_FALLBACK_INNERTUBE_API_KEY
            )
        except Exception as first_exc:
            api_key = _fetch_youtube_page_api_key(video_id)
            player_response = _fetch_youtube_player_response(video_id, api_key)
            _log(f'Player do YouTube renovado pela página para {video_id}: {first_exc}')

        tracks = _youtube_caption_tracks(player_response, allow_automatic=allow_automatic)
        for track in tracks:
            try:
                caption_request = Request(
                    track['baseUrl'],
                    headers={
                        'Referer': f'https://www.youtube.com/watch?v={video_id}',
                        'User-Agent': YOUTUBE_USER_AGENT,
                    },
                )
                with urlopen(caption_request, timeout=YOUTUBE_REQUEST_TIMEOUT_SECONDS) as response:
                    payload = response.read().decode('utf-8', errors='replace')
                transcript = _parse_youtube_timedtext(payload)
            except Exception as exc:
                _log(f'Falha ao ler faixa de legenda do YouTube para {video_id}: {exc}')
                continue

            if transcript is None:
                continue

            transcript['video_id'] = video_id
            transcript['source'] = (
                'youtube_automatic_captions' if track.get('kind') == 'asr' else 'youtube_captions'
            )
            _log(
                f'Legenda do player do YouTube encontrada para {video_id}: '
                f'{len(transcript["segments"])} segmentos'
            )
            return transcript
    except Exception as exc:
        _log(f'Player de legendas do YouTube indisponível para {video_id}: {exc}')
    return None


def _download_youtube_caption(video_id: str, automatic: bool) -> dict | None:
    """Baixa uma faixa de legenda em português sem baixar o vídeo."""
    source = 'automática' if automatic else 'manual'
    try:
        with tempfile.TemporaryDirectory(
            prefix=f'.{video_id}_captions-', dir=VIDEOS_DIR
        ) as temp_dir:
            options = {
                'skip_download': True,
                'writesubtitles': not automatic,
                'writeautomaticsub': automatic,
                'subtitleslangs': list(YOUTUBE_CAPTION_LANGS),
                'subtitlesformat': 'vtt',
                'outtmpl': str(Path(temp_dir) / '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])

            for caption_path in sorted(Path(temp_dir).glob('*.vtt')):
                transcript = _parse_vtt(caption_path.read_text(encoding='utf-8'))
                if transcript:
                    transcript['video_id'] = video_id
                    transcript['source'] = (
                        'youtube_automatic_captions' if automatic else 'youtube_captions'
                    )
                    _log(
                        f'Legenda {source} do YouTube encontrada para {video_id}: '
                        f'{len(transcript["segments"])} segmentos'
                    )
                    return transcript
    except Exception as exc:
        _log(f'Legenda {source} indisponível para {video_id}: {exc}')
    return None


USE_YOUTUBE_AUTO_CAPTIONS = os.environ.get(
    'USE_YOUTUBE_AUTO_CAPTIONS', 'false'
).strip().lower() in ('1', 'true', 'yes')


def _download_youtube_transcript(video_id: str) -> dict | None:
    """Busca legenda oficial do YouTube (manual prioritária, ou automática da plataforma) para evitar gastar recursos."""
    manual = _download_youtube_player_transcript(
        video_id, allow_automatic=False
    ) or _download_youtube_caption(video_id, automatic=False)
    if manual is not None:
        return manual

    if USE_YOUTUBE_AUTO_CAPTIONS:
        auto = _download_youtube_player_transcript(
            video_id, allow_automatic=True
        ) or _download_youtube_caption(video_id, automatic=True)
        if auto is not None:
            _log(
                f'Aproveitando legenda oficial da plataforma para {video_id} (economia de recursos)'
            )
            return auto

    return None


def _prepare_audio(video_path: str) -> tuple[str, bool]:
    """Extrai áudio MP3 de um arquivo de vídeo via ffmpeg.

    Args:
        video_path: caminho absoluto do arquivo .mp4

    Returns:
        Tupla (audio_path, should_delete) onde should_delete=True indica que
        o arquivo de áudio temporário deve ser deletado após uso.
    """
    audio_path = video_path.replace('.mp4', '_audio.mp3')
    subprocess.run(
        [
            'ffmpeg',
            '-i',
            video_path,
            '-vn',
            '-ar',
            '16000',
            '-ac',
            '1',
            '-b:a',
            '16k',
            audio_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return (audio_path, True)


def _split_audio(audio_path: str, video_id: str) -> tuple[list[str], str | None]:
    """Divide áudio grande em partes pequenas para respeitar o limite do Groq.

    Retorna os caminhos dos pedaços e o diretório temporário que deve ser
    removido pelo chamador. A codificação mono/16 kbit/s mantém os arquivos
    pequenos sem prejudicar a transcrição de fala.
    """
    chunks_dir = tempfile.mkdtemp(prefix=f'.{video_id}_chunks-', dir=VIDEOS_DIR)
    chunk_pattern = str(Path(chunks_dir) / 'chunk_%03d.mp3')
    try:
        subprocess.run(
            [
                'ffmpeg',
                '-i',
                audio_path,
                '-map',
                '0:a:0',
                '-f',
                'segment',
                '-segment_time',
                str(TRANSCRIPTION_CHUNK_SECONDS),
                '-reset_timestamps',
                '1',
                '-ar',
                '16000',
                '-ac',
                '1',
                '-c:a',
                'libmp3lame',
                '-b:a',
                '16k',
                chunk_pattern,
                '-y',
            ],
            check=True,
            capture_output=True,
        )
        chunks = sorted(str(path) for path in Path(chunks_dir).glob('chunk_*.mp3'))
        if not chunks:
            raise RuntimeError('ffmpeg não gerou partes de áudio')
        return chunks, chunks_dir
    except Exception:
        shutil.rmtree(chunks_dir, ignore_errors=True)
        raise


def transcribe_video(
    video_id: str,
    video_path: str,
    groq_client=None,
    db_conn=None,
    prompt: str | None = None,
) -> dict | None:
    """Obtém a transcrição do YouTube e usa Groq Whisper apenas como fallback.

    Args:
        video_id: youtube_video_id do vídeo
        video_path: caminho absoluto do arquivo .mp4 em /app/videos/
        groq_client: cliente Groq (None = produção, injetado = testes)
        db_conn: conexão PostgreSQL (None = não atualiza status; passar conn para atualizar)
        prompt: termos contextuais específicos para transcrição, somente quando o perfil for compatível

    Returns:
        dict com {'video_id', 'text', 'segments'} ou None em caso de falha
    """
    youtube_transcript = _download_youtube_transcript(video_id)
    if youtube_transcript is not None:
        return youtube_transcript

    audio_path = None
    should_delete_audio = False
    chunks_dir = None

    try:
        if groq_client is None:
            from groq import Groq

            groq_client = Groq()

        # Verificar tamanho do arquivo: >24MB aciona extração de áudio
        if os.path.getsize(video_path) > 24_000_000:
            _log(f'Arquivo {video_id} >24MB — extraindo áudio MP3 via ffmpeg')
            audio_path, should_delete_audio = _prepare_audio(video_path)
            file_to_transcribe = audio_path
        else:
            file_to_transcribe = video_path

        def _g(seg, key):
            return seg[key] if isinstance(seg, dict) else getattr(seg, key)

        transcription_files = [file_to_transcribe]
        if (
            file_to_transcribe == audio_path
            and os.path.exists(file_to_transcribe)
            and os.path.getsize(file_to_transcribe) > GROQ_SAFE_FILE_BYTES
        ):
            transcription_files, chunks_dir = _split_audio(audio_path, video_id)
            _log(
                f'Áudio de {video_id} excede {GROQ_SAFE_FILE_BYTES // 1_000_000}MB — '
                f'dividido em {len(transcription_files)} partes'
            )

        all_segments: list[dict[str, float | str]] = []
        text_parts = []
        for index, transcription_file in enumerate(transcription_files):
            _log(
                f'Iniciando transcrição Groq Whisper para {video_id}'
                + (
                    f' (parte {index + 1}/{len(transcription_files)})'
                    if len(transcription_files) > 1
                    else ''
                )
            )

            transcription_options = {
                'model': 'whisper-large-v3-turbo',
                'response_format': 'verbose_json',
                'timestamp_granularities': ['segment'],
                'language': 'pt',
                'temperature': 0.0,
            }
            if prompt:
                transcription_options['prompt'] = prompt

            with open(transcription_file, 'rb') as f:
                result = groq_client.audio.transcriptions.create(
                    file=f,
                    **transcription_options,
                )

            offset = index * TRANSCRIPTION_CHUNK_SECONDS if len(transcription_files) > 1 else 0
            all_segments.extend(
                {
                    'start': _g(seg, 'start') + offset,
                    'end': _g(seg, 'end') + offset,
                    'text': _g(seg, 'text'),
                }
                for seg in result.segments
            )
            text_parts.append(result.text)

        segments = all_segments

        _log(f'Transcrição concluída para {video_id}: {len(segments)} segmentos')
        return {
            'video_id': video_id,
            'text': '\n'.join(text_parts),
            'segments': segments,
        }

    except Exception as e:
        _log(f'Erro na transcrição de {video_id}: {e}')
        return None

    finally:
        # Limpar arquivo de áudio temporário se foi criado
        if should_delete_audio and audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            _log(f'Áudio temporário removido: {audio_path}')
        if chunks_dir:
            shutil.rmtree(chunks_dir, ignore_errors=True)
            _log(f'Partes de áudio temporárias removidas: {chunks_dir}')


def save_transcript(conn, video_id: str, transcript: dict) -> str:
    """Persiste a transcrição integral no banco e atualiza o sidecar atomicamente.

    Args:
        conn: conexão PostgreSQL ativa (quem chama é responsável por fechar)
        video_id: youtube_video_id
        transcript: dict com {'video_id', 'text', 'segments'}

    Returns:
        Caminho absoluto do arquivo JSON salvo
    """
    transcript_path = os.path.join(VIDEOS_DIR, f'{video_id}_transcript.json')
    transcript_json = json.dumps(transcript, ensure_ascii=False)
    transcript_text = str(transcript.get('text') or '')
    transcript_column = (
        'transcript_data=%s::json' if get_db_driver(conn) == 'pgsql' else 'transcript_data=%s'
    )

    os.makedirs(VIDEOS_DIR, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=VIDEOS_DIR,
            prefix=f'.{video_id}_transcript.',
            suffix='.tmp',
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name
            json.dump(transcript, temp_file, ensure_ascii=False, indent=2)

        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, transcript_data, transcript_text FROM source_videos '
                'WHERE youtube_video_id=%s',
                (video_id,),
            )
            existing = cur.fetchone()

        transcript_changed = existing is None
        if existing is not None:
            existing_data = existing.get('transcript_data')
            if isinstance(existing_data, str):
                try:
                    existing_data = json.loads(existing_data)
                except json.JSONDecodeError:
                    pass
            transcript_changed = (
                existing_data != transcript
                or str(existing.get('transcript_text') or '') != transcript_text
            )

        with conn.cursor() as cur:
            if transcript_changed and existing is not None:
                cur.execute(
                    'DELETE FROM source_video_topics WHERE source_video_id=%s',
                    (existing['id'],),
                )
                cur.execute(
                    f'UPDATE source_videos SET transcript_path=%s, {transcript_column}, '
                    'transcript_text=%s, topic_segmentation_status=%s, '
                    'topic_segmentation_error=NULL WHERE youtube_video_id=%s',
                    (transcript_path, transcript_json, transcript_text, 'pending', video_id),
                )
            else:
                cur.execute(
                    f'UPDATE source_videos SET transcript_path=%s, {transcript_column}, '
                    'transcript_text=%s WHERE youtube_video_id=%s',
                    (transcript_path, transcript_json, transcript_text, video_id),
                )
            if cur.rowcount != 1:
                raise LookupError(f'Vídeo {video_id} não encontrado para salvar a transcrição')

        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise

    try:
        os.replace(temp_path, transcript_path)
        temp_path = None
        _log(f'Transcrição completa salva em disco: {transcript_path}')
    except OSError as exc:
        _log(
            f'Transcrição integral arquivada no banco para {video_id}, '
            f'mas o sidecar não pôde ser atualizado: {exc}'
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as exc:
                _log(f'Arquivo temporário de transcrição não pôde ser removido: {exc}')

    _log(f'Transcrição integral arquivada no banco para {video_id}')

    return transcript_path
