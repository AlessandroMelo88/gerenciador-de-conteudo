"""
selector.py — Seleção de momentos via Claude Haiku e inserção em generated_clips.

Exporta:
  - select_moments(transcript, anthropic_client=None) -> list[dict]
  - insert_selected_moments(conn, source_video_id, video_id, moments) -> int

Convenções:
  - anthropic_client=None cria cliente de produção; injetado em testes
  - conn: quem chama é responsável por fechar
  - Score >= 7: insere em generated_clips com status 'pending_cut'
  - Score < 7: loga e descarta (não persiste)
"""
from datetime import datetime


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [AI] {msg}')


def select_moments(transcript: dict, anthropic_client=None) -> list[dict]:
    """Analisa transcrição com Claude Haiku e retorna momentos selecionados.

    Args:
        transcript: dict com {'video_id', 'text', 'segments'} — output de transcribe_video()
        anthropic_client: cliente Anthropic (None = produção, injetado = testes)

    Returns:
        Lista de dicts com {'start_time', 'end_time', 'score', 'reason'}, máx 3, sem overlap
    """
    raise NotImplementedError


def insert_selected_moments(conn, source_video_id: int, video_id: str, moments: list[dict]) -> int:
    """Filtra e insere momentos com score >= 7 em generated_clips.

    Args:
        conn: conexão pymysql ativa (quem chama é responsável por fechar)
        source_video_id: FK INT para source_videos.id
        video_id: youtube_video_id (para logging)
        moments: lista de dicts com {'start_time', 'end_time', 'score', 'reason'}

    Returns:
        Número de momentos inseridos (score >= 7)
    """
    raise NotImplementedError
