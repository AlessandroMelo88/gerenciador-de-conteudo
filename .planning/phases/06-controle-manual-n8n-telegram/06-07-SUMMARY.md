---
phase: 06-controle-manual-n8n-telegram
plan: 07
status: completed
completed_at: 2026-06-21
duration_minutes: ~45
requirements_addressed: [CTRL-01, CTRL-03, CTRL-04, CTRL-06]
---

# Plan 06-07 — Workflows n8n + SETUP + checkpoints manuais

Plano final da Phase 6. Entrega os workflows n8n executáveis, o procedimento operacional documentado e o validador estrutural local que dá feedback sem depender de Telegram/Cloudflare/n8n estarem online.

## Tasks

| # | Nome | Status | Commit |
|---|------|--------|--------|
| 1 | Completar 06-router.json + 06-cron-resumo-diario.json + SQL helper + atualizar SETUP.md | ✅ | `38902cc` |
| 2 | Setup operacional (Cloudflare Tunnel + Telegram bot + setWebhook + import workflows) | ⚠️ operator-side | — |
| 3 | Smoke end-to-end CTRL-01 (allowlist) + CTRL-06 (notify chega no Telegram) | ⚠️ operator-side | — |

### Task 1 (código — commit `38902cc`)

Entregas:

- `telegram-n8n/workflows/06-router.json` — router consolidado:
  - **Telegram Trigger** com `restrictToChatIds=={{ $env.TELEGRAM_CHAT_ID_ALLOWED }}` (CTRL-01)
  - **Switch Comando** roteia 6 comandos: `/status`, `/clipes`, `/aprovar`, `/rejeitar`, `/processar`, `/ajuda`
  - **/status** — query MySQL: counts de `pending`, `approved`, `published_today`
  - **/clipes** — `SELECT … WHERE status='pending' … LIMIT 10`
  - **/aprovar `<id>`** — guard `WHERE id=? AND status='pending'` + `ROW_COUNT()` check (rejeita se já approved/rejected/published)
  - **/rejeitar `<id>`** — `docker exec clip-processor python -m src.rejeitar <id>` (CTRL-03)
  - **/processar `<url>`** — `docker exec clip-processor python -m src.processar <url>` (CTRL-04)
  - **Webhook interno `/webhook/notify`** — recebe `upload_published`, `pipeline_failure`, `clip_ttl_warning` do clip-processor e encaminha mensagem ao chat do operador (CTRL-06)
  - Settings com `timezone: America/Sao_Paulo`
- `telegram-n8n/workflows/06-cron-resumo-diario.json` — cron `0 18 * * *` America/Sao_Paulo, conta clipes pending e envia resumo apenas ao chat permitido.
- `mysql/manual-workflow/approve-backlog.sql` — helper opcional: `UPDATE generated_clips SET status='approved' WHERE status='pending'` (guarda manual rápida para backlog antes do roteador).
- `telegram-n8n/SETUP.md` — procedimento atualizado para Cloudflare Tunnel + `setWebhook` (substitui o fluxo legado de polling/ngrok).

### Task 2 (operator-side + validação automatizada local)

Como o setup do bot Telegram, do Cloudflare Tunnel, do `setWebhook` e do import/activate dos workflows é 100% operacional (acesso a dashboards externos), Task 2 ficou marcada como **operator-side**. Para reduzir o risco de regressão silenciosa nos JSONs antes da importação, este plan adicionou um validador local:

