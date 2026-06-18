# Canal de Cortes — clip-processor daemon
# Phase 2: Aquisição de Vídeos
import signal
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from src.rss_poller import poll_all_channels
from src.db import get_db_connection, recover_stuck_downloads

def log(msg: str):
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}', flush=True)

scheduler = BlockingScheduler(timezone='America/Sao_Paulo')

def shutdown(signum, frame):
    log('[ACQU] Recebendo sinal de shutdown — encerrando scheduler')
    scheduler.shutdown(wait=False)

scheduler.add_job(
    poll_all_channels,
    'interval',
    hours=6,
    id='poll_rss',
    coalesce=True,
    max_instances=1,
    misfire_grace_time=300
)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

if __name__ == '__main__':
    log('[ACQU] Daemon iniciado — poll RSS a cada 6 horas')
    log(f'[ACQU] MYSQL_HOST: {os.environ.get("MYSQL_HOST", "não configurado")}')
    log(f'[ACQU] REDIS_HOST: {os.environ.get("REDIS_HOST", "não configurado")}')

    # Recovery: vídeos presos em 'downloading' voltam para 'pending'
    try:
        conn = get_db_connection()
        recover_stuck_downloads(conn)
        conn.close()
    except Exception as e:
        log(f'[ACQU] Aviso: recovery on startup falhou — {e}')

    # Executar imediatamente na inicialização (não esperar 6h)
    log('[ACQU] Executando poll inicial...')
    poll_all_channels()

    log('[ACQU] Scheduler iniciado — próximo poll em 6 horas')
    scheduler.start()
