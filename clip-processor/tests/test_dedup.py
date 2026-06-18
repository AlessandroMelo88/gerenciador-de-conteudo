"""
Testes ACQU-03: deduplicação via Redis com fallback para MySQL.

Módulo alvo: src.dedup
Exports esperados:
  - is_seen(video_id, redis_client, db_conn) -> bool
  - mark_failed_redis(video_id, redis_client)

RED state: imports falham pois src/dedup.py ainda não existe.
"""
from src.dedup import is_seen, mark_failed_redis


class TestIsSeen:

    def test_redis_hit(self, mock_redis, mock_db_conn):
        """redis.set() retorna None (chave existia = NX falhou) → is_seen() retorna True."""
        # NX=True: set retorna None se chave já existe
        mock_redis.set.return_value = None

        result = is_seen('dQw4w9WgXcQ', mock_redis, mock_db_conn)

        assert result is True

    def test_redis_miss_mysql_miss(self, mock_redis, mock_db_conn):
        """redis.set() retorna True (chave nova), MySQL fetchone() retorna None
        → is_seen() retorna False (vídeo realmente novo)."""
        mock_redis.set.return_value = True

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = None

        result = is_seen('dQw4w9WgXcQ', mock_redis, mock_db_conn)

        assert result is False

    def test_redis_fallback(self, mock_redis, mock_db_conn):
        """redis levanta RedisError → is_seen() consulta MySQL como fallback
        e retorna resultado do banco."""
        from redis.exceptions import RedisError

        mock_redis.set.side_effect = RedisError('connection refused')

        # MySQL diz que o vídeo existe
        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {'id': 42, 'youtube_video_id': 'dQw4w9WgXcQ'}

        result = is_seen('dQw4w9WgXcQ', mock_redis, mock_db_conn)

        # Fallback para MySQL: vídeo existe → True
        assert result is True

    def test_redis_fallback_mysql_miss(self, mock_redis, mock_db_conn):
        """redis levanta RedisError, MySQL também não encontra → retorna False."""
        from redis.exceptions import RedisError

        mock_redis.set.side_effect = RedisError('connection refused')

        mock_cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = None

        result = is_seen('newvideo12345', mock_redis, mock_db_conn)

        assert result is False


class TestMarkFailedRedis:

    def test_mark_failed_redis(self, mock_redis):
        """mark_failed_redis() chama redis.delete() com chave correta."""
        video_id = 'dQw4w9WgXcQ'

        mark_failed_redis(video_id, mock_redis)

        # Deve deletar a chave do vídeo do Redis
        mock_redis.delete.assert_called_once()
        call_args = mock_redis.delete.call_args[0][0]
        assert video_id in call_args
