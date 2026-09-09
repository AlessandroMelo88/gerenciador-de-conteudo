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
    def test_inside_evening_window_below_quota(self):
        """Deve permitir upload dentro da janela da noite (19h às 22h)."""
        r = make_redis(count=0)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(19, 30)) is True

    def test_inside_lunch_window_below_quota(self):
        """Deve permitir upload dentro da janela do almoço/meio-dia (12h às 14h)."""
        r = make_redis(count=0)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(12, 30)) is True
        assert qm.can_upload(now=dt_sp(13, 59)) is True

    def test_between_windows_denied_without_bypass(self):
        """Deve negar upload entre as janelas (ex: 15h) quando não há bypass."""
        r = make_redis(count=0)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(15, 0)) is False

    def test_between_windows_allowed_with_bypass(self):
        """Deve permitir upload fora das janelas quando bypass_window=True."""
        r = make_redis(count=0)
        qm = QuotaManager(r, max_uploads_per_day=2)
        assert qm.can_upload(now=dt_sp(15, 0), bypass_window=True) is True

    def test_after_evening_window_end(self):
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


# ---------------------------------------------------------------------------
# Wave 2 — RED tests: Multi-Canal (MCAN-03, MCAN-04)
# Estes testes falham até a implementação em Wave 3-4.
# ---------------------------------------------------------------------------

class TestQuotaManagerMultiCanal:
    """Testes RED para suporte a channel_id no QuotaManager (MCAN-03, MCAN-04)."""

    def test_key_includes_channel_id_when_provided(self):
        """MCAN-03: _key() deve incluir channel_id quando fornecido.

        QuotaManager(r, channel_id='UCabc123')._key(dt) deve retornar
        'youtube_uploads:UCabc123:2026-06-18'.
        """
        r = make_redis(count=0)
        qm = QuotaManager(r, channel_id='UCabc123')
        key = qm._key(dt_sp(20))
        assert key == 'youtube_uploads:UCabc123:2026-06-18'

    def test_key_fallback_without_channel_id(self):
        """Retrocompat: _key() sem channel_id retorna 'youtube_uploads:2026-06-18'."""
        r = make_redis(count=0)
        qm = QuotaManager(r)
        key = qm._key(dt_sp(20))
        assert key == 'youtube_uploads:2026-06-18'

    def test_two_channels_use_independent_redis_keys(self):
        """MCAN-04: Dois QuotaManager com channel_id diferentes usam keys Redis distintas.

        Canal UCaaa e UCbbb não compartilham quota.
        """
        r_a = make_redis(count=0)
        r_b = make_redis(count=0)
        qm_a = QuotaManager(r_a, max_uploads_per_day=2, channel_id='UCaaa')
        qm_b = QuotaManager(r_b, max_uploads_per_day=2, channel_id='UCbbb')

        key_a = qm_a._key(dt_sp(20))
        key_b = qm_b._key(dt_sp(20))

        # Keys devem ser diferentes para garantir independência de quota
        assert key_a != key_b
        assert 'UCaaa' in key_a
        assert 'UCbbb' in key_b

    def test_channel_a_quota_exhausted_does_not_block_channel_b(self):
        """MCAN-04: Quota atingida no canal A não bloqueia canal B."""
        # Canal A: quota atingida
        r_a = make_redis(count=2)
        qm_a = QuotaManager(r_a, max_uploads_per_day=2, channel_id='UCaaa')

        # Canal B: quota disponível
        r_b = make_redis(count=0)
        qm_b = QuotaManager(r_b, max_uploads_per_day=2, channel_id='UCbbb')

        assert qm_a.can_upload(now=dt_sp(20)) is False
        assert qm_b.can_upload(now=dt_sp(20)) is True


class TestLongoReservation:
    def test_curto_blocked_when_longo_waiting_and_slots_reserved(self):
        """Com MAX=5 / LONGO=2 e 3 uploads, curto bloqueia se ainda há longo na fila."""
        r = MagicMock()
        # total=3, longo=0 → reserva 2 → teto curto = 3
        r.get.side_effect = lambda key: '3' if not key.endswith(':longo') else '0'
        qm = QuotaManager(r, max_uploads_per_day=5, max_longo_per_day=2)
        assert qm.can_upload(now=dt_sp(20), format='curto', longo_waiting=True) is False
        assert qm.can_upload(now=dt_sp(20), format='longo', longo_waiting=True) is True

    def test_curto_unblocked_when_no_longo_waiting(self):
        """Sem longo na fila, curto pode usar o restante da cota total."""
        r = MagicMock()
        r.get.side_effect = lambda key: '3' if not key.endswith(':longo') else '0'
        qm = QuotaManager(r, max_uploads_per_day=5, max_longo_per_day=2)
        assert qm.can_upload(now=dt_sp(20), format='curto', longo_waiting=False) is True

    def test_normalize_scores_via_parse(self):
        from src.selector import _parse_moments

        moments = _parse_moments('{"moments":[{"start_time":0,"end_time":500,"score":0.95,"reason":"x"}]}')
        assert moments[0]['score'] == pytest.approx(9.5)
