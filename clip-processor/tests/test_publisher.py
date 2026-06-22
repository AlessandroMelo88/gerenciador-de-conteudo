"""
Testes para publisher.py — publicação de clips pendentes.
"""
import os
import pytest
from unittest.mock import MagicMock, call, patch
from datetime import datetime
from zoneinfo import ZoneInfo

from src.publisher import publish_pending_clips


TZ_SP = ZoneInfo('America/Sao_Paulo')


def dt_sp(hour):
    return datetime(2026, 6, 18, hour, 0, 0, tzinfo=TZ_SP)


def make_mock_uploader(video_id='yt_pub_test', should_fail=False, fail_msg='Upload error'):
    """Mock de YouTubeUploader."""
    uploader = MagicMock()
    if should_fail:
        uploader.upload_clip.side_effect = Exception(fail_msg)
    else:
        uploader.upload_clip.return_value = video_id
    return uploader


def make_mock_quota(can_upload=True):
    """Mock de QuotaManager injetável via patch."""
    quota = MagicMock()
    quota.can_upload.return_value = can_upload
    quota.record_upload.return_value = None
    return quota


def make_conn_with_clips(clips: list[dict]):
    """Cria mock de conexão MySQL com clips configurados."""
    conn = MagicMock()
    cursor = MagicMock()

    # fetchall para _select_pending_clips retorna clips configurados
    # fetchone para _cleanup_source_if_done retorna sem pendentes
    cursor.fetchall.return_value = clips
    cursor.fetchone.side_effect = [
        {'cnt': 0},   # non-terminal clips count
        {'cnt': 1},   # published clips count
        {'local_path': None},  # source_video local_path
    ] * (len(clips) + 5)  # extra para não falhar
    # Phase 6: guard de status no UPDATE approved→publishing usa cursor.rowcount.
    # Simula MySQL retornando 1 row afetada no UPDATE (caminho feliz).
    cursor.rowcount = 1

    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = MagicMock(
        __enter__=MagicMock(return_value=cursor),
        __exit__=MagicMock(return_value=False),
        fetchall=cursor.fetchall,
        fetchone=cursor.fetchone,
        execute=cursor.execute,
        rowcount=1,
    )
    return conn, cursor


SAMPLE_CLIP = {
    'id': 1,
    'source_video_id': 10,
    'clip_path': '/app/videos/clips/clip_001.mp4',
    'thumbnail_path': '/app/videos/thumbnails/clip_001.jpg',
    'title': 'Gol incrível do Vini Jr',
    'description': 'Descrição do clip',
    'tags': 'futebol,gol,vini',
    'destination_channel_id': 1,
    'channel_handle': '@sportv',
}


