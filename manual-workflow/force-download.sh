#!/usr/bin/env bash
# Força o download de vídeos com status 'pending' no banco.
# Útil para operar manualmente um backlog específico sem bypassar o downloader.
# Uso:
#   ./manual-workflow/force-download.sh           # processa todos os pending
#   ./manual-workflow/force-download.sh --limit 3 # processa até 3 vídeos

set -euo pipefail


LIMIT=10
if [[ $# -gt 0 && $# -ne 2 || $# -eq 2 && "$1" != "--limit" ]]; then
  echo "Uso: $0 [--limit N]" >&2
  exit 2
fi
if [[ $# -eq 2 ]]; then
  LIMIT="$2"
fi
if ! [[ "$LIMIT" =~ ^[1-9][0-9]*$ ]]; then
  echo "Erro: LIMIT deve ser um inteiro positivo." >&2
  exit 2
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         FORCE DOWNLOAD — Canal de Cortes                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Executando download de até $LIMIT vídeos pendentes..."
echo ""

docker compose exec -T clip-processor env "FORCE_DOWNLOAD_LIMIT=$LIMIT" python - <<'PY'
import os

from src.db import get_db_connection, update_status
from src.downloader import VIDEOS_DIR, download_video


limit = int(os.environ['FORCE_DOWNLOAD_LIMIT'])
conn = get_db_connection()
try:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT youtube_video_id, title FROM source_videos "
            "WHERE status = 'pending' AND paused = FALSE "
            "ORDER BY priority DESC, queue_position IS NULL, queue_position ASC, "
            "published_at DESC LIMIT %s",
            (limit,),
        )
        videos = cur.fetchall()

    if not videos:
        print('Nenhum vídeo com status pending encontrado.')
    else:
        print(f'Encontrados {len(videos)} vídeo(s) pendentes.')
        for video in videos:
            video_id = video['youtube_video_id']
            title = video['title'] or video_id
            print(f'[{video_id}] {title[:60]}')
            update_status(conn, video_id, 'downloading')
            if download_video(video_id):
                local_path = f'{VIDEOS_DIR}/{video_id}.mp4'
                update_status(conn, video_id, 'downloaded', local_path=local_path)
                print(f'  OK: {local_path}')
            else:
                update_status(conn, video_id, 'failed', clear_local_path=True)
                print('  ERRO: downloader retornou falha')
finally:
    conn.close()
PY

echo ""
echo "Done. Use list-pending-clips.sh para ver os clipes gerados."
echo ""
