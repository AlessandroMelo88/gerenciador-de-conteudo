"""
processar.py — Ingestão manual de vídeo YouTube via comando /processar do Telegram.

Implementação Phase 6 (Plan 06-04). Não bypassa o pipeline normal — apenas
insere o vídeo em `source_videos` com `status='pending'`; o daemon APScheduler
(Phase 2) cuida do resto (download → transcribe → select → cut → publishing).

Uso CLI:
    python -m src.processar <youtube_url>

Chamado pelo n8n via:
    docker exec clip-processor python -m src.processar <url>

Exporta:
  - YOUTUBE_URL_RE: regex que extrai videoId de URLs do YouTube
  - parse_video_id(url) -> Optional[str]
  - fetch_metadata(video_id) -> dict
  - upsert_source_video(conn, meta) -> Tuple[str, bool]
  - main(url) -> int
"""
import re
import sys
from datetime import datetime
from typing import Optional, Tuple

import yt_dlp

from src.db import get_db_connection


YOUTUBE_URL_RE = re.compile(
    r'(?:youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|embed\/|v\/)|youtu\.be\/)'
    r'(?P<id>[A-Za-z0-9_-]{11})'
)


def parse_video_id(url: str) -> Optional[str]:
    """Extrai videoId de 11 caracteres de uma URL YouTube. None se URL inválida.

    Suporta:
      - https://www.youtube.com/watch?v=ID
      - https://youtu.be/ID
      - https://www.youtube.com/shorts/ID
      - https://www.youtube.com/embed/ID
      - https://www.youtube.com/v/ID
    """
    if not url:
        return None
    match = YOUTUBE_URL_RE.search(url)
    return match.group('id') if match else None


def _normalize_upload_date(upload_date: Optional[str]) -> Optional[str]:
    """Converte 'YYYYMMDD' (formato yt-dlp) para 'YYYY-MM-DD HH:MM:SS' (TIMESTAMP MySQL).

    Retorna None se input vazio/inválido — coluna TIMESTAMP aceita NULL.
    """
    if not upload_date:
        return None
    try:
        dt = datetime.strptime(upload_date, '%Y%m%d')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None


def fetch_metadata(video_id: str) -> dict:
    """Busca title, channel_id, upload_date via yt-dlp metadata-only.

    Não consome quota YouTube Data API — yt-dlp scrapa a página pública.
    Levanta yt_dlp.utils.DownloadError (ou similar) se vídeo é privado/inexistente.

    Returns:
        dict com keys: youtube_video_id, title, channel_id, published_at
    """
    opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    url = f'https://www.youtube.com/watch?v={video_id}'
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        'youtube_video_id': info['id'],
        'title': (info.get('title') or '')[:500],
        'channel_id': info.get('channel_id'),  # 'UC...' externo do YouTube
        'published_at': _normalize_upload_date(info.get('upload_date')),
    }


def upsert_source_video(conn, meta: dict) -> Tuple[str, bool]:
    """Insere ou retorna status atual. Idempotente.

    Estratégia SELECT-then-INSERT (em vez de INSERT...ON DUPLICATE KEY):
    necessário para retornar o status atual ao chamador (mensagem do bot).

    Se o canal de origem não está em `source_channels`, cria pseudo-channel
    com `active=FALSE` (`channel_name='manual:UCxxx'`) — RSS poller não vai
    polar esse canal, mas a FK fica válida.

    Args:
        conn: conexão pymysql ativa (DictCursor)
        meta: dict com youtube_video_id, title, channel_id, published_at

    Returns:
        (status_atual_após_chamada, created_bool)
    """
    with conn.cursor() as cur:
        # 1) Resolver channel_id interno (FK). Cria pseudo-channel se necessário.
        cur.execute(
            'SELECT id FROM source_channels WHERE youtube_channel_id = %s',
            (meta['channel_id'],)
        )
        row = cur.fetchone()
        if row:
            internal_channel_id = row['id']
        else:
            cur.execute(
                'INSERT INTO source_channels '
                '(youtube_channel_id, channel_name, rss_url, active) '
                'VALUES (%s, %s, %s, FALSE)',
                (
                    meta['channel_id'],
                    f'manual:{meta["channel_id"]}',
                    f'https://www.youtube.com/feeds/videos.xml?channel_id={meta["channel_id"]}',
                )
            )
            internal_channel_id = cur.lastrowid

        # 2) Verificar se vídeo já existe
        cur.execute(
            'SELECT status FROM source_videos WHERE youtube_video_id = %s',
            (meta['youtube_video_id'],)
        )
        existing = cur.fetchone()
        if existing:
            conn.commit()  # commit do source_channels novo, caso tenha sido criado
            return (existing['status'], False)

        # 3) Inserir novo vídeo com status='pending' (não bypassa pipeline)
        cur.execute(
            'INSERT INTO source_videos '
            '(youtube_video_id, channel_id, title, published_at, status) '
            'VALUES (%s, %s, %s, %s, %s)',
            (
                meta['youtube_video_id'],
                internal_channel_id,
                meta['title'],
                meta['published_at'],
                'pending',
            )
        )
    conn.commit()
    return ('pending', True)


def main(url: str) -> int:
    """Entrypoint CLI. Exit codes:
      - 0: OK (inserido ou já existia)
      - 2: URL inválida
      - 3: metadata yt-dlp falhou (vídeo privado, inexistente, region-locked)
    """
    video_id = parse_video_id(url)
    if not video_id:
        print(f'ERRO: URL inválida: {url}')
        return 2

    try:
        meta = fetch_metadata(video_id)
    except Exception as exc:  # yt_dlp.utils.DownloadError ou similar
        print(f'ERRO: metadata falhou para {video_id}: {exc}')
        return 3

    conn = get_db_connection()
    try:
        status, created = upsert_source_video(conn, meta)
        verb = 'inserido' if created else 'já existia'
        print(f'OK: {video_id} {verb} — status={status} — título="{meta["title"]}"')
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ''))
