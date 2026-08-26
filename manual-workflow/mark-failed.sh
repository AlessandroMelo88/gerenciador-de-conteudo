#!/usr/bin/env bash
# Marca um clipe como falho (qualidade ruim, corte incorreto, etc.).
# Uso: ./manual-workflow/mark-failed.sh <CLIP_ID> "motivo"
# Exemplo: ./manual-workflow/mark-failed.sh 12 "Corte abrupto no meio da frase"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=postgres.sh
source "$SCRIPT_DIR/postgres.sh"

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

CLIP_TITLE=$(postgres_exec_vars \
  "SELECT title FROM generated_clips WHERE id = :'clip_id';" \
  -v "clip_id=$CLIP_ID")
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

postgres_exec_vars "
  UPDATE generated_clips
  SET status = 'failed', upload_error = :'motivo', updated_at = CURRENT_TIMESTAMP
  WHERE id = :'clip_id';" \
  -v "motivo=$MOTIVO" \
  -v "clip_id=$CLIP_ID"

echo ""
echo "✔ Clipe #$CLIP_ID marcado como falho."
echo ""
