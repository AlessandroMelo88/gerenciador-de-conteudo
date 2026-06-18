---
phase: 02-aquisicao-de-videos
plan: "04"
subsystem: infra
tags: [apscheduler, python, docker, daemon, scheduler, rss]

# Dependency graph
requires:
  - phase: 02-aquisicao-de-videos
    provides: db.py, rss_poller.py, dedup.py, downloader.py — módulos core do pipeline
  - phase: 01-infraestrutura-base
    provides: Docker Compose com clip-processor, MySQL e Redis configurados

provides:
  - Daemon BlockingScheduler funcional conectando todos os módulos do pipeline
  - Entry point main.py com agendamento RSS a cada 6 horas
  - Recovery automático de jobs stuck em 'downloading' na inicialização
  - Execução imediata do poll na boot (sem esperar 6 horas)
  - Signal handlers SIGTERM/SIGINT para shutdown graceful

affects:
  - 03-transcricao
  - 04-selecao-de-momentos
  - 05-publicacao

# Tech tracking
tech-stack:
  added: [apscheduler]
  patterns:
    - BlockingScheduler com coalesce=True e max_instances=1 para evitar execuções paralelas
    - Guard if __name__ == '__main__' para isolar scheduler de imports nos testes
    - Recovery-before-poll: recover_stuck_downloads antes de poll_all_channels na boot

key-files:
  created: []
  modified:
    - canaldecortes/clip-processor/src/main.py

key-decisions:
  - "Guard if __name__ == '__main__' mantido para que imports nos testes não disparem o scheduler"
  - "recover_stuck_downloads chamado ANTES de poll_all_channels — evita re-polling de jobs já em processamento"
  - "coalesce=True + max_instances=1 — evita execuções paralelas do poll se a anterior demorar"

patterns-established:
  - "Daemon pattern: recovery → poll imediato → scheduler blocking — padrão para daemons do pipeline"
  - "Logs com timestamp e prefixo [ACQU] para filtrar facilmente em docker logs"

requirements-completed: [ACQU-01, ACQU-02, ACQU-03, ORC-02]

# Metrics
duration: ~10min
completed: 2026-06-18
---

# Phase 2 Plan 04: Daemon main.py Summary

**BlockingScheduler APScheduler unindo todos os módulos do pipeline num daemon Docker com poll RSS a cada 6h, recovery on startup e execução imediata na boot**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-18T16:00:00Z (approx — Task 1 executada na sessão anterior)
- **Completed:** 2026-06-18T16:33:30Z
- **Tasks:** 2 (1 auto + 1 checkpoint:human-verify aprovado)
- **Files modified:** 1

## Accomplishments

- main.py substituiu o stub de Phase 1 com daemon completo usando APScheduler BlockingScheduler
- Recovery automático de jobs stuck em 'downloading' na inicialização — pitfall documentado em RESEARCH.md tratado
- Checkpoint humano aprovado: container clip-processor ativo, logs mostram "[ACQU] Daemon iniciado — poll RSS a cada 6 horas"

## Task Commits

Cada tarefa foi comitada atomicamente:

1. **Task 1: main.py daemon BlockingScheduler com recovery on startup** - `2ed7151` (feat)
2. **Task 2: checkpoint:human-verify** - aprovado pelo usuário ("aprovado")

**Plan metadata:** (este commit) (docs: complete plan)

## Files Created/Modified

- `canaldecortes/clip-processor/src/main.py` — Daemon entry point com BlockingScheduler, signal handlers SIGTERM/SIGINT, recover_stuck_downloads na boot e poll imediato na inicialização

## Decisions Made

- Guard `if __name__ == '__main__'` mantido para isolar scheduler dos testes — imports não disparam o agendador
- `recover_stuck_downloads` chamado ANTES de `poll_all_channels` — pitfall documentado: container restart não deve re-processar jobs já em andamento
- `coalesce=True + max_instances=1` no scheduler — evita execuções paralelas do poll caso uma iteração demore mais que 6 horas

## Deviations from Plan

None - plano executado exatamente como escrito.

## Issues Encountered

None — implementação seguiu exatamente o padrão APScheduler do RESEARCH.md Pattern 1.

## User Setup Required

None - nenhuma configuração externa necessária além do que já estava no .env.

## Next Phase Readiness

- Pipeline de aquisição completo: daemon coleta RSS, filtra duplicatas via Redis, baixa vídeos e armazena no banco
- Phase 3 (transcrição) pode consumir vídeos com status 'downloaded' da tabela source_videos
- Nenhum bloqueio identificado para avançar à Phase 3

---
*Phase: 02-aquisicao-de-videos*
*Completed: 2026-06-18*
