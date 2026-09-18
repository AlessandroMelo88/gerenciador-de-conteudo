"""Cliente HTTP de POST /api/offers.

- Lotes de até 100 itens.
- Retry com backoff exponencial em 429, 5xx, timeout e erro de conexão (respeita Retry-After).
- Sem retry em 401 (token errado) e 422 (validação): repetir não muda o resultado.
- Nunca loga o token.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

from affiliate_worker.models import MAX_BATCH, chunked

RETRY_STATUS = {429, 500, 502, 503, 504}
DEFAULT_TIMEOUT = 30


class ApiError(Exception):
    """Erro que interrompe o push inteiro (401, 503 persistente, configuração)."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


@dataclass
class BatchResult:
    index: int
    size: int
    status: int | None
    ok: bool
    body: dict | None = None
    # 422: {posição_no_lote: [mensagens]}; erros sem posição vão na chave -1
    item_errors: dict[int, list[str]] = field(default_factory=dict)
    error: str | None = None


def _parse_422(body: dict) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for key, messages in (body.get('errors') or {}).items():
        parts = str(key).split('.')
        pos = int(parts[1]) if len(parts) >= 2 and parts[0] == 'offers' and parts[1].isdigit() else -1
        msgs = messages if isinstance(messages, list) else [messages]
        out.setdefault(pos, []).extend(str(m) for m in msgs)
    if not out and body.get('message'):
        out[-1] = [str(body['message'])]
    return out


class ApiClient:
    def __init__(self, base_url: str, token: str, session=None, max_retries: int = 4,
                 backoff: float = 1.0, timeout: float = DEFAULT_TIMEOUT, sleep=time.sleep):
        if not base_url:
            raise ApiError('AFFILIATE_API_URL não definido')
        if not token:
            raise ApiError('AFFILIATE_API_TOKEN não definido')
        self.url = base_url.rstrip('/') + '/api/offers'
        self._token = token
        self.session = session or requests.Session()
        self.max_retries = max_retries
        self.backoff = backoff
        self.timeout = timeout
        self.sleep = sleep

    def __repr__(self) -> str:  # sem token
        return f'ApiClient(url={self.url!r})'

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self._token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _wait(self, attempt: int, resp=None) -> None:
        delay = self.backoff * (2 ** attempt)
        if resp is not None:
            retry_after = resp.headers.get('Retry-After') if getattr(resp, 'headers', None) else None
            if retry_after and str(retry_after).isdigit():
                delay = max(delay, float(retry_after))
        self.sleep(min(delay, 120))

    def post_batch(self, payload: list[dict], index: int = 0) -> BatchResult:
        if not 1 <= len(payload) <= MAX_BATCH:
            raise ValueError(f'lote precisa ter de 1 a {MAX_BATCH} itens (tem {len(payload)})')
        last_status = None
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.post(self.url, json={'offers': payload},
                                         headers=self._headers(), timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_status, last_error = None, f'{exc.__class__.__name__} ao falar com o servidor'
                if attempt < self.max_retries:
                    self._wait(attempt)
                    continue
                break

            status = resp.status_code
            if status == 200:
                return BatchResult(index, len(payload), status, True, body=_safe_json(resp))
            if status == 401:
                raise ApiError('401: token recusado. Confira AFFILIATE_API_TOKEN (igual ao configurado no painel).', 401)
            if status == 422:
                body = _safe_json(resp) or {}
                return BatchResult(index, len(payload), status, False, body=body,
                                   item_errors=_parse_422(body), error='422: validação recusada pelo servidor')
            if status in RETRY_STATUS:
                last_status, last_error = status, f'HTTP {status}'
                if attempt < self.max_retries:
                    self._wait(attempt, resp)
                    continue
                break
            return BatchResult(index, len(payload), status, False, body=_safe_json(resp),
                               error=f'HTTP {status} inesperado')

        if last_status == 503:
            raise ApiError('503: servidor indisponível ou sem token de API configurado '
                           '(defina o token no .env do painel). Push interrompido.', 503)
        return BatchResult(index, len(payload), last_status, False,
                           error=f'{last_error} após {self.max_retries + 1} tentativas')

    def push(self, payloads: list[dict], on_batch=None) -> list[BatchResult]:
        """Envia em lotes. 401/503 persistente interrompem (ApiError); 422/outros seguem para o próximo lote."""
        results = []
        for i, batch in enumerate(chunked(payloads, MAX_BATCH)):
            result = self.post_batch(batch, i)
            results.append(result)
            if on_batch:
                on_batch(result, batch)
        return results


def _safe_json(resp):
    try:
        data = resp.json()
        return data if isinstance(data, dict) else {'data': data}
    except ValueError:
        return None
