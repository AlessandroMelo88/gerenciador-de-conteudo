"""Import de ofertas preenchidas pelo operador (JSON ou CSV).

Hotmart, Eduzz, Kiwify e Monetizze não têm API pública de catálogo para afiliado:
o caminho é o operador copiar o link de afiliado da plataforma e colar aqui.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from affiliate_worker.models import Offer


class OfferImportError(Exception):
    """Arquivo ilegível ou em formato não suportado."""


def _price_to_cents(raw: str) -> int | str:
    """Converte '199,90', '199.90', 'R$ 1.299,90' em centavos. Devolve o texto se não der."""
    text = raw.strip().replace('R$', '').replace(' ', '')
    if ',' in text:
        text = text.replace('.', '').replace(',', '.')
    try:
        return int((Decimal(text) * 100).quantize(Decimal('1')))
    except (InvalidOperation, ValueError):
        return raw


def _normalize_row(row: dict) -> dict:
    row = {str(k).strip(): v for k, v in row.items() if k is not None}
    price = row.pop('price', None)
    if price and str(price).strip() and not str(row.get('price_cents') or '').strip():
        row['price_cents'] = _price_to_cents(str(price))
    return row


def load_csv(path: Path) -> list[dict]:
    text = path.read_text(encoding='utf-8-sig')
    if not text.strip():
        return []
    first_line = text.splitlines()[0]
    delimiter = ';' if first_line.count(';') > first_line.count(',') else ','
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    return [_normalize_row(row) for row in reader if any((v or '').strip() for v in row.values() if isinstance(v, str))]


def load_json(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except json.JSONDecodeError as exc:
        raise OfferImportError(f'JSON inválido em {path}: {exc}') from exc
    items = data.get('offers') if isinstance(data, dict) else data
    if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
        raise OfferImportError('JSON precisa ser uma lista de ofertas ou {"offers": [...]}')
    return [_normalize_row(item) for item in items]


def load_file(path: str | Path, default_niche: str | None = None) -> list[Offer]:
    path = Path(path)
    if not path.exists():
        raise OfferImportError(f'arquivo não encontrado: {path}')
    suffix = path.suffix.lower()
    if suffix == '.csv':
        rows = load_csv(path)
    elif suffix == '.json':
        rows = load_json(path)
    else:
        raise OfferImportError(f'formato não suportado: {suffix} (use .csv ou .json)')
    offers = []
    for row in rows:
        if default_niche and not str(row.get('niche') or '').strip():
            row['niche'] = default_niche
        offers.append(Offer.from_dict(row))
    return offers
