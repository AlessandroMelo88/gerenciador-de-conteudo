"""Worker de TTL para clipes pending (CTRL-05).

- Expira: clipes com status='pending' e created_at < NOW() - INTERVAL TTL_HOURS HOUR → 'rejected'.
- Avisa: clipes na janela [WARN_HOURS, TTL_HOURS) recebem 1 aviso via Laravel/Telegram
  (idempotente via Redis SET NX com TTL=24h).

Rodado periodicamente pelo APScheduler em main.py (IntervalTrigger hours=1).

Exporta:
  - TTL_HOURS, WARN_HOURS (constantes module-level)
  - run_ttl_once(conn=None, redis_client=None) -> dict
"""
import os
from datetime import datetime, timedelta

import redis

from src.db import get_db_connection
from src.telegram_notifier import notify


TTL_HOURS = int(os.getenv('CLIP_PENDING_TTL_HOURS', '48'))
WARN_HOURS = int(os.getenv('CLIP_PENDING_WARN_HOURS', '24'))
WARN_TTL_SECONDS = 24 * 3600  # mesma duração da janela do warn


def run_ttl_once(conn=None, redis_client=None) -> dict:
    """Executa 1 iteração do TTL: expira clipes >TTL_HOURS, avisa clipes WARN_HOURS-TTL_HOURS.

    Args:
        conn: conexão MySQL (DictCursor). Se None, cria nova e fecha ao final.
        redis_client: cliente Redis. Se None, cria a partir das envs REDIS_HOST/REDIS_PORT.

    Returns:
        {'expired': N, 'warned': M} — quantidade de clipes mudados.
    """
    own_db = conn is None
    own_redis = redis_client is None
    if own_db:
        conn = get_db_connection()
    if own_redis:
        redis_client = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'redis'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            decode_responses=True,
        )

    try:
        # Cortes calculados em Python: `NOW() - INTERVAL n HOUR` é sintaxe só do
        # MySQL e quebra no PostgreSQL (mesmo padrão de watchdog._horas_atras).
        agora = datetime.now()
        corte_ttl = agora - timedelta(hours=TTL_HOURS)
        corte_warn = agora - timedelta(hours=WARN_HOURS)

        # 1) Expirar clipes com mais de TTL_HOURS
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE generated_clips SET status='rejected' "
                "WHERE status='pending' AND created_at < %s",
                (corte_ttl,),
            )
            expired_count = cur.rowcount
            # Drain do cursor para liberar o resultset (no-op em UPDATE real;
            # consumido no contrato dos testes — fetchall slot 'expire query').
            try:
                cur.fetchall()
            except Exception:  # noqa: BLE001
                pass
        conn.commit()

        # 2) Listar clipes a ponto de expirar (entre WARN_HOURS e TTL_HOURS)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title FROM generated_clips "
                "WHERE status='pending' "
                "AND created_at < %s "
                "AND created_at > %s",
                (corte_warn, corte_ttl),
            )
            soon_to_expire = cur.fetchall()

        # 3) Enviar warn idempotente (Redis SET NX com TTL = WARN_TTL_SECONDS)
        warned = 0
        for clip in soon_to_expire:
            key = f'clip_warned:{clip["id"]}'
            if redis_client.set(key, '1', nx=True, ex=WARN_TTL_SECONDS):
                sent = notify('clip_ttl_warning', {
                    'clip_id': clip['id'],
                    'title': clip.get('title'),
                    'expires_in_hours': TTL_HOURS - WARN_HOURS,
                })
                if sent:
                    warned += 1
                else:
                    print(f'[TTL] warn POST falhou para clip {clip["id"]}')
                    # NÃO incrementa warned; Redis já marcou — mesmo tradeoff da Phase 6.

        print(f'[TTL] expired={expired_count} warned={warned}')
        return {'expired': expired_count, 'warned': warned}
    finally:
        if own_db:
            conn.close()
