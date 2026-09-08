# Canal de Cortes — clip-processor daemon
# Phase 5: Pipeline completo com publicação YouTube
import signal
import os
import threading
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
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

from src.pipeline_runner import run_pipeline_once, run_publish_only, run_ingest_cycle
from src.db import get_db_connection, recover_stuck_downloads, recover_stuck_selecting
from src import ttl_worker
from src.ttl_worker import run_ttl_once
from src.watchdog import run_watchdog_cycle
from src.internal_api import app as _internal_app

SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if sentry_sdk and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=os.environ.get('APP_ENV', 'production'),
    )


def log(msg: str):
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}', flush=True)


def _start_internal_api():
    _internal_app.run(host='0.0.0.0', port=8090, use_reloader=False, debug=False)


def run_recovery_once():
    """Roda os recoveries de estado preso. Agendado, não só no boot.

    Enquanto isso existia apenas no bloco de startup, tudo que travasse depois
    do container subir ficava preso até o próximo restart — na prática, dias.
    Também cobre a janela do erro `Errno 111` (clip-processor sobe antes do
    MySQL): o recovery de boot morre no except e antes ninguém tentava de novo.

    Falha é logada e engolida de propósito — recovery é manutenção oportunista,
    não pode derrubar o scheduler.
    """
    conn = None
    try:
        conn = get_db_connection()
        recover_stuck_downloads(conn)
        recover_stuck_selecting(conn)
    except Exception as e:
        log(f'[ACQU] Aviso: recovery periódico falhou — {e}')
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def run_watchdog_once():
    """Executa o ciclo de integridade e auto-cura do Watchdog."""
    conn = None
    try:
        conn = get_db_connection()
        run_watchdog_cycle(conn)
    except Exception as e:
        log(f'[WATCHDOG] Falha no ciclo periódico: {e}')
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


scheduler = BlockingScheduler(timezone='America/Sao_Paulo')


def shutdown(signum, frame):
    log('[ACQU] Recebendo sinal de shutdown — encerrando scheduler')
    scheduler.shutdown(wait=False)


# Ingestão (RSS/download/AI): repõe a janela de download ativo (DOWNLOAD_WINDOW_*
# em pipeline_runner.py) a cada 20min — substitui o antigo ciclo de 6h. Cadência
# maior faz vaga aberta (vídeo excluído no painel, ou publicação concluída) ser
# reposta rápido, em vez de esperar até 6h pelo próximo vídeo.
scheduler.add_job(
    run_ingest_cycle,
    'interval',
    minutes=20,
    id='ingest_cycle',
    coalesce=True,
    max_instances=1,
    misfire_grace_time=900,
)

# Publica clips já aprovados isoladamente, mesma cadência do ingest — evita
# represar a fila esperando quando a cota diária reseta ou libera espaço.
scheduler.add_job(
    run_publish_only,
    'interval',
    minutes=20,
    id='publish_cycle',
    coalesce=True,
    max_instances=1,
    misfire_grace_time=900,
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
    misfire_grace_time=900,
)

# Recovery de estados presos a cada 30min. Cadência menor que
# SELECTING_STUCK_HOURS (2h) pra pegar o travamento logo depois de ele passar do
# limite, em vez de esperar o próximo restart do container.
scheduler.add_job(
    run_recovery_once,
    'interval',
    minutes=30,
    id='state_recovery',
    coalesce=True,
    max_instances=1,
    misfire_grace_time=900,
)

# Watchdog de integridade e auto-cura: roda a cada 30min
scheduler.add_job(
    run_watchdog_once,
    'interval',
    minutes=30,
    id='watchdog_health',
    coalesce=True,
    max_instances=1,
    misfire_grace_time=900,
)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

if __name__ == '__main__':
    log('[ACQU] Daemon iniciado — ingestão + publish a cada 20 minutos')
    log(f'[ACQU] MYSQL_HOST: {os.environ.get("MYSQL_HOST", "não configurado")}')
    log(f'[ACQU] REDIS_HOST: {os.environ.get("REDIS_HOST", "não configurado")}')
    log(f'[ACQU] YOUTUBE_PRIVACY_STATUS: {os.environ.get("YOUTUBE_PRIVACY_STATUS", "private")}')
    log(f'[ACQU] MAX_UPLOADS_PER_DAY: {os.environ.get("MAX_UPLOADS_PER_DAY", "2")}')
    log(f'[BOOT] TTL worker agendado: a cada 1h (TTL={ttl_worker.TTL_HOURS}h, WARN={ttl_worker.WARN_HOURS}h)')
    log('[BOOT] Watchdog agendado: a cada 30min (auto-cura de fantasmas e monitor de janela)')

    # Recovery: vídeos presos em 'downloading' voltam para 'pending' e os
    # presos em 'selecting' voltam para 'downloaded' (senão seguram slot da
    # janela de download pra sempre e o pipeline para de baixar).
    run_recovery_once()

    # Watchdog inicial: auto-cura clipes fantasmas e valida saúde do disco/OAuth
    run_watchdog_once()

    # Sidecar HTTP interno consumido pelo painel Laravel (Phase 8).
    # Thread daemon → morre com o processo principal. Iniciado ANTES do ciclo
    # inicial do pipeline (que pode levar minutos) para que o painel tenha o
    # sidecar disponível imediatamente após o boot, sem depender do ciclo.
    threading.Thread(target=_start_internal_api, daemon=True, name='internal-api').start()
    log('[ACQU] Sidecar HTTP interno iniciado em 0.0.0.0:8090 (thread daemon)')

    # Executar imediatamente na inicialização (não esperar o primeiro tick de 20min)
    log('[ACQU] Executando ciclo inicial...')
    run_pipeline_once()

    log('[ACQU] Scheduler iniciado — próximo ciclo (ingest + publish) em 20 minutos')
    scheduler.start()
