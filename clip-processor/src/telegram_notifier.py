"""
telegram_notifier.py — Cliente HTTP que publica eventos do pipeline para o n8n.

Stub Phase 6 (Plan 06-01). Implementação real em Plan 06-06.

O n8n encaminha os eventos para o Telegram do operador (publicação, falhas,
expiração eminente, etc).

Eventos suportados (event_type):
  - 'clip_ready'           — clipe cortado e aguardando aprovação
  - 'clip_warn_expiry'     — clipe entrou em janela de aviso (WARN_HOURS)
  - 'clip_expired'         — clipe expirou (TTL_HOURS) e foi auto-rejeitado
  - 'upload_published'     — upload concluído com sucesso
  - 'pipeline_failure'     — erro em qualquer etapa do pipeline

Exporta:
  - N8N_NOTIFY_URL (constante module-level)
  - notify(event_type, payload, timeout=5.0) -> bool
"""
import os

N8N_NOTIFY_URL = os.getenv('N8N_NOTIFY_URL', 'http://n8n:5678/webhook/notify')


def notify(event_type: str, payload: dict, timeout: float = 5.0) -> bool:
    """POST para N8N_NOTIFY_URL com {event, payload}. Retorna True em 2xx, False em erro."""
    raise NotImplementedError("Phase 6 — implementar em Plan 06")
