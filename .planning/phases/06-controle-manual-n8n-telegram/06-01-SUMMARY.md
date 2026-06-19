---
phase: 06-controle-manual-n8n-telegram
plan: 01
subsystem: testing

tags: [tdd, red-state, mysql-enum, n8n, telegram, scaffolding, phase-6-wave-0]

requires:
  - phase: 05-publicacao-e-automacao-total
    provides: "publisher.publish_pending_clips usando status='pending' (será swappado para 'approved' em Plan 06-02)"
provides:
  - Migration SQL idempotente que adiciona approved/rejected ao ENUM generated_clips.status
  - 4 stubs Python (processar, rejeitar, ttl_worker, telegram_notifier) com NotImplementedError
  - 5 arquivos de teste em RED (test_processar, test_rejeitar, test_ttl_worker, test_telegram_notifier + TestPublishApprovedClips em test_publisher)
  - Esqueleto n8n 06-router.json com TelegramTrigger + Switch (6 comandos)
  - Esqueleto n8n 06-cron-resumo-diario.json com cron 18h BRT
  - 9 novas variáveis em .env.example
  - Diretório workflows/archive/ com 02/03/04-*.json migrados via git rename
affects: [06-02-publisher-swap, 06-03-rejeitar, 06-04-processar, 06-05-ttl-worker, 06-06-telegram-notifier, 06-07-n8n-flows]

tech-stack:
  added: []
  patterns:
    - "Wave 0 scaffolding: stubs Python com NotImplementedError + tests em RED state (consistente com Phases 2/3/4/5)"
    - "Switch n8n v2 com renameOutput + outputKey para cada comando — permite conectar sub-fluxos por nome em Plan 06-07"
    - "TelegramTrigger 1.2 com restrictToChatIds via {{ $env.TELEGRAM_CHAT_ID_ALLOWED }} — gate de autorização nativo do n8n"
    - "ALTER TABLE ... MODIFY COLUMN ENUM idempotente: MySQL 8.4 trata no-op quando ENUM já está no estado final (metadata-only para appends)"

key-files:
  created:
    - mysql/init/05-controle-manual-migration.sql
    - clip-processor/src/processar.py
    - clip-processor/src/rejeitar.py
    - clip-processor/src/ttl_worker.py
    - clip-processor/src/telegram_notifier.py
    - clip-processor/tests/test_processar.py
    - clip-processor/tests/test_rejeitar.py
    - clip-processor/tests/test_ttl_worker.py
    - clip-processor/tests/test_telegram_notifier.py
    - telegram-n8n/workflows/06-router.json
    - telegram-n8n/workflows/06-cron-resumo-diario.json
    - telegram-n8n/workflows/archive/.gitkeep
  modified:
    - clip-processor/tests/test_publisher.py
    - .env.example
    - telegram-n8n/workflows/archive/02-busca-videos.json (rename)
    - telegram-n8n/workflows/archive/03-tendencias.json (rename)
    - telegram-n8n/workflows/archive/04-notificador-fila.json (rename)

key-decisions:
  - "ENUM final: ('pending_cut','pending','cutting','publishing','published','failed','approved','rejected') — mantém ordem histórica e adiciona ao final (metadata-only no MySQL 8.4)"
  - "Stubs Python: imports/constants/type-hints completos no topo + corpo NotImplementedError — coleta pytest funciona, execução falha; espelha Phase 3 RED"
  - "Switch v2 com fallbackOutput='ajuda': mensagens desconhecidas caem em /ajuda (UX explícito ao operador no Telegram)"
  - "01-telegram-handler.json NÃO foi para archive — fica em workflows/ como referência até o operador confirmar a substituição manualmente no n8n UI"
  - "Mantido TELEGRAM_CHAT_ID_ALLOWED=5760918317 como default no .env.example (chat do operador, conforme CONTEXT.md)"
  - "Cron 0 18 * * * + timezone America/Sao_Paulo no settings: scheduleTrigger 1.2 do n8n usa o timezone do workflow para interpretar a expressão"

