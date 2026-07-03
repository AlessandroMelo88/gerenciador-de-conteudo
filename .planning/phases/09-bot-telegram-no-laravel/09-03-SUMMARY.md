---
phase: 09-bot-telegram-no-laravel
plan: "03"
subsystem: infra
tags: [python, flask, laravel, artisan-schedule, telegram, crontab, docker-compose]

requires:
  - phase: 09-01
    provides: "Telegram SDK instalado no Laravel, config/telegram.php, rota POST /internal/pipeline-event"

provides:
  - "telegram_notifier.py migrado para LARAVEL_NOTIFY_URL com Host header — elimina dependência do n8n"
  - "ttl_worker.py usa notify() do telegram_notifier em vez de requests.post direto para n8n"
  - "internal_api.py com endpoint POST /internal/process-url chamando processar_main(url)"
  - "Artisan Schedule registrado: dailyAt('18:00') BRT via routes/console.php"
  - "docker/php/crontab com linha schedule:run a cada minuto para o painel"
  - "clip-processor recebe LARAVEL_NOTIFY_URL e LARAVEL_HOST_HEADER via docker-compose.yml"

affects: [09-04, painel-laravel, bot-telegram-bot-commands]

tech-stack:
  added: []
  patterns:
    - "notify() do telegram_notifier como camada única para eventos do pipeline (sem requests.post direto em outros módulos)"
    - "Artisan Schedule via routes/console.php + crontab php schedule:run (substitui n8n cron 06-cron-resumo-diario.json)"
    - "docker cp + rebuild clip-processor após mudanças de src/ (src/ baked into image, não montado como volume)"

key-files:
  created: []
  modified:
    - clip-processor/src/telegram_notifier.py
    - clip-processor/src/ttl_worker.py
    - clip-processor/src/internal_api.py
    - clip-processor/tests/test_ttl_worker.py
    - painel/routes/console.php

key-decisions:
  - "ttl_worker.py remove import requests direto — usa notify() do telegram_notifier; testes atualizados para patch src.ttl_worker.notify"
  - "Artisan Schedule dailyAt('18:00') timezone America/Sao_Paulo equivale a cron 0 21 * * * UTC — verificado via artisan schedule:list"
  - "docker/php/crontab e docker-compose.yml ficam fora do repo canaldecortes/ — modificados no FS sem commit git (padrão Phase 6/8)"

requirements-completed: [BOT-03]

duration: 16min
completed: "2026-07-03"
---

# Phase 09 Plan 03: Migração Python + Artisan Schedule Summary

**telegram_notifier.py aponta para LARAVEL_NOTIFY_URL com Host header; internal_api.py ganha /internal/process-url; Artisan Schedule configura resumo diário às 18h BRT substituindo n8n cron**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-07-02T23:57:00Z
- **Completed:** 2026-07-03T00:13:27Z
- **Tasks:** 2
- **Files modified:** 5 (repo) + 2 (fora do repo: crontab, docker-compose.yml)

## Accomplishments
- telegram_notifier.py completamente substituído: LARAVEL_NOTIFY_URL + LARAVEL_HOST_HEADER + X-Internal-Token no header — elimina dependência do n8n para notificações do pipeline
- ttl_worker.py refatorado para usar notify() em vez de requests.post direto — consistência com o padrão centralizado de notificação
- internal_api.py ganha POST /internal/process-url que delega para processar_main(url) retornando {'exit_code': N} — bot Telegram pode disparar /processar via Laravel
- Artisan Schedule configurado: resumo diário às 18:00 BRT (0 21 * * * UTC) com skip silencioso quando pending=0
- docker/php/crontab atualizado com schedule:run; PHP container reconstruído e reiniciado
- docker-compose.yml com LARAVEL_NOTIFY_URL e LARAVEL_HOST_HEADER para o clip-processor

## Task Commits

1. **Task 1: Migrar telegram_notifier.py + ttl_worker.py + /internal/process-url** - `ab98f88` (feat + Rule 1 fix)
2. **Task 2: Artisan Schedule + crontab + docker-compose env vars** - `f3512cd` (feat)

