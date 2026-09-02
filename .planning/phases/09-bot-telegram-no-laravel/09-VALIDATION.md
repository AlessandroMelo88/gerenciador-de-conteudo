---
phase: 9
slug: bot-telegram-no-laravel
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-02
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (Laravel)** | Pest 4.7 + pest-plugin-laravel 4.1 |
| **Config file** | `painel/phpunit.xml` + `painel/tests/Pest.php` |
| **Quick run command** | `docker exec php bash -c "cd /var/www/html/painel && ./vendor/bin/pest tests/Feature/TelegramWebhookTest.php -x"` |
| **Full suite command (Laravel)** | `docker exec php bash -c "cd /var/www/html/painel && ./vendor/bin/pest"` |
| **Framework (Python)** | pytest com `pytest.ini` em `clip-processor/` |
| **Quick run (Python)** | `docker exec clip-processor python -m pytest tests/test_telegram_notifier.py tests/test_internal_api.py -x -v` |
| **Full suite (Python)** | `docker exec clip-processor python -m pytest -v` |
| **Estimated runtime** | ~30 segundos (Laravel) + ~15 segundos (Python) |

---

## Sampling Rate

- **After every task commit:** Run quick command específico ao arquivo de teste do task
- **After every plan wave:** Run full Laravel suite + full Python suite — ambos devem estar GREEN
- **Before `/gsd:verify-work`:** Full suite (Laravel + Python) deve estar GREEN
- **Max feedback latency:** 30 segundos

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 9-??-01 | 01 | 0 | BOT-01 | feature | `pest tests/Feature/TelegramWebhookTest.php -x` | ❌ Wave 0 | ⬜ pending |
| 9-??-02 | 01 | 0 | BOT-02 | feature | `pest tests/Feature/TelegramCommandsTest.php -x` | ❌ Wave 0 | ⬜ pending |
| 9-??-03 | 01 | 0 | BOT-03 | feature | `pest tests/Feature/PipelineEventTest.php -x` | ❌ Wave 0 | ⬜ pending |
| 9-??-04 | 01 | 1 | BOT-01 | feature | `pest tests/Feature/TelegramWebhookTest.php -x` | ❌ Wave 0 | ⬜ pending |
| 9-??-05 | 01 | 1 | BOT-01 | feature | `pest tests/Feature/TelegramWebhookTest.php::deduplication -x` | ❌ Wave 0 | ⬜ pending |
| 9-??-06 | 02 | 1 | BOT-02 | feature | `pest tests/Feature/TelegramCommandsTest.php -x` | ❌ Wave 0 | ⬜ pending |
| 9-??-07 | 02 | 1 | BOT-03 | feature | `pest tests/Feature/PipelineEventTest.php -x` | ❌ Wave 0 | ⬜ pending |
| 9-??-08 | 03 | 2 | BOT-03 | unit | `pytest tests/test_telegram_notifier.py -x -v` | ✅ (update) | ⬜ pending |
| 9-??-09 | 03 | 2 | BOT-03 | unit | `pytest tests/test_internal_api.py -x -v` | ✅ (update) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `painel/tests/Feature/TelegramWebhookTest.php` — stubs para BOT-01 (webhook recebe update, chat não autorizado, sem secret token) e BOT-02 (deduplicação update_id)
- [ ] `painel/tests/Feature/TelegramCommandsTest.php` — stubs para BOT-02 (6 comandos: /status, /clipes, /aprovar, /rejeitar, /processar, /ajuda)
- [ ] `painel/tests/Feature/PipelineEventTest.php` — stubs para BOT-03 (upload_published dispara Telegram, sem token → 401)
- [ ] `clip-processor/tests/test_telegram_notifier.py` — atualizar: trocar `N8N_NOTIFY_URL` por `LARAVEL_NOTIFY_URL`, adicionar verificação do `Host` header
- [ ] `clip-processor/tests/test_internal_api.py` — adicionar testes para `/internal/process-url`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Webhook registrado no Telegram via `setWebhook` | BOT-01 | Requer chamada à API Telegram real | `curl https://api.telegram.org/bot{TOKEN}/getWebhookInfo` e verificar `url` aponta para `alessandromelo.com.br/telegramcanal` |
| Nginx de produção responde ao `/telegramcanal` | BOT-01 | Config nginx em produção pode estar fora do repo | `curl -X POST https://alessandromelo.com.br/telegramcanal` retornar 200 |
| Bot desativado no n8n após migração | BOT-01 | n8n é sistema externo | Verificar no painel n8n que o workflow do bot está desativado |
| Cloudflare Tunnel desnecessário para bot | BOT-01 | Verificação de arquitetura operacional | Desativar Cloudflare Tunnel e confirmar que o bot ainda responde via nginx direto |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