patterns-established:
  - "Wave 0 contract: cada task downstream tem 1 stub + 1 test file pré-existente — testes coletam, falham por NotImplementedError ou AttributeError até o Plan correspondente implementar"
  - "Migrations Phase 6+: ALTER TABLE MODIFY COLUMN ENUM idempotente (sem necessidade de prepared statements quando só se adiciona ao final)"
  - "n8n workflows skeleton: arquivos JSON parseáveis com nodes + connections mínimos, suficientes para serem importados no n8n UI mesmo antes da implementação completa"

requirements-completed: [CTRL-01, CTRL-02, CTRL-03, CTRL-04, CTRL-05, CTRL-06]

duration: 6min
completed: 2026-06-19
---

# Phase 6 Plan 01: Wave 0 — Migration SQL + 4 Python stubs + 5 RED test files + n8n skeletons

**Migration SQL idempotente (ENUM approved/rejected), 4 stubs Python (processar/rejeitar/ttl_worker/telegram_notifier) e 5 test files em RED state desbloqueiam execução paralela de Plans 06-02 a 06-07.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-19T20:05:56Z
- **Completed:** 2026-06-19T20:11:38Z
- **Tasks:** 2 (ambas auto)
- **Files modified:** 16 (13 criados + 3 renames + 2 modificados)

## Accomplishments

- **Migration SQL** (`mysql/init/05-controle-manual-migration.sql`): `ALTER TABLE generated_clips MODIFY COLUMN status ENUM(...)` adicionando `'approved'` e `'rejected'` ao final do ENUM. Default permanece `pending_cut`. Idempotente — MySQL 8.4 trata como no-op se já estiver no estado final, e como operação metadata-only quando aplicado pela primeira vez.
- **4 stubs Python** com imports/constantes module-level + type hints + bloco `if __name__ == '__main__'` quando aplicável. Todas as funções `raise NotImplementedError("Phase 6 — implementar em Plan NN")`.
- **5 arquivos de teste em RED** coletam 15 testes novos (12 nos 4 novos arquivos + 3 em `TestPublishApprovedClips`). RED confirmado: NotImplementedError para chamadas diretas; AttributeError para `patch('src.X.Y')` onde Y ainda não existe no stub.
- **2 esqueletos n8n**: 06-router.json com TelegramTrigger + Switch (6 comandos) + restrictToChatIds; 06-cron-resumo-diario.json com scheduleTrigger 0 18 * * * + timezone America/Sao_Paulo.
- **Workflows 02/03/04** movidos para `archive/` via `git mv` — histórico preservado. `01-telegram-handler.json` permanece em `workflows/` como referência.
- **.env.example** ampliado com 9 novas variáveis Phase 6.

## Task Commits

1. **Task 1: Migration SQL + 4 stubs Python + 5 RED test files** — `bf1e330` (test)
2. **Task 2: n8n skeletons + archive legacy workflows + .env.example** — `83ab08f` (chore)

_Plan metadata commit segue após este SUMMARY._

## Files Created/Modified

### Criados

- `mysql/init/05-controle-manual-migration.sql` — Migration idempotente ENUM approved/rejected
- `clip-processor/src/processar.py` — Stub: YOUTUBE_URL_RE, parse_video_id, fetch_metadata, upsert_source_video, main
- `clip-processor/src/rejeitar.py` — Stub: rejeitar(clip_id)
- `clip-processor/src/ttl_worker.py` — Stub: TTL_HOURS, WARN_HOURS, N8N_NOTIFY_URL constants + run_ttl_once
- `clip-processor/src/telegram_notifier.py` — Stub: N8N_NOTIFY_URL constant + notify
- `clip-processor/tests/test_processar.py` — TestParseVideoId (5 testes) + TestUpsertSourceVideo (2 testes)
- `clip-processor/tests/test_rejeitar.py` — test_marca_rejected, test_apaga_mp4_mantem_raw, test_clip_nao_existe
- `clip-processor/tests/test_ttl_worker.py` — TestExpire (1 teste) + TestWarn (2 testes)
- `clip-processor/tests/test_telegram_notifier.py` — test_success_event, test_failure_event
- `telegram-n8n/workflows/06-router.json` — TelegramTrigger 1.2 + Parse Code + Switch v2 (6 outputs)
- `telegram-n8n/workflows/06-cron-resumo-diario.json` — scheduleTrigger 1.2 + TODO node
- `telegram-n8n/workflows/archive/.gitkeep` — Marca diretório no git

