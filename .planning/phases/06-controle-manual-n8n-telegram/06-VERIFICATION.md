---
phase: 06-controle-manual-n8n-telegram
status: human_needed
created: 2026-06-21
verifier: inline (Claude main loop — gsd-verifier subagent caiu por API error 2x)
test_suite_result: 104/104 passed in 240.76s
---

# Phase 6 Verification — Controle Manual N8N + Telegram

## Goal

Operador aprova ou rejeita clipes pré-cortados via comandos no Telegram orquestrados pelo n8n; pipeline continua autônomo até a aprovação, e o publisher passa a publicar apenas clipes com status `approved`, respeitando quota e janela horária existentes.

## Method

Verificação inline (o subagent gsd-verifier caiu duas vezes por API connection error). Validações realizadas:
1. `grep` automatizado contra padrões críticos em todos os arquivos modificados pelos 7 plans
2. Validação JSON dos workflows n8n via `python3 scripts/validate-phase6-n8n.py` — 17/17 PASS
3. Full test suite local: 104/104 passed em 240.76s (sem regressão em Phases 1-5)

## Success Criteria — Code-Side Verification

| # | Critério | Verificação | Status |
|---|----------|-------------|--------|
| SC1 | Bot Telegram responde aos 6 comandos + ignora chats fora da allowlist | Router `06-router.json` tem TelegramTrigger com `restrictToChatIds=={{ $env.TELEGRAM_CHAT_ID_ALLOWED }}` e Switch com 6 rules + fallback `ajuda` | ✅ código |
| SC2 | Migration adiciona approved/rejected ao ENUM; publisher seleciona approved | `mysql/init/05-controle-manual-migration.sql` contém `approved`+`rejected`; `publisher.py:63` usa `WHERE gc.status = 'approved'` e guard `WHERE id=%s AND status='approved'` | ✅ |
| SC3 | `/aprovar` muda pending→approved; `/rejeitar` muda para rejected + apaga MP4 mantendo raw | Router `Aprovar: UPDATE` tem guard `AND status='pending'` + `ROW_COUNT()` check; `rejeitar.py` faz UPDATE com guard `status IN ('pending','approved')`, `os.remove(clip_path)`, NÃO deleta raw video | ✅ |
| SC4 | `/processar` baixa metadata, insere/atualiza `source_videos` status `pending`, idempotente | `processar.py`: `parse_video_id` (5 formatos), `fetch_metadata` via yt-dlp `skip_download=True`, `upsert_source_video` idempotente (SELECT-then-INSERT) com pseudo-channel `manual:UCxxx active=FALSE` | ✅ |
| SC5 | Worker TTL converte pending→rejected após 48h; warn 24h antes | `ttl_worker.run_ttl_once`: UPDATE em massa com `INTERVAL TTL_HOURS HOUR`; warn idempotente via `redis.set('clip_warned:{id}', '1', nx=True, ex=24*3600)`; `IntervalTrigger(hours=1)` em `main.py` com `id='clip_pending_ttl'` | ✅ |
| SC6 | n8n recebe webhook via Cloudflare Tunnel (sem ngrok); allowlist 5760918317 | docker-compose raiz tem serviço `cloudflared` + env vars `WEBHOOK_URL=${N8N_WEBHOOK_URL}`, `N8N_HOST=${N8N_HOST}`, `N8N_PROTOCOL=https`; allowlist via env `TELEGRAM_CHAT_ID_ALLOWED` (default `5760918317` em `.env.example`) | ✅ código (⚠️ tunnel ativo = operator-side) |
| SC7 | 3 notificações proativas: upload_published, pipeline_failure, resumo 18h | `publisher.py` chama `notify('upload_published', {...})` após `_mark_clip_published`; `pipeline_runner.py` chama `notify('pipeline_failure', {stage, error_msg})` em 3 stages; cron `06-cron-resumo-diario.json` com `0 18 * * *` America/Sao_Paulo e `skip se 0 pendentes` (IF "Tem Pending?") | ✅ |

## Requirement Traceability

