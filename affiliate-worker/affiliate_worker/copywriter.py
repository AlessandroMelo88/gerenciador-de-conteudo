"""Geração de cta_text / copy_short / copy_long.

Ordem (regra do projeto: todo caminho de IA nasce com fallback Groq):
  Anthropic (claude-haiku-4-5) → Groq (GROQ_MODEL) → template determinístico.
O template garante que `copy` nunca trava o fluxo.
"""
from __future__ import annotations

import json
import os
import re
import sys

from affiliate_worker.models import MAX_COPY_SHORT, MAX_CTA, Offer

ANTHROPIC_MODEL = 'claude-haiku-4-5'
DEFAULT_GROQ_MODEL = 'qwen/qwen3.8-27b'  # mesmo default do clip-processor/src/metadata_generator.py
PROVIDERS = ('auto', 'anthropic', 'groq', 'template')

BASE_RULES = (
    'Você escreve copy de divulgação de ofertas de afiliado em português do Brasil. '
    'Regras obrigatórias: '
    '1) Use somente os dados fornecidos. Não invente preço, desconto, frete, brinde, prazo, estoque ou escassez. '
    '2) Não prometa resultado nem afirme ganho de renda, saúde, emagrecimento ou cura garantidos. '
    '3) Não inclua links, URLs nem encurtadores (o link rastreável é anexado depois). '
    '4) Sem hashtags em excesso (no máximo 2) e sem caixa alta gritada. '
    'Formato: responda APENAS um objeto JSON com as chaves "cta_text" (chamada curta, até 60 caracteres), '
    '"copy_short" (até 280 caracteres, para Telegram ou comentário fixado) e '
    '"copy_long" (2 a 4 parágrafos separados por linha em branco, para descrição de vídeo ou blog).'
)
NICHE_TONE = {
    'futebol': 'Tom: de torcedor para torcedor, direto, animado, sem exagero.',
    'politica': (
        'Tom: sóbrio e informativo. Sem posicionamento partidário, sem atacar ou elogiar políticos, '
        'partidos ou ideologias. Apresente o conteúdo pelo que ele oferece.'
    ),
}
DEFAULT_TONE = 'Tom: claro, honesto e objetivo.'

OUTPUT_SCHEMA = {
    'format': {
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'cta_text': {'type': 'string'},
                'copy_short': {'type': 'string'},
                'copy_long': {'type': 'string'},
            },
            'required': ['cta_text', 'copy_short', 'copy_long'],
            'additionalProperties': False,
        },
    }
}

_URL_RE = re.compile(r'(https?://\S+|www\.\S+)', re.IGNORECASE)


class CopyError(Exception):
    """Saída de IA inválida ou incompleta."""


def _log(msg: str) -> None:
    print(f'[copy] {msg}', file=sys.stderr)


def system_prompt(niche: str | None) -> str:
    return f'{BASE_RULES} {NICHE_TONE.get((niche or "").lower(), DEFAULT_TONE)}'


def format_price(price_cents: int | None, currency: str | None) -> str | None:
    if not isinstance(price_cents, int) or isinstance(price_cents, bool):
        return None
    reais, cents = divmod(price_cents, 100)
    number = f'{reais:,}'.replace(',', '.') + f',{cents:02d}'
    cur = (currency or 'BRL').upper()
    return f'R$ {number}' if cur == 'BRL' else f'{cur} {number}'


def build_user_prompt(offer: Offer) -> str:
    lines = [
        f'Nicho: {offer.niche or "-"}',
        f'Rede: {offer.network or "-"}',
        f'Produto: {offer.title or "-"}',
    ]
    if offer.description:
        lines.append(f'Descrição fornecida: {offer.description}')
    price = format_price(offer.price_cents, offer.currency)
    lines.append(f'Preço informado: {price}' if price else 'Preço: não informado (não mencione preço)')
    lines.append('Gere o JSON pedido.')
    return '\n'.join(lines)


def parse_json_output(text: str) -> dict:
    """Parse defensivo: tolera cercas ```json, bloco <think> e texto antes/depois do objeto."""
    if not isinstance(text, str) or not text.strip():
        raise CopyError('resposta vazia')
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', cleaned).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find('{'), cleaned.rfind('}')
        if start == -1 or end <= start:
            raise CopyError('resposta sem objeto JSON')
        try:
            data = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as exc:
            raise CopyError(f'JSON inválido: {exc}') from exc
    if not isinstance(data, dict):
        raise CopyError('JSON não é objeto')
    return data


def _strip_urls(text: str) -> str:
    return re.sub(r'[ \t]{2,}', ' ', _URL_RE.sub('', text)).strip()


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(' ', 1)[0].rstrip(' ,;:.-')
    return (cut or text[: limit - 1]) + '…'


