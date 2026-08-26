#!/usr/bin/env bash
# Lista clipes prontos para publicar (status=pending em generated_clips).
# Uso:
#   ./manual-workflow/list-pending-clips.sh             # lista todos os pendentes
#   ./manual-workflow/list-pending-clips.sh --id 42     # detalha um clipe específico
#   ./manual-workflow/list-pending-clips.sh --all-status # inclui todos os status

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=postgres.sh
source "$SCRIPT_DIR/postgres.sh"

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

  postgres_exec_expanded "
    SELECT
      gc.id,
      gc.title,
      gc.score,
      gc.status,
      ROUND((gc.end_time - gc.start_time)::numeric, 1) AS duracao_segundos,
      gc.clip_path,
      gc.thumbnail_path,
      sv.title AS video_origem,
      sc.channel_name AS canal_origem,
      gc.created_at
    FROM generated_clips gc
    JOIN source_videos sv ON gc.source_video_id = sv.id
    JOIN source_channels sc ON sv.channel_id = sc.id
    WHERE gc.id = $CLIP_ID"

  echo ""
  echo "── TÍTULO ──────────────────────────────────"
  postgres_exec "SELECT title FROM generated_clips WHERE id = $CLIP_ID;"
  echo ""
  echo "── DESCRIÇÃO ───────────────────────────────"
  postgres_exec "SELECT description FROM generated_clips WHERE id = $CLIP_ID;"
  echo ""
  echo "── TAGS ────────────────────────────────────"
  postgres_exec "SELECT tags FROM generated_clips WHERE id = $CLIP_ID;"
  echo ""
  exit 0
fi

# ─── Listagem geral ──────────────────────────────────────────────────────────
STATUS_FILTER="gc.status = 'pending'"
if [[ "$MODE" == "all" ]]; then
  STATUS_FILTER="TRUE"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         CANAL DE CORTES — CLIPES DISPONÍVEIS                        ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

TOTAL=$(postgres_exec "SELECT COUNT(*) FROM generated_clips gc WHERE $STATUS_FILTER;")

if [[ "$TOTAL" == "0" ]]; then
  echo "  Nenhum clipe encontrado."
  echo ""
  echo "  Dica: O pipeline pode não ter rodado ainda. Verifique:"
  echo "    docker compose logs --tail=50 clip-processor"
  exit 0
fi

echo "  Total: $TOTAL clipe(s)"
echo ""

postgres_exec_pretty "
  SELECT
    gc.id              AS ID,
    gc.score           AS Score,
    gc.status          AS Status,
    CONCAT(ROUND((gc.end_time - gc.start_time)::numeric, 0), 's') AS Duracao,
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
echo "    docker compose cp clip-processor:/app/videos/clips/<arquivo>.mp4 ~/Desktop/"
echo "    docker compose cp clip-processor:/app/videos/thumbnails/<arquivo>.jpg ~/Desktop/"
echo ""

# Resumo por status
echo "── Resumo por status ──────────────────────────────────────────────────"
postgres_exec_pretty "
  SELECT
    status             AS Status,
    COUNT(*)           AS Quantidade
  FROM generated_clips
  GROUP BY status
  ORDER BY CASE status
    WHEN 'pending' THEN 1
    WHEN 'publishing' THEN 2
    WHEN 'published' THEN 3
    WHEN 'failed' THEN 4
    WHEN 'cutting' THEN 5
    WHEN 'pending_cut' THEN 6
    ELSE 99
  END;"
echo ""
