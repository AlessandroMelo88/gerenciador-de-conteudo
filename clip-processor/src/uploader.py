"""
uploader.py — Upload de clips para YouTube Data API v3.

Exporta:
  - YouTubeUploader.upload_clip(clip) -> youtube_video_id
"""
from __future__ import annotations

import os
import sys
import time
import types
from pathlib import Path
from typing import Any

from src.db import get_db_connection as db_connect
from src.media_contract import validate_short_media

DEFAULT_TOKEN_FILE = '/app/youtube/token-futebol-em-cortes.json'
YOUTUBE_UPLOAD_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
]
CAPTION_LANGUAGE = 'pt-BR'
CAPTION_TRACK_NAME = 'Português (Brasil) — Legenda revisada'


class PostUploadError(RuntimeError):
    """Falha depois de o YouTube já ter criado o vídeo.

    O publisher persiste o ID e deixa o clip pendente para que o próximo ciclo
    retome a legenda/processamento sem enviar um vídeo duplicado.
    """

    def __init__(self, video_id: str, message: str):
        super().__init__(message)
        self.video_id = video_id


class CaptionNotReadyError(FileNotFoundError):
    """O clip precisa ser reprocessado antes de poder ser publicado."""


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _http_status(exc: Exception) -> int | None:
    status = getattr(getattr(exc, 'resp', None), 'status', None)
    return int(status) if status is not None else None


class _CredentialsFallback:  # pragma: no cover - local tests without optional deps
    @classmethod
    def from_authorized_user_file(cls, *args, **kwargs):
        raise ModuleNotFoundError('google')


Credentials: Any
try:
    from google.oauth2.credentials import Credentials as _GoogleCredentials
except ModuleNotFoundError:
    Credentials = _CredentialsFallback
else:
    Credentials = _GoogleCredentials


class _MediaFileUploadFallback:  # pragma: no cover - local tests without optional deps
    def __init__(self, path, **kwargs):
        self.path = path
        self.kwargs = kwargs


MediaFileUpload: Any
try:
    from googleapiclient.http import MediaFileUpload as _GoogleMediaFileUpload
except ModuleNotFoundError:
    MediaFileUpload = _MediaFileUploadFallback
else:
    MediaFileUpload = _GoogleMediaFileUpload


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

    # ModuleType is populated dynamically so tests can import the optional SDK.
    errors_module.__dict__['HttpError'] = HttpError
    googleapiclient_module.__dict__['errors'] = errors_module
    sys.modules.setdefault('googleapiclient', googleapiclient_module)
    sys.modules.setdefault('googleapiclient.errors', errors_module)


class _RefreshErrorFallback(Exception):  # pragma: no cover - local tests without optional deps
    pass


RefreshError: Any
try:
    from google.auth.exceptions import RefreshError as _GoogleRefreshError
except ModuleNotFoundError:
    RefreshError = _RefreshErrorFallback
else:
    RefreshError = _GoogleRefreshError