def normalize_copy(data: dict) -> dict:
    """Valida e ajusta a saída. Campo faltando/vazio = CopyError (cai para o próximo provedor)."""
    out = {}
    for key in ('cta_text', 'copy_short', 'copy_long'):
        value = data.get(key)
        if not isinstance(value, str) or not _strip_urls(value):
            raise CopyError(f'campo ausente ou vazio: {key}')
        out[key] = _strip_urls(value)
    out['cta_text'] = _truncate(out['cta_text'], MAX_CTA)
    out['copy_short'] = _truncate(out['copy_short'], MAX_COPY_SHORT)
    return out


def _anthropic_text(response) -> str:
    for block in getattr(response, 'content', None) or []:
        text = getattr(block, 'text', None)
        if isinstance(text, str):
            return text
    raise CopyError('resposta da Anthropic sem bloco de texto')


def generate_via_anthropic(offer: Offer, client=None) -> dict:
    if client is None:
        if not os.environ.get('ANTHROPIC_API_KEY'):
            raise CopyError('ANTHROPIC_API_KEY não definido')
        import anthropic
        client = anthropic.Anthropic()
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system_prompt(offer.niche),
        messages=[{'role': 'user', 'content': build_user_prompt(offer)}],
        output_config=OUTPUT_SCHEMA,
    )
    return normalize_copy(parse_json_output(_anthropic_text(response)))


def generate_via_groq(offer: Offer, client=None) -> dict:
    if client is None:
        if not os.environ.get('GROQ_API_KEY'):
            raise CopyError('GROQ_API_KEY não definido')
        from groq import Groq
        client = Groq()
    model = os.environ.get('GROQ_MODEL') or DEFAULT_GROQ_MODEL
    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': system_prompt(offer.niche)},
            {'role': 'user', 'content': build_user_prompt(offer)},
        ],
        response_format={'type': 'json_object'},
        temperature=0.4,
        max_tokens=1024,
    )
    return normalize_copy(parse_json_output(response.choices[0].message.content))


def generate_via_template(offer: Offer) -> dict:
    """Fallback determinístico. Só usa dados reais da oferta; nada de promessa."""
    niche = (offer.niche or '').lower()
    title = (offer.title or 'esta oferta').strip()
    price = format_price(offer.price_cents, offer.currency)
    price_line = f' Preço informado: {price} (sujeito a alteração na loja).' if price else ''
    desc = _strip_urls(offer.description or '')

    if niche == 'futebol':
        cta = 'Ver oferta'
        short = f'{title} — pra quem vive o futebol.{price_line} Confira os detalhes no link.'
        intro = f'{title}: uma opção pra quem acompanha e joga futebol.'
    elif niche == 'politica':
        cta = 'Conhecer o conteúdo'
        short = f'{title}.{price_line} Veja os detalhes e decida se faz sentido para você.'
        intro = f'{title} é uma indicação de conteúdo para quem acompanha política e atualidades.'
    else:
        cta = 'Ver detalhes'
        short = f'{title}.{price_line} Confira os detalhes no link.'
        intro = f'{title}.'

    paragraphs = [intro]
    if desc:
        paragraphs.append(desc)
    if price:
        paragraphs.append(f'Preço informado no momento da consulta: {price}. Valores e condições podem mudar; confira na página da oferta.')
    paragraphs.append('Link de afiliado: ao comprar por ele, o canal pode receber uma comissão, sem custo extra para você.')
    return normalize_copy({'cta_text': cta, 'copy_short': short, 'copy_long': '\n\n'.join(paragraphs)})


def generate_copy(offer: Offer, provider: str = 'auto', anthropic_client=None, groq_client=None) -> tuple[dict, str]:
    """Gera copy e devolve (campos, provedor_usado).

    provider: auto = Anthropic → Groq → template; anthropic/groq = só aquele, depois template;
    template = direto no template. provedor_usado ∈ anthropic | groq | template.
    """
    if provider not in PROVIDERS:
        raise ValueError(f'provider inválido: {provider} (use {", ".join(PROVIDERS)})')
    chain = {
        'auto': ('anthropic', 'groq'),
        'anthropic': ('anthropic',),
        'groq': ('groq',),
        'template': (),
    }[provider]
    for name in chain:
        try:
            if name == 'anthropic':
                return generate_via_anthropic(offer, anthropic_client), 'anthropic'
            return generate_via_groq(offer, groq_client), 'groq'
        except Exception as exc:  # qualquer falha de IA cai para o próximo; o fluxo não trava
            _log(f'{name} falhou para "{(offer.title or "")[:60]}": {exc.__class__.__name__}: {exc}')
    return generate_via_template(offer), 'template'


def apply_copy(offer: Offer, provider: str = 'auto', **clients) -> str | None:
    """Preenche só os campos de copy vazios. Retorna provedor usado ou None se nada a fazer."""
    if not offer.has_affiliate_url() or not offer.needs_copy():
        return None
    data, used = generate_copy(offer, provider, **clients)
    for key, value in data.items():
        if not getattr(offer, key):
            setattr(offer, key, value)
    if not offer.ai_provider:
        # o contrato não tem "template": texto determinístico escrito pelo worker conta como manual
        offer.ai_provider = used if used in ('anthropic', 'groq') else 'manual'
    return used
