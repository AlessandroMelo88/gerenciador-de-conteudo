"""
transcriber.py — Transcrição de vídeos via Groq Whisper API.

Exporta:
  - transcribe_video(video_id, video_path, groq_client=None, db_conn=None) -> dict | None
  - save_transcript(conn, video_id, transcript) -> str

Convenções:
  - groq_client=None cria cliente de produção; injetado em testes (padrão do projeto)
  - db_conn=None: save_transcript recebe conn explícito — quem chama fecha a conexão
  - Logging via _log() com tag [AI]
"""
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

VIDEOS_DIR = '/app/videos'

# O Groq recusa uploads perto de 25 MB; a requisição multipart ainda soma overhead, então
# áudio acima de GROQ_SAFE_FILE_BYTES é fatiado em partes de TRANSCRIPTION_CHUNK_SECONDS.
GROQ_SAFE_FILE_BYTES = 20_000_000
TRANSCRIPTION_CHUNK_SECONDS = 900


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [AI] {msg}')


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
            'ffmpeg', '-i', video_path,
            '-vn',
            '-ar', '16000',
            '-ac', '1',
            '-b:a', '16k',
            audio_path, '-y',
        ],
        check=True,
        capture_output=True,
    )
    return (audio_path, True)


def _split_audio(audio_path: str, video_id: str) -> tuple[list[str], str]:
    """Divide áudio grande em partes de TRANSCRIPTION_CHUNK_SECONDS (mono, 16 kbit/s).

    Retorna (caminhos ordenados, diretório temporário) — o chamador remove o diretório.
    Sem isso, um podcast de 2h gerava um MP3 acima do limite do Groq e a transcrição falhava.
    """
    chunks_dir = tempfile.mkdtemp(prefix=f'.{video_id}_chunks-', dir=VIDEOS_DIR)
    try:
        subprocess.run(
            [
                'ffmpeg', '-i', audio_path,
                '-map', '0:a:0',
                '-f', 'segment',
                '-segment_time', str(TRANSCRIPTION_CHUNK_SECONDS),
                '-reset_timestamps', '1',
                '-ar', '16000',
                '-ac', '1',
                '-c:a', 'libmp3lame',
                '-b:a', '16k',
                str(Path(chunks_dir) / 'chunk_%03d.mp3'), '-y',
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
    """Transcreve um vídeo via Groq Whisper API.

    Args:
        video_id: youtube_video_id do vídeo
        video_path: caminho absoluto do arquivo .mp4 em /app/videos/
        groq_client: cliente Groq (None = produção, injetado = testes)
        db_conn: conexão pymysql (None = não atualiza status; passar conn para atualizar)
        prompt: termos de contexto opcionais para o Whisper (nomes próprios, jargão); omitido = sem viés

    Returns:
        dict com {'video_id', 'text', 'segments'} ou None em caso de falha
    """
    if groq_client is None:
        from groq import Groq
        groq_client = Groq()

    audio_path = None
    should_delete_audio = False
    chunks_dir = None

    try:
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
            audio_path
            and file_to_transcribe == audio_path
            and os.path.getsize(audio_path) > GROQ_SAFE_FILE_BYTES
        ):
            transcription_files, chunks_dir = _split_audio(audio_path, video_id)
            _log(
                f'Áudio de {video_id} excede {GROQ_SAFE_FILE_BYTES // 1_000_000}MB — '
                f'dividido em {len(transcription_files)} partes'
            )

        segments = []
        text_parts = []
        for index, transcription_file in enumerate(transcription_files):
            _log(
                f'Iniciando transcrição Groq Whisper para {video_id}'
                + (f' (parte {index + 1}/{len(transcription_files)})' if len(transcription_files) > 1 else '')
            )
            options = {
                'model': 'whisper-large-v3-turbo',
                'response_format': 'verbose_json',
                'timestamp_granularities': ['segment'],
                'language': 'pt',
                'temperature': 0.0,
            }
            if prompt:
                options['prompt'] = prompt
            with open(transcription_file, 'rb') as f:
                result = groq_client.audio.transcriptions.create(file=f, **options)

            # cada parte reinicia o relógio em 0: soma o deslocamento da parte
            offset = index * TRANSCRIPTION_CHUNK_SECONDS if len(transcription_files) > 1 else 0
            segments.extend(
                {'start': _g(seg, 'start') + offset, 'end': _g(seg, 'end') + offset, 'text': _g(seg, 'text')}
                for seg in result.segments
            )
            text_parts.append(result.text)

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
    """Salva JSON de transcrição em disco e atualiza transcript_path no banco.

    Args:
        conn: conexão pymysql ativa (quem chama é responsável por fechar)
        video_id: youtube_video_id
        transcript: dict com {'video_id', 'text', 'segments'}

    Returns:
        Caminho absoluto do arquivo JSON salvo
    """
    transcript_path = os.path.join(VIDEOS_DIR, f'{video_id}_transcript.json')

    with open(transcript_path, 'w', encoding='utf-8') as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)

    _log(f'Transcrição salva em disco: {transcript_path}')

    with conn.cursor() as cur:
        cur.execute(
            'UPDATE source_videos SET transcript_path=%s WHERE youtube_video_id=%s',
            (transcript_path, video_id),
        )

    conn.commit()
    _log(f'transcript_path atualizado no banco para {video_id}')

    return transcript_path