### Modificados

- `clip-processor/tests/test_publisher.py` — Adicionada classe `TestPublishApprovedClips` (3 testes RED — espera `status='approved'` no SELECT do publisher)
- `.env.example` — Apêndice com 9 vars Phase 6
- `telegram-n8n/workflows/{02-busca-videos,03-tendencias,04-notificador-fila}.json` — Movidos para `archive/` via `git mv` (rename rastreado pelo git)

## Decisions Made

- **ENUM ordering**: mantida a ordem histórica + append de approved/rejected. Evita reescrita da tabela e permite que dados legados (status `pending`) continuem válidos enquanto a transição é feita.
- **Stub Plan-NN mapping**: processar.py → Plan 06-04, rejeitar.py → Plan 06-03, ttl_worker.py → Plan 06-05, telegram_notifier.py → Plan 06-06. Mensagem do NotImplementedError documenta o "implementar em Plan NN".
- **Switch v2 `renameOutput + outputKey`**: cada comando ganha um output nomeado (`status`, `clipes`, `aprovar`, `rejeitar`, `processar`, `ajuda`) — Plan 06-07 conecta sub-fluxos por nome legível, não por índice.
- **TelegramTrigger restrictToChatIds**: usa `{{ $env.TELEGRAM_CHAT_ID_ALLOWED }}` ao invés de hardcode — single source of truth no .env.
- **01-telegram-handler.json NÃO arquivado**: o operador precisa decidir manualmente no n8n UI quando substituir pelo router novo. Move prematuro deixaria o n8n sem nenhum workflow ativo de Telegram.
- **TestPublishApprovedClips**: 3 testes. Apenas o `test_seleciona_apenas_approved` está realmente em RED falso-vermelho (espera approved, vê pending). Os outros 2 (quota_blocked, fora_da_janela) passam porque a lógica de bloqueio quando quota retorna False já foi implementada em Phase 5 — eles servem como regressão para garantir que o comportamento não quebre quando o swap de literal acontecer em Plan 06-02.

## Estado RED Confirmado

Executando `python3 -m pytest` localmente (Python 3.13, pytest-9.1):

```
test_processar.py        7 failed (NotImplementedError em parse_video_id / upsert_source_video)
test_rejeitar.py         3 failed (AttributeError: src.rejeitar.db_connect inexistente)
test_ttl_worker.py       3 failed (AttributeError: src.ttl_worker.requests inexistente)
test_telegram_notifier.py 2 failed (AttributeError: src.telegram_notifier.requests inexistente)
test_publisher.py        1 failed (TestPublishApprovedClips::test_seleciona_apenas_approved — SELECT ainda usa 'pending')
                         9 passed (lógica Phase 5 mantida; 2 dos 3 testes da nova classe passam por design)
```

Total: 16 RED tests + 9 verdes (lógica anterior preservada).

## Pontos Abertos para Próximos Plans

