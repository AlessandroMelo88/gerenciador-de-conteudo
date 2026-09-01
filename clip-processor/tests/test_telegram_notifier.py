"""
Testes para telegram_notifier.py — cliente HTTP que dispara eventos para o Laravel.

Decisão Phase 9: telegram_notifier.py passa a chamar LARAVEL_NOTIFY_URL
(http://nginx/internal/pipeline-event com Host: canaldecortes.local)
em vez de N8N_NOTIFY_URL.

Testes test_notifier_uses_laravel_url e test_notifier_sends_host_header estão
em RED até o Plan 09-03 renomear N8N_NOTIFY_URL → LARAVEL_NOTIFY_URL.
"""
import pytest
from unittest.mock import MagicMock, patch
import requests

from src.telegram_notifier import notify


def test_failure_event():
    """notify() captura RequestException e retorna False sem propagar."""
    payload = {'stage': 'cutting', 'error': 'ffmpeg crashed'}
    with patch('src.telegram_notifier.requests.post') as mock_post:
        mock_post.side_effect = requests.RequestException('connection refused')
        result = notify('pipeline_failure', payload)
    assert result is False


def test_http_4xx_returns_false():
    """notify() retorna False quando o endpoint retorna 4xx."""
    with patch('src.telegram_notifier.requests.post') as mock_post:
        mock_post.return_value = MagicMock(status_code=400)
        result = notify('upload_published', {})
    assert result is False


def test_notifier_uses_laravel_url():
    """notify() faz POST para LARAVEL_NOTIFY_URL — RED até Plan 09-03.

    Importa LARAVEL_NOTIFY_URL dentro do teste (padrão Phase 7) para não
    quebrar a coleta de testes se o símbolo ainda não existe no módulo.
    """
    from src.telegram_notifier import LARAVEL_NOTIFY_URL  # existe após Plan 09-03

    payload = {'clip_id': 42, 'youtube_video_id': 'abc123'}
    with patch('src.telegram_notifier.requests.post') as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        result = notify('upload_published', payload)

    assert result is True
    assert mock_post.call_count == 1
    url_used = (
        mock_post.call_args.args[0]
        if mock_post.call_args.args
        else mock_post.call_args.kwargs.get('url', '')
    )
    assert url_used == LARAVEL_NOTIFY_URL, (
        f'Expected LARAVEL_NOTIFY_URL={LARAVEL_NOTIFY_URL!r}, got {url_used!r}'
    )
    body = mock_post.call_args.kwargs.get('json') or {}
    assert body.get('event') == 'upload_published'
    assert body.get('payload') == payload


def test_notifier_sends_host_header():
    """notify() inclui header Host para nginx routing — RED até Plan 09-03."""
    with patch('src.telegram_notifier.requests.post') as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        notify('pipeline_failure', {'stage': 'download', 'error_msg': 'timeout'})

    headers = mock_post.call_args.kwargs.get('headers', {})
    assert 'Host' in headers, (
        'notify() deve enviar header Host para que nginx roteie para canaldecortes.local'
    )
