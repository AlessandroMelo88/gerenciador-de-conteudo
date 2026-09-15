"""
rejeitar.py — Rejeição manual de clip via comando /rejeitar do Telegram (CTRL-03).

Implementado em Plan 06-03.

Marca o clip como 'rejected' (apenas se status atual estiver em pending|approved),
remove do disco todos os artefatos do clip (MP4 final, <id>_raw.mp4, <id>_subtitled.mp4,
<id>.srt e thumbnail) e PRESERVA o raw video do source_videos para permitir recorte
futuro (decisão explícita em 06-CONTEXT.md).

É o único caminho de rejeição que apaga arquivo: o painel monta o volume de vídeos
read-only e chama este módulo via POST /internal/reject-clip.

Uso CLI:
    docker exec clip-processor python -m src.rejeitar <clip_id>

Chamado pelo n8n via executeCommand no workflow 06-router.

Exit codes:
    0 — sucesso (clip marcado como rejected; MP4 removido quando existia)
    1 — clip não existe
    2 — clip em status terminal/invalido (rejected, published, failed, cutting, publishing)
        ou argumentos inválidos no entrypoint CLI

Exporta:
    - rejeitar(clip_id) -> int
"""
import os
import sys

# Alias `db_connect` para preservar o nome esperado pelos testes
# (patch('src.rejeitar.db_connect', ...))
from src.db import get_db_connection as db_connect

VIDEOS_DIR = '/app/videos'


def _clip_artifacts(clip_id: int, clip_path: str | None) -> list[str]:
    """Arquivos em disco de um clip. Só clip_path e thumbnail_path ficam no banco;
    <id>_raw.mp4, <id>_subtitled.mp4 e <id>.srt não estão em coluna nenhuma
    (CLAUDE.md, regra 3), então o caminho é montado pelo id."""
    paths = [
        os.path.join(VIDEOS_DIR, 'clips', f'{clip_id}.mp4'),
        os.path.join(VIDEOS_DIR, 'clips', f'{clip_id}_raw.mp4'),
        os.path.join(VIDEOS_DIR, 'clips', f'{clip_id}_subtitled.mp4'),
        os.path.join(VIDEOS_DIR, 'clips', f'{clip_id}.srt'),
        os.path.join(VIDEOS_DIR, 'thumbnails', f'{clip_id}.jpg'),
    ]
    if clip_path and clip_path not in paths:
        paths.insert(0, clip_path)
    return paths


# Status do clip que aceitam transição para 'rejected'.
# - pending: clip recém-cortado aguardando aprovação manual
# - approved: clip já aprovado mas ainda não publicado (race: rejeitar vence o publisher)
_REJECTABLE_STATUSES = ('pending', 'approved')


def rejeitar(clip_id: int) -> int:
    """Marca o clip como rejected, remove os artefatos do clip, preserva raw video.

    Comportamento:
      1. SELECT clip_path, status FROM generated_clips WHERE id=clip_id
      2. Se clip não existe → retorna 1
      3. Se status NÃO está em (pending, approved) → retorna 2
      4. UPDATE generated_clips SET status='rejected'
         WHERE id=clip_id AND status IN ('pending','approved')
      5. Se UPDATE afetou linha → remove cada artefato do clip que existir no disco
      6. NÃO remove source_videos.local_path (raw video preservado para recorte futuro)

    Args:
        clip_id: ID inteiro do clip na tabela generated_clips

    Returns:
        0 em sucesso, 1 se clip não existe, 2 se status inválido para rejeição.
    """
    conn = db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT clip_path, status FROM generated_clips WHERE id=%s',
                (clip_id,)
            )
            row = cur.fetchone()

            if not row:
                print(f'ERRO: clip {clip_id} não existe')
                return 1

            if row['status'] not in _REJECTABLE_STATUSES:
                print(
                    f'ERRO: clip {clip_id} está em status {row["status"]!r} '
                    f'(esperado: pending ou approved)'
                )
                return 2

            cur.execute(
                "UPDATE generated_clips SET status='rejected' "
                "WHERE id=%s AND status IN ('pending', 'approved')",
                (clip_id,)
            )
            affected = cur.rowcount

        conn.commit()

        removed = []
        if affected:
            for path in _clip_artifacts(clip_id, row['clip_path']):
                if os.path.exists(path):
                    os.remove(path)
                    removed.append(path)
        print(f'OK: clip {clip_id} rejeitado, {len(removed)} arquivo(s) removido(s)')
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python -m src.rejeitar <clip_id>')
        sys.exit(2)
    try:
        _clip_id = int(sys.argv[1])
    except ValueError:
        print(f'ERRO: clip_id inválido: {sys.argv[1]!r}')
        sys.exit(2)
    sys.exit(rejeitar(_clip_id))
