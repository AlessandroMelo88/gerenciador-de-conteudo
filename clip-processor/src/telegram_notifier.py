"""
telegram_notifier.py — Cliente HTTP que publica eventos do pipeline para o Laravel.

Decisão (Phase 9): o clip-processor NÃO conhece TELEGRAM_BOT_TOKEN. Faz POST
para o endpoint interno do Laravel (rede docker) que centraliza credencial e
formatação das mensagens. O Laravel encaminha para o Telegram do operador.

O header Host é obrigatório para o nginx rotear corretamente para
canaldecortes.local (Pitfall 3 do Research: sem Host → nginx serve default_server).

Eventos suportados (event_type):
  - 'clip_ttl_warning'   — clipe entrou em janela de aviso (WARN_HOURS)
  - 'upload_published'   — upload concluído com sucesso
  - 'pipeline_failure'   — erro crítico em qualquer etapa do pipeline
  - 'watchdog_alert'     — alerta ou auto-cura de deadlock, clips fantasmas ou fila ociosa
  - 'oauth_warning'      — ausência ou problema em credencial OAuth dos canais destino
  - 'disk_warning'       — volume de armazenamento com pouco espaço livre

Comportamento best-effort: nunca propaga exceções (não derruba o pipeline por
um problema de rede no notificador).

Exporta:
  - LARAVEL_NOTIFY_URL (constante module-level)
  - LARAVEL_HOST_HEADER (constante module-level)
  - notify(event_type, payload, timeout=5.0) -> bool
"""
import os

import requests


LARAVEL_NOTIFY_URL = os.getenv(
    'LARAVEL_NOTIFY_URL',
    'http://nginx/internal/pipeline-event',
)
LARAVEL_HOST_HEADER = os.getenv('LARAVEL_HOST_HEADER', 'canaldecortes.local')
INTERNAL_TOKEN = os.getenv('CLIP_PROCESSOR_INTERNAL_TOKEN', '')


def notify(event_type: str, payload: dict, timeout: float = 5.0) -> bool:
    """POST para LARAVEL_NOTIFY_URL com {event, payload}. Retorna True em 2xx, False em erro.

    Best-effort: erros de rede/HTTP são logados em stderr mas NUNCA propagados.
    """
    try:
        resp = requests.post(
            LARAVEL_NOTIFY_URL,
            json={'event': event_type, 'payload': payload},
            headers={
                'Host': LARAVEL_HOST_HEADER,
                'X-Internal-Token': INTERNAL_TOKEN,
            },
            timeout=timeout,
        )
        if resp.status_code >= 400:
            print(f'[NOTIFY] warn: Laravel retornou HTTP {resp.status_code} para {event_type}')
            return False
        return True
    except requests.RequestException as exc:
        print(f'[NOTIFY] warn: falha ao notificar {event_type}: {exc}')
        return False
