"""
Testes para QuotaManager — controle de quota e janela de publicação.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from src.quota_manager import QuotaManager, UPLOAD_WINDOW_START, UPLOAD_WINDOW_END


TZ_SP = ZoneInfo('America/Sao_Paulo')


def make_redis(count=None):
    """Helper: mock Redis com contador configurável."""
    r = MagicMock()
    r.get.return_value = str(count) if count is not None else None
    r.incr.return_value = (count or 0) + 1
    r.expire.return_value = True
    return r


def dt_sp(hour, minute=0):
    """Helper: datetime no fuso São Paulo."""
    return datetime(2026, 6, 18, hour, minute, 0, tzinfo=TZ_SP)


class TestCanUpload:
    def test_inside_window_below_quota(self):
        """Deve permitir upload dentro da janela e abaixo da quota."""
        r = make_redis(count=0)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(19, 30)) is True

    def test_before_window_start(self):
        """Deve negar upload antes das 19h."""
        r = make_redis(count=0)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(18, 59)) is False

    def test_after_window_end(self):
        """Deve negar upload às 22h ou depois."""
        r = make_redis(count=0)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(22, 0)) is False

    def test_outside_window_midnight(self):
        """Deve negar upload à meia-noite."""
        r = make_redis(count=0)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(0, 0)) is False

    def test_quota_reached(self):
        """Deve negar upload quando quota diária atingida."""
        r = make_redis(count=2)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(20, 0)) is False

    def test_quota_not_yet_reached(self):
        """Deve permitir quando count < max."""
        r = make_redis(count=1)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(20, 0)) is True

    def test_env_value_above_ceiling_is_clamped(self, monkeypatch):
        """MAX_UPLOADS_PER_DAY > 6 deve ser reduzido para 6."""
        monkeypatch.setenv('MAX_UPLOADS_PER_DAY', '100')
        r = make_redis(count=0)
        qm = QuotaManager(r)  # lê do env
        assert qm._max == 6

    def test_default_max_is_two(self, monkeypatch):
        """Sem env, default é 2."""
        monkeypatch.delenv('MAX_UPLOADS_PER_DAY', raising=False)
        r = make_redis(count=0)
        qm = QuotaManager(r)
        assert qm._max == 2

    def test_no_redis_key_treats_as_zero(self):
        """Redis retornando None (chave não existe) deve contar como 0."""
        r = make_redis(count=None)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(20, 0)) is True


class TestRecordUpload:
    def test_increments_redis_key(self):
        """record_upload deve chamar INCR no Redis."""
        r = make_redis(count=None)
        r.incr.return_value = 1
        qm = QuotaManager(r, max_uploads_per_day=2)
        qm.record_upload(now=dt_sp(20, 0))
        r.incr.assert_called_once()

    def test_sets_ttl_on_first_upload(self):
        """Primeiro upload do dia deve definir TTL até meia-noite."""
        r = make_redis(count=None)
        r.incr.return_value = 1  # primeiro upload
        qm = QuotaManager(r, max_uploads_per_day=2)
        qm.record_upload(now=dt_sp(20, 0))
        # TTL deve ser chamado
        r.expire.assert_called_once()
        # TTL deve ser positivo (segundos até meia-noite)
        ttl_arg = r.expire.call_args[0][1]
        assert ttl_arg > 0

    def test_does_not_reset_ttl_on_second_upload(self):
        """Segundo upload não deve redefinir o TTL."""
        r = make_redis(count=1)
        r.incr.return_value = 2  # segundo upload
        qm = QuotaManager(r, max_uploads_per_day=2)
        qm.record_upload(now=dt_sp(20, 0))
        r.expire.assert_not_called()

    def test_ttl_points_to_next_sao_paulo_midnight(self):
        """TTL deve ser o número de segundos até meia-noite em SP."""
        r = make_redis(count=None)
        r.incr.return_value = 1
        qm = QuotaManager(r, max_uploads_per_day=2)

        now = dt_sp(20, 0)  # 20:00 SP = 4h até meia-noite
        qm.record_upload(now=now)

        ttl = r.expire.call_args[0][1]
        # 20h → meia-noite = 4 horas = 14400 segundos
        assert 14000 < ttl <= 14400
