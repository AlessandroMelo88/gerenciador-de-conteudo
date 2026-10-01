"""Bug 11 — o container tem de honrar SIGTERM (`docker stop` sem virar exit 137).

Reproduz com um processo de verdade: o daemon roda um job longo (um corte de
FFmpeg, por exemplo) numa thread do pool do APScheduler, recebe SIGTERM e precisa
sair dentro do prazo de graça do Docker.

Causa apurada em 01/10/2026: o handler chamava `scheduler.shutdown()` dentro do
sinal, na mesma thread que executa `scheduler.start()`. O shutdown apagava os
jobs no meio de `_process_jobs` (JobLookupError) e, pior, a thread do pool com o
job em curso não é daemon — o interpretador espera por ela no encerramento.
"""
import os
import signal
import subprocess
import sys
import textwrap
import time

import pytest

pytest.importorskip('flask')
pytest.importorskip('apscheduler')

CLIP_PROCESSOR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DRIVER = textwrap.dedent('''
    import sys, time
    import src.main as m

    for job in list(m.scheduler.get_jobs()):
        job.remove()

    def job_longo():
        print("JOB_INICIO", flush=True)
        time.sleep(120)

    m.scheduler.add_job(job_longo, "interval", seconds=1, max_instances=1)
    m.install_signal_handlers()
    print("PRONTO", flush=True)
    m.run_scheduler_until_stopped()
    print("FIM", flush=True)
''')


def _sobe_daemon(grace='2', job_longo=True):
    env = dict(os.environ, SHUTDOWN_GRACE_SECONDS=grace, PYTHONUNBUFFERED='1')
    driver = DRIVER if job_longo else DRIVER.replace('time.sleep(120)', 'pass')
    proc = subprocess.Popen(
        [sys.executable, '-c', driver],
        cwd=CLIP_PROCESSOR_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc


def _espera_linha(proc, marcador, timeout=20):
    limite = time.time() + timeout
    while time.time() < limite:
        linha = proc.stdout.readline()
        if marcador in linha:
            return
        if not linha and proc.poll() is not None:
            break
    proc.kill()
    raise AssertionError(f'marcador {marcador!r} não apareceu')


@pytest.mark.skipif(sys.platform == 'win32', reason='SIGTERM POSIX')
class TestSigtermShutdown:
    def test_sigterm_com_job_em_curso_sai_dentro_do_prazo_com_codigo_zero(self):
        proc = _sobe_daemon(grace='2')
        try:
            _espera_linha(proc, 'PRONTO')
            _espera_linha(proc, 'JOB_INICIO')

            inicio = time.time()
            proc.send_signal(signal.SIGTERM)
            codigo = proc.wait(timeout=15)
            duracao = time.time() - inicio
        finally:
            if proc.poll() is None:
                proc.kill()

        assert codigo == 0
        assert duracao < 8

    def test_sigterm_sem_job_em_curso_sai_limpo_e_imediato(self):
        proc = _sobe_daemon(grace='5', job_longo=False)
        try:
            _espera_linha(proc, 'PRONTO')
            time.sleep(1.5)

            inicio = time.time()
            proc.send_signal(signal.SIGTERM)
            codigo = proc.wait(timeout=15)
            duracao = time.time() - inicio
            saida = proc.stdout.read()
        finally:
            if proc.poll() is None:
                proc.kill()

        assert codigo == 0
        assert duracao < 4
        assert 'FIM' in saida
        assert 'Traceback' not in saida


class TestHandlerSoSinaliza:
    def test_handler_nao_chama_scheduler_shutdown_dentro_do_sinal(self):
        import src.main as m
        from unittest.mock import patch

        m._stop_event.clear()
        try:
            with patch.object(m.scheduler, 'shutdown') as shutdown:
                m.shutdown(signal.SIGTERM, None)
            shutdown.assert_not_called()
            assert m._stop_event.is_set()
        finally:
            m._stop_event.clear()