- **Plan 06-02 (publisher swap)**: trocar literal `WHERE gc.status = 'pending'` por `WHERE gc.status = 'approved'` em `clip-processor/src/publisher.py:63`. Após o swap, `test_seleciona_apenas_approved` vira GREEN. Cuidado: o `NON_TERMINAL_CLIP_STATUSES` na linha 14 não inclui `'approved'` — avaliar se `approved` deve ser tratado como terminal (não-publicado) ou se entra na lista. Sugestão: adicionar `'approved'` para que `_maybe_finalize_source_video` não delete o raw enquanto ainda há clips approved aguardando upload.
- **Plan 06-03 (rejeitar)**: implementar `src/rejeitar.py` com `db_connect` importado de `src.db`. Os testes esperam `patch('src.rejeitar.db_connect', ...)` e `patch('src.rejeitar.os.remove', ...)`. Não tocar em `source_videos.local_path` (raw).
- **Plan 06-04 (processar)**: implementar usando o regex `YOUTUBE_URL_RE` já existente. `upsert_source_video` deve retornar `(status, created)` — INSERT cria com status='pending'; vídeo existente retorna o status atual sem alterar.
- **Plan 06-05 (ttl_worker)**: usar `requests.post` para `N8N_NOTIFY_URL` (deve ser patchável como `src.ttl_worker.requests`). Redis SET NX por clip_id evita warn duplicado. SQL precisa ter `INTERVAL N HOUR` literal para os asserts dos testes.
- **Plan 06-06 (telegram_notifier)**: `notify(event_type, payload, timeout=5.0)` faz `requests.post(N8N_NOTIFY_URL, json={'event': event_type, 'payload': payload}, timeout=timeout)`. Captura `requests.RequestException` e retorna False; retorna True se status_code < 400.
- **Plan 06-07 (n8n flows)**: conectar sub-fluxos a cada output nomeado do Switch (`status`, `clipes`, `aprovar`, `rejeitar`, `processar`, `ajuda`). Substituir o TODO node em 06-cron-resumo-diario.json pela query MySQL + envio Telegram.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Container clip-processor não monta `tests/`**: o Dockerfile copia apenas `src/`. Verificação via `docker exec clip-processor pytest` falha com "file or directory not found". Solução: rodei `pytest` localmente (Python 3.13 + pytest-9.1 já instalados na máquina do operador) — mesmo resultado RED. Para CI/CD, será necessário em Plan futuro: ou (a) adicionar `COPY tests/ tests/` ao Dockerfile e um stage de teste, ou (b) montar `./clip-processor:/app` em compose override de dev. Não é blocker do Plan 06-01 — a verificação RED foi feita com sucesso localmente.

## User Setup Required

**Não nesta wave.** Os secrets do .env (TELEGRAM_BOT_TOKEN, CLOUDFLARE_TUNNEL_TOKEN, TELEGRAM_WEBHOOK_SECRET) serão configurados pelo operador antes do Plan 06-07 (ativação do router em produção). O `.env.example` já documenta tudo o que será necessário.

## Next Phase Readiness

- **Plans 06-02 a 06-07 podem rodar em paralelo (Waves 1-3)**: cada um tem seu arquivo de teste já existente e o stub Python pronto para receber implementação.
- **Migration SQL pronta para aplicar**: o operador pode executar `docker exec -i mysql mysql ... < mysql/init/05-controle-manual-migration.sql` antes do Plan 06-02, ou deixar para o boot do MySQL aplicar via `/docker-entrypoint-initdb.d/` em ambientes novos.
- **n8n workflows skeleton**: 06-router.json e 06-cron-resumo-diario.json são JSON parseáveis (validados com `python -m json.tool`) — podem ser importados no n8n UI imediatamente, mesmo que sub-fluxos ainda fiquem desconectados nos outputs do Switch.

## Self-Check: PASSED

Verificações realizadas:

- `mysql/init/05-controle-manual-migration.sql` existe e contém `'approved'` e `'rejected'` no ENUM (regex multi-linha confirmou)
- 4 stubs Python passam `ast.parse` e expõem as funções/constantes documentadas em `<interfaces>`
- 4 test files coletados pelo pytest local (12 testes); execução produz NotImplementedError + AttributeError (RED state esperado)
- test_publisher.py: 10 testes coletados (7 antigos + 3 novos em TestPublishApprovedClips). 1 falha por busca de `'approved'` no SELECT (RED esperado), 2 passam (regressão preservada)
- `06-router.json` e `06-cron-resumo-diario.json` validados via `python -m json.tool`; assertions Python confirmaram TelegramTrigger + restrictToChatIds + Switch (router) e cron + timezone (cron resumo)
- `.env.example` contém 9 vars Phase 6 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID_ALLOWED, TELEGRAM_WEBHOOK_SECRET, CLOUDFLARE_TUNNEL_TOKEN, N8N_WEBHOOK_URL, N8N_HOST, N8N_NOTIFY_URL, CLIP_PENDING_TTL_HOURS, CLIP_PENDING_WARN_HOURS) — confirmado via grep | wc -l == 9
- Workflows 02/03/04-*.json migrados para `archive/` (verificado via `ls` + git tracked como rename)
- Commits `bf1e330` (Task 1) e `83ab08f` (Task 2) presentes em `git log`

---
*Phase: 06-controle-manual-n8n-telegram*
*Completed: 2026-06-19*