class TestPublishPendingClips:
    def test_default_seleciona_pending_quando_manual_approval_off(self):
        """Default (MANUAL_APPROVAL_REQUIRED ausente): publisher pega clips 'pending'."""
        conn, cursor = make_conn_with_clips([SAMPLE_CLIP])
        redis = MagicMock()
        uploader = make_mock_uploader(video_id='yt_auto_01')

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('MANUAL_APPROVAL_REQUIRED', None)
            with patch('src.publisher.QuotaManager') as MockQuota:
                MockQuota.return_value.can_upload.return_value = True
                publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))

        select_calls = [
            c for c in cursor.execute.call_args_list
            if c.args and 'SELECT' in str(c.args[0]).upper()
            and 'gc.status = %s' in str(c.args[0])
        ]
        assert select_calls, 'SELECT parametrizado não encontrado'
        assert select_calls[0].args[1] == ('pending',), (
            f"Default deve selecionar status='pending' para auto-publicar. "
            f'Params: {select_calls[0].args[1]}'
        )

    def test_successful_upload_transitions_to_published(self):
        """Upload bem-sucedido: pending → publishing → published."""
        conn, cursor = make_conn_with_clips([SAMPLE_CLIP])
        redis = MagicMock()
        uploader = make_mock_uploader(video_id='yt_success_01')

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = True
            result = publish_pending_clips(
                conn, redis, uploader=uploader, now=dt_sp(20)
            )

        assert result == 1
        uploader.upload_clip.assert_called_once()

    def test_failed_upload_sets_status_failed_does_not_increment_quota(self):
        """Upload com erro: status vai para 'failed', quota não é incrementada."""
        conn, cursor = make_conn_with_clips([SAMPLE_CLIP])
        redis = MagicMock()
        uploader = make_mock_uploader(should_fail=True, fail_msg='API error 500')

        with patch('src.publisher.QuotaManager') as MockQuota:
            mock_quota_instance = MagicMock()
            mock_quota_instance.can_upload.return_value = True
            mock_quota_instance.record_upload.return_value = None
            MockQuota.return_value = mock_quota_instance

            result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))

        assert result == 0
        mock_quota_instance.record_upload.assert_not_called()

    def test_quota_blocked_leaves_clip_as_pending(self):
        """Quando quota/janela bloqueada, clip deve continuar como pending."""
        conn, cursor = make_conn_with_clips([SAMPLE_CLIP])
        redis = MagicMock()
        uploader = make_mock_uploader()

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = False
            result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(15))

        assert result == 0
        uploader.upload_clip.assert_not_called()

    def test_no_pending_clips_returns_zero(self):
        """Sem clips pendentes, retorna 0 sem chamar o uploader."""
        conn, cursor = make_conn_with_clips([])
        redis = MagicMock()
        uploader = make_mock_uploader()

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = True
            result = publish_pending_clips(conn, redis, uploader=uploader)

        assert result == 0
        uploader.upload_clip.assert_not_called()

    def test_quota_stops_remaining_clips(self):
        """Quando quota bloqueia no segundo clip, o terceiro não é tentado."""
        clips = [
            {**SAMPLE_CLIP, 'id': 1},
            {**SAMPLE_CLIP, 'id': 2},
            {**SAMPLE_CLIP, 'id': 3},
        ]
        conn, cursor = make_conn_with_clips(clips)
        redis = MagicMock()
        uploader = make_mock_uploader()

        # Primeira chamada: pode; segunda: bloqueada
        with patch('src.publisher.QuotaManager') as MockQuota:
            mock_quota = MagicMock()
            mock_quota.can_upload.side_effect = [True, False]
            MockQuota.return_value = mock_quota

            result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))

        # Só o primeiro clip foi publicado
        assert result == 1
        assert uploader.upload_clip.call_count == 1

    def test_failure_in_one_clip_continues_to_next_if_quota_allows(self):
        """Falha em um clip não para os próximos (quota ainda permite)."""
        clips = [
            {**SAMPLE_CLIP, 'id': 1},
            {**SAMPLE_CLIP, 'id': 2},
        ]
        conn, cursor = make_conn_with_clips(clips)
        redis = MagicMock()

        # Primeiro upload falha, segundo tem sucesso
        uploader = MagicMock()
        uploader.upload_clip.side_effect = [Exception('fail'), 'yt_vid_2']

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = True
            result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))

        assert result == 1  # Apenas o segundo foi publicado

    def test_raw_file_remains_while_another_clip_is_still_pending(self):
        """Arquivo bruto não deve ser removido se outro clip do mesmo vídeo ainda está pendente."""
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = [SAMPLE_CLIP]
        # Retorna 1 clip não-terminal (ainda há pendente)
        cursor.fetchone.return_value = {'cnt': 1}
        # Phase 6: guard de status precisa de rowcount=1 para o UPDATE approved→publishing
        cursor.rowcount = 1

        conn.cursor.return_value = MagicMock(
            __enter__=MagicMock(return_value=cursor),
            __exit__=MagicMock(return_value=False),
            fetchall=cursor.fetchall,
            fetchone=cursor.fetchone,
            execute=cursor.execute,
        )
        redis = MagicMock()
        uploader = make_mock_uploader()

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = True
            with patch('src.publisher.os.remove') as mock_remove:
                publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))
                mock_remove.assert_not_called()


@patch.dict(os.environ, {'MANUAL_APPROVAL_REQUIRED': 'true'})
class TestPublishApprovedClips:
    """Phase 6 — quando MANUAL_APPROVAL_REQUIRED=true, publisher seleciona 'approved'.

    Default (env var ausente ou 'false') publica 'pending' direto — coberto em TestPublishPendingClips.
    """

    def test_seleciona_apenas_approved(self):
        """O SELECT que busca clips para publicar deve passar 'approved' como parâmetro."""
        conn, cursor = make_conn_with_clips([SAMPLE_CLIP])
        redis = MagicMock()
        uploader = make_mock_uploader(video_id='yt_approved_01')

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = True
            publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))

        # Procura o SELECT — deve ter passado 'approved' como parâmetro
        select_calls = [
            c for c in cursor.execute.call_args_list
            if c.args and 'SELECT' in str(c.args[0]).upper()
            and 'gc.status = %s' in str(c.args[0])
        ]
        assert select_calls, f'SELECT parametrizado não encontrado. Calls: {cursor.execute.call_args_list}'
        select_params = select_calls[0].args[1] if len(select_calls[0].args) > 1 else None
        assert select_params == ('approved',), (
            f"publisher deve selecionar status='approved' com MANUAL_APPROVAL_REQUIRED=true. "
            f'Params vistos: {select_params}'
        )

    def test_quota_blocked_leaves_clip_as_approved(self):
        """Quando QuotaManager bloqueia, publisher NÃO chama YouTubeUploader e clip permanece approved."""
        conn, cursor = make_conn_with_clips([SAMPLE_CLIP])
        redis = MagicMock()
        uploader = make_mock_uploader()

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = False
            result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(15))

        assert result == 0
        uploader.upload_clip.assert_not_called()
        # Nenhum UPDATE para status='publishing' ou 'published'
        terminal_updates = [
            c for c in cursor.execute.call_args_list
            if c.args
            and 'UPDATE' in str(c.args[0]).upper()
            and ('publishing' in str(c.args[0]) or 'published' in str(c.args[0]))
        ]
        assert len(terminal_updates) == 0, (
            'Clip não deve transicionar de approved enquanto quota bloqueia'
        )

    def test_fora_da_janela_horaria(self):
        """Fora da janela horária (QuotaManager.can_upload=False), publisher pula sem mexer no clip."""
        conn, cursor = make_conn_with_clips([SAMPLE_CLIP])
        redis = MagicMock()
        uploader = make_mock_uploader()

        with patch('src.publisher.QuotaManager') as MockQuota:
            # can_upload retorna False (fora da janela)
            MockQuota.return_value.can_upload.return_value = False
            result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(3))

        assert result == 0
        uploader.upload_clip.assert_not_called()


