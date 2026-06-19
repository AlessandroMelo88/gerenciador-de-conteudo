"""
uploader.py — Upload de clips para YouTube Data API v3.

Exporta:
  - YouTubeUploader.upload_clip(clip) -> youtube_video_id
"""
import os
import sys
import types
from pathlib import Path


DEFAULT_TOKEN_FILE = '/app/token.json'
YOUTUBE_UPLOAD_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
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


class YouTubeUploader:
    """Cliente fino para videos.insert + thumbnails.set."""

    def __init__(
        self,
        token_file: str | None = None,
        youtube_factory=None,
        service=None,
        service_factory=None,
        media_upload_factory=None,
    ):
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

        if thumbnail_path:
            thumb_media = self._media_upload_factory(
                thumbnail_path,
                chunksize=-1,
                resumable=True,
            )
            service.thumbnails().set(
                videoId=video_id,
                media_body=thumb_media,
            ).execute()

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

        creds = Credentials.from_authorized_user_file(str(token_path), YOUTUBE_UPLOAD_SCOPES)
        if getattr(creds, 'expired', False) and getattr(creds, 'refresh_token', None):
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        return creds

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