**Plan metadata:** (docs commit — veja abaixo)

## Files Created/Modified
- `clip-processor/src/telegram_notifier.py` — LARAVEL_NOTIFY_URL + LARAVEL_HOST_HEADER + notify() com Host header
- `clip-processor/src/ttl_worker.py` — remove N8N_NOTIFY_URL e import requests; usa notify() do telegram_notifier
- `clip-processor/src/internal_api.py` — adiciona import processar_main + endpoint POST /internal/process-url
- `clip-processor/tests/test_ttl_worker.py` — atualiza patches de requests.post para notify (Rule 1)
- `painel/routes/console.php` — Schedule::call dailyAt('18:00') timezone America/Sao_Paulo

## Decisions Made
- ttl_worker.py remove `import requests` direto e usa notify() do telegram_notifier — elimina duplicação de lógica HTTP e garante Header Host em todas as chamadas ao Laravel
- Artisan Schedule verificado como `0 21 * * *` UTC = 18:00 BRT (UTC-3) via `artisan schedule:list`
- docker/php/crontab e docker-compose.yml permanecem fora do repo canaldecortes/ (padrão Phase 6/8)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Atualização de test_ttl_worker.py para novo patch target**
- **Found during:** Task 1 (execução do full test suite após a implementação)
- **Issue:** test_ttl_worker.py patchava `src.ttl_worker.requests.post` que deixou de existir após remover `import requests` de ttl_worker.py. 3 testes falharam: test_expire_marca_rejected_apos_48h, test_warn_envia_para_n8n, test_no_warn_duplicado
- **Fix:** Substituiu patches de `src.ttl_worker.requests.post` por `src.ttl_worker.notify`; renomeou test_warn_envia_para_n8n → test_warn_envia_notificacao (nome preciso: agora vai para Laravel, não n8n)
- **Files modified:** clip-processor/tests/test_ttl_worker.py
- **Verification:** 3 testes ttl_worker GREEN após correção
- **Committed in:** ab98f88 (Task 1 commit)

**2. [Rule 3 - Blocking] Rebuild do clip-processor necessário após recreate do container**
- **Found during:** Task 2 (verificação pós-restart do container)
- **Issue:** `docker compose up -d clip-processor` recriou o container (por mudança de env vars), revertendo os arquivos copiados via `docker cp` de volta ao estado da imagem antiga. LARAVEL_NOTIFY_URL não estava disponível como símbolo Python.
- **Fix:** Executou `docker compose build clip-processor` para baked-in novas source files; depois `docker compose up -d clip-processor`; depois `docker cp` para copiar tests/ (não incluídas no Dockerfile) de volta ao container recriado
- **Files modified:** (nenhum arquivo de repo — apenas operação docker)
- **Verification:** `python -c "from src.telegram_notifier import LARAVEL_NOTIFY_URL; print(LARAVEL_NOTIFY_URL)"` retorna URL correta; 16/16 testes GREEN
- **Committed in:** N/A (operação de runtime)

---

**Total deviations:** 2 auto-fixadas (1 bug de interface de teste, 1 bloqueio de rebuild docker)
**Impact on plan:** Ambas necessárias para correctness. Sem scope creep.

## Issues Encountered
- Container `clip-processor` não monta `src/` como volume (baked into image) — docker cp de source files é temporário; rebuild da imagem necessário para persistir mudanças após recreate do container.
- Container `clip-processor` não inclui `tests/` na imagem (Dockerfile copia apenas `src/`) — docker cp de tests/ necessário após todo rebuild.

## Next Phase Readiness
- Lado Python totalmente migrado: clip-processor notifica Laravel (não n8n) para todos os eventos do pipeline
- internal_api.py tem /internal/process-url pronto para o bot Laravel delegar /processar
- Artisan Schedule operacional para resumo diário
- Próximo: Plan 09-04 (bot commands Laravel: /status, /clipes, /aprovar, /rejeitar, /processar)

---
*Phase: 09-bot-telegram-no-laravel*
*Completed: 2026-07-03*
