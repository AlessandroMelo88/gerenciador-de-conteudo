"""
Testes para processar.py — ingestão manual de vídeo YouTube via /processar.

Estado RED até Plan 06-04. Imports no topo: ModuleNotFoundError até stub existir;
após stub, testes falham com NotImplementedError ao invocar as funções.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.processar import (
    YOUTUBE_URL_RE,
    parse_video_id,
    fetch_metadata,
    upsert_source_video,
    main,
)


class TestParseVideoId:
    def test_watch_url(self):
        """URL clássica https://www.youtube.com/watch?v=ID retorna o videoId."""
        assert parse_video_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ') == 'dQw4w9WgXcQ'

    def test_youtu_be(self):
        """URL curta https://youtu.be/ID retorna o videoId."""
        assert parse_video_id('https://youtu.be/dQw4w9WgXcQ') == 'dQw4w9WgXcQ'

    def test_shorts(self):
        """URL de Shorts https://www.youtube.com/shorts/ID retorna o videoId."""
        assert parse_video_id('https://www.youtube.com/shorts/dQw4w9WgXcQ') == 'dQw4w9WgXcQ'

    def test_embed(self):
        """URL de embed https://www.youtube.com/embed/ID retorna o videoId."""
        assert parse_video_id('https://www.youtube.com/embed/dQw4w9WgXcQ') == 'dQw4w9WgXcQ'

    def test_invalid_returns_none(self):
        """URL sem videoId reconhecível retorna None."""
        assert parse_video_id('https://example.com/foo') is None


class TestUpsertSourceVideo:
    def test_status_pending(self, mock_db_conn):
        """Clip novo: INSERT cria registro com status='pending' e retorna (status, created=True)."""
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchone.return_value = None  # não existe ainda
        meta = {
            'youtube_video_id': 'dQw4w9WgXcQ',
            'title': 'Test',
            'channel_id': 'UCxxxx',
            'duration_seconds': 600,
            'published_at': '2026-06-19T12:00:00Z',
        }

        status, created = upsert_source_video(mock_db_conn, meta)

        assert status == 'pending'
        assert created is True

    def test_idempotente(self, mock_db_conn):
        """Clip já existe: retorna (status_atual, created=False) sem alterar."""
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchone.return_value = {'id': 42, 'status': 'downloaded'}
        meta = {
            'youtube_video_id': 'dQw4w9WgXcQ',
            'title': 'Test',
            'channel_id': 'UCxxxx',
            'duration_seconds': 600,
            'published_at': '2026-06-19T12:00:00Z',
        }

        status, created = upsert_source_video(mock_db_conn, meta)

        assert status == 'downloaded'
        assert created is False
