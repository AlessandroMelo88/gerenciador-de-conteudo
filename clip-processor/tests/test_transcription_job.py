"""
test_transcription_job.py — Testes unitários para transcription_job.py (QUICK-1).

Feature "Transcrição Local": worker de background que baixa áudio de uma URL do
YouTube e roda whisper-cpp local, persistindo status/progresso em transcription_jobs
(MySQL). Isolado do pipeline principal — nunca toca source_videos/generated_clips.

Estado inicial: RED — módulo src.transcription_job não existe ainda.
Após implementação: GREEN.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.transcription_job import (
    create_transcription_job,
    update_job,
    process_transcription_job,
    start_transcription_job,
)
from src.internal_api import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr('src.internal_api.INTERNAL_TOKEN', 'test-token-123')
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


class TestCreateTranscriptionJob:

    def test_inserts_pending_job_and_returns_id(self):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.lastrowid = 7

        job_id = create_transcription_job(mock_conn, 'https://youtube.com/watch?v=abc')

        assert job_id == 7
        mock_conn.commit.assert_called()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        assert 'transcription_jobs' in sql
        assert 'pending' in sql or 'pending' in call_args[0][1]


class TestUpdateJob:

    def test_updates_only_passed_fields(self):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        update_job(mock_conn, 5, status='downloading', progress_percent=10)

        mock_conn.commit.assert_called()
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert 'status' in sql
        assert 'progress_percent' in sql
        assert 'srt_path' not in sql
        assert 'error_message' not in sql
        assert 'downloading' in params
        assert 10 in params

    def test_updates_srt_path_and_error_message_when_passed(self):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        update_job(mock_conn, 5, status='done', progress_percent=100, srt_path='/app/videos/transcripts/5.srt')

        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert 'srt_path' in sql
        assert '/app/videos/transcripts/5.srt' in params

        update_job(mock_conn, 6, status='failed', error_message='boom')
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert 'error_message' in sql
        assert 'boom' in params


class TestProcessTranscriptionJob:

    def test_happy_path_updates_status_progression(self):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {'youtube_url': 'https://youtube.com/watch?v=abc'}

        with patch('src.transcription_job.get_db_connection', return_value=mock_conn), \
             patch('src.transcription_job.update_job') as mock_update, \
             patch('src.transcription_job._download_audio', return_value='/app/videos/transcripts/1_audio.wav') as mock_download, \
             patch('src.transcription_job._run_whisper', return_value='/app/videos/transcripts/1.srt') as mock_whisper, \
             patch('os.remove'), \
             patch('os.path.exists', return_value=True):
            process_transcription_job(1)

        mock_download.assert_called_once_with(1, 'https://youtube.com/watch?v=abc')
        mock_whisper.assert_called_once_with(1, '/app/videos/transcripts/1_audio.wav')

        statuses = [call.kwargs.get('status') for call in mock_update.call_args_list]
        assert 'downloading' in statuses
        assert 'transcribing' in statuses
        assert 'done' in statuses

        done_call = [c for c in mock_update.call_args_list if c.kwargs.get('status') == 'done'][0]
        assert done_call.kwargs.get('progress_percent') == 100
        assert done_call.kwargs.get('srt_path') == '/app/videos/transcripts/1.srt'

    def test_error_path_marks_failed_and_does_not_raise(self):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {'youtube_url': 'https://youtube.com/watch?v=abc'}

        with patch('src.transcription_job.get_db_connection', return_value=mock_conn), \
             patch('src.transcription_job.update_job') as mock_update, \
             patch('src.transcription_job._download_audio', side_effect=RuntimeError('yt-dlp failed')), \
             patch('os.remove'), \
             patch('os.path.exists', return_value=True):
            # Não deve propagar exceção — thread de background não pode matar o processo.
            process_transcription_job(1)

        statuses = [call.kwargs.get('status') for call in mock_update.call_args_list]
        assert 'failed' in statuses
        failed_call = [c for c in mock_update.call_args_list if c.kwargs.get('status') == 'failed'][0]
        assert 'yt-dlp failed' in failed_call.kwargs.get('error_message')


class TestStartTranscriptionJob:

    def test_creates_job_and_starts_daemon_thread(self):
        mock_conn = MagicMock()

        with patch('src.transcription_job.get_db_connection', return_value=mock_conn), \
             patch('src.transcription_job.create_transcription_job', return_value=42) as mock_create, \
             patch('src.transcription_job.threading.Thread') as mock_thread_cls:
            mock_thread = MagicMock()
            mock_thread_cls.return_value = mock_thread

            job_id = start_transcription_job('https://youtube.com/watch?v=abc')

        assert job_id == 42
        mock_create.assert_called_once_with(mock_conn, 'https://youtube.com/watch?v=abc')
        mock_thread_cls.assert_called_once()
        _, kwargs = mock_thread_cls.call_args
        assert kwargs['args'] == (42,)
        assert kwargs['daemon'] is True
        mock_thread.start.assert_called_once()
        mock_conn.close.assert_called_once()


# ── Testes para /internal/transcribe ──────────────────────────────────────────


def test_transcribe_requires_auth(client):
    resp = client.post('/internal/transcribe', json={'url': 'https://youtube.com/watch?v=abc'})
    assert resp.status_code == 401


def test_transcribe_returns_job_id(client):
    with patch('src.internal_api.start_transcription_job') as mock_start:
        mock_start.return_value = 42
        resp = client.post(
            '/internal/transcribe',
            json={'url': 'https://youtube.com/watch?v=abc'},
            headers={'X-Internal-Token': 'test-token-123'},
        )
    assert resp.status_code == 200
    assert resp.get_json()['job_id'] == 42
    mock_start.assert_called_once_with('https://youtube.com/watch?v=abc')


def test_transcribe_missing_url_returns_400(client):
    resp = client.post(
        '/internal/transcribe',
        json={},
        headers={'X-Internal-Token': 'test-token-123'},
    )
    assert resp.status_code == 400