- `scripts/validate-phase6-n8n.py` — 17 checks estruturais sem chamadas externas:
  - JSON parseável (router + cron)
  - Tipos de nó obrigatórios presentes
  - Telegram Trigger com allowlist via env
  - Switch roteia os 6 comandos esperados
  - Queries `/status`, `/clipes`, `/aprovar` contêm contratos críticos
  - `/rejeitar` e `/processar` chamam `docker exec clip-processor python -m src.<modulo>`
  - Webhook `/notify` roteia os 3 eventos proativos
  - Cron `0 18 * * *` em America/Sao_Paulo
  - `approve-backlog.sql` guarda `WHERE status='pending'`
  - `SETUP.md` contém Cloudflare Tunnel, `CLOUDFLARE_TUNNEL_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `setWebhook`, nomes dos workflows
- `telegram-n8n/SETUP.md` ganhou §3.4.1 instruindo o operador a rodar o validador antes do import.
- `.planning/phases/06-controle-manual-n8n-telegram/06-VALIDATION.md` atualizado: validation tasks `6-07-01`/`6-07-02` apontam para o script e estão ✅ green.
- `.planning/phases/06-controle-manual-n8n-telegram/.continue-here-06-07-manual.md` — memo de continuação documentando o roteiro operacional passo a passo para uma sessão futura retomar.

**Resultado da validação:**

```
$ python3 scripts/validate-phase6-n8n.py
PASS [router] router has required n8n node types
PASS [router] router timezone is America/Sao_Paulo
PASS [router] telegram trigger restricts to TELEGRAM_CHAT_ID_ALLOWED
PASS [router] switch routes all six Telegram commands
PASS [router] /status query covers pending, approved, published_today
PASS [router] /clipes query lists up to 10 pending clips
PASS [router] /aprovar validates integer input and guards pending status
PASS [router] /rejeitar validates integer input and calls src.rejeitar
PASS [router] /processar validates URL-like input and calls src.processar
PASS [router] notify webhook routes upload, failure, and TTL warning events
PASS [router] router has critical connection graph entries
PASS [cron] daily summary runs at 18h BRT
PASS [cron] daily summary counts pending clips
PASS [cron] daily summary sends only to allowed chat
PASS [cron] daily summary has critical connection graph entries
PASS [docs] approve-backlog.sql is present and guarded to pending clips
PASS [docs] SETUP.md documents Cloudflare, Telegram webhook, and workflow import
OK: Phase 6 n8n artifacts are structurally valid
```

17/17 PASS.

### Task 3 (operator-side — deferido)

Smoke end-to-end exige o bot ativo e o tunnel up. **Não foi executado.** Deferido para o operador conforme `.continue-here-06-07-manual.md`. Roteiro:

1. Do chat do operador (ID `5760918317`): `/ajuda`, `/status`, `/clipes` devem responder.
2. De um chat NÃO autorizado: `/ajuda` deve ser ignorado (sem execução em n8n) por 30s → confirma CTRL-01.
3. Aprovar 1 clip via `/aprovar <id>` durante a janela 19h-22h BRT → upload sai → mensagem `upload_published` chega no chat → confirma CTRL-06.

## Decisões registradas

- **Router consolidado num único JSON** (em vez de 6 sub-workflows) — facilita import/export, allowlist é aplicada uma vez no trigger
- **Cron separado** do router — schedule trigger não compartilha contexto com Telegram Trigger; manter em arquivos distintos respeita o padrão n8n
- **Webhook `/notify` interno** dentro do mesmo router — single source of truth para mensagens proativas; n8n encaminha via Telegram node usando as mesmas credenciais do bot
- **`approve-backlog.sql` como helper opcional** — operador pode rodar via `mysql` CLI para aprovar backlog acumulado antes de adotar o fluxo `/aprovar`; guarded em `WHERE status='pending'` para idempotência
- **`validate-phase6-n8n.py` como port de entrada para CI futuro** — não substitui smoke real mas previne regressão silenciosa nos JSONs antes do import

## Arquivos modificados/criados

```
telegram-n8n/workflows/06-router.json                      (preenchido)
telegram-n8n/workflows/06-cron-resumo-diario.json          (preenchido)
telegram-n8n/SETUP.md                                      (atualizado: Cloudflare Tunnel + §3.4.1 validador)
mysql/manual-workflow/approve-backlog.sql                  (criado)
scripts/validate-phase6-n8n.py                             (criado — 17 checks)
.planning/phases/06-.../06-VALIDATION.md                   (6-07-01/02 ✅ green)
.planning/phases/06-.../.continue-here-06-07-manual.md     (memo operacional)
.planning/STATE.md                                         (atualizado)
.planning/ROADMAP.md                                       (06-07 marcado)
```

## Pendências (não bloqueantes para fechamento de código)

- Operador precisa executar `.continue-here-06-07-manual.md` para CTRL-01 + CTRL-06 ficarem GREEN end-to-end na realidade
- Primeiro upload real ainda deve ser `YOUTUBE_PRIVACY_STATUS=private` + `MAX_UPLOADS_PER_DAY=1` (carry-over da Phase 5)

## Self-Check

- [x] Task 1 commitada atomicamente
- [x] Task 2 entregou artefato automatizado (validador) + handoff documentado para operador
- [x] Task 3 explicitamente deferida; pendências registradas em STATE/blockers
- [x] SUMMARY criado
- [x] STATE.md atualizado
- [x] ROADMAP.md atualizado
- [x] Validador estrutural: 17/17 PASS
