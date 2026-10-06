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

    def test_thumbnail_failure_is_graceful(self, tmp_path):
        """Falha no upload da thumbnail customizada deve logar aviso e manter o vídeo publicado."""
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
            result = uploader.upload_clip({
                'clip_path': str(clip_file),
                'title': 'Clip thumb fail',
                'thumbnail_path': str(thumb_file),
            })
            assert result == 'thumb_fail_vid'

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


# --- verify_channel: guard contra token do canal errado (incidente 02/10/2026) ---

class _FakeChannels:
    def __init__(self, items, raise_exc=None):
        self._items = items
        self._raise = raise_exc

    def list(self, **kwargs):
        outer = self

        class _Req:
            def execute(self):
                if outer._raise:
                    raise outer._raise
                return {'items': outer._items}

        return _Req()


class _FakeService:
    def __init__(self, items, raise_exc=None):
        self._channels = _FakeChannels(items, raise_exc)

    def channels(self):
        return self._channels


def _uploader_with(items, raise_exc=None):
    from src.uploader import YouTubeUploader
    return YouTubeUploader(service=_FakeService(items, raise_exc))


def test_verify_channel_aceita_canal_esperado():
    up = _uploader_with([{'id': 'UC_CERTO', 'snippet': {'title': 'Futebol em Cortes'}}])
    up.verify_channel('UC_CERTO')  # não levanta


def test_verify_channel_bloqueia_canal_errado():
    from src.uploader import WrongChannelError
    up = _uploader_with([{'id': 'UC_PESSOAL', 'snippet': {'title': 'Alessandro Melo'}}])
    with pytest.raises(WrongChannelError):
        up.verify_channel('UC_CERTO')


def test_verify_channel_bloqueia_token_sem_canal():
    from src.uploader import WrongChannelError
    up = _uploader_with([])
    with pytest.raises(WrongChannelError):
        up.verify_channel('UC_CERTO')


def test_verify_channel_deixa_passar_quando_nao_da_para_conferir():
    """Escopo insuficiente não é prova de canal errado — avisa e segue."""
    up = _uploader_with([], raise_exc=RuntimeError('insufficient scopes'))
    up.verify_channel('UC_CERTO')  # não levanta


def test_verify_channel_ignora_placeholder():
    up = _uploader_with([{'id': 'UC_QUALQUER', 'snippet': {'title': 'x'}}])
    up.verify_channel('UC_PLACEHOLDER_PODCAST')  # não levanta


# --- privacidade do upload: escolha do clip → padrão do canal → env ---

class TestResolvePrivacidade:
    def _body(self, clip, env=None):
        from src.uploader import YouTubeUploader
        base = {'title': 't', 'clip_path': '/x.mp4'}
        with patch.dict(os.environ, env or {}, clear=False):
            if env is None:
                os.environ.pop('YOUTUBE_PRIVACY_STATUS', None)
            return YouTubeUploader(service=MagicMock())._build_video_body({**base, **clip})

    def test_escolha_do_clip_vence_o_canal(self):
        body = self._body({'privacy_status': 'public', 'channel_default_privacy': 'private'})
        assert body['status']['privacyStatus'] == 'public'

    def test_sem_escolha_herda_o_padrao_do_canal(self):
        body = self._body({'privacy_status': None, 'channel_default_privacy': 'public'})
        assert body['status']['privacyStatus'] == 'public'

    def test_sem_canal_cai_na_env(self):
        body = self._body({}, env={'YOUTUBE_PRIVACY_STATUS': 'public'})
        assert body['status']['privacyStatus'] == 'public'

    def test_sem_nada_continua_private(self):
        """Default histórico: nada configurado em lugar nenhum."""
        body = self._body({})
        assert body['status']['privacyStatus'] == 'private'

    def test_valor_invalido_e_ignorado_e_cai_para_o_proximo(self):
        body = self._body({'privacy_status': 'lixo', 'channel_default_privacy': 'public'})
        assert body['status']['privacyStatus'] == 'public'
