"""
dedup.py — Deduplicação de vídeos via Redis com fallback para MySQL.

Exporta:
  - is_seen(video_id, redis_client, db_conn) -> bool
  - mark_failed_redis(video_id, redis_client)

Lógica:
  1. Tenta setar chave no Redis com NX (not exists) e TTL de 30 dias
  2. Se Redis retorna None → chave já existia → vídeo visto → True
  3. Se Redis levanta RedisError → fallback para MySQL
  4. MySQL: SELECT id WHERE youtube_video_id = %s → True se existe, False se não
"""
import redis
from datetime import datetime


REDIS_TTL = 30 * 24 * 3600  # 30 dias em segundos


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [DEDUP] {msg}')


def is_seen(video_id: str, redis_client, db_conn) -> bool:
    """Verifica se o vídeo já foi processado anteriormente.

    Consulta o Redis primeiro. Em caso de falha do Redis, faz fallback para MySQL.

    Args:
        video_id: ID do vídeo YouTube (11 caracteres)
        redis_client: instância de redis.Redis ativa
        db_conn: conexão pymysql ativa

    Returns:
        True se o vídeo já foi visto antes, False se é novo
    """
    key = f'video:{video_id}'

    try:
        result = redis_client.set(key, 1, ex=REDIS_TTL, nx=True)
        if result is None:
            # set() com NX retorna None se a chave já existia
            _log(f'Redis HIT: {video_id} já visto')
            return True
        # set() retornou True (truthy): chave foi criada agora → vídeo potencialmente novo
        # Mas ainda precisamos checar se está no MySQL (caso Redis tenha sido limpo)
        # Conforme behavior: redis miss vai para MySQL fallback
    except redis.RedisError as exc:
        _log(f'Redis ERROR: {exc} — fazendo fallback para MySQL')

    # Fallback MySQL: consultar se vídeo já existe na tabela source_videos
    with db_conn.cursor() as cur:
        cur.execute(
            'SELECT id FROM source_videos WHERE youtube_video_id = %s',
            (video_id,)
        )
        row = cur.fetchone()

    if row is not None:
        _log(f'MySQL HIT: {video_id} encontrado no banco')
        return True

    _log(f'MISS: {video_id} é um vídeo novo')
    return False


def mark_failed_redis(video_id: str, redis_client) -> None:
    """Remove a chave do vídeo do Redis quando o download falha.

    Isso permite que o vídeo seja detectado novamente em polls futuros
    e uma nova tentativa de download seja feita.

    Args:
        video_id: ID do vídeo YouTube
        redis_client: instância de redis.Redis ativa
    """
    key = f'video:{video_id}'
    try:
        redis_client.delete(key)
        _log(f'Chave Redis removida para retry: {key}')
    except redis.RedisError as exc:
        _log(f'AVISO: falha ao remover chave Redis {key}: {exc}')
