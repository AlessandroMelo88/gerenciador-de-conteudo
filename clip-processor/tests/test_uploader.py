"""
Testes para YouTubeUploader — upload de clips e thumbnails.
Todas as chamadas YouTube API são mockadas.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.uploader import PostUploadError, YouTubeUploader


@pytest.fixture(autouse=True)
def mock_media_contract_for_fake_files(monkeypatch):
    """Os testes de API usam bytes falsos; o contrato real é coberto separadamente."""
    monkeypatch.setattr(
        'src.uploader.validate_short_media',
        lambda path: {'duration': 30.0, 'width': 1080, 'height': 1920},
    )


def make_youtube_mock(video_id='yt_test_abc123'):
    """Cria um mock do serviço YouTube que simula upload bem-sucedido."""
    yt = MagicMock()

    # Simula upload em um único chunk
    insert_request = MagicMock()
    insert_request.next_chunk.return_value = (None, {'id': video_id})
    yt.videos.return_value.insert.return_value = insert_request

    # Simula upload de thumbnail
    yt.thumbnails.return_value.set.return_value.execute.return_value = {}

    return yt


def make_uploader(token_file='/fake/token.json', video_id='yt_test_abc123'):
    """Cria YouTubeUploader com credenciais e YouTube mockados."""
    yt = make_youtube_mock(video_id)

    with patch('src.uploader.os.path.exists', return_value=True):
        with patch('src.uploader.Credentials.from_authorized_user_file') as mock_creds:
            mock_creds.return_value.expired = False
            uploader = YouTubeUploader(
                token_file=token_file,
                youtube_factory=lambda creds: yt,
            )
    uploader._load_credentials = lambda: MagicMock(expired=False)
    return uploader, yt


class TestUploadClip:
    def test_video_body_sanitizes_youtube_unsupported_angle_brackets(self):
        uploader, _ = make_uploader()

        body = uploader._build_video_body(
            {
                'title': 'Como usar <vector> no C++',
                'description': 'A comparação x < 5 aparece no trecho.',
                'tags': ['C++', 'vector'],
            }
        )

        assert body['snippet']['title'] == 'Como usar ‹vector› no C++'
        assert '<' not in body['snippet']['description']
        assert '>' not in body['snippet']['description']

    def test_video_body_blocks_descriptions_over_youtube_utf8_byte_limit(self):
        uploader, _ = make_uploader()

        with pytest.raises(ValueError, match='5000 bytes'):
            uploader._build_video_body(
                {
                    'title': 'Privacidade digital',
                    'description': 'é' * 2501,
                    'tags': ['privacidade'],
                }
            )

    def test_upload_blocks_profanity_in_manual_metadata_before_youtube_api(self, tmp_path):
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        uploader, yt = make_uploader()

        with patch('src.uploader.MediaFileUpload'):
            with pytest.raises(ValueError, match='linguagem vulgar forte'):
                uploader.upload_clip(
                    {
                        'clip_path': str(clip_file),
                        'title': 'Diploma genérico sem palavrão',
                        'description': 'Resumo do corte.',
                        'tags': 'educação, p0rr4',
                    }
                )

        yt.videos.return_value.insert.assert_not_called()

    def test_short_media_contract_runs_before_youtube_upload(self, tmp_path, monkeypatch):
        """Um arquivo fora do contrato é bloqueado antes de criar vídeo no YouTube."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        yt = make_youtube_mock('blocked_vid')
        uploader = YouTubeUploader(token_file='/fake/token.json', service=yt)

        def _mock_validate(path):
            raise ValueError('mídia inválida')

        monkeypatch.setattr('src.uploader.validate_short_media', _mock_validate)

        with pytest.raises(ValueError, match='mídia inválida'):
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Short inválido',
                    'format': 'curto',
                }
            )

        yt.videos.return_value.insert.assert_not_called()

    def test_successful_upload_returns_video_id(self, tmp_path):
        """Upload bem-sucedido deve retornar o youtube_video_id."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')

        yt = make_youtube_mock('abc_vid_id')
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            result = uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Gol incrível do Vini Jr',
                    'description': 'Descrição do clip',
                    'tags': 'futebol,gol,vini',
                }
            )

        assert result == 'abc_vid_id'

    def test_production_clip_uploads_official_caption_before_publication(
        self, tmp_path, monkeypatch
    ):
        """Clips do pipeline devem publicar a faixa pt-BR revisada antes de ficarem públicos."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        srt_file = tmp_path / 'clip.srt'
        srt_file.write_text(
            '1\n00:00:00,000 --> 00:00:02,000\nSenior cansado\n',
            encoding='utf-8',
        )
        monkeypatch.setenv('YOUTUBE_WAIT_FOR_HD', 'false')

        yt = make_youtube_mock('caption_vid')
        media_factory = MagicMock(side_effect=lambda path, **kwargs: {'path': path, **kwargs})
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            service=yt,
            media_upload_factory=media_factory,
        )

        result = uploader.upload_clip(
            {
                'clip_path': str(clip_file),
                'title': 'Clip com legenda oficial',
                'format': 'curto',
            }
        )

        assert result == 'caption_vid'
        insert_kwargs = yt.captions.return_value.insert.call_args.kwargs
        assert insert_kwargs['part'] == 'snippet'
        assert insert_kwargs['body']['snippet'] == {
            'videoId': 'caption_vid',
            'language': 'pt-BR',
            'name': 'Português (Brasil) — Legenda revisada',
            'isDraft': False,
        }
        assert insert_kwargs['sync'] is False
        assert insert_kwargs['media_body']['path'] == str(srt_file)
        assert (
            yt.videos.return_value.insert.call_args.kwargs['body']['status']['privacyStatus']
            == 'private'
        )
        assert (
            yt.videos.return_value.update.call_args.kwargs['body']['status']['privacyStatus']
            == 'public'
        )

    def test_production_clip_requires_srt_before_video_insert(self, tmp_path):
        """Um clip de produção sem SRT não pode ser publicado sem legenda oficial."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        yt = make_youtube_mock('no_srt_vid')
        uploader = YouTubeUploader(token_file='/fake/token.json', service=yt)

        with pytest.raises(FileNotFoundError, match='Arquivo de legenda não encontrado'):
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Clip sem SRT',
                    'format': 'longo',
                }
            )

        yt.videos.return_value.insert.assert_not_called()

    def test_partial_upload_is_reused_after_caption_failure(self, tmp_path, monkeypatch):
        """Falha na legenda salva o ID e uma retomada não cria vídeo duplicado."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        srt_file = tmp_path / 'clip.srt'
        srt_file.write_text('1\n00:00:00,000 --> 00:00:01,000\nTexto\n', encoding='utf-8')
        monkeypatch.setenv('YOUTUBE_WAIT_FOR_HD', 'false')

        yt = make_youtube_mock('partial_vid')
        yt.captions.return_value.insert.return_value.execute.side_effect = RuntimeError(
            'caption scope missing'
        )
        media_factory = MagicMock(side_effect=lambda path, **kwargs: {'path': path, **kwargs})
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            service=yt,
            media_upload_factory=media_factory,
        )
        clip = {
            'clip_path': str(clip_file),
            'title': 'Clip parcial',
            'format': 'curto',
            'subtitle_path': str(srt_file),
        }

        with pytest.raises(PostUploadError) as error:
            uploader.upload_clip(clip)
        assert error.value.video_id == 'partial_vid'

        yt.captions.return_value.insert.return_value.execute.side_effect = None
        clip['youtube_video_id'] = error.value.video_id
        assert uploader.upload_clip(clip) == 'partial_vid'
        yt.videos.return_value.insert.assert_called_once()

    def test_existing_caption_track_is_updated_on_retry(self, tmp_path, monkeypatch):
        """Retry após 409 atualiza a mesma faixa em vez de criar uma segunda."""
        import googleapiclient.errors

        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        srt_file = tmp_path / 'clip.srt'
        srt_file.write_text('1\n00:00:00,000 --> 00:00:01,000\nTexto novo\n', encoding='utf-8')
        monkeypatch.setenv('YOUTUBE_WAIT_FOR_HD', 'false')

        yt = make_youtube_mock('existing_caption_vid')
        yt.captions.return_value.insert.return_value.execute.side_effect = (
            googleapiclient.errors.HttpError(MagicMock(status=409), b'caption exists')
        )
        yt.captions.return_value.list.return_value.execute.return_value = {
            'items': [
                {
                    'id': 'caption_track_01',
                    'snippet': {
                        'language': 'pt-BR',
                        'name': 'Português (Brasil) — Legenda revisada',
                    },
                }
            ]
        }
        media_factory = MagicMock(side_effect=lambda path, **kwargs: {'path': path, **kwargs})
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            service=yt,
            media_upload_factory=media_factory,
        )

        assert (
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Retry de legenda',
                    'format': 'curto',
                    'subtitle_path': str(srt_file),
                }
            )
            == 'existing_caption_vid'
        )

        update_kwargs = yt.captions.return_value.update.call_args.kwargs
        assert update_kwargs['part'] == 'id'
        assert update_kwargs['body'] == {'id': 'caption_track_01'}
        assert update_kwargs['media_body']['path'] == str(srt_file)

    def test_hd_processing_finishes_before_publication(self, tmp_path, monkeypatch):
        """Vídeo de produção só muda para público após processingStatus=succeeded."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        srt_file = tmp_path / 'clip.srt'
        srt_file.write_text('1\n00:00:00,000 --> 00:00:01,000\nTexto\n', encoding='utf-8')
        monkeypatch.setenv('YOUTUBE_WAIT_FOR_HD', 'true')
        monkeypatch.setenv('YOUTUBE_PROCESSING_TIMEOUT_SECONDS', '10')
        monkeypatch.setenv('YOUTUBE_PROCESSING_POLL_SECONDS', '1')

        yt = make_youtube_mock('hd_vid')
        yt.videos.return_value.list.return_value.execute.side_effect = [
            {'items': [{'processingDetails': {'processingStatus': 'processing'}}]},
            {'items': [{'processingDetails': {'processingStatus': 'succeeded'}}]},
        ]
        uploader = YouTubeUploader(token_file='/fake/token.json', service=yt)

        with patch('src.uploader.time.sleep'):
            assert (
                uploader.upload_clip(
                    {
                        'clip_path': str(clip_file),
                        'title': 'Clip HD',
                        'format': 'curto',
                        'subtitle_path': str(srt_file),
                    }
                )
                == 'hd_vid'
            )

        assert yt.videos.return_value.list.call_count == 2
        assert (
            yt.videos.return_value.update.call_args.kwargs['body']['status']['privacyStatus']
            == 'public'
        )

    def test_missing_clip_file_raises_file_not_found(self):
        """clip_path inexistente deve levantar FileNotFoundError antes da API."""
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: MagicMock(),
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with pytest.raises(FileNotFoundError, match='Arquivo de clip não encontrado'):
            uploader.upload_clip(
                {
                    'clip_path': '/nonexistent/clip.mp4',
                    'title': 'Título',
                }
            )

    def test_missing_clip_path_raises_value_error(self):
        """Ausência de clip_path deve levantar ValueError."""
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: MagicMock(),
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with pytest.raises(ValueError, match='clip_path é obrigatório'):
            uploader.upload_clip({'title': 'Título'})

    def test_missing_title_raises_value_error(self, tmp_path):
        """Ausência de title deve levantar ValueError."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake')

        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: MagicMock(),
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with pytest.raises(ValueError, match='title é obrigatório'):
            uploader.upload_clip({'clip_path': str(clip_file)})

    def test_missing_token_file_raises_file_not_found(self, tmp_path):
        """token_file inexistente deve levantar FileNotFoundError."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake')

        uploader = YouTubeUploader(token_file='/nonexistent/token.json')

        with pytest.raises(FileNotFoundError, match='Token OAuth não encontrado'):
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Título',
                }
            )

    def test_thumbnail_upload_called_when_path_exists(self, tmp_path):
        """Se thumbnail_path existir, thumbnails().set() deve ser chamado."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        thumb_file = tmp_path / 'thumb.jpg'
        thumb_file.write_bytes(b'fake_jpg')

        yt = make_youtube_mock('thumb_vid')
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Clip com thumb',
                    'thumbnail_path': str(thumb_file),
                }
            )

        yt.thumbnails.return_value.set.assert_called_once()

    def test_thumbnail_permission_failure_keeps_video_published(self, tmp_path):
        """403 na thumbnail não pode gerar retry/duplicata do vídeo."""
        import googleapiclient.errors

        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        thumb_file = tmp_path / 'thumb.jpg'
        thumb_file.write_bytes(b'fake_jpg')

        yt = make_youtube_mock('thumb_fail_vid')
        yt.thumbnails.return_value.set.return_value.execute.side_effect = (
            googleapiclient.errors.HttpError(MagicMock(status=403), b'forbidden')
        )

        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            result = uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Clip thumb fail',
                    'thumbnail_path': str(thumb_file),
                }
            )

        assert result == 'thumb_fail_vid'

    def test_thumbnail_non_permission_failure_preserves_video_id_for_idempotent_retry(
        self, tmp_path
    ):
        """Falha depois do insert mantém o ID para a retentativa não duplicar vídeo."""
        import googleapiclient.errors

        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        thumb_file = tmp_path / 'thumb.jpg'
        thumb_file.write_bytes(b'fake_jpg')

        yt = make_youtube_mock('thumb_bad_request_vid')
        yt.thumbnails.return_value.set.return_value.execute.side_effect = (
            googleapiclient.errors.HttpError(MagicMock(status=400), b'bad request')
        )

        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            with pytest.raises(PostUploadError) as error:
                uploader.upload_clip(
                    {
                        'clip_path': str(clip_file),
                        'title': 'Clip thumb bad request',
                        'thumbnail_path': str(thumb_file),
                    }
                )

        assert error.value.video_id == 'thumb_bad_request_vid'

    def test_description_over_youtube_limit_is_rejected_before_insert(self, tmp_path):
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        yt = make_youtube_mock('description_vid')
        uploader = YouTubeUploader(token_file='/fake/token.json', service=yt)

        with pytest.raises(ValueError, match='descrição excede o limite'):
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Título claro',
                    'description': 'x' * 5001,
                }
            )

        yt.videos.return_value.insert.assert_not_called()

    def test_tags_string_is_parsed_as_list(self, tmp_path):
        """Tags em formato string separado por vírgula devem virar lista."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')

        yt = make_youtube_mock('tags_vid')
        yt.videos.return_value.insert.return_value.next_chunk.return_value = (
            None,
            {'id': 'tags_vid'},
        )

        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Teste tags',
                    'tags': 'futebol, gol, brasil',
                }
            )

        call_kwargs = yt.videos.return_value.insert.call_args[1]
        tags_in_body = call_kwargs['body']['snippet']['tags']
        assert isinstance(tags_in_body, list)
        assert 'futebol' in tags_in_body
        assert 'gol' in tags_in_body

    def test_default_privacy_status_is_public(self, tmp_path, monkeypatch):
        """Quando YOUTUBE_PRIVACY_STATUS não está setado, default é public."""
        monkeypatch.delenv('YOUTUBE_PRIVACY_STATUS', raising=False)
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')

        yt = make_youtube_mock('default_pub_vid')
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Default public clip',
                }
            )

        call_kwargs = yt.videos.return_value.insert.call_args[1]
        assert call_kwargs['body']['status']['privacyStatus'] == 'public'

    def test_privacy_status_from_env(self, tmp_path, monkeypatch):
        """YOUTUBE_PRIVACY_STATUS do env deve ser usado no upload quando configurado."""
        monkeypatch.setenv('YOUTUBE_PRIVACY_STATUS', 'unlisted')
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')

        yt = make_youtube_mock('unlisted_vid')
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            uploader.upload_clip(
                {
                    'clip_path': str(clip_file),
                    'title': 'Unlisted clip',
                }
            )

        call_kwargs = yt.videos.return_value.insert.call_args[1]
        assert call_kwargs['body']['status']['privacyStatus'] == 'unlisted'


# ---------------------------------------------------------------------------
# Wave 2 — RED tests: Channel Slug token path (MCAN-01)
# Estes testes falham até a implementação em Wave 3-4.
# ---------------------------------------------------------------------------


class TestYouTubeUploaderChannelSlug:
    """Testes RED para suporte a channel_slug no YouTubeUploader (MCAN-01)."""

    def test_channel_slug_determines_token_file_path(self):
        """MCAN-01: channel_slug='futebol-em-cortes' → token_file='/app/youtube/token-futebol-em-cortes.json'."""

        uploader = YouTubeUploader(channel_slug='futebol-em-cortes')
        assert uploader.token_file == '/app/youtube/token-futebol-em-cortes.json'

    def test_no_channel_slug_uses_default_token_file(self):
        """Retrocompat: sem channel_slug, usa DEFAULT_TOKEN_FILE."""
        from src.uploader import DEFAULT_TOKEN_FILE

        uploader = YouTubeUploader()
        assert uploader.token_file == DEFAULT_TOKEN_FILE

    def test_explicit_token_file_overrides_channel_slug(self):
        """Retrocompat: token_file explícito tem precedência sobre channel_slug."""
        uploader = YouTubeUploader(token_file='/custom/path.json')
        assert uploader.token_file == '/custom/path.json'
