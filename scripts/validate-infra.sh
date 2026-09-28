#!/usr/bin/env bash
# validate-infra.sh — verificações rápidas da infraestrutura do projeto
# Uso: ./scripts/validate-infra.sh

set -euo pipefail

PASS=0
FAIL=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

postgres_psql() {
  (
    cd "$PROJECT_DIR"
    docker compose exec -T postgres sh -c \
      'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"' \
      -- "$@"
  )
}

# Senha do MySQL: nunca hardcoded. Vem do ambiente ou do .env do compose compartilhado.
# Ver bug 16 em Docs/sistema/BUGS.md — o literal daqui estava publicado no GitHub.
DB_PASS="${MYSQL_ROOT_PASSWORD:-$(grep -m1 "^MYSQL_ROOT_PASSWORD=" "$COMPOSE_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d "\"")}"

check() {
  local label="$1"
  shift
  if "$@" &>/dev/null; then
    echo "  PASS: $label"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $label"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "=== Phase 1 — Infraestrutura Base — Validation ==="
echo ""

echo "[INFRA-01] Docker services"
check "PostgreSQL responde" postgres_psql -Atqc 'SELECT 1;'
check "Redis responde" bash -c "cd '$PROJECT_DIR' && docker compose exec -T redis redis-cli ping | grep -qx PONG"
check "clip-processor Up" bash -c "cd '$PROJECT_DIR' && docker compose ps clip-processor | grep -Ei 'up|running'"
check "nginx Up" bash -c "cd '$PROJECT_DIR' && docker compose ps nginx | grep -Ei 'up|running'"

echo ""
echo "[INFRA-02] PostgreSQL schema"
check "banco PostgreSQL responde" postgres_psql -Atqc 'SELECT current_database() IS NOT NULL;'
check "migrations Laravel aplicadas" postgres_psql -Atqc 'SELECT COUNT(*) > 0 FROM migrations;'
check "tabela source_channels existe" postgres_psql -Atqc "SELECT to_regclass('public.source_channels') IS NOT NULL;"
check "tabela source_videos existe" postgres_psql -Atqc "SELECT to_regclass('public.source_videos') IS NOT NULL;"
check "tabela destination_channels existe" postgres_psql -Atqc "SELECT to_regclass('public.destination_channels') IS NOT NULL;"
check "tabela generated_clips existe" postgres_psql -Atqc "SELECT to_regclass('public.generated_clips') IS NOT NULL;"
check "usuario clips_user existe" postgres_psql -Atqc "SELECT 1 FROM pg_roles WHERE rolname = current_user;"

echo ""
echo "[INFRA-04] Secrets e credenciais"
ENV_FILE="$PROJECT_DIR/.env"
check ".env existe" test -f "$ENV_FILE"
check "GROQ_API_KEY configurada" bash -c "grep -q '^GROQ_API_KEY=.' '$ENV_FILE' 2>/dev/null"
check "CLIPS_DB_PASSWORD configurada" bash -c "grep -q 'CLIPS_DB_PASSWORD=.' '$ENV_FILE' 2>/dev/null"
check "CLIP_PROCESSOR_INTERNAL_TOKEN configurado" bash -c "grep -q '^CLIP_PROCESSOR_INTERNAL_TOKEN=.' '$ENV_FILE' 2>/dev/null"

TOKEN_FILE="$(find "$PROJECT_DIR/youtube" -maxdepth 1 -type f -name 'token-*.json' -print -quit 2>/dev/null || true)"
if [ -n "$TOKEN_FILE" ] && [ -f "$TOKEN_FILE" ]; then
  check "token OAuth tem refresh_token" python3 -c "
import json, sys
with open('$TOKEN_FILE') as f:
    d = json.load(f)
assert d.get('refresh_token'), 'NO REFRESH TOKEN'
print('OK')
"
else
  echo "  SKIP: nenhum token-*.json gerado (pendente de OAuth)"
fi

echo ""
echo "=== Resultado: ${PASS} PASS / ${FAIL} FAIL ==="
echo ""

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
