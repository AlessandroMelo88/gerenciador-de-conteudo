"""
Testes para telegram_notifier.py — cliente HTTP que dispara eventos para o n8n.

Estado RED até Plan 06-06.
"""
import pytest
from unittest.mock import MagicMock, patch
import requests

from src.telegram_notifier import notify, N8N_NOTIFY_URL


def test_success_event():
    """notify('upload_published', payload): POST para N8N_NOTIFY_URL com event+payload, retorna True em 2xx."""
    payload = {'clip_id': 42, 'youtube_video_id': 'abc123'}

    with patch('src.telegram_notifier.requests.post') as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        result = notify('upload_published', payload)

    assert result is True
    assert mock_post.call_count == 1
    call_kwargs = mock_post.call_args
    # URL deve ser N8N_NOTIFY_URL
    assert call_kwargs.args[0] == N8N_NOTIFY_URL or call_kwargs.kwargs.get('url') == N8N_NOTIFY_URL
    # body contém event e payload
    body = call_kwargs.kwargs.get('json') or {}
    assert body.get('event') == 'upload_published'
    assert body.get('payload') == payload


def test_failure_event():
    """notify('pipeline_failure', payload) captura RequestException e retorna False sem propagar."""
    payload = {'stage': 'cutting', 'error': 'ffmpeg crashed'}

    with patch('src.telegram_notifier.requests.post') as mock_post:
        mock_post.side_effect = requests.RequestException('connection refused')
        result = notify('pipeline_failure', payload)

    assert result is False
