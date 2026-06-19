#!/usr/bin/env bash
# Força o download de vídeos com status 'pending' no banco.
# Útil enquanto o wiring gap do download não está resolvido automaticamente.
# Uso:
#   ./manual-workflow/force-download.sh           # processa todos os pending
#   ./manual-workflow/force-download.sh --limit 3 # processa até 3 vídeos

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

LIMIT=10
for arg in "$@"; do
  case "$arg" in
    --limit) LIMIT_NEXT=1 ;;
    *) [[ "${LIMIT_NEXT:-0}" == "1" ]] && { LIMIT="$arg"; LIMIT_NEXT=0; } ;;
  esac
done

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         FORCE DOWNLOAD — Canal de Cortes                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Executando download de até $LIMIT vídeos pendentes..."
echo ""

docker exec clip-processor python -c "
import sys
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

from src.db import get_connection
from src.downloader import download_video
from src.dedup import VideoDeduplicator

limit = $LIMIT

conn = get_connection()
dedup = VideoDeduplicator(conn)

with conn.cursor() as cur:
    cur.execute('''
        SELECT id, youtube_video_id, title
        FROM source_videos
        WHERE status = %s
        LIMIT %s
    ''', ('pending', limit))
    videos = cur.fetchall()

if not videos:
    print('Nenhum vídeo com status pending encontrado.')
    sys.exit(0)

print(f'Encontrados {len(videos)} vídeo(s) pendentes.')
print()

for vid in videos:
    vid_id, yt_id, title = vid['id'], vid['youtube_video_id'], vid['title']
    print(f'[{vid_id}] {title[:60]}...' if title and len(title) > 60 else f'[{vid_id}] {title}')
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE source_videos SET status = %s WHERE id = %s',
                ('downloading', vid_id)
            )
        conn.commit()

        url = f'https://www.youtube.com/watch?v={yt_id}'
        local_path = download_video(url, vid_id)

        with conn.cursor() as cur:
            cur.execute(
                'UPDATE source_videos SET status = %s, local_path = %s WHERE id = %s',
                ('downloaded', local_path, vid_id)
            )
        conn.commit()
        print(f'  OK: {local_path}')
    except Exception as e:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE source_videos SET status = %s WHERE id = %s',
                ('failed', vid_id)
            )
        conn.commit()
        print(f'  ERRO: {e}')
    print()

conn.close()
print('Concluído.')
"

echo ""
echo "Done. Use list-pending-clips.sh para ver os clipes gerados."
echo ""