| ID | Origem | Coverage | Status |
|----|--------|----------|--------|
| CTRL-01 | Plan 06-01 (skeleton), 06-07 (router allowlist + smoke) | Código ✅; allowlist real exige operador rodar setWebhook | ⚠️ operator smoke pendente |
| CTRL-02 | Plan 06-01 (ENUM), 06-02 (publisher swap) | ✅ código + 10/10 testes publisher GREEN |
| CTRL-03 | Plan 06-01 (stub), 06-03 (implementação) | ✅ código + 3/3 testes rejeitar GREEN |
| CTRL-04 | Plan 06-01 (stub), 06-04 (implementação) | ✅ código + 7/7 testes processar GREEN |
| CTRL-05 | Plan 06-01 (stub), 06-05 (implementação) | ✅ código + 3/3 testes ttl_worker GREEN |
| CTRL-06 | Plan 06-01 (stub), 06-06 (notifier + integrações + cloudflared) | Código ✅ + 2/2 testes notifier GREEN; entrega real exige operador subir tunnel | ⚠️ operator smoke pendente |

Todos os 6 requirement IDs presentes em `REQUIREMENTS.md` (6 ocorrências de `CTRL-0[1-6]`).

## Test Suite Results

```
104 passed in 240.76s (0:04:00)
```

Sem regressão em Phases 1-5. Cobertura específica Phase 6:
- `test_publisher.py`: 10/10 (3 da nova classe `TestPublishApprovedClips` + 7 originais)
- `test_rejeitar.py`: 3/3 (`test_marca_rejected`, `test_apaga_mp4_mantem_raw`, `test_clip_nao_existe`)
- `test_processar.py`: 7/7 (`TestParseVideoId` 5 + `TestUpsertSourceVideo` 2)
- `test_ttl_worker.py`: 3/3 (`TestExpire` 1 + `TestWarn` 2)
- `test_telegram_notifier.py`: 2/2 (`test_success_event`, `test_failure_event`)

## Structural Validation

`scripts/validate-phase6-n8n.py` — 17/17 PASS:
- Router: 11 checks (tipos de nó, timezone, allowlist, 6 comandos, queries SQL, ExecuteCommand, webhook /notify, connections)
- Cron: 4 checks (timezone, cron expression, COUNT(*) query, allowlist no envio)
- Docs: 2 checks (approve-backlog.sql + SETUP.md completos)

## Gaps / Pendências Operacionais

Status `human_needed` — não há gaps de código, mas 2 itens exigem operador para CTRL-01 e CTRL-06 ficarem GREEN end-to-end:

### Human Verification Required

1. **Setup Cloudflare Tunnel + bot Telegram + setWebhook**
   - Memo passo a passo: `.planning/phases/06-controle-manual-n8n-telegram/.continue-here-06-07-manual.md`
   - Procedimento: `telegram-n8n/SETUP.md`
   - Após setup: subir `cloudflared`, importar/ativar `06-router.json` + `06-cron-resumo-diario.json` no n8n

2. **Smoke tests end-to-end (CTRL-01 + CTRL-06)**
   - Do chat `5760918317`: `/ajuda`, `/status`, `/clipes` devem responder
   - De um chat NÃO permitido: `/ajuda` deve ser ignorado por 30s → confirma allowlist (CTRL-01)
   - Aprovar 1 clip via `/aprovar <id>` durante janela 19h-22h BRT → upload sai → mensagem `upload_published` chega no Telegram → confirma CTRL-06

### Operator carry-over de Phase 5

- Primeiro upload real deve usar `YOUTUBE_PRIVACY_STATUS=private` + `MAX_UPLOADS_PER_DAY=1` (já registrado em STATE/Blockers)

## Recommendation

Todo o trabalho de código da Phase 6 está **concluído e verificado** com cobertura automatizada de 104 testes + 17 checks estruturais. Os itens marcados ⚠️ são exclusivamente operator-side e foram documentados de forma que uma sessão futura (ou o operador diretamente) possa fechar sem retornar ao código.

Status sugerido para Phase 6: **complete (code) + 2 itens human-verification documentados**.
