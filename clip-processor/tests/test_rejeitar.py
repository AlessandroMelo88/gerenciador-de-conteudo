"""
Testes para rejeitar.py — comando /rejeitar do Telegram.

Estado RED até Plan 06-03.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.rejeitar import rejeitar


def test_marca_rejected(mock_db_conn):
    """rejeitar(123): executa UPDATE generated_clips SET status='rejected' WHERE id=123."""
    cursor = mock_db_conn.cursor.return_value
    cursor.fetchone.return_value = {
        'id': 123,
        'status': 'pending',
        'clip_path': '/app/videos/clips/clip_123.mp4',
    }

    with patch('src.rejeitar.db_connect', return_value=mock_db_conn), \
         patch('src.rejeitar.os.path.exists', return_value=False), \
         patch('src.rejeitar.os.remove'):
        rejeitar(123)

    # Pelo menos uma chamada UPDATE com status='rejected' e id=123
    update_calls = [
        c for c in cursor.execute.call_args_list
        if 'UPDATE' in str(c).upper() and 'rejected' in str(c)
    ]
    assert len(update_calls) >= 1
    last_call = update_calls[-1]
    args = last_call.args
    assert 123 in (args[1] if len(args) > 1 else ())


def test_apaga_mp4_mantem_raw(mock_db_conn):
    """rejeitar apaga clip_path mas NÃO toca source_videos.local_path (raw)."""
    cursor = mock_db_conn.cursor.return_value
    cursor.fetchone.return_value = {
        'id': 7,
        'status': 'pending',
        'clip_path': '/app/videos/clips/clip_007.mp4',
        'source_local_path': '/app/videos/raw/video_xyz.mp4',
    }

    with patch('src.rejeitar.db_connect', return_value=mock_db_conn), \
         patch('src.rejeitar.os.path.exists', return_value=True) as mock_exists, \
         patch('src.rejeitar.os.remove') as mock_remove:
        rejeitar(7)

    removed_paths = [c.args[0] for c in mock_remove.call_args_list]
    assert '/app/videos/clips/clip_007.mp4' in removed_paths
    assert '/app/videos/raw/video_xyz.mp4' not in removed_paths


def test_clip_nao_existe(mock_db_conn):
    """rejeitar(999) com fetchone=None retorna 1 e não executa UPDATE."""
    cursor = mock_db_conn.cursor.return_value
    cursor.fetchone.return_value = None

    with patch('src.rejeitar.db_connect', return_value=mock_db_conn):
        result = rejeitar(999)

    assert result == 1
    update_calls = [
        c for c in cursor.execute.call_args_list
        if 'UPDATE' in str(c).upper() and 'rejected' in str(c)
    ]
    assert len(update_calls) == 0
