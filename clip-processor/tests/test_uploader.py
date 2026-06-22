"""
Testes para YouTubeUploader — upload de clips e thumbnails.
Todas as chamadas YouTube API são mockadas.
"""
import os
import pytest
from unittest.mock import MagicMock, patch

from src.uploader import YouTubeUploader


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
            result = uploader.upload_clip({
                'clip_path': str(clip_file),
                'title': 'Gol incrível do Vini Jr',
                'description': 'Descrição do clip',
                'tags': 'futebol,gol,vini',
            })

        assert result == 'abc_vid_id'

    def test_missing_clip_file_raises_file_not_found(self):
        """clip_path inexistente deve levantar FileNotFoundError antes da API."""
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: MagicMock(),
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with pytest.raises(FileNotFoundError, match='Arquivo de clip não encontrado'):
            uploader.upload_clip({
                'clip_path': '/nonexistent/clip.mp4',
                'title': 'Título',
            })

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
            uploader.upload_clip({
                'clip_path': str(clip_file),
                'title': 'Título',
            })

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
            uploader.upload_clip({
                'clip_path': str(clip_file),
                'title': 'Clip com thumb',
                'thumbnail_path': str(thumb_file),
            })

        yt.thumbnails.return_value.set.assert_called_once()

    def test_thumbnail_failure_propagates(self, tmp_path):
        """Falha no upload da thumbnail deve ser propagada ao caller."""
        import googleapiclient.errors
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')
        thumb_file = tmp_path / 'thumb.jpg'
        thumb_file.write_bytes(b'fake_jpg')

        yt = make_youtube_mock('thumb_fail_vid')
        yt.thumbnails.return_value.set.return_value.execute.side_effect = \
            googleapiclient.errors.HttpError(MagicMock(status=400), b'error')

        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            with pytest.raises(googleapiclient.errors.HttpError):
                uploader.upload_clip({
                    'clip_path': str(clip_file),
                    'title': 'Clip thumb fail',
                    'thumbnail_path': str(thumb_file),
                })

    def test_tags_string_is_parsed_as_list(self, tmp_path):
        """Tags em formato string separado por vírgula devem virar lista."""
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')

        yt = make_youtube_mock('tags_vid')
        yt.videos.return_value.insert.return_value.next_chunk.return_value = \
            (None, {'id': 'tags_vid'})

        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            uploader.upload_clip({
                'clip_path': str(clip_file),
                'title': 'Teste tags',
                'tags': 'futebol, gol, brasil',
            })

        call_kwargs = yt.videos.return_value.insert.call_args[1]
        tags_in_body = call_kwargs['body']['snippet']['tags']
        assert isinstance(tags_in_body, list)
        assert 'futebol' in tags_in_body
        assert 'gol' in tags_in_body

    def test_privacy_status_from_env(self, tmp_path, monkeypatch):
        """YOUTUBE_PRIVACY_STATUS do env deve ser usado no upload."""
        monkeypatch.setenv('YOUTUBE_PRIVACY_STATUS', 'public')
        clip_file = tmp_path / 'clip.mp4'
        clip_file.write_bytes(b'fake_mp4')

        yt = make_youtube_mock('public_vid')
        uploader = YouTubeUploader(
            token_file='/fake/token.json',
            youtube_factory=lambda creds: yt,
        )
        uploader._load_credentials = lambda: MagicMock(expired=False)

        with patch('src.uploader.MediaFileUpload'):
            uploader.upload_clip({
                'clip_path': str(clip_file),
                'title': 'Public clip',
            })

        call_kwargs = yt.videos.return_value.insert.call_args[1]
        assert call_kwargs['body']['status']['privacyStatus'] == 'public'


# ---------------------------------------------------------------------------
# Wave 2 — RED tests: Channel Slug token path (MCAN-01)
# Estes testes falham até a implementação em Wave 3-4.
# ---------------------------------------------------------------------------

class TestYouTubeUploaderChannelSlug:
    """Testes RED para suporte a channel_slug no YouTubeUploader (MCAN-01)."""

    def test_channel_slug_determines_token_file_path(self):
        """MCAN-01: channel_slug='futebol-em-cortes' → token_file='/app/youtube/token-futebol-em-cortes.json'."""
        from src.uploader import DEFAULT_TOKEN_FILE

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
