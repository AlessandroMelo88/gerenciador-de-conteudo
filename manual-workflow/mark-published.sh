#!/usr/bin/env bash
# Marca um clipe como publicado no banco após upload manual no YouTube Studio.
# Uso: ./manual-workflow/mark-published.sh <CLIP_ID> <YOUTUBE_VIDEO_ID>
# Exemplo: ./manual-workflow/mark-published.sh 42 dQw4w9WgXcQ

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=postgres.sh
source "$SCRIPT_DIR/postgres.sh"

if [[ $# -lt 2 ]]; then
  echo "Uso: $0 <CLIP_ID> <YOUTUBE_VIDEO_ID>"
  echo "Exemplo: $0 42 dQw4w9WgXcQ"
  exit 1
fi

CLIP_ID="$1"
YT_VIDEO_ID="$2"

# Valida que CLIP_ID é número
if ! [[ "$CLIP_ID" =~ ^[0-9]+$ ]]; then
  echo "Erro: CLIP_ID deve ser um número inteiro. Recebido: '$CLIP_ID'"
  exit 1
fi

if ! [[ "$YT_VIDEO_ID" =~ ^[A-Za-z0-9_-]{11}$ ]]; then
  echo "Erro: YOUTUBE_VIDEO_ID deve ter 11 caracteres válidos do YouTube."
  exit 1
fi

# Verifica se o clipe existe e está pendente
CURRENT_STATUS=$(postgres_exec_vars \
  "SELECT status FROM generated_clips WHERE id = :'clip_id' LIMIT 1;" \
  -v "clip_id=$CLIP_ID")

if [[ -z "$CURRENT_STATUS" ]]; then
  echo "Erro: Clipe #$CLIP_ID não encontrado."
  exit 1
fi

if [[ "$CURRENT_STATUS" == "published" ]]; then
  echo "Aviso: Clipe #$CLIP_ID já está marcado como publicado."
  EXISTING_YT=$(postgres_exec_vars \
    "SELECT youtube_video_id FROM generated_clips WHERE id = :'clip_id';" \
    -v "clip_id=$CLIP_ID")
  echo "  YouTube Video ID atual: $EXISTING_YT"
  read -r -p "Deseja sobrescrever? (s/N) " CONFIRM
  if [[ "${CONFIRM,,}" != "s" ]]; then
    echo "Operação cancelada."
    exit 0
  fi
fi

if [[ "$CURRENT_STATUS" == "failed" ]]; then
  echo "Aviso: Clipe #$CLIP_ID tem status 'failed'."
  read -r -p "Deseja marcar como publicado mesmo assim? (s/N) " CONFIRM
  if [[ "${CONFIRM,,}" != "s" ]]; then
    echo "Operação cancelada."
    exit 0
  fi
fi

# Mostra o que vai ser atualizado
echo ""
CLIP_TITLE=$(postgres_exec_vars \
  "SELECT title FROM generated_clips WHERE id = :'clip_id';" \
  -v "clip_id=$CLIP_ID")
echo "Confirmando publicação:"
echo "  Clip ID:         #$CLIP_ID"
echo "  Título:          $CLIP_TITLE"
echo "  Status atual:    $CURRENT_STATUS"
echo "  YouTube Video:   https://youtu.be/$YT_VIDEO_ID"
echo ""
read -r -p "Confirmar? (s/N) " CONFIRM
if [[ "${CONFIRM,,}" != "s" ]]; then
  echo "Operação cancelada."
  exit 0
fi

# Atualiza generated_clips
postgres_exec_vars "
  UPDATE generated_clips
  SET
    status = 'published',
    youtube_video_id = :'youtube_video_id',
    published_at = CURRENT_TIMESTAMP,
    upload_error = NULL
  WHERE id = :'clip_id';" \
  -v "clip_id=$CLIP_ID" \
  -v "youtube_video_id=$YT_VIDEO_ID"

# Verifica se todos os clips do source_video estão em estado terminal
SOURCE_VIDEO_ID=$(postgres_exec_vars \
  "SELECT source_video_id FROM generated_clips WHERE id = :'clip_id';" \
  -v "clip_id=$CLIP_ID")
PENDING_CLIPS=$(postgres_exec_vars "
  SELECT COUNT(*) FROM generated_clips
  WHERE source_video_id = :'source_video_id'
    AND status NOT IN ('published', 'failed');" \
  -v "source_video_id=$SOURCE_VIDEO_ID")

if [[ "$PENDING_CLIPS" == "0" ]]; then
  # Todos os clips do vídeo fonte foram processados — atualiza source_videos
  postgres_exec_vars "
    UPDATE source_videos
    SET status = 'published', updated_at = CURRENT_TIMESTAMP
    WHERE id = :'source_video_id';" \
    -v "source_video_id=$SOURCE_VIDEO_ID"
  echo ""
  echo "  Todos os clipes do vídeo fonte #$SOURCE_VIDEO_ID foram processados."
  echo "  Status do vídeo fonte atualizado para 'published'."
fi

echo ""
echo "✔ Clipe #$CLIP_ID marcado como publicado."
echo "  YouTube: https://youtu.be/$YT_VIDEO_ID"
echo "  YouTube Studio: https://studio.youtube.com/video/$YT_VIDEO_ID/edit"
echo ""
