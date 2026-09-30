"""Sidecar de embeddings (FastAPI) — só a rede interna do compose, sem porta publicada.

POST /embed   Authorization: Bearer <EMBEDDER_TOKEN>
              {"texts": ["..."], "kind": "query" | "passage"}
              -> {"model": "...", "dim": 384, "vectors": [[...]]}
GET  /health  -> {"status": "ok", "model": "...", "dim": 384}

Erros: 401 token ausente/errado (e também EMBEDDER_TOKEN vazio: fail-closed, nunca
"sem token = aberto"); 422 payload; 503 modelo não carregado.
"""
import hmac
import logging
import os
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

import embed_lib

log = logging.getLogger('embedder')

MAX_TEXTS = 64
MAX_CHARS = 8000  # o e5 trunca em 512 tokens de qualquer jeito


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=MAX_TEXTS)
    kind: Literal['query', 'passage']


def create_app(embedder: embed_lib.Embedder | None = None, token: str | None = None) -> FastAPI:
    embedder = embedder or embed_lib.get_embedder()
    # O token é lido na criação; vazio nunca autoriza ninguém.
    expected = os.environ.get('EMBEDDER_TOKEN', '') if token is None else token

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            embedder.load()
        except embed_lib.EmbedderError as e:
            log.error('modelo não carregou no startup: %s', e)  # /embed responde 503
        yield

    app = FastAPI(title='canaldecortes-embedder', lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)

    def require_token(authorization: str | None = Header(default=None)) -> None:
        scheme, _, given = (authorization or '').partition(' ')
        well_formed = bool(expected) and scheme.lower() == 'bearer' and bool(given)
        # compare_digest sempre roda (tempo constante), mesmo se o formato já falhou
        same = hmac.compare_digest(given.encode(), expected.encode())
        if not (well_formed and same):
            raise HTTPException(status_code=401, detail='unauthorized',
                                headers={'WWW-Authenticate': 'Bearer'})

    @app.get('/health')
    def health():
        if not embedder.loaded:
            raise HTTPException(status_code=503, detail='model not loaded')
        return {'status': 'ok', 'model': embedder.name, 'dim': embedder.dim}

    @app.post('/embed', dependencies=[Depends(require_token)])
    def embed(req: EmbedRequest):
        if any(len(t) > MAX_CHARS for t in req.texts):
            raise HTTPException(status_code=422, detail=f'texto maior que {MAX_CHARS} caracteres')
        if not embedder.loaded:
            raise HTTPException(status_code=503, detail='model not loaded')
        try:
            vectors = embedder.embed(req.texts, req.kind)
        except embed_lib.EmbedderError as e:
            log.error('falha ao embutir: %s', e)
            raise HTTPException(status_code=503, detail='embedding failed') from None
        return {'model': embedder.name, 'dim': embedder.dim, 'vectors': vectors}

    return app


app = create_app()
