#!/usr/bin/env bash
# validate-infra.sh — Phase 1 health checks
# Executar a partir de: /Users/alessandrobm1/develop/server/wordpress/
# Uso: bash canaldecortes/scripts/validate-infra.sh

set -euo pipefail

PASS=0
FAIL=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_DIR="$(dirname "$PROJECT_DIR")"

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
check "n8n responde em :5678" curl -sf --max-time 5 http://localhost:5678/healthz
check "whisper responde em :8000" curl -sf --max-time 5 http://localhost:8000/health
check "clip-processor Up" bash -c "cd '$COMPOSE_DIR' && docker compose ps clip-processor | grep -i 'up\|running'"
check "n8n Up" bash -c "cd '$COMPOSE_DIR' && docker compose ps n8n | grep -i 'up\|running'"
check "whisper Up" bash -c "cd '$COMPOSE_DIR' && docker compose ps whisper | grep -i 'up\|running'"

echo ""
echo "[INFRA-02] MySQL schema"
check "banco clips_automation existe" bash -c "docker exec mysql mysql -uroot -prootpassword -e 'SHOW DATABASES;' 2>/dev/null | grep clips_automation"
check "tabela source_channels existe" bash -c "docker exec mysql mysql -uroot -prootpassword clips_automation -e 'DESCRIBE source_channels;' 2>/dev/null | grep youtube_channel_id"
check "tabela source_videos existe" bash -c "docker exec mysql mysql -uroot -prootpassword clips_automation -e 'DESCRIBE source_videos;' 2>/dev/null | grep youtube_video_id"
check "tabela generated_clips existe" bash -c "docker exec mysql mysql -uroot -prootpassword clips_automation -e 'DESCRIBE generated_clips;' 2>/dev/null | grep source_video_id"
check "usuario clips_user existe" bash -c "docker exec mysql mysql -uroot -prootpassword -e 'SELECT User FROM mysql.user WHERE User=\"clips_user\";' 2>/dev/null | grep clips_user"

echo ""
echo "[INFRA-04] Secrets e credenciais"
ENV_FILE="$PROJECT_DIR/.env"
check ".env existe" test -f "$ENV_FILE"
check "N8N_ENCRYPTION_KEY configurada" bash -c "grep -q 'N8N_ENCRYPTION_KEY=.' '$ENV_FILE' 2>/dev/null"
check "ANTHROPIC_API_KEY configurada" bash -c "grep -q 'ANTHROPIC_API_KEY=.' '$ENV_FILE' 2>/dev/null"
check "CLIPS_DB_PASSWORD configurada" bash -c "grep -q 'CLIPS_DB_PASSWORD=.' '$ENV_FILE' 2>/dev/null"

TOKEN_FILE="$PROJECT_DIR/youtube/token.json"
if [ -f "$TOKEN_FILE" ] && [ "$(cat "$TOKEN_FILE")" != "{}" ]; then
  check "token.json tem refresh_token" python3 -c "
import json, sys
with open('$TOKEN_FILE') as f:
    d = json.load(f)
assert d.get('refresh_token'), 'NO REFRESH TOKEN'
print('OK')
"
else
  echo "  SKIP: token.json ainda não gerado (pendente — INFRA-03/04)"
fi

echo ""
echo "=== Resultado: ${PASS} PASS / ${FAIL} FAIL ==="
echo ""

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
