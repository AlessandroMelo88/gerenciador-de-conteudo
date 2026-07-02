"""
quota_manager.py — Limite diario e janela de horario para uploads YouTube.

Exporta:
  - QuotaManager: guarda contagem diaria no Redis e valida janela 19h-22h.
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


SAO_PAULO_TZ = ZoneInfo('America/Sao_Paulo')
DEFAULT_MAX_UPLOADS_PER_DAY = 2
ABSOLUTE_MAX_UPLOADS_PER_DAY = 6
UPLOAD_WINDOW_START_HOUR = 19
UPLOAD_WINDOW_END_HOUR = 22
UPLOAD_WINDOW_START = UPLOAD_WINDOW_START_HOUR
UPLOAD_WINDOW_END = UPLOAD_WINDOW_END_HOUR


class QuotaManager:
    """Controla uploads diarios do YouTube por data local de Sao_Paulo."""

    def __init__(self, redis_client, max_uploads_per_day: int | None = None, channel_id: str | None = None):
        self.redis_client = redis_client
        self.max_uploads_per_day = self._resolve_limit(max_uploads_per_day)
        self._max = self.max_uploads_per_day
        self.channel_id = channel_id

    def can_upload(self, now: datetime | None = None) -> bool:
        """Retorna True se horario e quota permitirem upload."""
        now = self._local_now(now)
        if not self._is_upload_window(now):
            return False

        current_count = int(self.redis_client.get(self._key(now)) or 0)
        return current_count < self.max_uploads_per_day

    def record_upload(self, now: datetime | None = None) -> int:
        """Incrementa contador diario e garante TTL ate a proxima meia-noite."""
        now = self._local_now(now)
        key = self._key(now)
        new_count = int(self.redis_client.incr(key))
        if new_count == 1:
            ttl = self._seconds_until_next_midnight(now)
            self.redis_client.expire(key, ttl)
        return new_count

    def _resolve_limit(self, value: int | None) -> int:
        if value is None:
            value = int(os.environ.get('MAX_UPLOADS_PER_DAY', DEFAULT_MAX_UPLOADS_PER_DAY))
        return max(0, min(int(value), ABSOLUTE_MAX_UPLOADS_PER_DAY))

    def _local_now(self, now: datetime | None) -> datetime:
        if now is None:
            return datetime.now(SAO_PAULO_TZ)
        if now.tzinfo is None:
            return now.replace(tzinfo=SAO_PAULO_TZ)
        return now.astimezone(SAO_PAULO_TZ)

    def _is_upload_window(self, now: datetime) -> bool:
        if os.environ.get('UPLOAD_WINDOW_BYPASS', 'false').lower() == 'true':
            return True
        return UPLOAD_WINDOW_START_HOUR <= now.hour < UPLOAD_WINDOW_END_HOUR

    def _key(self, now: datetime) -> str:
        date_str = now.strftime('%Y-%m-%d')
        if self.channel_id:
            return f'youtube_uploads:{self.channel_id}:{date_str}'
        return f'youtube_uploads:{date_str}'

    def _seconds_until_next_midnight(self, now: datetime) -> int:
        next_day = (now + timedelta(days=1)).date()
        midnight = datetime.combine(next_day, datetime.min.time(), tzinfo=SAO_PAULO_TZ)
        return max(1, int((midnight - now).total_seconds()))
