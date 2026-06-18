"""
rss_poller.py — Monitor de feeds RSS de canais YouTube e inserção de vídeos novos.

Exporta:
  - poll_all_channels(db_conn=None, redis_client=None)

Comportamento:
  - Busca canais ativos do MySQL
  - Para cada canal, faz GET no rss_url e parseia com feedparser
  - Para cada entrada: extrai video_id, verifica deduplicação, insere se novo
  - Resiliência por canal: falha em um canal não aborta os demais
  - Nova conexão MySQL por chamada (evita timeout de 6h) — exceto quando db_conn passado (testes)
"""
import os
import re
import requests
import feedparser
import redis
from datetime import datetime

from src.db import get_db_connection, insert_video
from src.dedup import is_seen


REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [ACQU] {msg}')


def _extract_video_id(entry) -> str | None:
    """Extrai o video_id de uma entrada de feed RSS.

    Tenta yt_videoid primeiro (namespace YouTube), com fallback para regex no link.

    Args:
        entry: entrada do feedparser

    Returns:
        video_id (11 chars) ou None se não encontrado
    """
    video_id = entry.get('yt_videoid')
    if video_id:
        return video_id

    # Fallback: extrair da URL do link
    link = entry.get('link', '')
    match = re.search(r'v=([A-Za-z0-9_-]{11})', link)
    if match:
        return match.group(1)

    return None


def poll_all_channels(db_conn=None, redis_client=None) -> None:
    """Monitora feeds RSS de todos os canais ativos e insere vídeos novos.

    Args:
        db_conn: conexão pymysql (opcional — se None, cria nova conexão para produção)
        redis_client: cliente Redis (opcional — se None, cria nova conexão para produção)
    """
    # Gerenciar conexões: nova por chamada em produção, injetada em testes
    _own_db = db_conn is None
    _own_redis = redis_client is None

    if _own_db:
        db_conn = get_db_connection()

    if _own_redis:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
        )

    try:
        # Buscar canais ativos
        with db_conn.cursor() as cur:
            cur.execute('SELECT id, channel_name, rss_url FROM source_channels WHERE active = TRUE')
            channels = cur.fetchall()

        total_new = 0

        for channel in channels:
            channel_id = channel['id']
            channel_name = channel['channel_name']
            rss_url = channel['rss_url']

            try:
                # Buscar feed RSS via HTTP e parsear com feedparser
                response = requests.get(rss_url, timeout=30)
                if response.status_code != 200:
                    _log(f'AVISO: canal {channel_name} retornou HTTP {response.status_code}')
                    continue

                feed = feedparser.parse(response.text)
                entries = feed.entries if hasattr(feed, 'entries') else []

                _log(f'Canal {channel_name}: {len(entries)} entradas no feed')

                for entry in entries:
                    video_id = _extract_video_id(entry)

                    if video_id is None:
                        _log(f'AVISO: entrada sem video_id no canal {channel_name} — pulando')
                        continue

                    if is_seen(video_id, redis_client, db_conn):
                        continue

                    # Vídeo novo — extrair metadados e inserir
                    title = entry.get('title', video_id)
                    published_at = entry.get('published', None)

                    insert_video(db_conn, video_id, channel_id, title, published_at)
                    _log(f'Novo vídeo detectado: {video_id} — {title}')
                    total_new += 1

            except Exception as exc:
                _log(f'ERRO ao processar canal {channel_name}: {exc}')
                continue

        _log(f'Poll concluído: {total_new} vídeo(s) novo(s) inserido(s)')

    finally:
        if _own_db:
            db_conn.close()
