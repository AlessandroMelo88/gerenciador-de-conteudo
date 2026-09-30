# Postgres 17 (alpine) + pgvector, para a busca vetorial das transcrições.
#
# Continua na mesma base alpine (musl) da imagem anterior: mesmo volume, mesma
# collation, sem pg_upgrade. NÃO trocar por imagem Debian reaproveitando o volume
# (a ordenação de texto muda e os índices ficariam inconsistentes).
#
# Compila na própria máquina (A1 arm64 ou Mac arm64): docker compose build postgres
FROM postgres:17-alpine

# Tag fixa do pgvector, para o build ser reprodutível.
ARG PGVECTOR_VERSION=v0.8.0

# with_llvm=no: o postgres alpine é construído com JIT (llvm) e o pgxs exigiria o
# clang da mesma versão (que muda a cada release do alpine). Sem bitcode nada se
# perde: o pgvector roda normalmente em código nativo.
# OPTFLAGS vazio: sem -march=native, o binário roda em qualquer CPU arm64/x86_64.
RUN set -eux; \
    apk add --no-cache --virtual .build-deps git build-base; \
    git clone --branch "${PGVECTOR_VERSION}" --depth 1 https://github.com/pgvector/pgvector.git /tmp/pgvector; \
    cd /tmp/pgvector; \
    make with_llvm=no OPTFLAGS="" -j"$(nproc)"; \
    make with_llvm=no OPTFLAGS="" install; \
    cd /; rm -rf /tmp/pgvector; \
    apk del .build-deps
