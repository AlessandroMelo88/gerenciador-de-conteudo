#!/usr/bin/env python3
"""Run one pipeline stage from the repository host using the root .env file."""

from __future__ import annotations

import argparse
import fcntl
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLIP_PROCESSOR_DIR = PROJECT_ROOT / 'clip-processor'
STAGES = ('poll', 'download', 'ai', 'render', 'publish', 'maintenance')


def _load_env() -> None:
    try:
        from dotenv import dotenv_values
    except ImportError as exc:
        raise RuntimeError(
            'python-dotenv não está instalado; execute scripts/install_native_worker.sh'
        ) from exc

    env_file = PROJECT_ROOT / '.env'
    if not env_file.is_file():
        raise RuntimeError('Arquivo .env não encontrado; copie .env.native.example para .env')
    for key, value in dotenv_values(env_file).items():
        if value is not None:
            os.environ.setdefault(key, value)


def _resolve_path(name: str, default: Path, container_default: str | None = None) -> str:
    value = os.environ.get(name)
    if not value or (container_default and value == container_default):
        path = default
    else:
        path = Path(os.path.expandvars(os.path.expanduser(value)))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
    resolved = str(path.resolve())
    os.environ[name] = resolved
    return resolved


def _configure_native_environment() -> Path:
    default_videos = PROJECT_ROOT / 'var' / 'videos'
    default_youtube = PROJECT_ROOT / 'youtube'
    videos_dir = _resolve_path('VIDEOS_DIR', default_videos, '/app/videos')
    assets_dir = _resolve_path('ASSETS_DIR', PROJECT_ROOT / 'assets', '/app/assets')
    branding_dir = _resolve_path('BRANDING_DIR', PROJECT_ROOT / 'branding', '/app/branding')
    youtube_dir = _resolve_path('YOUTUBE_DIR', default_youtube, '/app/youtube')

    secrets_file = os.environ.get('YOUTUBE_CLIENT_SECRETS')
    if not secrets_file or secrets_file == '/app/youtube/client_secret.json':
        secrets_file = str(Path(youtube_dir) / 'client_secret.json')
    elif not Path(secrets_file).is_absolute():
        secrets_file = str((PROJECT_ROOT / secrets_file).resolve())
    os.environ['YOUTUBE_CLIENT_SECRETS'] = str(Path(secrets_file).expanduser().resolve())

    cookies_file = os.environ.get('YOUTUBE_COOKIES_FILE')
    if not cookies_file or cookies_file == '/app/youtube/cookies.txt':
        cookies_file = str(Path(youtube_dir) / 'cookies.txt')
    elif not Path(cookies_file).is_absolute():
        cookies_file = str((PROJECT_ROOT / cookies_file).resolve())
    os.environ['YOUTUBE_COOKIES_FILE'] = str(Path(cookies_file).expanduser().resolve())

    if os.environ.get('POSTGRES_HOST') in (None, '', 'postgres'):
        os.environ['POSTGRES_HOST'] = os.environ.get('NATIVE_POSTGRES_HOST', '127.0.0.1')
    if os.environ.get('REDIS_HOST') in (None, '', 'redis'):
        os.environ['REDIS_HOST'] = os.environ.get('NATIVE_REDIS_HOST', '127.0.0.1')

    os.environ['PYTHONPATH'] = os.pathsep.join(
        part for part in (str(CLIP_PROCESSOR_DIR), os.environ.get('PYTHONPATH', '')) if part
    )
    path_entries = [
        str(CLIP_PROCESSOR_DIR / '.venv' / 'bin'),
        '/opt/homebrew/bin',
        '/opt/homebrew/sbin',
        '/usr/local/bin',
        '/usr/local/sbin',
        os.environ.get('PATH', ''),
    ]
    os.environ['PATH'] = os.pathsep.join(dict.fromkeys(part for part in path_entries if part))
    for directory in (videos_dir, assets_dir, branding_dir, youtube_dir):
        Path(directory).mkdir(parents=True, exist_ok=True)
    runtime_dir = _resolve_path(
        'NATIVE_WORKER_RUNTIME_DIR', PROJECT_ROOT / 'var' / 'native-worker'
    )
    return Path(runtime_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=STAGES, required=True)
    args = parser.parse_args()

    try:
        _load_env()
        runtime_dir = _configure_native_environment()
    except (RuntimeError, OSError) as exc:
        print(f'[NATIVE WORKER] {exc}', file=sys.stderr, flush=True)
        return 2

    lock_dir = runtime_dir / 'locks'
    log_dir = runtime_dir / 'logs'
    lock_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f'{args.stage}.lock'
    with lock_path.open('a+') as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f'[NATIVE WORKER:{args.stage}] outra execução ainda está ativa; ignorando', flush=True)
            return 0

        command = [
            sys.executable,
            '-m',
            'src.worker',
            '--stage',
            args.stage,
            '--once',
        ]
        log_path = log_dir / f'{args.stage}.log'
        if log_path.exists() and log_path.stat().st_size >= 10 * 1024 * 1024:
            for index in (3, 2, 1):
                old_path = log_path.with_suffix(f'.log.{index}')
                if index == 3 and old_path.exists():
                    old_path.unlink()
                elif old_path.exists():
                    old_path.replace(log_path.with_suffix(f'.log.{index + 1}'))
            log_path.replace(log_path.with_suffix('.log.1'))

        with log_path.open('a', encoding='utf-8') as log_file:
            log_file.write(f'\n[NATIVE WORKER:{args.stage}] início\n')
            log_file.flush()
            completed = subprocess.run(
                command,
                cwd=CLIP_PROCESSOR_DIR,
                env=os.environ.copy(),
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            log_file.write(
                f'[NATIVE WORKER:{args.stage}] fim; exit_code={completed.returncode}\n'
            )
        return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())
