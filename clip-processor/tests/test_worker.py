"""Contratos do entrypoint de workers por etapa."""

from unittest.mock import MagicMock, patch

import pytest

import src.worker as worker


@pytest.mark.parametrize(
    ('stage', 'target'),
    [
        ('poll', 'poll_sources_only'),
        ('download', '_download_pending_videos'),
        ('ai', 'process_downloaded_videos'),
        ('render', 'process_pending_clips'),
        ('publish', 'publish_pending_clips'),
    ],
)
def test_run_stage_dispatches_to_only_the_selected_stage(stage, target, monkeypatch):
    monkeypatch.setenv('PIPELINE_ENABLED', 'true')
    conn = MagicMock()
    redis_client = MagicMock()
    calls = []

    with (
        patch('src.worker.get_db_connection', return_value=conn),
        patch('src.worker._redis_client', return_value=redis_client),
        patch('src.worker._acquire_stage_lock', return_value=('key', 'token')),
        patch('src.worker._release_stage_lock'),
        patch('src.worker.poll_sources_only') as poll,
        patch('src.worker._download_pending_videos') as download,
        patch('src.worker.process_downloaded_videos') as ai,
        patch('src.worker.process_pending_clips') as render,
        patch('src.worker.publish_pending_clips', return_value=0) as publish,
    ):
        worker.run_stage_once(stage)
        calls = [mock for mock in (poll, download, ai, render, publish) if mock.called]

    assert len(calls) == 1
    assert calls[0]._mock_name == target
    if stage == 'poll':
        poll.assert_called_once_with(db_conn=conn, redis_client=redis_client)
    elif stage == 'download':
        download.assert_called_once_with(conn)
    elif stage == 'ai':
        ai.assert_called_once_with(conn)
    elif stage == 'render':
        render.assert_called_once_with(conn)
    else:
        publish.assert_called_once_with(conn, redis_client)
    conn.close.assert_called_once()


def test_maintenance_recovers_and_runs_ttl(monkeypatch):
    conn = MagicMock()
    redis_client = MagicMock()
    monkeypatch.setenv('PIPELINE_ENABLED', 'true')

    with (
        patch('src.worker.get_db_connection', return_value=conn),
        patch('src.worker._redis_client', return_value=redis_client),
        patch('src.worker._acquire_stage_lock', return_value=('key', 'token')),
        patch('src.worker._release_stage_lock'),
        patch('src.worker.recover_stuck_downloads') as downloads,
        patch('src.worker.recover_stuck_transcribing') as transcribing,
        patch('src.worker.recover_stuck_selecting') as selecting,
        patch('src.worker.recover_stuck_publishing') as publishing,
        patch('src.worker.run_ttl_once') as ttl,
    ):
        worker.run_stage_once('maintenance')

    downloads.assert_called_once_with(conn)
    transcribing.assert_called_once_with(conn)
    selecting.assert_called_once_with(conn)
    publishing.assert_called_once_with(conn)
    ttl.assert_called_once_with(conn=conn, redis_client=redis_client)


def test_disabled_pipeline_does_not_open_connections(monkeypatch):
    monkeypatch.setenv('PIPELINE_ENABLED', 'false')
    with patch('src.worker.get_db_connection') as get_db:
        worker.run_stage_once('render')
    get_db.assert_not_called()


def test_redis_lock_release_uses_owner_token():
    client = MagicMock()

    worker._release_stage_lock(client, ('lock:pipeline_stage:ai', 'token'))

    client.eval.assert_called_once()
    assert client.eval.call_args.args[2:] == ('lock:pipeline_stage:ai', 'token')
