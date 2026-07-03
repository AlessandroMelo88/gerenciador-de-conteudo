"""
Testes para ttl_worker.py — expiração automática de clips pending.

Estado RED até Plan 06-05.
Atualizado em Plan 09-03: ttl_worker.py usa notify() do telegram_notifier
em vez de requests.post direto — testes agora patcham src.ttl_worker.notify.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.ttl_worker import run_ttl_once, TTL_HOURS, WARN_HOURS


class TestExpire:
    def test_expire_marca_rejected_apos_48h(self, mock_db_conn, mock_redis):
        """run_ttl_once: clips pending > TTL_HOURS são marcados rejected via UPDATE."""
        cursor = mock_db_conn.cursor.return_value
        # Primeiro fetchall: clips expirados
        cursor.fetchall.return_value = [
            {'id': 1, 'created_at': '2026-06-17T00:00:00Z'},
        ]

        with patch('src.ttl_worker.notify'):
            run_ttl_once(conn=mock_db_conn, redis_client=mock_redis)

        # Pelo menos um UPDATE com status='rejected' e WHERE created_at + INTERVAL
        update_sqls = [
            str(c).upper() for c in cursor.execute.call_args_list
            if 'UPDATE' in str(c).upper() and 'REJECTED' in str(c).upper()
        ]
        assert len(update_sqls) >= 1
        joined = ' '.join(update_sqls)
        assert 'INTERVAL' in joined and 'HOUR' in joined


class TestWarn:
    def test_warn_envia_notificacao(self, mock_db_conn, mock_redis):
        """run_ttl_once: clips entre WARN_HOURS e TTL_HOURS disparam notify() para Laravel."""
        cursor = mock_db_conn.cursor.return_value
        # Simula 2 clips na janela de aviso
        cursor.fetchall.side_effect = [
            [],  # expire query
            [    # warn query
                {'id': 10, 'title': 'Clip 10', 'created_at': '2026-06-18T00:00:00Z'},
                {'id': 11, 'title': 'Clip 11', 'created_at': '2026-06-18T01:00:00Z'},
            ],
        ]
        # Redis SET NX retorna True (chave não existia antes)
        mock_redis.set.return_value = True

        with patch('src.ttl_worker.notify') as mock_notify:
            mock_notify.return_value = True
            run_ttl_once(conn=mock_db_conn, redis_client=mock_redis)

        assert mock_notify.call_count >= 2

    def test_no_warn_duplicado(self, mock_db_conn, mock_redis):
        """Redis SET NX False (já avisou): NÃO dispara notify() extra."""
        cursor = mock_db_conn.cursor.return_value
        cursor.fetchall.side_effect = [
            [],  # expire query
            [{'id': 10, 'title': 'Clip 10', 'created_at': '2026-06-18T00:00:00Z'}],
        ]
        # Redis SET NX retorna False — já existe
        mock_redis.set.return_value = False

        with patch('src.ttl_worker.notify') as mock_notify:
            mock_notify.return_value = True
            run_ttl_once(conn=mock_db_conn, redis_client=mock_redis)

        assert mock_notify.call_count == 0
