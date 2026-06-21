---
phase: 6
slug: controle-manual-n8n-telegram
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-19
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (já configurado em `clip-processor/pytest.ini`) |
| **Config file** | `clip-processor/pytest.ini` (`addopts = -v --tb=short`) |
| **Quick run command** | `docker exec clip-processor pytest tests/test_<file>.py -x` |
| **Full suite command** | `docker exec clip-processor pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~30s suite completa, ~5s por arquivo |

Fixtures compartilhadas (já em `clip-processor/tests/conftest.py`): `mock_db_conn`, `mock_redis`, `sample_video_id`.

---

## Sampling Rate

- **After every task commit:** `docker exec clip-processor pytest tests/test_<arquivo>.py -x`
- **After every plan wave:** `docker exec clip-processor pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite verde + 3 checkpoints manuais (Telegram allowlist, Cloudflare Tunnel, `getWebhookInfo`)
- **Max feedback latency:** ~30 segundos para suíte completa

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-W0-01 | 01 | 0 | CTRL-02 | smoke (SQL) | `docker exec mysql mysql -uclips_user -p$CLIPS_DB_PASSWORD clips_automation -e "SHOW COLUMNS FROM generated_clips LIKE 'status'" \| grep -E 'approved.*rejected'` | ❌ W0 (`mysql/init/05-controle-manual-migration.sql`) | ⬜ pending |
| 6-W0-02 | 01 | 0 | CTRL-02 | unit | `pytest tests/test_publisher.py::TestPublishApprovedClips -x` | ✅ (modificar) | ⬜ pending |
| 6-W0-03 | 01 | 0 | CTRL-03 | unit | `pytest tests/test_rejeitar.py -x` | ❌ W0 | ⬜ pending |
| 6-W0-04 | 01 | 0 | CTRL-04 | unit | `pytest tests/test_processar.py -x` | ❌ W0 | ⬜ pending |
| 6-W0-05 | 01 | 0 | CTRL-05 | unit | `pytest tests/test_ttl_worker.py -x` | ❌ W0 | ⬜ pending |
| 6-W0-06 | 01 | 0 | CTRL-06 | unit | `pytest tests/test_telegram_notifier.py -x` | ❌ W0 | ⬜ pending |
| 6-W0-07 | 01 | 0 | CTRL-01 | smoke (JSON) | `python -c "import json; w=json.load(open('telegram-n8n/workflows/06-router.json')); assert any(n['type']=='n8n-nodes-base.telegramTrigger' and 'restrictToChatIds' in n['parameters'].get('additionalFields',{}) for n in w['nodes'])"` | ❌ W0 | ⬜ pending |
| 6-02-01 | 02 | 1 | CTRL-02 | unit | `pytest tests/test_publisher.py::TestPublishApprovedClips::test_seleciona_apenas_approved -x` | ✅ | ⬜ pending |
| 6-02-02 | 02 | 1 | CTRL-02 | unit | `pytest tests/test_publisher.py::TestPublishApprovedClips::test_quota_blocked_leaves_clip_as_approved -x` | ✅ | ⬜ pending |
| 6-02-03 | 02 | 1 | CTRL-02 | unit | `pytest tests/test_publisher.py::TestPublishApprovedClips::test_fora_da_janela_horaria -x` | ✅ | ⬜ pending |
| 6-03-01 | 03 | 1 | CTRL-03 | unit | `pytest tests/test_rejeitar.py::test_marca_rejected -x` | ✅ | ⬜ pending |
| 6-03-02 | 03 | 1 | CTRL-03 | unit | `pytest tests/test_rejeitar.py::test_apaga_mp4_mantem_raw -x` | ✅ | ⬜ pending |
| 6-03-03 | 03 | 1 | CTRL-03 | unit | `pytest tests/test_rejeitar.py::test_clip_nao_existe -x` | ✅ | ⬜ pending |
| 6-04-01 | 04 | 1 | CTRL-04 | unit | `pytest tests/test_processar.py::TestParseVideoId -x` | ✅ | ⬜ pending |
| 6-04-02 | 04 | 1 | CTRL-04 | unit | `pytest tests/test_processar.py::TestUpsertSourceVideo::test_status_pending -x` | ✅ | ⬜ pending |
| 6-04-03 | 04 | 1 | CTRL-04 | unit | `pytest tests/test_processar.py::TestUpsertSourceVideo::test_idempotente -x` | ✅ | ⬜ pending |
| 6-05-01 | 05 | 2 | CTRL-05 | unit | `pytest tests/test_ttl_worker.py::TestExpire -x` | ✅ | ⬜ pending |
| 6-05-02 | 05 | 2 | CTRL-05 | unit | `pytest tests/test_ttl_worker.py::TestWarn -x` | ✅ | ⬜ pending |
| 6-05-03 | 05 | 2 | CTRL-05 | unit | `pytest tests/test_ttl_worker.py::TestWarn::test_no_warn_duplicado -x` | ✅ | ⬜ pending |
| 6-06-01 | 06 | 2 | CTRL-06 | unit | `pytest tests/test_telegram_notifier.py::test_success_event -x` | ✅ | ⬜ pending |
| 6-06-02 | 06 | 2 | CTRL-06 | unit | `pytest tests/test_telegram_notifier.py::test_failure_event -x` | ✅ | ⬜ pending |
| 6-06-03 | 06 | 2 | CTRL-06 | smoke (compose) | `grep -A2 cloudflared docker-compose.yml \| grep CLOUDFLARE_TUNNEL_TOKEN && grep -E "WEBHOOK_URL\|N8N_PROTOCOL" docker-compose.yml` | ✅ | ⬜ pending |
| 6-07-01 | 07 | 3 | CTRL-01, CTRL-06 | smoke (JSON validation) | `python3 scripts/validate-phase6-n8n.py` | ✅ | ✅ green |
| 6-07-02 | 07 | 3 | CTRL-06 | smoke (cron) | `python3 scripts/validate-phase6-n8n.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `mysql/init/05-controle-manual-migration.sql` — migration ENUM (CTRL-02)
- [ ] `clip-processor/src/processar.py` — skeleton + RED test (CTRL-04)
- [ ] `clip-processor/src/rejeitar.py` — skeleton + RED test (CTRL-03)
- [ ] `clip-processor/src/ttl_worker.py` — skeleton + RED test (CTRL-05)
- [ ] `clip-processor/src/telegram_notifier.py` — skeleton + RED test (CTRL-06)
- [ ] `clip-processor/tests/test_processar.py` — RED imports
- [ ] `clip-processor/tests/test_rejeitar.py` — RED imports
- [ ] `clip-processor/tests/test_ttl_worker.py` — RED imports
- [ ] `clip-processor/tests/test_telegram_notifier.py` — RED imports
- [ ] `clip-processor/tests/test_publisher.py` — adicionar classe `TestPublishApprovedClips` (RED swap)
- [ ] `telegram-n8n/workflows/06-router.json` — esqueleto com TelegramTrigger + Switch (sem implementação completa, só estrutura)
- [ ] `telegram-n8n/workflows/06-cron-resumo-diario.json` — esqueleto com scheduleTrigger 18h
- [ ] `docker-compose.yml` — adicionar serviço `cloudflared` + env vars n8n (`WEBHOOK_URL`, `N8N_PROTOCOL=https`, `N8N_HOST`)
- [ ] `.env.example` — adicionar `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID_ALLOWED`, `TELEGRAM_WEBHOOK_SECRET`, `CLOUDFLARE_TUNNEL_TOKEN`, `N8N_WEBHOOK_URL`, `N8N_HOST`, `CLIP_PENDING_TTL_HOURS`, `CLIP_PENDING_WARN_HOURS`, `N8N_NOTIFY_URL`

*Estrutura de teste segue padrão Phase 2/3/5: imports no topo dos `test_*.py` produzem `ModuleNotFoundError` como RED válido até os módulos serem criados.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Cloudflare Tunnel ativo e DNS apontado | CTRL-06 | Exige conta CF e domínio do operador; não pode ser automatizado | (1) `docker logs cloudflared` mostra `Connection registered`; (2) `curl -I https://<tunnel-host>` retorna 200/404 do n8n; (3) checkpoint no dashboard CF: "Healthy" |
| Telegram `setWebhook` aponta para Cloudflare Tunnel | CTRL-06 | Operação de uma vez via Telegram Bot API com token real | `curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" \| jq .result.url` deve mostrar URL do tunnel + `pending_update_count=0` |
| Bot ignora silenciosamente chats fora da allowlist | CTRL-01 | Comportamento de não-resposta só verificável com chat real fora da allowlist | Enviar `/ajuda` de chat secundário → nenhuma resposta em 30s; n8n executions log não mostra erro |
| `/aprovar` produz upload no YouTube respeitando janela | CTRL-02, CTRL-06 | Janela 19h-22h BRT + quota; teste real do ciclo completo | Aprovar 1 clip às 18h; confirmar que upload sai só após 19h; YouTube Studio mostra vídeo (mode privado primeiro) |
| Notificação proativa de falha crítica | CTRL-06 | Disparo depende de erro real do pipeline | Forçar falha (ex: revogar token YouTube por 1 min); ver mensagem no Telegram |

## Local Artifact Validation

Plan 06-07 adds a repo-local validator for checks that do not require Telegram, Cloudflare, n8n runtime or YouTube:

```bash
python3 scripts/validate-phase6-n8n.py
```

Current coverage:
- `06-router.json` and `06-cron-resumo-diario.json` parse as JSON.
- Router contains required node types and routes all six commands.
- `/aprovar`, `/rejeitar`, `/processar`, `/status`, `/clipes` contain the critical SQL/command contracts.
- Internal `/webhook/notify` routes the 3 supported proactive events.
- Daily cron is `0 18 * * *` in timezone `America/Sao_Paulo`.
- `approve-backlog.sql` and `SETUP.md` contain required operational instructions.

This does **not** replace the manual-only checks above. It prevents accidental JSON/workflow regression before import.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
