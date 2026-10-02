"""
retention_backfill.py — carga retroativa da retenção (SPEC-001 R15).

Rodado À MÃO, uma vez, depois que os canais forem re-autorizados com o escopo
`yt-analytics.readonly`. Fica separado do job diário de propósito: carga histórica e operação têm
perfis de cota e de risco diferentes, e misturar as duas esconde qual delas estourou o teto.

    docker compose exec clip-processor python -m src.retention_backfill --dias 400
"""
import argparse
import sys

from src.retention_collector import run_retention_collection_once

DIAS_PADRAO = 400  # cobre o projeto inteiro (primeiro commit em 17/06/2026)


def main(argv=None, runner=run_retention_collection_once) -> int:
    parser = argparse.ArgumentParser(description='Carga retroativa da retenção por clip.')
    parser.add_argument('--dias', type=int, default=DIAS_PADRAO,
                        help=f'quantos dias para trás considerar (padrão: {DIAS_PADRAO})')
    args = parser.parse_args(argv)

    gravadas = runner(dias=args.dias)
    print(f'[RETENCAO] Backfill concluído: {gravadas} linha(s) gravadas em {args.dias} dias.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
