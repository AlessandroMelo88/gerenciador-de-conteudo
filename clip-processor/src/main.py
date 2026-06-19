# Canal de Cortes — clip-processor daemon
# Phase 5: Pipeline completo com publicação YouTube
import signal
import os
from datetime import datetime
try:
    from apscheduler.schedulers.blocking import BlockingScheduler
except ModuleNotFoundError:
    class _FallbackJob:
        def __init__(self, id, coalesce, max_instances):
            self.id = id
            self.coalesce = coalesce
            self.max_instances = max_instances

    class BlockingScheduler:  # pragma: no cover - local test fallback
        def __init__(self, timezone=None):
            self.timezone = timezone
            self._jobs = []

        def add_job(self, func, trigger, **kwargs):
            self._jobs.append(_FallbackJob(
                kwargs.get('id'),
                kwargs.get('coalesce'),
                kwargs.get('max_instances'),
            ))

        def get_jobs(self):
            return self._jobs

        def shutdown(self, wait=False):
            return None

        def start(self):
            return None
from src.pipeline_runner import run_pipeline_once
from src.db import get_db_connection, recover_stuck_downloads
from src import ttl_worker
from src.ttl_worker import run_ttl_once


def log(msg: str):
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}', flush=True)


scheduler = BlockingScheduler(timezone='America/Sao_Paulo')


def shutdown(signum, frame):
    log('[ACQU] Recebendo sinal de shutdown — encerrando scheduler')
    scheduler.shutdown(wait=False)


scheduler.add_job(
    run_pipeline_once,
    'interval',
    hours=6,
    id='pipeline_cycle',
    coalesce=True,
    max_instances=1,
    misfire_grace_time=300,
)

# CTRL-05: TTL worker — auto-rejeita clips pending >TTL_HOURS e avisa em WARN_HOURS.
# Roda a cada 1h. next_run_time omitido → primeira execução em now + 1h
# (evita rodar TTL antes do banco estar quente após boot).
scheduler.add_job(
    run_ttl_once,
    'interval',
    hours=1,
    id='clip_pending_ttl',
    coalesce=True,
    max_instances=1,
    misfire_grace_time=300,
)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

if __name__ == '__main__':
    log('[ACQU] Daemon iniciado — ciclo completo a cada 6 horas')
    log(f'[ACQU] MYSQL_HOST: {os.environ.get("MYSQL_HOST", "não configurado")}')
    log(f'[ACQU] REDIS_HOST: {os.environ.get("REDIS_HOST", "não configurado")}')
    log(f'[ACQU] YOUTUBE_PRIVACY_STATUS: {os.environ.get("YOUTUBE_PRIVACY_STATUS", "private")}')
    log(f'[ACQU] MAX_UPLOADS_PER_DAY: {os.environ.get("MAX_UPLOADS_PER_DAY", "2")}')
    log(f'[BOOT] TTL worker agendado: a cada 1h (TTL={ttl_worker.TTL_HOURS}h, WARN={ttl_worker.WARN_HOURS}h)')

    # Recovery: vídeos presos em 'downloading' voltam para 'pending'
    try:
        conn = get_db_connection()
        recover_stuck_downloads(conn)
        conn.close()
    except Exception as e:
        log(f'[ACQU] Aviso: recovery on startup falhou — {e}')

    # Executar imediatamente na inicialização (não esperar 6h)
    log('[ACQU] Executando ciclo inicial...')
    run_pipeline_once()

    log('[ACQU] Scheduler iniciado — próximo ciclo em 6 horas')
    scheduler.start()
