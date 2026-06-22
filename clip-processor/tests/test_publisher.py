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


def make_conn_with_clips(clips: list[dict], dest_channels: list[dict] | None = None):
    """Cria mock de conexão MySQL com clips configurados.

    Args:
        clips: clips pendentes a retornar por _fetch_pending_clips / _fetch_pending_clips_for_channel
        dest_channels: canais-destino para _fetch_destination_channels.
                       None (padrão) → [] que ativa o fallback legado em publish_pending_clips.
    """
    conn = MagicMock()
    cursor = MagicMock()

    # Multi-canal: _fetch_destination_channels é chamado primeiro.
    # Por padrão, retorna [] para ativar o fallback legado (_fetch_pending_clips).
    # Testes multi-canal passam dest_channels explicitamente.
    actual_dest_channels = dest_channels if dest_channels is not None else []
    cursor.fetchall.side_effect = [
        actual_dest_channels,   # _fetch_destination_channels
        clips,                  # _fetch_pending_clips (fallback) OU _fetch_pending_clips_for_channel
    ] + [clips] * (len(clips) + 10)  # extra fetchall calls se houver múltiplos canais

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
        # Multi-canal: params pode ser ('pending',) [legacy] ou ('pending', dest_id) [multi-canal]
        status_param = select_calls[0].args[1][0] if select_calls[0].args[1] else None
        assert status_param == 'pending', (
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
        # Multi-canal: primeiro fetchall retorna [] (fallback legado), segundo retorna [SAMPLE_CLIP]
        cursor.fetchall.side_effect = [[], [SAMPLE_CLIP]] + [[]] * 10
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
        # Multi-canal: params pode ser ('approved',) [legacy] ou ('approved', dest_id) [multi-canal]
        status_param = select_calls[0].args[1][0] if select_calls[0].args[1] else None
        assert status_param == 'approved', (
            f"publisher deve selecionar status='approved' com MANUAL_APPROVAL_REQUIRED=true. "
            f'Params vistos: {select_calls[0].args[1]}'
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
        # Chamar _fetch_pending_clips_for_channel diretamente — reset do side_effect
        cursor.fetchall.side_effect = None
        cursor.fetchall.return_value = [clip_canal_1]

        clips = _fetch_pending_clips_for_channel(conn, 1)  # positional arg

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
        cursor.fetchall.side_effect = None
        cursor.fetchall.return_value = []

        clips = _fetch_pending_clips_for_channel(conn, 1)  # positional arg

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

    def test_fetch_destination_channels_returns_active(self):
        """MCAN-01: _fetch_destination_channels retorna apenas canais ativos."""
        from src.publisher import _fetch_destination_channels

        dest_channels = [
            {'id': 1, 'slug': 'futebol-br', 'name': 'Futebol BR', 'niche': 'futebol',
             'youtube_channel_id': 'UCaaa', 'credit_template': 'Vídeo de {channel_handle}'},
            {'id': 2, 'slug': 'esportes-ao-vivo', 'name': 'Esportes Ao Vivo', 'niche': 'esportes',
             'youtube_channel_id': 'UCbbb', 'credit_template': None},
        ]
        conn, cursor = make_conn_with_clips([])
        # Reset side_effect e usar return_value para teste direto desta função
        cursor.fetchall.side_effect = None
        cursor.fetchall.return_value = dest_channels

        result = _fetch_destination_channels(conn)

        assert len(result) == 2
        execute_calls = [str(c) for c in cursor.execute.call_args_list]
        assert any('active' in c.lower() or 'WHERE' in c for c in execute_calls), \
            'SELECT deve filtrar por active = TRUE'

    def test_publish_multi_canal_loop_publishes_to_both_channels(self):
        """MCAN-01/03: publish_pending_clips itera por canais-destino e publica clips de cada."""
        clip_ch1 = {**SAMPLE_CLIP, 'id': 1, 'destination_channel_id': 1}
        clip_ch2 = {**SAMPLE_CLIP, 'id': 2, 'destination_channel_id': 2, 'channel_handle': '@espn'}

        dest_ch1 = {'id': 1, 'slug': 'futebol-br', 'youtube_channel_id': 'UCaaa',
                    'credit_template': None, 'name': 'Futebol BR'}
        dest_ch2 = {'id': 2, 'slug': 'esportes', 'youtube_channel_id': 'UCbbb',
                    'credit_template': None, 'name': 'Esportes'}

        conn, cursor = make_conn_with_clips([])
        redis = MagicMock()
        uploader = make_mock_uploader(video_id='yt_multi_01')

        # _fetch_destination_channels retorna 2 canais
        # _fetch_pending_clips_for_channel retorna 1 clip por canal
        cursor.fetchall.side_effect = [
            [dest_ch1, dest_ch2],   # _fetch_destination_channels
            [clip_ch1],              # _fetch_pending_clips_for_channel(conn, 1)
            [clip_ch2],              # _fetch_pending_clips_for_channel(conn, 2)
        ]

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = True
            result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))

        # Deve publicar 2 clips (1 por canal)
        assert result == 2
        assert uploader.upload_clip.call_count == 2

    def test_append_credits_called_when_template_and_handle_available(self):
        """COPY-02: append_credits é chamado antes do upload quando credit_template e channel_handle presentes."""
        clip_with_handle = {
            **SAMPLE_CLIP,
            'id': 1,
            'destination_channel_id': 1,
            'channel_handle': '@sportv',
            'description': 'Descrição original',
        }
        dest = {'id': 1, 'slug': 'futebol-br', 'youtube_channel_id': 'UCaaa',
                'credit_template': 'Crédito: {channel_handle}', 'name': 'Futebol BR'}

        conn, cursor = make_conn_with_clips([])
        redis = MagicMock()
        uploader = make_mock_uploader(video_id='yt_credits_01')

        cursor.fetchall.side_effect = [
            [dest],
            [clip_with_handle],
        ]

        with patch('src.publisher.QuotaManager') as MockQuota:
            MockQuota.return_value.can_upload.return_value = True
            with patch('src.publisher.append_credits', return_value='Desc + Crédito') as mock_credits:
                result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))

        assert result == 1
        mock_credits.assert_called_once_with(
            'Descrição original',
            'Crédito: {channel_handle}',
            '@sportv',
        )
