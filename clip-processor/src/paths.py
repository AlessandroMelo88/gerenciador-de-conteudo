"""Paths shared by Docker workers and direct Linux/macOS workers."""

from __future__ import annotations

import os
from pathlib import Path


def configured_path(name: str, default: str) -> str:
    """Return an expanded absolute path from an environment setting."""
    value = os.path.expandvars(os.path.expanduser(os.environ.get(name, default)))
    return str(Path(value).resolve())


VIDEOS_DIR = configured_path('VIDEOS_DIR', '/app/videos')
YOUTUBE_DIR = configured_path('YOUTUBE_DIR', '/app/youtube')
BRANDING_DIR = configured_path('BRANDING_DIR', '/app/branding')
YOUTUBE_CLIENT_SECRETS = configured_path(
    'YOUTUBE_CLIENT_SECRETS', os.path.join(YOUTUBE_DIR, 'client_secret.json')
)
YOUTUBE_COOKIES_FILE = configured_path(
    'YOUTUBE_COOKIES_FILE', os.path.join(YOUTUBE_DIR, 'cookies.txt')
)


def resolve_stored_video_path(value: object) -> str | None:
    """Map paths saved by Docker workers to the configured host video directory."""
    if not value:
        return None
    path = Path(os.fspath(value)).expanduser()
    try:
        relative = path.relative_to('/app/videos')
    except ValueError:
        return str(path)
    return str((Path(VIDEOS_DIR) / relative).resolve())
