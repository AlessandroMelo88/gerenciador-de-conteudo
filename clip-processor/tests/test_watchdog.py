"""
test_watchdog.py — Testes unitários para o módulo watchdog.py (monitoramento e auto-cura).
"""
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

from src.watchdog import (
    check_disk_space,
    check_ghost_clips,
    check_download_window_health,
    check_approval_queue_activity,
    check_youtube_tokens,
    run_watchdog_cycle,
)

SAO_PAULO_TZ = ZoneInfo('America/Sao_Paulo')


class TestCheckDiskSpace:
    def test_disk_space_healthy(self):
        # 100 GB total, 50 GB used, 50 GB free (50% used)
        with patch('shutil.disk_usage', return_value=(100 * 1024**3, 50 * 1024**3, 50 * 1024**3)):
            result = check_disk_space('/dummy')
            assert result is None

    def test_disk_space_low_free(self):
        # 100 GB total, 97 GB used, 3 GB free (3 GB < 5 GB)
        with patch('shutil.disk_usage', return_value=(100 * 1024**3, 97 * 1024**3, 3 * 1024**3)):
            result = check_disk_space('/dummy')
            assert result is not None
            assert result['level'] == 'warning'
            assert result['free_gb'] == 3.0
            assert result['used_percent'] == 97.0


class TestCheckGhostClips:
    def test_no_ghost_clips(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchall.return_value = []

        with patch('src.watchdog.notify') as mock_notify:
            curated = check_ghost_clips(mock_db_conn)
            assert curated == 0
            assert mock_notify.call_count == 0

    def test_ghost_clip_auto_healed(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchall.return_value = [
            {'id': 42, 'source_video_id': 10, 'clip_path': '/app/videos/clip_42.mp4', 'status': 'approved', 'title': 'Ghost Clip'},
        ]
        # Simula que o vídeo fonte não tem outros clipes pendentes
        cursor.fetchone.return_value = {'c': 0}

        with patch('os.path.exists', return_value=False), \
             patch('src.watchdog.notify') as mock_notify:
            curated = check_ghost_clips(mock_db_conn)
            assert curated == 1
            assert mock_notify.call_count == 1
            mock_db_conn.commit.assert_called()

            # Verifica que foram executadas queries de UPDATE para o clipe e o vídeo fonte
            executed_sqls = [str(call[0][0]) for call in cursor.execute.call_args_list]
            assert any("UPDATE generated_clips SET status = 'failed'" in sql for sql in executed_sqls)
            assert any("UPDATE source_videos SET status = 'published'" in sql for sql in executed_sqls)


class TestCheckDownloadWindowHealth:
    def test_window_healthy_when_slots_available(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchone.return_value = {'occupied': 3}

        with patch('src.watchdog.notify') as mock_notify:
            healthy = check_download_window_health(mock_db_conn)
            assert healthy is True
            assert mock_notify.call_count == 0

    def test_window_deadlock_detected(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        # 1st query: 7 slots ocupados; 2nd query: 0 vídeos ativos recentes
        cursor.fetchone.side_effect = [
            {'occupied': 7},
            {'active_recent': 0},
        ]

        with patch('src.watchdog.notify') as mock_notify:
            healthy = check_download_window_health(mock_db_conn)
            assert healthy is False
            assert mock_notify.call_count == 1
            args, kwargs = mock_notify.call_args
            assert args[0] == 'watchdog_alert'
            assert args[1]['type'] == 'download_window_deadlock'

    def test_window_full_but_active(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        # 1st query: 7 slots ocupados; 2nd query: 2 vídeos ativos recentes
        cursor.fetchone.side_effect = [
            {'occupied': 7},
            {'active_recent': 2},
        ]

        with patch('src.watchdog.notify') as mock_notify:
            healthy = check_download_window_health(mock_db_conn)
            assert healthy is True
            assert mock_notify.call_count == 0


class TestCheckApprovalQueueActivity:
    def test_approval_queue_idle_in_daytime(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchone.side_effect = [
            {'pending_count': 0},
            {'created_recent': 0},
        ]

        daytime = datetime(2026, 9, 8, 14, 0, 0, tzinfo=SAO_PAULO_TZ)
        with patch('src.watchdog.datetime') as mock_dt, \
             patch('src.watchdog.notify') as mock_notify:
            mock_dt.now.return_value = daytime
            check_approval_queue_activity(mock_db_conn)
            assert mock_notify.call_count == 1

    def test_approval_queue_night_skipped(self, mock_db_conn):
        nighttime = datetime(2026, 9, 8, 3, 0, 0, tzinfo=SAO_PAULO_TZ)
        with patch('src.watchdog.datetime') as mock_dt, \
             patch('src.watchdog.notify') as mock_notify:
            mock_dt.now.return_value = nighttime
            check_approval_queue_activity(mock_db_conn)
            assert mock_notify.call_count == 0


class TestCheckYouTubeTokens:
    def test_token_missing_triggers_warning(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchall.return_value = [
            {'id': 1, 'title': 'Futebol em Cortes', 'slug': 'futebol-em-cortes', 'active': 1},
        ]

        with patch('os.path.exists', return_value=False), \
             patch('src.watchdog.notify') as mock_notify:
            warnings = check_youtube_tokens(mock_db_conn, token_dir='/tmp/tokens')
            assert len(warnings) == 1
            assert 'futebol-em-cortes' in warnings[0]
            assert mock_notify.call_count == 1

    def test_token_present_no_warning(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchall.return_value = [
            {'id': 1, 'title': 'Futebol em Cortes', 'slug': 'futebol-em-cortes', 'active': 1},
        ]

        with patch('os.path.exists', return_value=True), \
             patch('src.watchdog.notify') as mock_notify:
            warnings = check_youtube_tokens(mock_db_conn, token_dir='/tmp/tokens')
            assert len(warnings) == 0
            assert mock_notify.call_count == 0


class TestRunWatchdogCycle:
    def test_run_watchdog_cycle_executes_all(self, mock_db_conn):
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = {'occupied': 0}

        with patch('src.watchdog.check_disk_space', return_value=None), \
             patch('src.watchdog.notify'):
            summary = run_watchdog_cycle(mock_db_conn)
            assert 'timestamp' in summary
            assert summary['ghost_clips_healed'] == 0
            assert summary['window_healthy'] is True