# ---------------------------------------------------------------------------
# Wave 2 — RED tests: Multi-Canal (MCAN-02, MCAN-04)
# Estes testes falham até a implementação em Wave 3-4.
# ---------------------------------------------------------------------------

class TestPublisherMultiCanal:
    """Testes RED para roteamento multi-canal no publisher (MCAN-02, MCAN-04)."""

    def test_fetch_pending_clips_for_channel_returns_correct_dest(self):
        """MCAN-02: _fetch_pending_clips_for_channel filtra por destination_channel_id.

        Clips com destination_channel_id=1 são retornados; clips com
        destination_channel_id=2 não.
        """
        from src.publisher import _fetch_pending_clips_for_channel

        clip_canal_1 = {**SAMPLE_CLIP, 'id': 1, 'destination_channel_id': 1}

        conn, cursor = make_conn_with_clips([clip_canal_1])
        cursor.fetchall.return_value = [clip_canal_1]

        clips = _fetch_pending_clips_for_channel(conn, dest_id=1)

        assert len(clips) == 1
        assert clips[0]['destination_channel_id'] == 1
        execute_calls = [str(c) for c in cursor.execute.call_args_list]
        assert any('1' in c for c in execute_calls), (
            'SELECT deve filtrar por destination_channel_id=1'
        )

    def test_fetch_pending_clips_excludes_other_channels(self):
        """MCAN-02: clips de canal 2 não aparecem na busca do canal 1."""
        from src.publisher import _fetch_pending_clips_for_channel

        conn, cursor = make_conn_with_clips([])
        cursor.fetchall.return_value = []

        clips = _fetch_pending_clips_for_channel(conn, dest_id=1)

        assert clips == []

    def test_quota_canal_1_does_not_block_canal_2(self):
        """MCAN-04: quota atingida no canal 1 não bloqueia publicação no canal 2.

        Cada canal-destino tem seu próprio QuotaManager com channel_id distinto.
        Dois canais publicam independentemente — quota de um não afeta o outro.
        """
        clip_canal_1 = {**SAMPLE_CLIP, 'id': 1, 'destination_channel_id': 1}
        clip_canal_2 = {**SAMPLE_CLIP, 'id': 2, 'destination_channel_id': 2}

        # Canal 1: quota bloqueada
        conn_1, _ = make_conn_with_clips([clip_canal_1])
        redis_1 = MagicMock()
        uploader_1 = make_mock_uploader()

        # Canal 2: quota disponível
        conn_2, _ = make_conn_with_clips([clip_canal_2])
        redis_2 = MagicMock()
        uploader_2 = make_mock_uploader(video_id='yt_canal2_01')

        with patch('src.publisher.QuotaManager') as MockQuota:
            mock_q1 = MagicMock()
            mock_q1.can_upload.return_value = False
            mock_q2 = MagicMock()
            mock_q2.can_upload.return_value = True
            MockQuota.side_effect = [mock_q1, mock_q2]

            result_1 = publish_pending_clips(conn_1, redis_1, uploader=uploader_1, now=dt_sp(20))
            result_2 = publish_pending_clips(conn_2, redis_2, uploader=uploader_2, now=dt_sp(20))

        assert result_1 == 0  # Canal 1 bloqueado
        assert result_2 == 1  # Canal 2 publica normalmente
        uploader_1.upload_clip.assert_not_called()
        uploader_2.upload_clip.assert_called_once()
