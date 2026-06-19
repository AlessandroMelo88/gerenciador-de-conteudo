"""
Testes para pipeline_runner.py — ciclo completo do pipeline.
"""
import pytest
from unittest.mock import MagicMock, patch, call

from src.pipeline_runner import run_pipeline_once


class TestRunPipelineOnce:
    def test_calls_poll_then_publish(self):
        """Deve chamar poll_all_channels antes de publish_pending_clips."""
        call_order = []

        def fake_poll(**kwargs):
            call_order.append('poll')

        def fake_publish(conn, redis, **kwargs):
            call_order.append('publish')
            return 0

        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels', side_effect=fake_poll), \
             patch('src.pipeline_runner.publish_pending_clips', side_effect=fake_publish), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

        assert call_order == ['poll', 'publish']

    def test_reuses_injected_db_and_redis(self):
        """Conexões injetadas devem ser passadas para os sub-módulos."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels') as mock_poll, \
             patch('src.pipeline_runner.publish_pending_clips') as mock_pub, \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

        # poll_all_channels deve receber a conexão injetada
        mock_poll.assert_called_once_with(db_conn=mock_conn, redis_client=mock_redis)

        # publish_pending_clips deve receber conn e redis
        pub_args = mock_pub.call_args
        assert pub_args[0][0] is mock_conn
        assert pub_args[0][1] is mock_redis

    def test_does_not_close_injected_db_connection(self):
        """Conexão injetada não deve ser fechada pelo runner (responsabilidade do caller)."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner.publish_pending_clips'), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

        mock_conn.close.assert_not_called()

    def test_publish_failure_does_not_propagate(self):
        """Erro em publish_pending_clips não deve propagar — scheduler continua."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()

        with patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner.publish_pending_clips',
                   side_effect=Exception('publish bombed')), \
             patch('src.pipeline_runner.YouTubeUploader'):
            # Não deve levantar exceção
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

    def test_poll_failure_does_not_skip_publish(self):
        """Erro em poll_all_channels não deve impedir tentativa de publicação."""
        call_order = []

        mock_conn = MagicMock()
        mock_redis = MagicMock()

        def fake_poll(**kwargs):
            call_order.append('poll_failed')
            raise Exception('poll bombed')

        def fake_publish(conn, redis, **kwargs):
            call_order.append('publish')
            return 0

        with patch('src.pipeline_runner.poll_all_channels', side_effect=fake_poll), \
             patch('src.pipeline_runner.publish_pending_clips', side_effect=fake_publish), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once(db_conn=mock_conn, redis_client=mock_redis)

        assert 'poll_failed' in call_order
        assert 'publish' in call_order

    def test_creates_own_connection_when_none_injected(self):
        """Sem injeção, deve criar e fechar a própria conexão."""
        mock_conn = MagicMock()
        mock_redis_instance = MagicMock()

        with patch('src.pipeline_runner.get_db_connection', return_value=mock_conn) as mock_get_db, \
             patch('src.pipeline_runner.redis_lib.Redis', return_value=mock_redis_instance), \
             patch('src.pipeline_runner.poll_all_channels'), \
             patch('src.pipeline_runner.publish_pending_clips'), \
             patch('src.pipeline_runner.YouTubeUploader'):
            run_pipeline_once()

        mock_get_db.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_scheduler_compatible_coalesce(self):
        """Importar main.py não deve iniciar o scheduler (coalesce = True verificado via import)."""
        # Verifica que main.py pode ser importado sem iniciar o scheduler
        import importlib
        import src.main as main_module

        job = None
        for j in main_module.scheduler.get_jobs():
            if j.id == 'pipeline_cycle':
                job = j
                break

        assert job is not None, 'Job pipeline_cycle não encontrado no scheduler'
        assert job.coalesce is True, 'coalesce deve ser True'
        assert job.max_instances == 1, 'max_instances deve ser 1'