class YouTubeUploader:
    """Publica vídeo, legenda oficial, thumbnail e visibilidade final."""

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
        if clip.get('format') == 'curto':
            validate_short_media(clip_path)
        thumbnail_path = clip.get('thumbnail_path')
        if thumbnail_path and not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f'Arquivo de thumbnail não encontrado: {thumbnail_path}')
        caption_path = self._resolve_caption_path(clip, clip_path)
        target_privacy = self._privacy_status()
        quality_gate = self._quality_gate_enabled(clip)
        existing_video_id = clip.get('youtube_video_id')

        service = self._get_service()
        initial_privacy = (
            'private'
            if target_privacy != 'private' and (caption_path or quality_gate)
            else target_privacy
        )

        video_id: str | None = None
        if existing_video_id:
            video_id = str(existing_video_id)
            print(f'[YT] Retomando vídeo já criado: {video_id}', flush=True)
        else:
            body = self._build_video_body(clip, privacy_status=initial_privacy)
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

        try:
            if caption_path:
                self._upload_official_caption(service, video_id, caption_path)

            if quality_gate:
                self._wait_for_processing(service, video_id)

            if target_privacy != initial_privacy:
                self._set_privacy(service, video_id, target_privacy)
        except PostUploadError:
            raise
        except Exception as exc:
            raise PostUploadError(
                video_id,
                f'Falha ao finalizar publicação do vídeo {video_id}: {exc}',
            ) from exc

        # Mantém a compatibilidade do fluxo existente: falhas que não sejam
        # 403 na thumbnail continuam sendo propagadas ao chamador. Legenda e
        # processamento, que podem deixar um upload parcial, já foram
        # concluídos acima com retomada idempotente.
        if thumbnail_path:
            self._upload_thumbnail(service, video_id, thumbnail_path)

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

    def _privacy_status(self) -> str:
        privacy_status = os.environ.get('YOUTUBE_PRIVACY_STATUS', 'public').strip().lower()
        if privacy_status not in {'private', 'unlisted', 'public'}:
            raise ValueError(f'YOUTUBE_PRIVACY_STATUS inválido: {privacy_status}')
        return privacy_status

    def _resolve_caption_path(self, clip: dict, clip_path: str) -> str | None:
        """Localiza o SRT produzido junto do MP4 de produção."""
        caption_path = clip.get('subtitle_path')
        if not caption_path and clip.get('format') in {'curto', 'longo'}:
            caption_path = str(Path(clip_path).with_suffix('.srt'))
        if not caption_path:
            return None
        if not os.path.isfile(caption_path):
            raise CaptionNotReadyError(f'Arquivo de legenda não encontrado: {caption_path}')
        if os.path.getsize(caption_path) == 0:
            raise CaptionNotReadyError(f'Arquivo de legenda vazio: {caption_path}')
        return str(caption_path)

    def _quality_gate_enabled(self, clip: dict) -> bool:
        """Aplica a espera HD apenas a registros reais do pipeline."""
        return clip.get('format') in {'curto', 'longo'} and _env_bool('YOUTUBE_WAIT_FOR_HD', True)

    def _upload_thumbnail(self, service, video_id: str, thumbnail_path: str) -> None:
        thumb_media = self._media_upload_factory(
            thumbnail_path,
            chunksize=-1,
            resumable=True,
        )
        try:
            service.thumbnails().set(
                videoId=video_id,
                media_body=thumb_media,
            ).execute()
        except Exception as exc:
            # Canais sem verificação suficiente podem receber 403 somente na
            # thumbnail; isso não deve transformar um upload concluído em
            # retry/duplicata.
            if _http_status(exc) == 403:
                print(
                    f'[YT] Aviso: thumbnail recusada para {video_id}; vídeo mantido como publicado',
                    flush=True,
                )
                return
            raise

    def _caption_body(self, video_id: str) -> dict:
        return {
            'snippet': {
                'videoId': video_id,
                'language': CAPTION_LANGUAGE,
                'name': CAPTION_TRACK_NAME,
                'isDraft': False,
            }
        }

    def _caption_media(self, caption_path: str):
        return self._media_upload_factory(
            caption_path,
            chunksize=-1,
            resumable=False,
            mimetype='application/octet-stream',
        )

    def _upload_official_caption(self, service, video_id: str, caption_path: str) -> None:
        """Cria ou atualiza a faixa pt-BR revisada, de forma idempotente."""
        try:
            service.captions().insert(
                part='snippet',
                body=self._caption_body(video_id),
                media_body=self._caption_media(caption_path),
                sync=False,
            ).execute()
            print(f'[YT] Legenda oficial enviada para {video_id}', flush=True)
            return
        except Exception as exc:
            if _http_status(exc) != 409:
                raise

        response = service.captions().list(part='snippet', videoId=video_id).execute() or {}
        tracks = response.get('items', [])
        existing = next(
            (
                item
                for item in tracks
                if item.get('snippet', {}).get('language') == CAPTION_LANGUAGE
                and item.get('snippet', {}).get('name') == CAPTION_TRACK_NAME
            ),
            None,
        )
        if not existing or not existing.get('id'):
            raise RuntimeError(
                f'Conflito ao criar legenda pt-BR de {video_id}, mas a faixa existente '
                'não foi localizada'
            )

        service.captions().update(
            part='id',
            body={'id': existing['id']},
            media_body=self._caption_media(caption_path),
            sync=False,
        ).execute()
        print(f'[YT] Legenda oficial atualizada para {video_id}', flush=True)

    def _wait_for_processing(self, service, video_id: str) -> None:
        """Aguarda o YouTube concluir o processamento antes de tornar público."""
        try:
            timeout = max(float(os.environ.get('YOUTUBE_PROCESSING_TIMEOUT_SECONDS', '900')), 0)
        except ValueError:
            timeout = 900.0
        try:
            poll_seconds = max(float(os.environ.get('YOUTUBE_PROCESSING_POLL_SECONDS', '10')), 1)
        except ValueError:
            poll_seconds = 10.0

        deadline = time.monotonic() + timeout
        while True:
            response = (
                service.videos()
                .list(
                    part='processingDetails,status',
                    id=video_id,
                )
                .execute()
                or {}
            )
            items = response.get('items', [])
            if not items:
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        f'YouTube não encontrou o vídeo {video_id} durante o processamento'
                    )
                time.sleep(min(poll_seconds, max(deadline - time.monotonic(), 0.1)))
                continue

            processing_status = (items[0].get('processingDetails') or {}).get('processingStatus')
            if processing_status == 'succeeded':
                print(f'[YT] Processamento HD concluído para {video_id}', flush=True)
                return
            if processing_status in {'failed', 'terminated'}:
                raise RuntimeError(
                    f'Processamento do vídeo {video_id} terminou com status {processing_status}'
                )
            if time.monotonic() >= deadline:
                raise TimeoutError(f'Processamento HD do vídeo {video_id} excedeu {timeout:.0f}s')

            time.sleep(min(poll_seconds, max(deadline - time.monotonic(), 0.1)))

    def _set_privacy(self, service, video_id: str, privacy_status: str) -> None:
        service.videos().update(
            part='status',
            body={
                'id': video_id,
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False,
                },
            },
        ).execute()
        print(f'[YT] Visibilidade final de {video_id}: {privacy_status}', flush=True)

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
                self._flag_expired()  # persiste no PostgreSQL antes de re-raise
                raise
        return creds

    def _flag_expired(self) -> None:
        """Marca destination_channels.oauth_expired_flag=TRUE para o slug atual.

        Best-effort: se channel_slug for None (uso legado), silenciosamente skip.
        Se a conexão PostgreSQL falhar, log e continua (não substitui a exceção RefreshError).
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

    def _resolve_category_id(self, clip: dict) -> str:
        """Resolve a categoria do YouTube com base no nicho (28 = Ciência e Tecnologia)."""
        niche = str(
            clip.get('destination_niche') or clip.get('target_niche') or clip.get('niche') or ''
        ).lower()
        if any(k in niche for k in ('futebol', 'sport', 'esporte')):
            return '17'
        if any(k in niche for k in ('podcast', 'entrevista', 'humor')):
            return '24'
        # Default para canais de tecnologia, IA, Linux, programação (Hacker Libertário)
        return '28'

    def _build_video_body(self, clip: dict, privacy_status: str | None = None) -> dict:
        if privacy_status is None:
            privacy_status = self._privacy_status()
        return {
            'snippet': {
                'title': str(clip.get('title'))[:100],
                'description': str(clip.get('description') or ''),
                'tags': self._parse_tags(clip.get('tags')),
                'categoryId': self._resolve_category_id(clip),
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False,
            },
        }

    def _parse_tags(self, tags) -> list[str]:
        if tags is None:
            return []
        if isinstance(tags, str):
            raw_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        else:
            raw_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
        valid_tags = []
        total_len = 0
        for tag in raw_tags:
            cleaned = tag.replace('<', '').replace('>', '').strip()
            if not cleaned:
                continue
            if total_len + len(cleaned) + 1 > 400:
                break
            valid_tags.append(cleaned)
            total_len += len(cleaned) + 1
        return valid_tags
