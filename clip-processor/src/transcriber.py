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
import subprocess
from datetime import datetime

VIDEOS_DIR = '/app/videos'


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
            '-b:a', '32k',
            audio_path, '-y',
        ],
        check=True,
        capture_output=True,
    )
    return (audio_path, True)


def transcribe_video(video_id: str, video_path: str, groq_client=None, db_conn=None) -> dict | None:
    """Transcreve um vídeo via Groq Whisper API.

    Args:
        video_id: youtube_video_id do vídeo
        video_path: caminho absoluto do arquivo .mp4 em /app/videos/
        groq_client: cliente Groq (None = produção, injetado = testes)
        db_conn: conexão pymysql (None = não atualiza status; passar conn para atualizar)

    Returns:
        dict com {'video_id', 'text', 'segments'} ou None em caso de falha
    """
    if groq_client is None:
        from groq import Groq
        groq_client = Groq()

    audio_path = None
    should_delete_audio = False

    try:
        # Verificar tamanho do arquivo: >24MB aciona extração de áudio
        if os.path.getsize(video_path) > 24_000_000:
            _log(f'Arquivo {video_id} >24MB — extraindo áudio MP3 via ffmpeg')
            audio_path, should_delete_audio = _prepare_audio(video_path)
            file_to_transcribe = audio_path
        else:
            file_to_transcribe = video_path

        _log(f'Iniciando transcrição Groq Whisper para {video_id}')
        with open(file_to_transcribe, 'rb') as f:
            result = groq_client.audio.transcriptions.create(
                file=f,
                model='whisper-large-v3-turbo',
                response_format='verbose_json',
                timestamp_granularities=['segment'],
                language='pt',
                temperature=0.0,
            )

        segments = [
            {'start': seg.start, 'end': seg.end, 'text': seg.text}
            for seg in result.segments
        ]

        _log(f'Transcrição concluída para {video_id}: {len(segments)} segmentos')
        return {
            'video_id': video_id,
            'text': result.text,
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
