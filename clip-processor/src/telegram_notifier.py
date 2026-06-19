"""
telegram_notifier.py — Cliente HTTP que publica eventos do pipeline para o n8n.

Decisão (Phase 6): o clip-processor NÃO conhece TELEGRAM_BOT_TOKEN. Ele faz POST
para um webhook interno do n8n (rede docker) que centraliza credencial e
formatação das mensagens. O n8n encaminha para o Telegram do operador.

Eventos suportados (event_type):
  - 'clip_ready'           — clipe cortado e aguardando aprovação
  - 'clip_warn_expiry'     — clipe entrou em janela de aviso (WARN_HOURS)
  - 'clip_expired'         — clipe expirou (TTL_HOURS) e foi auto-rejeitado
  - 'upload_published'     — upload concluído com sucesso
  - 'pipeline_failure'     — erro crítico em qualquer etapa do pipeline

Comportamento best-effort: nunca propaga exceções (não derruba o pipeline por
um problema de rede no notificador).

Exporta:
  - N8N_NOTIFY_URL (constante module-level)
  - notify(event_type, payload, timeout=5.0) -> bool
"""
import os

import requests


N8N_NOTIFY_URL = os.getenv('N8N_NOTIFY_URL', 'http://n8n:5678/webhook/notify')


def notify(event_type: str, payload: dict, timeout: float = 5.0) -> bool:
    """POST para N8N_NOTIFY_URL com {event, payload}. Retorna True em 2xx, False em erro.

    Best-effort: erros de rede/HTTP são logados em stderr mas NUNCA propagados.
    """
    try:
        resp = requests.post(
            N8N_NOTIFY_URL,
            json={'event': event_type, 'payload': payload},
            timeout=timeout,
        )
        if resp.status_code >= 400:
            print(f'[NOTIFY] warn: n8n retornou HTTP {resp.status_code} para {event_type}')
            return False
        return True
    except requests.RequestException as exc:
        print(f'[NOTIFY] warn: falha ao notificar {event_type}: {exc}')
        return False
