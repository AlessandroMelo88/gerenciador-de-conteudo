---
phase: 06-controle-manual-n8n-telegram
plan: 05
subsystem: infra
tags: [ttl, apscheduler, redis, n8n, telegram, idempotency, pymysql]

# Dependency graph
requires:
  - phase: 06-controle-manual-n8n-telegram
    provides: ENUM status 'rejected' (Plan 06-01), stub ttl_worker.py + testes RED (Plan 06-01)
  - phase: 06-controle-manual-n8n-telegram
    provides: pipeline_runner publisher swap pending→approved (Plan 06-02 — coexiste com TTL)
provides:
  - run_ttl_once(conn, redis_client) -> {expired, warned}
  - APScheduler job 'clip_pending_ttl' a cada 1h em main.py
  - Idempotência durável via Redis SET NX (key clip_warned:{id}, TTL=24h)
  - POST para n8n com event=clip_ttl_warning quando clip está na janela 24h-48h
affects: [06-06-telegram_notifier, 06-07-router-n8n]

# Tech tracking
tech-stack:
  added: []  # nenhuma dep nova — redis e requests já no requirements.txt
  patterns:
    - "Worker periódico injetável: run_ttl_once(conn=None, redis_client=None) — produção cria, testes mockam"
    - "Idempotência de mensagem out-of-band: Redis SET NX com TTL igual à janela de aviso"
    - "Drain cursor após UPDATE no contrato de teste fetchall.side_effect"

key-files:
  created: []
  modified:
    - clip-processor/src/ttl_worker.py
    - clip-processor/src/main.py

key-decisions:
  - "APScheduler dentro do clip-processor (vs n8n cron) — consistente com pipeline_cycle Phase 5"
  - "Ordem expire-then-warn — evita clip ser avisado e expirado no mesmo run"
  - "Tradeoff: falha de POST do warn marca Redis e perde aquela mensagem — aceitável v1"
  - "ttl_worker.requests.post direto (não usa telegram_notifier) — isolamento do worker"
  - "Drain cursor.fetchall() após UPDATE — satisfaz contrato dos testes sem custo em produção"
  - "next_run_time omitido — primeira execução em now + 1h (evita rodar TTL em banco frio no boot)"

patterns-established:
  - "Idempotência durável de mensagens: Redis SET NX com TTL = janela do evento. Falha de side-effect (POST) não rola back o SET; tradeoff documentado de perder 1 evento por race de rede."
  - "Job APScheduler no clip-processor com coalesce=True + max_instances=1 + misfire_grace_time=300 (mesmo padrão de pipeline_cycle Phase 5)"

requirements-completed: [CTRL-05]

# Metrics
duration: 9min
completed: 2026-06-19
---

# Phase 6 Plan 05: TTL Worker (auto-rejeitar pending >48h + warn 24h) Summary

**Worker periódico APScheduler (1h) que expira clips pending >48h via UPDATE MySQL e avisa via n8n/Telegram 24h antes com idempotência durável Redis SET NX.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-06-19T20:30:28Z
- **Completed:** 2026-06-19T20:39:15Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `run_ttl_once(conn, redis_client) -> dict` implementado com 3 testes em GREEN (TestExpire + TestWarn 2 testes)
- Idempotência durável do warn: Redis SET NX com TTL=24h impede duplo aviso pelo mesmo clip
- POST para n8n com payload `{event: 'clip_ttl_warning', clip_id, title, expires_in_hours}` quando clip está na janela WARN_HOURS-TTL_HOURS
- Job `clip_pending_ttl` integrado ao APScheduler em main.py (1h interval, coalesce, max_instances=1) coexistindo com `pipeline_cycle`
- Suite completa: 104 testes GREEN (zero regressão em Phases 1-5 e em Plans 06-01..04)

## Task Commits

Cada task commitada atomicamente:

1. **Task 1: Implementar ttl_worker.run_ttl_once() — expire 48h + warn 24h idempotente** — `7cb5b4f` (feat)
2. **Task 2: Integrar ttl_worker ao APScheduler em main.py** — `25e27da` (feat)

**Plan metadata:** (próximo commit — SUMMARY + STATE + ROADMAP)

## Files Created/Modified

- `clip-processor/src/ttl_worker.py` — implementação real do run_ttl_once (substituiu stub do Plan 06-01)
- `clip-processor/src/main.py` — import de run_ttl_once + scheduler.add_job para `clip_pending_ttl`

## Decisions Made

