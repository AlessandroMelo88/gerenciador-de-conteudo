"""
rejeitar.py — Rejeição manual de clip via comando /rejeitar do Telegram.

Stub Phase 6 (Plan 06-01). Implementação real em Plan 06-03.

Marca o clip como 'rejected', apaga o .mp4 final mas mantém o raw do source_video
(para reuso em re-cortes futuros).

Exporta:
  - rejeitar(clip_id) -> int (exit code: 0=sucesso, 1=clip não existe, 2=erro)
"""
import sys


def rejeitar(clip_id: int) -> int:
    """Marca clip_id como rejected, apaga clip_path mas mantém raw do source_video."""
    raise NotImplementedError("Phase 6 — implementar em Plan 03")


if __name__ == '__main__':
    sys.exit(rejeitar(int(sys.argv[1])))
