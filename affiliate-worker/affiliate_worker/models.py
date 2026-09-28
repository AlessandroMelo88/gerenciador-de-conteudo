"""Modelo Offer e validação local espelhando o contrato de POST /api/offers.

A ideia é falhar cedo aqui, com mensagem clara, em vez de receber 422 do servidor.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from urllib.parse import urlparse

NETWORKS = (
    'hotmart', 'eduzz', 'kiwify', 'monetizze', 'amazon',
    'mercadolivre', 'shopee', 'awin', 'manual',
)
AI_PROVIDERS = ('anthropic', 'groq', 'claude-local', 'manual')

MAX_TITLE = 255
MAX_CTA = 255
MAX_EXTERNAL_ID = 255
MAX_COPY_SHORT = 280
MAX_BATCH = 100

# Campos enviados ao servidor (ordem do contrato). `status` nunca é enviado.
PAYLOAD_FIELDS = (
    'network', 'external_id', 'niche', 'title', 'affiliate_url', 'description',
    'product_url', 'image_url', 'price_cents', 'currency', 'commission_percent',
    'cta_text', 'copy_short', 'copy_long', 'ai_provider',
)
# Campos só locais (controle do worker), nunca vão no payload.
LOCAL_FIELDS = ('pushed_at', 'server_id', 'server_status', 'tracking_url')

_SLUG_RE = re.compile(r'^[a-z0-9]+(?:[-_][a-z0-9]+)*$')
_CURRENCY_RE = re.compile(r'^[A-Z]{3}$')


def is_http_url(value: str | None) -> bool:
    """True só para URL absoluta http/https com host. Rejeita javascript:, data:, relativa etc."""
    if not value or not isinstance(value, str):
        return False
    value = value.strip()
    if any(ch.isspace() for ch in value):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme.lower() in ('http', 'https') and bool(parsed.netloc)


def _blank_to_none(value):
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


@dataclass
class Offer:
    network: str | None = None
    title: str | None = None
    niche: str | None = None
    affiliate_url: str | None = None
    external_id: str | None = None
    description: str | None = None
    product_url: str | None = None
    image_url: str | None = None
    price_cents: int | None = None
    currency: str | None = None
    commission_percent: float | None = None
    cta_text: str | None = None
    copy_short: str | None = None
    copy_long: str | None = None
    ai_provider: str | None = None
    # controle local
    pushed_at: str | None = None
    server_id: int | None = None
    server_status: str | None = None
    tracking_url: str | None = None
    extra_warnings: list[str] = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict) -> 'Offer':
        """Constrói a partir de dict (JSON/CSV). Chaves desconhecidas viram aviso, não erro."""
        known = {f.name for f in fields(cls)} - {'extra_warnings'}
        kwargs = {}
        warnings = []
        for key, value in (data or {}).items():
            key = str(key).strip()
            if key == 'status':
                warnings.append('campo "status" ignorado (o servidor define; oferta chega como draft)')
                continue
            if key not in known:
                if _blank_to_none(value) is not None:
                    warnings.append(f'campo desconhecido ignorado: {key}')
                continue
            kwargs[key] = _blank_to_none(value)
        offer = cls(**kwargs)
        offer.extra_warnings = warnings
        offer._coerce()
        return offer

    def _coerce(self) -> None:
        """Normaliza tipos vindos de CSV (tudo string). Valor inválido é mantido para a validação acusar."""
        for name in ('network', 'niche', 'ai_provider'):
            val = getattr(self, name)
            if isinstance(val, str):
                setattr(self, name, val.lower())
        if isinstance(self.currency, str):
            self.currency = self.currency.upper()
        if self.external_id is not None and not isinstance(self.external_id, str):
            self.external_id = str(self.external_id)
        if isinstance(self.price_cents, str):
            try:
                self.price_cents = int(self.price_cents)
            except ValueError:
                pass
        elif isinstance(self.price_cents, float) and self.price_cents.is_integer():
            self.price_cents = int(self.price_cents)
        if isinstance(self.commission_percent, str):
            try:
                self.commission_percent = float(self.commission_percent.replace(',', '.').rstrip('%'))
            except ValueError:
                pass

    def has_affiliate_url(self) -> bool:
        return bool(self.affiliate_url and str(self.affiliate_url).strip())

    def needs_copy(self) -> bool:
        return not (self.cta_text and self.copy_short and self.copy_long)

    def key(self) -> tuple:
        """Chave de deduplicação local (mesma lógica de upsert do servidor quando há external_id)."""
        if self.external_id:
            return (self.network, 'id', self.external_id)
        return (self.network, 'url', self.affiliate_url or self.product_url or self.title)

    def validate(self) -> list[str]:
        """Retorna lista de erros (vazia = válido para push)."""
        errors: list[str] = []
        if self.network not in NETWORKS:
            errors.append(f'network inválido: {self.network!r} (aceitos: {", ".join(NETWORKS)})')
        if not self.title or not isinstance(self.title, str):
            errors.append('title é obrigatório')
        elif len(self.title) > MAX_TITLE:
            errors.append(f'title com {len(self.title)} caracteres (máximo {MAX_TITLE})')
        if not self.niche or not isinstance(self.niche, str) or not _SLUG_RE.match(self.niche):
            errors.append(f'niche obrigatório e em formato slug (ex. futebol, politica): {self.niche!r}')
        if not self.has_affiliate_url():
            errors.append('affiliate_url ausente (o worker nunca inventa link; cole o link da rede)')
        elif not is_http_url(self.affiliate_url):
            errors.append(f'affiliate_url precisa ser http/https: {self.affiliate_url!r}')
        for name in ('product_url', 'image_url'):
            val = getattr(self, name)
            if val is not None and not is_http_url(val):
                errors.append(f'{name} precisa ser http/https: {val!r}')
        if self.external_id is not None and len(self.external_id) > MAX_EXTERNAL_ID:
            errors.append(f'external_id com mais de {MAX_EXTERNAL_ID} caracteres')
        if self.price_cents is not None and (
            isinstance(self.price_cents, bool) or not isinstance(self.price_cents, int) or self.price_cents < 0
        ):
            errors.append(f'price_cents precisa ser inteiro >= 0: {self.price_cents!r}')
        if self.currency is not None and (not isinstance(self.currency, str) or not _CURRENCY_RE.match(self.currency)):
            errors.append(f'currency precisa ter 3 letras (ex. BRL): {self.currency!r}')
        if self.commission_percent is not None:
            if isinstance(self.commission_percent, bool) or not isinstance(self.commission_percent, (int, float)):
                errors.append(f'commission_percent precisa ser número: {self.commission_percent!r}')
            elif not 0 <= self.commission_percent <= 100:
                errors.append(f'commission_percent fora de 0–100: {self.commission_percent!r}')
        if self.cta_text is not None and len(self.cta_text) > MAX_CTA:
            errors.append(f'cta_text com mais de {MAX_CTA} caracteres')
        if self.copy_short is not None and len(self.copy_short) > MAX_COPY_SHORT:
            errors.append(f'copy_short com mais de {MAX_COPY_SHORT} caracteres')
        if self.ai_provider is not None and self.ai_provider not in AI_PROVIDERS:
            errors.append(f'ai_provider inválido: {self.ai_provider!r} (aceitos: {", ".join(AI_PROVIDERS)})')
        return errors

    def to_payload(self) -> dict:
        """Dict pronto para a API: só campos do contrato, sem None."""
        return {name: getattr(self, name) for name in PAYLOAD_FIELDS if getattr(self, name) is not None}

    def to_dict(self) -> dict:
        """Dict para armazenamento local (inclui controle local, sem None)."""
        out = self.to_payload()
        for name in LOCAL_FIELDS:
            if getattr(self, name) is not None:
                out[name] = getattr(self, name)
        return out


def chunked(items: list, size: int = MAX_BATCH) -> list[list]:
    if size < 1:
        raise ValueError('size precisa ser >= 1')
    return [items[i:i + size] for i in range(0, len(items), size)]
