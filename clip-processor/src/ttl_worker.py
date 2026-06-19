"""
ttl_worker.py — Worker APScheduler que expira clips pending após TTL.

Stub Phase 6 (Plan 06-01). Implementação real em Plan 06-05.

- Após TTL_HOURS (48h default): marca clips pending como 'rejected' (auto-expiry).
- Após WARN_HOURS (24h default): notifica via n8n webhook (Telegram) que clipe está
  prestes a expirar. Usa Redis SET NX para garantir warn único por clipe.

Exporta:
  - TTL_HOURS, WARN_HOURS, N8N_NOTIFY_URL (constantes module-level)
  - run_ttl_once(conn=None, redis_client=None) -> dict
"""
import os

TTL_HOURS = int(os.getenv('CLIP_PENDING_TTL_HOURS', '48'))
WARN_HOURS = int(os.getenv('CLIP_PENDING_WARN_HOURS', '24'))
N8N_NOTIFY_URL = os.getenv('N8N_NOTIFY_URL', 'http://n8n:5678/webhook/notify')


def run_ttl_once(conn=None, redis_client=None) -> dict:
    """Executa uma passada do TTL worker. Retorna métricas {expired, warned, errors}."""
    raise NotImplementedError("Phase 6 — implementar em Plan 05")