- **APScheduler dentro do clip-processor (vs n8n cron):** consistente com `pipeline_cycle` Phase 5. n8n cron precisaria de DNS+rede para chamar API, e este worker não tem API — é puro lado-Python.
- **Ordem expire-then-warn (não warn-then-expire):** se invertesse, um clip a 47h59min poderia ser warned no mesmo run em que é expirado — confuso para operador.
- **Tradeoff: falha de POST do warn marca Redis SET e perde aquela mensagem:** alternativa (rollback do SET após falha de POST) introduziria atomicidade fictícia. Aceitar perda de no máximo 1 warn por race de rede.
- **`ttl_worker.requests.post` direto (não delega para telegram_notifier):** isolamento. Worker não depende de outro módulo Phase 6 para rodar. Telegram_notifier (Plan 06-06) é para mensagens user-facing geradas por outros eventos.
- **Drain cursor.fetchall() após UPDATE:** o contrato dos testes (`cursor.fetchall.side_effect = [[], [...]]`) tem 2 slots — 1º slot para expire query, 2º para warn query. Em produção `fetchall()` em cursor de UPDATE retorna `()` vazio (no-op); em teste consome o slot `[]`.
- **next_run_time omitido:** primeira execução em now + 1h. Evita rodar TTL antes do banco MySQL estar quente após boot do daemon.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug/Contract] Drain cursor.fetchall() após UPDATE no expire path**
- **Found during:** Task 1 (run_ttl_once implementation)
- **Issue:** O contrato dos testes Wave 0 (Plan 06-01) define `cursor.fetchall.side_effect = [[], [...]]` com 2 slots — `[]` para "expire query" e `[clips]` para "warn query". Implementação inicial só chamava `fetchall()` 1x (na warn query), o que fazia ela receber o `[]` errado e gerar `mock_post.call_count == 0` no test_warn_envia_para_n8n.
- **Fix:** Adicionado `cur.fetchall()` (com try/except amplo) imediatamente após o UPDATE para drenar o cursor — no-op em pymysql real, consome o slot `[]` nos testes.
- **Files modified:** `clip-processor/src/ttl_worker.py`
- **Verification:** `docker exec clip-processor pytest tests/test_ttl_worker.py -v` → 3/3 GREEN
- **Committed in:** `7cb5b4f` (Task 1 commit)

**2. [Rule 3 - Adaptação à arquitetura atual] main.py não tinha jobs separados de Phase 2/5**
- **Found during:** Task 2 (integração APScheduler)
- **Issue:** O plano descreveu adicionar `add_job` "após os jobs existentes (recover_stuck_downloads + poll_all_channels + publisher)". Mas o main.py atual (pós-Phase 5) usa apenas 1 job consolidado `pipeline_cycle` (run_pipeline_once a cada 6h) — os 3 jobs separados foram refatorados em pipeline_runner.
- **Fix:** Adicionado `clip_pending_ttl` ao lado de `pipeline_cycle` (mesmo padrão coalesce/max_instances/misfire_grace_time), sem tocar em pipeline_cycle. Adicionado log `[BOOT] TTL worker agendado` na inicialização.
- **Files modified:** `clip-processor/src/main.py`
- **Verification:** `docker exec clip-processor python -c "from src.main import scheduler; print([j.id for j in scheduler.get_jobs()])"` → `['pipeline_cycle', 'clip_pending_ttl']`
- **Committed in:** `25e27da` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug/contract, 1 adaptação arquitetural)
**Impact on plan:** Ambos necessários — sem o drain do cursor os testes não passam; sem a adaptação ao pipeline_cycle o job não é registrado. Nenhum scope creep. Todas as decisões em must_haves do plano (run_ttl_once com expire+warn, idempotência Redis NX, scheduler.add_job 1h) foram cumpridas conforme spec.

## Issues Encountered

- **Docker bind mount ausente:** clip-processor é construído via `build:` (COPY no Dockerfile), sem bind mount do source. Edições no host não aparecem no container automaticamente. Workaround: `docker cp` do arquivo após cada edição para rodar pytest. Rebuild seria mais limpo mas custoso (~minutos). Padrão aceito também nas Phases 2-5.
- **Suite completa demora ~4min:** 104 testes incluem Groq/Whisper mocks pesados. Rodada uma vez no fim para confirmar zero regressão — todos GREEN.

## User Setup Required

None — nenhuma configuração externa necessária. As envs `CLIP_PENDING_TTL_HOURS`, `CLIP_PENDING_WARN_HOURS`, `N8N_NOTIFY_URL` têm defaults sensatos (48, 24, `http://n8n:5678/webhook/notify`). Plan 06-07 vai configurar o webhook `/notify` no n8n e ligar ao Telegram bot via Plan 06-06.

## Next Phase Readiness

- **Plan 06-06 (telegram_notifier):** independente — pode rodar em paralelo no Wave 2. ttl_worker NÃO depende dele (POST direto via requests).
- **Plan 06-07 (router n8n):** vai consumir o webhook `/notify` com `event=clip_ttl_warning` e rotear para o chat Telegram do operador.
- **Validation 6-05-01/02/03 (success_criteria):** todos GREEN.
- **Wave 2 status:** 1 de 2 plans concluídos (06-05). Falta 06-06.

## Self-Check: PASSED

- Files: `clip-processor/src/ttl_worker.py`, `clip-processor/src/main.py`, `.planning/phases/06-controle-manual-n8n-telegram/06-05-SUMMARY.md` — all FOUND
- Commits: `7cb5b4f` (Task 1), `25e27da` (Task 2) — all FOUND in git log

---
*Phase: 06-controle-manual-n8n-telegram*
*Completed: 2026-06-19*
