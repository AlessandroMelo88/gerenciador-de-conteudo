"""CLI: python -m affiliate_worker <comando>.

Comandos: search, import, copy, push, run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from affiliate_worker import copywriter
from affiliate_worker.api_client import ApiClient, ApiError
from affiliate_worker.models import MAX_BATCH, Offer, chunked
from affiliate_worker.sources import manual, mercadolivre
from affiliate_worker.storage import Storage, now_iso

ROOT = Path(__file__).resolve().parent.parent


def info(msg: str) -> None:
    print(msg, file=sys.stderr)


def warn(msg: str) -> None:
    print(f'AVISO: {msg}', file=sys.stderr)


def _label(offer: Offer) -> str:
    return f'[{offer.network}:{offer.external_id or "-"}] {(offer.title or "(sem título)")[:70]}'


# ---------------------------------------------------------------- comandos

def cmd_search(args, storage: Storage) -> int:
    if args.source != 'mercadolivre':
        info(f'fonte não suportada: {args.source}')
        return 2
    result = mercadolivre.search(args.query, args.niche, args.limit)
    if not result.ok:
        info(f'ERRO: {result.error}')
        return 1
    storage.save_candidates(result.candidates)
    info(f'{len(result.candidates)} candidatos gravados em {storage.candidates_path}')
    info('Candidatos NÃO têm affiliate_url. Gere o link no painel do Mercado Livre Afiliados, '
         f'preencha "affiliate_url" no arquivo e rode: import --file {storage.candidates_path}')
    return 0


def cmd_import(args, storage: Storage) -> int:
    try:
        offers = manual.load_file(args.file, default_niche=getattr(args, 'niche', None))
    except manual.OfferImportError as exc:
        info(f'ERRO: {exc}')
        return 1
    if not offers:
        warn('nenhuma oferta no arquivo')
        return 1
    for offer in offers:
        for w in offer.extra_warnings:
            warn(f'{_label(offer)}: {w}')
        errors = [e for e in offer.validate() if not e.startswith('affiliate_url ausente')]
        for e in errors:
            warn(f'{_label(offer)}: {e}')
        if not offer.has_affiliate_url():
            warn(f'{_label(offer)}: sem affiliate_url — fica fora do push até o link ser preenchido')
    added, updated = storage.merge_ready(offers)
    info(f'import: {added} novas, {updated} atualizadas em {storage.ready_path}')
    return 0


def cmd_copy(args, storage: Storage) -> int:
    offers = storage.load_ready()
    counts = {'anthropic': 0, 'groq': 0, 'template': 0}
    skipped_no_link = 0
    for offer in offers:
        if not offer.has_affiliate_url():
            skipped_no_link += 1
            continue
        used = copywriter.apply_copy(offer, provider=args.provider)
        if used:
            counts[used] += 1
            offer.pushed_at = None  # copy nova precisa ser reenviada
    storage.save_ready(offers)
    total = sum(counts.values())
    info(f'copy: {total} geradas (anthropic={counts["anthropic"]}, groq={counts["groq"]}, '
         f'template={counts["template"]})')
    if skipped_no_link:
        warn(f'{skipped_no_link} ofertas sem affiliate_url ignoradas')
    return 0


def select_pushable(offers: list[Offer], force: bool = False) -> tuple[list[Offer], list[tuple[Offer, list[str]]]]:
    """Separa ofertas prontas das bloqueadas (sem link ou inválidas). Já enviadas são puladas sem --force."""
    ready, blocked = [], []
    for offer in offers:
        if offer.pushed_at and not force:
            continue
        errors = offer.validate()
        if errors:
            blocked.append((offer, errors))
        else:
            ready.append(offer)
    return ready, blocked


def cmd_push(args, storage: Storage, client: ApiClient | None = None) -> int:
    offers = storage.load_ready()
    ready, blocked = select_pushable(offers, force=args.force)
    for offer, errors in blocked:
        if not offer.has_affiliate_url():
            warn(f'{_label(offer)}: SEM affiliate_url — fora do push (o worker não cria link)')
        else:
            warn(f'{_label(offer)}: inválida, fora do push: {"; ".join(errors)}')
    if not ready:
        info('push: nada a enviar')
        return 0 if not blocked else 1

    payloads = [o.to_payload() for o in ready]
    if args.dry_run:
        batches = chunked(payloads, MAX_BATCH)
        print(json.dumps([{'offers': b} for b in batches], ensure_ascii=False, indent=2))
        info(f'dry-run: {len(payloads)} ofertas em {len(batches)} lote(s); nada foi enviado')
        return 0

    if client is None:
        try:
            client = ApiClient(os.environ.get('AFFILIATE_API_URL', ''), os.environ.get('AFFILIATE_API_TOKEN', ''))
        except ApiError as exc:
            info(f'ERRO: {exc} (defina no affiliate-worker/.env)')
            return 1

    failed = 0

    def on_batch(result, batch_payload):
        nonlocal failed
        batch_offers = ready[result.index * MAX_BATCH: result.index * MAX_BATCH + result.size]
        if result.ok:
            body = result.body or {}
            info(f'lote {result.index + 1}: created={body.get("created")} updated={body.get("updated")} '
                 f'skipped={body.get("skipped")}')
            returned = body.get('offers') if isinstance(body.get('offers'), list) else []
            for i, offer in enumerate(batch_offers):
                srv = returned[i] if i < len(returned) and isinstance(returned[i], dict) else {}
                offer.pushed_at = now_iso()
                offer.server_id = srv.get('id')
                offer.server_status = srv.get('status')
                offer.tracking_url = srv.get('tracking_url')
                storage.append_pushed({'result': srv.get('result', 'ok'), 'status_code': 200,
                                       'network': offer.network, 'external_id': offer.external_id,
                                       'title': offer.title, 'server_id': srv.get('id'),
                                       'server_status': srv.get('status'), 'tracking_url': srv.get('tracking_url')})
        else:
            failed += result.size
            info(f'lote {result.index + 1}: FALHOU — {result.error}')
            for pos, msgs in sorted(result.item_errors.items()):
                who = _label(batch_offers[pos]) if 0 <= pos < len(batch_offers) else '(lote)'
                warn(f'{who}: {"; ".join(msgs)}')
            for i, offer in enumerate(batch_offers):
                storage.append_pushed({'result': 'error', 'status_code': result.status,
                                       'network': offer.network, 'external_id': offer.external_id,
                                       'title': offer.title, 'error': result.error,
                                       'errors': result.item_errors.get(i, [])})
        storage.save_ready(offers)  # persiste a cada lote: queda no meio não reenvia o que já foi

    try:
        client.push(payloads, on_batch=on_batch)
    except ApiError as exc:
        info(f'ERRO: {exc}')
        storage.append_pushed({'result': 'aborted', 'status_code': exc.status, 'error': str(exc)})
        return 1
    info(f'push: {len(payloads) - failed} enviadas, {failed} com falha, {len(blocked)} bloqueadas localmente')
    return 0 if failed == 0 else 1


def cmd_run(args, storage: Storage) -> int:
    rc = cmd_import(args, storage)
    if rc != 0:
        return rc
    cmd_copy(argparse.Namespace(provider=args.provider), storage)
    return cmd_push(argparse.Namespace(dry_run=args.dry_run, force=False), storage)


# ---------------------------------------------------------------- parser

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='python -m affiliate_worker',
        description='Worker local de afiliados: busca/importa ofertas, gera copy e envia ao painel como draft.',
    )
    parser.add_argument('--data-dir', help='diretório de dados (default: affiliate-worker/data ou AFFILIATE_DATA_DIR)')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('search', help='busca candidatos (sem affiliate_url) e grava data/candidates.json')
    p.add_argument('--source', default='mercadolivre', choices=['mercadolivre'])
    p.add_argument('--query', required=True)
    p.add_argument('--niche', required=True, help='slug do nicho no painel, ex. futebol')
    p.add_argument('--limit', type=int, default=20)

    p = sub.add_parser('import', help='importa ofertas de um .csv ou .json para data/ready.json')
    p.add_argument('--file', required=True)
    p.add_argument('--niche', help='nicho padrão para linhas sem niche')

    p = sub.add_parser('copy', help='gera cta_text/copy_short/copy_long para ofertas com link e sem copy')
    p.add_argument('--provider', default='auto', choices=copywriter.PROVIDERS)

    p = sub.add_parser('push', help='envia ofertas prontas ao servidor em lotes de até 100')
    p.add_argument('--dry-run', action='store_true', help='imprime o payload sem enviar')
    p.add_argument('--force', action='store_true', help='reenvia também as já enviadas')

    p = sub.add_parser('run', help='atalho: import + copy + push')
    p.add_argument('--file', required=True)
    p.add_argument('--niche', help='nicho padrão para linhas sem niche')
    p.add_argument('--provider', default='auto', choices=copywriter.PROVIDERS)
    p.add_argument('--dry-run', action='store_true')
    return parser


COMMANDS = {'search': cmd_search, 'import': cmd_import, 'copy': cmd_copy, 'push': cmd_push, 'run': cmd_run}


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env')  # não sobrescreve variáveis já definidas no ambiente
    except ImportError:
        pass
    args = build_parser().parse_args(argv)
    storage = Storage(args.data_dir)
    return COMMANDS[args.command](args, storage)
