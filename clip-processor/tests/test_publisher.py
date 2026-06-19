"""
Testes para publisher.py — publicação de clips pendentes.
"""
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
}


class TestPublishPendingClips:
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


class TestPublishApprovedClips:
    """Phase 6 — publisher.py deve passar a selecionar status='approved' (não 'pending').

    Estado RED até Plan 06-02: o SELECT em publisher._fetch_pending_clips ainda
    usa WHERE gc.status = 'pending'. Esses testes ficam vermelhos até o swap
    do literal pending → approved.
    """

    def test_seleciona_apenas_approved(self):
        """O SELECT que busca clips para publicar deve filtrar por status='approved'."""
        conn, cursor = make_conn_with_clips([SAMPLE_CLIP])
        redis = MagicMock()
        uploader = make_mock_uploader(video_id='yt_approved_01')

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = True
            publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))

        # Procura o SELECT que filtra por status — DEVE ser approved
        select_sqls = [
            str(c.args[0]) for c in cursor.execute.call_args_list
            if c.args and 'SELECT' in str(c.args[0]).upper()
            and 'STATUS' in str(c.args[0]).upper()
        ]
        joined = ' '.join(select_sqls)
        assert "'approved'" in joined, (
            f"publisher deve selecionar status='approved' (Phase 6). SELECTs vistos: {select_sqls}"
        )
        assert "'pending'" not in joined, (
            "publisher ainda referencia status='pending' — swap Phase 6 não foi aplicado"
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
