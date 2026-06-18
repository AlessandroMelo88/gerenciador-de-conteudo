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
from datetime import datetime

VIDEOS_DIR = '/app/videos'


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [AI] {msg}')


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
    raise NotImplementedError


def save_transcript(conn, video_id: str, transcript: dict) -> str:
    """Salva JSON de transcrição em disco e atualiza transcript_path no banco.

    Args:
        conn: conexão pymysql ativa (quem chama é responsável por fechar)
        video_id: youtube_video_id
        transcript: dict com {'video_id', 'text', 'segments'}

    Returns:
        Caminho absoluto do arquivo JSON salvo
    """
    raise NotImplementedError
