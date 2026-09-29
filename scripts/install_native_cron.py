#!/usr/bin/env python3
"""Install or remove this project's host-native worker cron entries."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '# BEGIN gerenciador-de-conteudo native workers'
END = '# END gerenciador-de-conteudo native workers'


def _worker_lines() -> list[str]:
    python = ROOT / 'clip-processor' / '.venv' / 'bin' / 'python'
    runner = ROOT / 'scripts' / 'run_native_worker.py'
    root_q, python_q, runner_q = map(shlex.quote, (str(ROOT), str(python), str(runner)))
    lines = []
    for stage, schedule in (
        ('poll', '*/20 * * * *'),
        ('download', '*/15 * * * *'),
        ('ai', '*/15 * * * *'),
        ('render', '*/15 * * * *'),
        ('maintenance', '*/30 * * * *'),
        # The publisher checks São Paulo time and permits long videos at 06/14/22,
        # Shorts at 12/20, with a maximum of one upload per channel in each slot.
        ('publish', '0 * * * *'),
    ):
        lines.append(f'{schedule} cd {root_q} && {python_q} {runner_q} --stage {stage}')
    return lines


def _read_crontab() -> list[str]:
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.splitlines()
    if 'no crontab' in result.stderr.lower():
        return []
    raise RuntimeError(result.stderr.strip() or 'Não foi possível ler o crontab atual')


def _without_project_block(lines: list[str]) -> list[str]:
    kept = []
    inside = False
    seen_begin = False
    for line in lines:
        if line == BEGIN:
            if inside or seen_begin:
                raise RuntimeError('Há marcadores de cron duplicados ou malformados; nada foi alterado')
            inside = True
            seen_begin = True
            continue
        if line == END:
            if not inside:
                raise RuntimeError('Marcador final de cron sem início; nada foi alterado')
            inside = False
            continue
        if not inside:
            kept.append(line)
    if inside:
        raise RuntimeError('Bloco de cron sem marcador final; nada foi alterado')
    return kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove', action='store_true', help='remove somente o bloco deste projeto')
    args = parser.parse_args()
    python = ROOT / 'clip-processor' / '.venv' / 'bin' / 'python'
    if not args.remove and (not (ROOT / '.env').is_file() or not python.is_file()):
        print('Execute scripts/install_native_worker.sh e configure .env primeiro.', file=sys.stderr)
        return 2

    try:
        existing = _without_project_block(_read_crontab())
        if not args.remove:
            existing.extend(['', BEGIN, *_worker_lines(), END])
        payload = '\n'.join(existing).rstrip() + ('\n' if existing else '')
        subprocess.run(['crontab', '-'], input=payload, text=True, check=True)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'Não foi possível atualizar o crontab: {exc}', file=sys.stderr)
        return 1

    action = 'removido' if args.remove else 'instalado'
    print(f'Bloco de cron {action}; as demais entradas foram preservadas.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
