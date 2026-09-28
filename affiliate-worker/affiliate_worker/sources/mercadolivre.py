"""Busca de candidatos no Mercado Livre pela API oficial (api.mercadolibre.com, site MLB).

Só gera candidatos: sem affiliate_url. O link de afiliado sai do gerador de links do
programa Mercado Livre Afiliados e é colado pelo operador. Sem scraping de HTML.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import requests

from affiliate_worker.models import Offer

API_BASE = 'https://api.mercadolibre.com'
PAGE_SIZE = 50  # máximo por página aceito pela busca
TIMEOUT = 15


@dataclass
class SearchResult:
    candidates: list[Offer] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _to_offer(item: dict, niche: str) -> Offer:
    price = item.get('price')
    image = item.get('thumbnail') or None
    if isinstance(image, str) and image.startswith('http://'):
        image = 'https://' + image[len('http://'):]
    return Offer(
        network='mercadolivre',
        external_id=str(item.get('id')) if item.get('id') else None,
        niche=niche,
        title=(str(item.get('title') or '').strip()[:255] or None),
        product_url=item.get('permalink') or None,
        image_url=image,
        price_cents=int(round(float(price) * 100)) if isinstance(price, (int, float)) else None,
        currency=item.get('currency_id') or 'BRL',
        affiliate_url=None,
    )


def search(query: str, niche: str, limit: int = 20, session=None, token: str | None = None) -> SearchResult:
    """Busca itens. Nunca levanta exceção de rede/HTTP: devolve SearchResult.error com mensagem amigável."""
    session = session or requests.Session()
    token = token if token is not None else os.environ.get('MERCADOLIVRE_ACCESS_TOKEN', '').strip()
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    limit = max(1, min(int(limit), 1000))
    result = SearchResult()
    offset = 0
    while len(result.candidates) < limit:
        page = min(PAGE_SIZE, limit - len(result.candidates))
        params = {'q': query, 'limit': page, 'offset': offset}
        try:
            resp = session.get(f'{API_BASE}/sites/MLB/search', params=params, headers=headers, timeout=TIMEOUT)
        except requests.Timeout:
            result.error = f'Mercado Livre não respondeu em {TIMEOUT}s (timeout). Tente de novo mais tarde.'
            return result
        except requests.RequestException as exc:
            result.error = f'falha de rede ao consultar o Mercado Livre: {exc.__class__.__name__}'
            return result

        if resp.status_code in (401, 403):
            if token:
                result.error = (
                    f'Mercado Livre recusou a busca (HTTP {resp.status_code}) mesmo com '
                    'MERCADOLIVRE_ACCESS_TOKEN. O token pode ter expirado (dura ~6h) ou o app não tem permissão.'
                )
            else:
                result.error = (
                    f'Mercado Livre recusou a busca anônima (HTTP {resp.status_code}). A API passou a exigir '
                    'autenticação: crie um app em developers.mercadolivre.com.br, gere um access token e defina '
                    'MERCADOLIVRE_ACCESS_TOKEN no .env. Enquanto isso, use "import" com ofertas preenchidas à mão.'
                )
            return result
        if resp.status_code == 429:
            result.error = 'Mercado Livre limitou as requisições (HTTP 429). Aguarde alguns minutos.'
            return result
        if resp.status_code != 200:
            result.error = f'Mercado Livre respondeu HTTP {resp.status_code} na busca.'
            return result
        try:
            data = resp.json()
        except ValueError:
            result.error = 'Mercado Livre devolveu resposta que não é JSON.'
            return result

        items = data.get('results') if isinstance(data, dict) else None
        if not isinstance(items, list):
            result.error = 'resposta do Mercado Livre sem a lista "results".'
            return result
        for item in items:
            if isinstance(item, dict) and item.get('title'):
                result.candidates.append(_to_offer(item, niche))
        total = (data.get('paging') or {}).get('total')
        offset += page
        if not items or (isinstance(total, int) and offset >= total):
            break
    result.candidates = result.candidates[:limit]
    return result
