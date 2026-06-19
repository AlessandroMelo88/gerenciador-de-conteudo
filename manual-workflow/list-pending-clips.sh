#!/usr/bin/env bash
# Lista clipes prontos para publicar (status=pending em generated_clips).
# Uso:
#   ./manual-workflow/list-pending-clips.sh             # lista todos os pendentes
#   ./manual-workflow/list-pending-clips.sh --id 42     # detalha um clipe específico
#   ./manual-workflow/list-pending-clips.sh --all-status # inclui todos os status

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Carrega variáveis de ambiente
if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT_DIR/.env"
  set +a
fi

DB_HOST="${CLIPS_DB_HOST:-mysql}"
DB_PORT="${CLIPS_DB_PORT:-3306}"
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

mysql_exec_pretty() {
  docker exec -i mysql mysql \
    -h 127.0.0.1 \
    -u "$DB_USER" \
    -p"$DB_PASS" \
    "$DB_NAME" \
    -e "$1" 2>/dev/null
}

MODE="pending"
CLIP_ID=""

for arg in "$@"; do
  case "$arg" in
    --all-status) MODE="all" ;;
    --id) MODE="detail" ;;
    [0-9]*) CLIP_ID="$arg" ;;
  esac
done

# ─── Detalhe de um clip específico ──────────────────────────────────────────
if [[ "$MODE" == "detail" && -n "$CLIP_ID" ]]; then
  echo ""
  echo "══════════════════════════════════════════════"
  echo "  CLIP #${CLIP_ID} — Detalhes"
  echo "══════════════════════════════════════════════"

  mysql_exec_pretty "
    SELECT
      gc.id,
      gc.title,
      gc.score,
      gc.status,
      ROUND(gc.end_time - gc.start_time, 1) AS duracao_segundos,
      gc.clip_path,
      gc.thumbnail_path,
      sv.title AS video_origem,
      sc.channel_name AS canal_origem,
      gc.created_at
    FROM generated_clips gc
    JOIN source_videos sv ON gc.source_video_id = sv.id
    JOIN source_channels sc ON sv.channel_id = sc.id
    WHERE gc.id = $CLIP_ID\G"

  echo ""
  echo "── TÍTULO ──────────────────────────────────"
  mysql_exec "SELECT title FROM generated_clips WHERE id = $CLIP_ID;"
  echo ""
  echo "── DESCRIÇÃO ───────────────────────────────"
  mysql_exec "SELECT description FROM generated_clips WHERE id = $CLIP_ID;"
  echo ""
  echo "── TAGS ────────────────────────────────────"
  mysql_exec "SELECT tags FROM generated_clips WHERE id = $CLIP_ID;"
  echo ""
  exit 0
fi

# ─── Listagem geral ──────────────────────────────────────────────────────────
STATUS_FILTER="gc.status = 'pending'"
if [[ "$MODE" == "all" ]]; then
  STATUS_FILTER="1=1"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         CANAL DE CORTES — CLIPES DISPONÍVEIS                        ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

TOTAL=$(mysql_exec "SELECT COUNT(*) FROM generated_clips gc WHERE $STATUS_FILTER;")

if [[ "$TOTAL" == "0" ]]; then
  echo "  Nenhum clipe encontrado."
  echo ""
  echo "  Dica: O pipeline pode não ter rodado ainda. Verifique:"
  echo "    docker logs clip-processor --tail 50"
  exit 0
fi

echo "  Total: $TOTAL clipe(s)"
echo ""

mysql_exec_pretty "
  SELECT
    gc.id              AS ID,
    gc.score           AS Score,
    gc.status          AS Status,
    CONCAT(ROUND(gc.end_time - gc.start_time, 0), 's') AS Duracao,
    LEFT(gc.title, 55) AS Titulo,
    sc.channel_name    AS Canal,
    DATE(gc.created_at) AS Criado
  FROM generated_clips gc
  JOIN source_videos sv ON gc.source_video_id = sv.id
  JOIN source_channels sc ON sv.channel_id = sc.id
  WHERE $STATUS_FILTER
  ORDER BY gc.score DESC, gc.created_at DESC
  LIMIT 50;"

echo ""
echo "──────────────────────────────────────────────────────────────────────"
echo "  Comandos úteis:"
echo "    Ver detalhes:      ./manual-workflow/list-pending-clips.sh --id <ID>"
echo "    Marcar publicado:  ./manual-workflow/mark-published.sh <ID> <YT_VIDEO_ID>"
echo "    Marcar falho:      ./manual-workflow/mark-failed.sh <ID> \"motivo\""
echo ""
echo "  Para copiar o vídeo do Docker:"
echo "    docker cp clip-processor:/app/videos/clips/<arquivo>.mp4 ~/Desktop/"
echo "    docker cp clip-processor:/app/videos/thumbnails/<arquivo>.jpg ~/Desktop/"
echo ""

# Resumo por status
echo "── Resumo por status ──────────────────────────────────────────────────"
mysql_exec_pretty "
  SELECT
    status             AS Status,
    COUNT(*)           AS Quantidade
  FROM generated_clips
  GROUP BY status
  ORDER BY FIELD(status, 'pending', 'publishing', 'published', 'failed', 'cutting', 'pending_cut');"
echo ""
