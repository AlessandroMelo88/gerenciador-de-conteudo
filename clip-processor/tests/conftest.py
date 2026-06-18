"""
Fixtures compartilhadas para todos os testes do clip-processor.
Fornece: mock_redis, mock_db_conn, sample_rss_xml, sample_video_id
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_redis():
    """MagicMock simulando redis.Redis.

    - .set() retorna True por padrão (NX success — chave não existia)
    - .get() retorna None por padrão (chave não encontrada)
    - .delete() retorna 1 por padrão
    """
    client = MagicMock()
    client.set.return_value = True
    client.get.return_value = None
    client.delete.return_value = 1
    return client


@pytest.fixture
def mock_db_conn():
    """MagicMock simulando conexão pymysql com suporte a context manager em cursor().

    Uso:
        with conn.cursor() as cur:
            cur.execute(...)
            cur.fetchone()
    """
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    cursor.execute.return_value = None
    cursor.fetchall.return_value = []
    # Suporta: with conn.cursor() as cur:
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    # Também suporta: cur = conn.cursor(); cur.execute(...)
    conn.cursor.return_value = MagicMock(
        __enter__=MagicMock(return_value=cursor),
        __exit__=MagicMock(return_value=False),
        fetchone=cursor.fetchone,
        execute=cursor.execute,
        fetchall=cursor.fetchall,
    )
    return conn


@pytest.fixture
def sample_rss_xml():
    """Feed RSS Atom do YouTube com 2 entradas válidas.

    VideoIds: 'abc123def456' e 'xyz789uvw012'
    """
    return """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <title>Canal de Futebol</title>
  <entry>
    <yt:videoId>abc123def456</yt:videoId>
    <title>Gol incrível do Vini Jr</title>
    <published>2026-06-18T10:00:00+00:00</published>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123def456"/>
  </entry>
  <entry>
    <yt:videoId>xyz789uvw012</yt:videoId>
    <title>Pênalti polêmico na Champions</title>
    <published>2026-06-17T15:30:00+00:00</published>
    <link rel="alternate" href="https://www.youtube.com/watch?v=xyz789uvw012"/>
  </entry>
</feed>"""


@pytest.fixture
def sample_video_id():
    """ID de vídeo YouTube válido (11 caracteres)."""
    return 'dQw4w9WgXcQ'
