"""
video_processor.py — Corte, legendas, thumbnail e processamento de clips.

Exporta:
  - cut_clip(source_path, start_time, end_time, output_path) -> str
  - generate_srt(transcript, start_time, end_time, srt_path) -> str
  - burn_subtitles(input_clip_path, srt_path, output_path) -> str
  - extract_thumbnail(clip_path, thumbnail_path, at_seconds=None) -> str
  - process_clip(conn, clip_id, anthropic_client=None) -> bool

Convenções:
  - FFmpeg é chamado via subprocess.run(check=True, capture_output=True)
  - Diretórios são constantes patcháveis em testes
  - conn: quem chama é responsável por fechar
"""
import subprocess
from datetime import datetime

from src.metadata_generator import generate_metadata, update_clip_metadata


VIDEOS_DIR = '/app/videos'
CLIPS_DIR = '/app/clips'
THUMBNAILS_DIR = '/app/thumbnails'


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [VID] {msg}')


def cut_clip(source_path: str, start_time: float, end_time: float, output_path: str) -> str:
    """Corta um trecho do vídeo fonte e converte para 1080x1920."""
    raise NotImplementedError


def generate_srt(transcript: dict, start_time: float, end_time: float, srt_path: str) -> str:
    """Gera arquivo SRT relativo ao início do clip a partir dos segmentos Whisper."""
    raise NotImplementedError


def burn_subtitles(input_clip_path: str, srt_path: str, output_path: str) -> str:
    """Queima legendas SRT no clip usando FFmpeg."""
    raise NotImplementedError


def extract_thumbnail(clip_path: str, thumbnail_path: str, at_seconds: float = None) -> str:
    """Extrai um frame do clip como thumbnail JPG."""
    raise NotImplementedError


def process_clip(conn, clip_id: int, anthropic_client=None) -> bool:
    """Processa um registro de generated_clips com status pending_cut."""
    raise NotImplementedError
