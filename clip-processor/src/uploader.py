"""
uploader.py — Upload de clips para YouTube Data API v3.

Exporta:
  - YouTubeUploader.upload_clip(clip) -> youtube_video_id
"""
import os
import sys
import types
from pathlib import Path

from src.db import get_db_connection as db_connect


DEFAULT_TOKEN_FILE = '/app/youtube/token-futebol-em-cortes.json'
YOUTUBE_UPLOAD_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
]


try:
    from google.oauth2.credentials import Credentials
except ModuleNotFoundError:
    class Credentials:  # pragma: no cover - fallback only for local tests without deps
        @classmethod
        def from_authorized_user_file(cls, *args, **kwargs):
            raise ModuleNotFoundError('google')


try:
    from googleapiclient.http import MediaFileUpload
except ModuleNotFoundError:
    class MediaFileUpload:  # pragma: no cover - fallback only for local tests without deps
        def __init__(self, path, **kwargs):
            self.path = path
            self.kwargs = kwargs


try:
    import googleapiclient.errors  # noqa: F401
except ModuleNotFoundError:
    googleapiclient_module = types.ModuleType('googleapiclient')
    errors_module = types.ModuleType('googleapiclient.errors')

    class HttpError(Exception):
        def __init__(self, resp, content):
            super().__init__(content)
            self.resp = resp
            self.content = content

    errors_module.HttpError = HttpError
    googleapiclient_module.errors = errors_module
    sys.modules.setdefault('googleapiclient', googleapiclient_module)
    sys.modules.setdefault('googleapiclient.errors', errors_module)


try:
    from google.auth.exceptions import RefreshError
except ModuleNotFoundError:
    class RefreshError(Exception):  # pragma: no cover - fallback only for local tests without deps
        pass


class YouTubeUploader:
    """Cliente fino para videos.insert + thumbnails.set."""

    def __init__(
        self,
        token_file: str | None = None,
        channel_slug: str | None = None,
        youtube_factory=None,
        service=None,
        service_factory=None,
        media_upload_factory=None,
    ):
        self.channel_slug = channel_slug  # armazenado para uso em _flag_expired / _clear_expired
        if channel_slug:
            self.token_file = f'/app/youtube/token-{channel_slug}.json'
        else:
            self.token_file = token_file or os.environ.get('YOUTUBE_TOKEN_FILE', DEFAULT_TOKEN_FILE)
        self._youtube_factory = youtube_factory
        self._service = service
        self._service_factory = service_factory
        self._media_upload_factory = media_upload_factory or MediaFileUpload

    def upload_clip(self, clip: dict) -> str:
        clip_path = self._validate_clip(clip)
        thumbnail_path = clip.get('thumbnail_path')
        if thumbnail_path and not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f'Arquivo de thumbnail não encontrado: {thumbnail_path}')

        service = self._get_service()
        body = self._build_video_body(clip)
        media = self._media_upload_factory(
            clip_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/mp4',
        )

        request = service.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media,
        )
        response = self._execute_resumable(request)
        video_id = response.get('id') if response else None
        if not video_id:
            raise RuntimeError('YouTube upload did not return a video id')

        # Self-healing OAuth flag
        self._clear_expired()

        if thumbnail_path:
            try:
                thumb_media = self._media_upload_factory(
                    thumbnail_path,
                    chunksize=-1,
                    resumable=True,
                )
                service.thumbnails().set(
                    videoId=video_id,
                    media_body=thumb_media,
                ).execute()
            except Exception as e:
                print(f'[UPLOADER] Aviso: não foi possível enviar thumbnail customizada para {video_id}: {e}', file=sys.stderr)

        return video_id

    def _validate_clip(self, clip: dict) -> str:
        clip_path = clip.get('clip_path')
        if not clip_path:
            raise ValueError('clip_path é obrigatório')
        if not clip.get('title'):
            raise ValueError('title é obrigatório')
        if not os.path.exists(clip_path):
            raise FileNotFoundError(f'Arquivo de clip não encontrado: {clip_path}')
        return str(clip_path)

    def _load_credentials(self):
        token_path = Path(self.token_file)
        if not token_path.exists():
            raise FileNotFoundError(f'Token OAuth não encontrado: {self.token_file}')

        creds = Credentials.from_authorized_user_file(str(token_path))
        if getattr(creds, 'expired', False) and getattr(creds, 'refresh_token', None):
            from google.auth.transport.requests import Request
            try:
                creds.refresh(Request())
                try:
                    token_path.write_text(creds.to_json())
                except Exception as save_err:
                    print(f'[UPLOADER] Aviso: não foi possível persistir token atualizado: {save_err}', file=sys.stderr)
            except RefreshError:
                self._flag_expired()  # persiste no MySQL antes de re-raise
                raise
        return creds

    def _flag_expired(self) -> None:
        """Marca destination_channels.oauth_expired_flag=TRUE para o slug atual.

        Best-effort: se channel_slug for None (uso legado), silenciosamente skip.
        Se a conexão MySQL falhar, log e continua (não substitui a exceção RefreshError).
        """
        if not getattr(self, 'channel_slug', None):
            return
        try:
            conn = db_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE destination_channels SET oauth_expired_flag = TRUE WHERE slug = %s',
                        (self.channel_slug,),
                    )
                    conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # pragma: no cover — defensive
            import logging
            logging.getLogger(__name__).warning('Falha ao marcar oauth_expired_flag: %s', exc)

    def _clear_expired(self) -> None:
        """Self-healing: reseta oauth_expired_flag=FALSE após upload bem-sucedido."""
        if not getattr(self, 'channel_slug', None):
            return
        try:
            conn = db_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE destination_channels SET oauth_expired_flag = FALSE WHERE slug = %s',
                        (self.channel_slug,),
                    )
                    conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # pragma: no cover
            import logging
            logging.getLogger(__name__).warning('Falha ao limpar oauth_expired_flag: %s', exc)

    def _get_service(self):
        if self._service is not None:
            return self._service

        creds = self._load_credentials()
        if self._youtube_factory is not None:
            self._service = self._youtube_factory(creds)
            return self._service

        if self._service_factory is None:
            from googleapiclient.discovery import build
            self._service_factory = build

        self._service = self._service_factory('youtube', 'v3', credentials=creds)
        return self._service

    def _execute_resumable(self, request) -> dict:
        if hasattr(request, 'next_chunk'):
            response = None
            while response is None:
                _, response = request.next_chunk()
            return response
        return request.execute()

    def _build_video_body(self, clip: dict) -> dict:
        return {
            'snippet': {
                'title': str(clip.get('title'))[:100],
                'description': str(clip.get('description') or ''),
                'tags': self._parse_tags(clip.get('tags')),
                'categoryId': '17',
            },
            'status': {
                'privacyStatus': os.environ.get('YOUTUBE_PRIVACY_STATUS', 'private'),
                'selfDeclaredMadeForKids': False,
            },
        }

    def _parse_tags(self, tags) -> list[str]:
        if tags is None:
            return []
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        return [str(tag).strip() for tag in tags if str(tag).strip()]
