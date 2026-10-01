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
# Teto de segurança do total diário (clamp de MAX_UPLOADS_PER_DAY). Sobrescrevível
# por env ABSOLUTE_MAX_UPLOADS_PER_DAY; o padrão 10 só cobre o plano do canal de
# futebol (6 Shorts + 4 longos) — o limite real em produção continua sendo
# MAX_UPLOADS_PER_DAY (padrão 2).
DEFAULT_ABSOLUTE_MAX_UPLOADS_PER_DAY = 10
ABSOLUTE_MAX_UPLOADS_PER_DAY = DEFAULT_ABSOLUTE_MAX_UPLOADS_PER_DAY
DEFAULT_MAX_LONGO_UPLOADS_PER_DAY = 2
UPLOAD_WINDOWS = [
    (12, 14),  # Janela 1: Almoço / Meio-dia (12h às 14h BRT)
    (19, 22),  # Janela 2: Noite / Horário Nobre (19h às 22h BRT)
]
UPLOAD_WINDOW_START_HOUR = 19
UPLOAD_WINDOW_END_HOUR = 22
UPLOAD_WINDOW_START = UPLOAD_WINDOW_START_HOUR
UPLOAD_WINDOW_END = UPLOAD_WINDOW_END_HOUR


class QuotaManager:
    """Controla uploads diarios do YouTube por data local de Sao_Paulo.

    MAX_CURTO_UPLOADS_PER_DAY (env, opcional):
      - teto de uploads 'curto' no dia; sem a env não há teto de curto (só o
        total). Curtos + longos nunca passam de MAX_UPLOADS_PER_DAY.

    MIN_UPLOAD_SPACING_MINUTES (env, opcional, padrão 0 = desligado):
      - intervalo mínimo entre dois uploads do mesmo canal, para não publicar
        em rajada no mesmo ciclo (o publisher roda a cada 20 min).

    MAX_LONGO_UPLOADS_PER_DAY:
      - teto de uploads 'longo' no dia;
      - quando ainda há longo publishable na fila, reserva esses slots na cota
        total (curto só usa total − slots_longo_ainda_não_usados). Sem longo
        na fila, a reserva some e curto pode usar o total.
    """

    def __init__(
        self,
        redis_client,
        max_uploads_per_day: int | None = None,
        channel_id: str | None = None,
        max_longo_per_day: int | None = None,
        max_curto_per_day: int | None = None,
        min_spacing_minutes: int | None = None,
    ):
        self.redis_client = redis_client
        self.max_uploads_per_day = self._resolve_limit(max_uploads_per_day)
        self._max = self.max_uploads_per_day
        self.max_longo_per_day = self._resolve_longo_limit(max_longo_per_day)
        self.max_curto_per_day = self._resolve_curto_limit(max_curto_per_day)
        self.min_spacing_minutes = self._resolve_spacing(min_spacing_minutes)
        self.channel_id = channel_id

    def has_capacity(self, now: datetime | None = None, bypass_window: bool = False) -> bool:
        """Janela + cota total, ignorando reserva por formato.

        Usado para decidir se o ciclo de publicação inteiro deve parar
        (quota total esgotada) versus só pular um clip por causa da reserva
        de formato (outro clip de formato diferente ainda pode publicar).
        """
        now = self._local_now(now)
        if not self._is_upload_window(now, bypass_window=bypass_window):
            return False

        current_count = int(self.redis_client.get(self._key(now)) or 0)
        if current_count >= self.max_uploads_per_day:
            return False
        return not self._within_spacing(now)

    def can_upload(
        self,
        now: datetime | None = None,
        format: str = 'curto',
        *,
        longo_waiting: bool = False,
        bypass_window: bool = False,
    ) -> bool:
        """Retorna True se horario e quota (total + formato/reserva) permitirem upload."""
        now = self._local_now(now)
        if not self.has_capacity(now=now, bypass_window=bypass_window):
            return False

        current_count = int(self.redis_client.get(self._key(now)) or 0)
        longo_count = int(self.redis_client.get(self._format_key(now, 'longo')) or 0)

        if format == 'longo':
            if longo_count >= self.max_longo_per_day:
                return False
            return True

        # Curto: teto próprio (opcional) e, depois, a reserva do longo.
        if self.max_curto_per_day is not None:
            curto_count = max(0, current_count - longo_count)
            if curto_count >= self.max_curto_per_day:
                return False

        # Curto: se há longo publishable, não come os slots reservados pra ele.
        if longo_waiting and self.max_longo_per_day > 0:
            reserved = max(0, self.max_longo_per_day - longo_count)
            curto_ceiling = self.max_uploads_per_day - reserved
            if current_count >= curto_ceiling:
                return False

        return True

    def record_upload(self, now: datetime | None = None, format: str = 'curto') -> int:
        """Incrementa contador diario (total e, se 'longo', o de formato) e garante TTL."""
        now = self._local_now(now)
        key = self._key(now)
        new_count = int(self.redis_client.incr(key))
        if new_count == 1:
            ttl = self._seconds_until_next_midnight(now)
            self.redis_client.expire(key, ttl)

        if format == 'longo':
            longo_key = self._format_key(now, 'longo')
            longo_new_count = int(self.redis_client.incr(longo_key))
            if longo_new_count == 1:
                self.redis_client.expire(longo_key, self._seconds_until_next_midnight(now))

        if self.min_spacing_minutes > 0:
            self.redis_client.set(
                self._last_upload_key(now), str(int(now.timestamp())),
                ex=self._seconds_until_next_midnight(now),
            )

        return new_count

    def _resolve_limit(self, value: int | None) -> int:
        if value is None:
            value = int(os.environ.get('MAX_UPLOADS_PER_DAY', DEFAULT_MAX_UPLOADS_PER_DAY))
        return max(0, min(int(value), self._absolute_max()))

    @staticmethod
    def _absolute_max() -> int:
        raw = os.environ.get('ABSOLUTE_MAX_UPLOADS_PER_DAY', '').strip()
        return int(raw) if raw else ABSOLUTE_MAX_UPLOADS_PER_DAY

    def _resolve_longo_limit(self, value: int | None) -> int:
        if value is None:
            value = int(os.environ.get('MAX_LONGO_UPLOADS_PER_DAY', DEFAULT_MAX_LONGO_UPLOADS_PER_DAY))
        return max(0, min(int(value), self.max_uploads_per_day))

    def _resolve_curto_limit(self, value: int | None) -> int | None:
        """None = sem teto de curto (comportamento anterior)."""
        if value is None:
            raw = os.environ.get('MAX_CURTO_UPLOADS_PER_DAY', '').strip()
            if not raw:
                return None
            value = int(raw)
        return max(0, min(int(value), self.max_uploads_per_day))

    def _resolve_spacing(self, value: int | None) -> int:
        if value is None:
            value = int(os.environ.get('MIN_UPLOAD_SPACING_MINUTES', '0') or 0)
        return max(0, int(value))

    def _within_spacing(self, now: datetime) -> bool:
        if self.min_spacing_minutes <= 0:
            return False
        raw = self.redis_client.get(self._last_upload_key(now))
        try:
            last_ts = int(raw)
        except (TypeError, ValueError):
            return False
        return now.timestamp() - last_ts < self.min_spacing_minutes * 60

    def _local_now(self, now: datetime | None) -> datetime:
        if now is None:
            return datetime.now(SAO_PAULO_TZ)
        if now.tzinfo is None:
            return now.replace(tzinfo=SAO_PAULO_TZ)
        return now.astimezone(SAO_PAULO_TZ)

    def _is_upload_window(self, now: datetime, bypass_window: bool = False) -> bool:
        if bypass_window or os.environ.get('UPLOAD_WINDOW_BYPASS', 'false').lower() == 'true':
            return True
        return any(start <= now.hour < end for start, end in UPLOAD_WINDOWS)

    def _key(self, now: datetime) -> str:
        date_str = now.strftime('%Y-%m-%d')
        if self.channel_id:
            return f'youtube_uploads:{self.channel_id}:{date_str}'
        return f'youtube_uploads:{date_str}'

    def _format_key(self, now: datetime, format: str) -> str:
        return f'{self._key(now)}:{format}'

    def _last_upload_key(self, now: datetime) -> str:
        return f'{self._key(now)}:last_upload_ts'

    def _seconds_until_next_midnight(self, now: datetime) -> int:
        next_day = (now + timedelta(days=1)).date()
        midnight = datetime.combine(next_day, datetime.min.time(), tzinfo=SAO_PAULO_TZ)
        return max(1, int((midnight - now).total_seconds()))
