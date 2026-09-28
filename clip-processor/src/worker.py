"""Workers independentes das etapas do pipeline do Canal de Cortes.

O deployment roda uma instância por etapa:

    poll -> download -> ai -> render -> publish

Cada processo abre a própria conexão, usa uma trava Redis específica da etapa
e só compartilha PostgreSQL/``/app/videos``. Assim o render pesado não bloqueia
descoberta, download ou publicação. O argumento ``--stage`` também deixa o
mesmo binário pronto para uma futura escala horizontal controlada.
"""

from __future__ import annotations

import argparse
import os
import signal
import time
import uuid
from datetime import datetime
from threading import Event

import redis

from src.db import (
    get_db_connection,
    recover_cutting_on_boot,
    recover_stuck_downloads,
    recover_stuck_publishing,
    recover_stuck_selecting,
    recover_stuck_transcribing,
)
from src.pipeline_runner import _download_pending_videos
from src.publisher import publish_pending_clips
from src.rss_poller import (
    poll_sources_only,
    process_downloaded_videos,
    process_pending_clips,
)
from src.ttl_worker import run_ttl_once

STAGES = ('poll', 'download', 'ai', 'render', 'publish', 'maintenance')
DEFAULT_INTERVALS = {
    'poll': 1200,
    'download': 30,
    'ai': 10,
    'render': 10,
    'publish': 600,
    'maintenance': 1800,
}
LOCK_TTL_SECONDS = int(os.environ.get('WORKER_LOCK_TTL_SECONDS', '7200'))
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
STOP = Event()


def _log(stage: str, message: str) -> None:
    print(
        f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [WORKER:{stage}] {message}',
        flush=True,
    )


def pipeline_enabled() -> bool:
    return os.environ.get('PIPELINE_ENABLED', 'true').strip().lower() in {
        '1',
        'true',
        'yes',
        'on',
    }


def _redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def _acquire_stage_lock(client, stage: str) -> tuple[str, str] | None:
    key = f'lock:pipeline_stage:{stage}'
    token = uuid.uuid4().hex
    try:
        if client.set(key, token, nx=True, ex=LOCK_TTL_SECONDS):
            return key, token
    except Exception as exc:
        _log(stage, f'Aviso: Redis indisponível para lock ({exc}); seguindo com DB')
        # Chave vazia é o sentinel "sem Redis". Não confundir com None, que
        # significa que outra instância já possui o lock.
        return '', ''
    return None


def _release_stage_lock(client, lock: tuple[str, str] | None) -> None:
    if not lock:
        return
    key, token = lock
    if not key:
        return
    try:
        client.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then "
            "return redis.call('del', KEYS[1]) else return 0 end",
            1,
            key,
            token,
        )
    except Exception:
        # O TTL protege contra lock órfão; nunca apagar lock de outro worker.
        pass


def _run_maintenance(conn, redis_client) -> None:
    recover_stuck_downloads(conn)
    recover_stuck_transcribing(conn)
    recover_stuck_selecting(conn)
    recover_stuck_publishing(conn)
    run_ttl_once(conn=conn, redis_client=redis_client)


def run_stage_once(stage: str) -> None:
    """Executa uma rodada da etapa informada; erros não derrubam o loop."""
    if stage != 'maintenance' and not pipeline_enabled():
        _log(stage, 'Pausado por PIPELINE_ENABLED=false')
        return

    conn = None
    redis_client = None
    lock = None
    try:
        conn = get_db_connection()
        redis_client = _redis_client()
        lock = _acquire_stage_lock(redis_client, stage)
        if lock is None:
            _log(stage, 'Outra instância já está executando esta etapa — pulando')
            return

        if stage == 'poll':
            poll_sources_only(db_conn=conn, redis_client=redis_client)
        elif stage == 'download':
            _download_pending_videos(conn)
        elif stage == 'ai':
            process_downloaded_videos(conn)
        elif stage == 'render':
            process_pending_clips(conn)
        elif stage == 'publish':
            published = publish_pending_clips(conn, redis_client)
            _log(stage, f'Rodada finalizada: {published} publicado(s)')
        elif stage == 'maintenance':
            _run_maintenance(conn, redis_client)
        else:  # pragma: no cover - argparse filtra
            raise ValueError(f'Etapa desconhecida: {stage}')
    except Exception as exc:
        _log(stage, f'ERRO na rodada: {exc}')
    finally:
        _release_stage_lock(redis_client, lock)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _shutdown(signum, frame) -> None:
    _log('system', f'Recebendo sinal {signum} — encerrando worker')
    STOP.set()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=STAGES, default=os.environ.get('WORKER_STAGE', 'poll'))
    parser.add_argument(
        '--interval',
        type=int,
        default=int(os.environ.get('WORKER_INTERVAL_SECONDS', '0')),
        help='intervalo entre rodadas; 0 usa o padrão da etapa',
    )
    args = parser.parse_args()
    interval = max(1, args.interval or DEFAULT_INTERVALS[args.stage])

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    _log(args.stage, f'Iniciado — intervalo={interval}s; lock_ttl={LOCK_TTL_SECONDS}s')

    if args.stage == 'render':
        conn = None
        try:
            conn = get_db_connection()
            recover_cutting_on_boot(conn)
        except Exception as exc:
            _log(args.stage, f'Aviso: recovery de cutting no boot falhou — {exc}')
        finally:
            if conn is not None:
                conn.close()

    while not STOP.is_set():
        started = time.monotonic()
        run_stage_once(args.stage)
        elapsed = time.monotonic() - started
        _log(args.stage, f'Próxima rodada em {interval}s (duração={elapsed:.1f}s)')
        STOP.wait(interval)


if __name__ == '__main__':
    main()
