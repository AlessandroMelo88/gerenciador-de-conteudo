"""RED tests for internal_api sidecar (implementação GREEN no Plan 08-07)."""
import os
import pytest
from unittest.mock import patch, MagicMock

from src.internal_api import app, resolve_channel, reject_clip, purge_old_videos


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr('src.internal_api.INTERNAL_TOKEN', 'test-token-123')
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_resolve_channel_requires_auth(client):
    resp = client.post('/internal/resolve-channel', json={'url': 'https://youtube.com/@x'})
    assert resp.status_code == 401


def test_resolve_channel_returns_channel_data(client):
    # This test drives Plan 08-07 GREEN: resolve_channel must return a dict with
    # channel_id, channel_name, channel_handle when yt-dlp succeeds.
    fake_json = '{"id":"UCxxx","channel":"Nome","uploader_id":"@handle"}'
    with patch('src.internal_api.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_json, stderr='')
        resp = client.post(
            '/internal/resolve-channel',
            json={'url': 'https://youtube.com/@handle'},
            headers={'X-Internal-Token': 'test-token-123'},
        )
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body['channel_id'] == 'UCxxx'
    assert body['channel_name'] == 'Nome'
    assert body['channel_handle'] == '@handle'


def test_resolve_channel_returns_422_on_ytdlp_failure(client):
    with patch('src.internal_api.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='not a channel')
        resp = client.post(
            '/internal/resolve-channel',
            json={'url': 'https://youtube.com/@nope'},
            headers={'X-Internal-Token': 'test-token-123'},
        )
    assert resp.status_code == 422
    assert resp.get_json()['error'] == 'yt-dlp failed'


def test_reject_clip_requires_auth(client):
    resp = client.post('/internal/reject-clip', json={'clip_id': 42})
    assert resp.status_code == 401


def test_reject_clip_calls_rejeitar_and_returns_exit_code(client):
    with patch('src.internal_api.rejeitar') as mock_rejeitar:
        mock_rejeitar.return_value = 0
        resp = client.post(
            '/internal/reject-clip',
            json={'clip_id': 42},
            headers={'X-Internal-Token': 'test-token-123'},
        )
    assert resp.status_code == 200
    assert resp.get_json()['exit_code'] == 0
    mock_rejeitar.assert_called_once_with(42)


def test_reject_clip_propagates_exit_code_1(client):
    with patch('src.internal_api.rejeitar') as mock_rejeitar:
        mock_rejeitar.return_value = 1  # clip não existe
        resp = client.post(
            '/internal/reject-clip',
            json={'clip_id': 999},
            headers={'X-Internal-Token': 'test-token-123'},
        )
    assert resp.status_code == 200
    assert resp.get_json()['exit_code'] == 1


# ── Testes para /internal/process-url (Phase 9, BOT-03) ──────────────────────
# RED até Plan 09-03 adicionar o endpoint em internal_api.py.


def test_process_url_requires_auth(client):
    """POST /internal/process-url sem token retorna 401."""
    resp = client.post('/internal/process-url', json={'url': 'https://youtube.com/watch?v=abc'})
    assert resp.status_code == 401


def test_process_url_calls_processar_main_and_returns_exit_code(client):
    """POST /internal/process-url chama processar_main(url) e retorna {'exit_code': N}."""
    with patch('src.internal_api.processar_main') as mock_proc:
        mock_proc.return_value = 0
        resp = client.post(
            '/internal/process-url',
            json={'url': 'https://youtube.com/watch?v=abc'},
            headers={'X-Internal-Token': 'test-token-123'},
        )
    assert resp.status_code == 200
    assert resp.get_json()['exit_code'] == 0
    mock_proc.assert_called_once_with('https://youtube.com/watch?v=abc', fmt='curto')


def test_process_url_passes_format_longo(client):
    """POST /internal/process-url com format='longo' repassa fmt='longo' pro processar_main."""
    with patch('src.internal_api.processar_main') as mock_proc:
        mock_proc.return_value = 0
        resp = client.post(
            '/internal/process-url',
            json={'url': 'https://youtube.com/watch?v=abc', 'format': 'longo'},
            headers={'X-Internal-Token': 'test-token-123'},
        )
    assert resp.status_code == 200
    mock_proc.assert_called_once_with('https://youtube.com/watch?v=abc', fmt='longo')


def test_process_url_missing_url_returns_400(client):
    """POST /internal/process-url sem campo 'url' retorna 400."""
    resp = client.post(
        '/internal/process-url',
        json={},
        headers={'X-Internal-Token': 'test-token-123'},
    )
    assert resp.status_code == 400


# ── Testes para /internal/purge-old-videos ────────────────────────────────────


def test_purge_old_videos_requires_auth(client):
    resp = client.post('/internal/purge-old-videos', json={'before_date': '2026-07-10'})
    assert resp.status_code == 401


def test_purge_old_videos_missing_date_returns_400(client):
    resp = client.post(
        '/internal/purge-old-videos',
        json={},
        headers={'X-Internal-Token': 'test-token-123'},
    )
    assert resp.status_code == 400


def test_purge_old_videos_deletes_rows_and_frees_files(client, mocker):
    """purge_old_videos apaga linhas sem clips e libera arquivo de linhas com clips
    (desde que nenhum clip pending_cut/cutting dependa do bruto), e limpa as chaves
    Redis de deduplicação das linhas apagadas."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.rowcount = 5
    mock_cursor.fetchall.side_effect = [
        [{'youtube_video_id': 'abc123xyz01'}],  # SELECT video_ids antes do DELETE
        [{'id': 42, 'local_path': '/app/videos/abc.mp4'}],  # SELECT rows_with_file
    ]
    mocker.patch('src.internal_api.get_db_connection', return_value=mock_conn)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.getsize', return_value=1024 * 1024)
    mock_remove = mocker.patch('os.remove')
    mock_redis = MagicMock()
    mocker.patch('src.internal_api.redis.Redis', return_value=mock_redis)

    result = purge_old_videos('2026-07-10')

    assert result == {'deleted_rows': 5, 'freed_bytes': 1024 * 1024}
    mock_remove.assert_called_once_with('/app/videos/abc.mp4')
    mock_redis.delete.assert_called_once_with('video:abc123xyz01')


def test_purge_old_videos_route_returns_result(client, mocker):
    mocker.patch('src.internal_api.purge_old_videos', return_value={'deleted_rows': 3, 'freed_bytes': 2048})

    resp = client.post(
        '/internal/purge-old-videos',
        json={'before_date': '2026-07-10'},
        headers={'X-Internal-Token': 'test-token-123'},
    )
    assert resp.status_code == 200
    assert resp.get_json() == {'deleted_rows': 3, 'freed_bytes': 2048}
