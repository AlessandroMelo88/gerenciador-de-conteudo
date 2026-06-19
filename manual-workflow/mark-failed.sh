#!/usr/bin/env bash
# Marca um clipe como falho (qualidade ruim, corte incorreto, etc.).
# Uso: ./manual-workflow/mark-failed.sh <CLIP_ID> "motivo"
# Exemplo: ./manual-workflow/mark-failed.sh 12 "Corte abrupto no meio da frase"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ $# -lt 2 ]]; then
  echo "Uso: $0 <CLIP_ID> \"motivo\""
  echo "Exemplo: $0 12 \"Corte abrupto no meio da frase\""
  exit 1
fi

CLIP_ID="$1"
MOTIVO="$2"

if ! [[ "$CLIP_ID" =~ ^[0-9]+$ ]]; then
  echo "Erro: CLIP_ID deve ser um número inteiro."
  exit 1
fi

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi

DB_USER="${CLIPS_DB_USER:-clips_user}"
DB_PASS="${CLIPS_DB_PASSWORD:-}"
DB_NAME="${CLIPS_DB_NAME:-clips_automation}"

mysql_exec() {
  docker exec -i mysql mysql \
    -h 127.0.0.1 \
    -u "$DB_USER" \
    -p"$DB_PASS" \
    "$DB_NAME" \
    --silent \
    --skip-column-names \
    -e "$1" 2>/dev/null
}

CLIP_TITLE=$(mysql_exec "SELECT title FROM generated_clips WHERE id = $CLIP_ID;")
if [[ -z "$CLIP_TITLE" ]]; then
  echo "Erro: Clipe #$CLIP_ID não encontrado."
  exit 1
fi

echo "Marcando clipe #$CLIP_ID como falho:"
echo "  Título: $CLIP_TITLE"
echo "  Motivo: $MOTIVO"
read -r -p "Confirmar? (s/N) " CONFIRM
if [[ "${CONFIRM,,}" != "s" ]]; then
  echo "Operação cancelada."
  exit 0
fi

MOTIVO_ESCAPED="${MOTIVO//\'/\'\'}"
mysql_exec "
  UPDATE generated_clips
  SET status = 'failed', upload_error = '$MOTIVO_ESCAPED', updated_at = UTC_TIMESTAMP()
  WHERE id = $CLIP_ID;"

echo ""
echo "✔ Clipe #$CLIP_ID marcado como falho."
echo ""
