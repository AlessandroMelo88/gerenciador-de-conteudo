---
phase: 06-controle-manual-n8n-telegram
plan: 06
subsystem: notifications

tags: [telegram, n8n, webhook, cloudflared, best-effort, pipeline-events, phase-6-wave-2]

requires:
  - phase: 06-controle-manual-n8n-telegram
    provides: "Plan 06-01 entregou stub telegram_notifier.py + test_telegram_notifier.py (2 testes RED) e .env.example com N8N_NOTIFY_URL/N8N_WEBHOOK_URL/N8N_HOST/CLOUDFLARE_TUNNEL_TOKEN"
provides:
  - "telegram_notifier.notify(event_type, payload, timeout=5.0) — POST best-effort para N8N_NOTIFY_URL com JSON {event, payload}; True em 2xx, False em erro (nunca propaga)"
  - "Integração em publisher.py: notify('upload_published', {clip_id, youtube_video_id, youtube_url, title}) após _mark_clip_published"
  - "Integração em pipeline_runner.py: notify('pipeline_failure', {stage, error_msg}) em 3 estágios críticos (poll/download/publish)"
  - "Serviço cloudflared no docker-compose.yml raiz com CLOUDFLARE_TUNNEL_TOKEN"
  - "n8n service ampliado com WEBHOOK_URL, N8N_HOST, N8N_PROTOCOL=https, N8N_PORT=5678"
affects:
  - "06-07-n8n-flows: webhook /webhook/notify do n8n consome os 2 eventos do clip-processor; cloudflared expõe o webhook do Telegram via Cloudflare Zero Trust"

tech-stack:
  added:
    - "cloudflare/cloudflared:latest (docker service)"
  patterns:
    - "Best-effort notifier: try/except RequestException + status_code check; nunca propaga exceções — falha de notificação não derruba o pipeline"
    - "Webhook proxy pattern: clip-processor não conhece TELEGRAM_BOT_TOKEN; faz POST para n8n interno (rede docker) que centraliza credencial e formatação"
    - "Cloudflare Tunnel via container: cloudflared service com command=tunnel run --token ${...}; sem porta aberta no host, sem ngrok, sem reverse proxy custom"
    - "n8n env vars para webhook público: WEBHOOK_URL + N8N_HOST + N8N_PROTOCOL=https permitem que o n8n gere URLs corretas atrás do tunnel"

key-files:
  created: []
  modified:
    - clip-processor/src/telegram_notifier.py
    - clip-processor/src/publisher.py
    - clip-processor/src/pipeline_runner.py
    - /Users/alessandrobm1/develop/server/wordpress/docker-compose.yml

key-decisions:
  - "notify() implementado com try/except amplo (requests.RequestException) + status_code check: status_code >= 400 retorna False sem raise — best-effort puro"
  - "Default N8N_NOTIFY_URL = http://n8n:5678/webhook/notify (rede docker interna) — em produção operador pode redirecionar via .env sem mudar código"
  - "publisher.py chama notify APÓS _mark_clip_published e _maybe_finalize_source_video: garantia de que o evento 'upload_published' só dispara quando o estado do DB já é terminal-positivo"
  - "pipeline_runner.py dispara notify('pipeline_failure', ...) nos 3 except do orquestrador (poll/download/publish): cada estágio já era try/except isolado; injetou-se a notificação em cada um sem mudar fluxo de controle"
  - "Cloudflared como container separado (não sidecar do n8n): permite restart independente, depends_on: [n8n] garante ordem mas não acopla lifecycle"
  - "n8n N8N_PORT=5678 literal (não env var): tunnel sempre aponta para essa porta interna; mudar porta requer mudança coordenada no Tunnel CF e no compose — explicito é melhor que parametrizado"

patterns-established:
  - "Notifier best-effort: módulo dedicado com 1 função pura (notify) + 1 constante module-level (URL) — fácil de mockar via patch('src.notifier.requests.post')"
  - "Integração de notify em pipeline já existente: 1 import + 1 chamada por ponto crítico, sem mudar try/except existente — nunca encadear notify dentro de try novo"
  - "Cloudflare Tunnel para serviços internos: padrão reaproveitável para qualquer webhook futuro (não só n8n)"

requirements-completed: [CTRL-06]

duration: ~35min
completed: 2026-06-19
---

# Phase 6 Plan 06: telegram_notifier + Cloudflare Tunnel

**Notifier HTTP best-effort que envia 2 eventos (`upload_published`, `pipeline_failure`) para webhook interno do n8n, com cloudflared service expondo o webhook público para o Telegram via Cloudflare Zero Trust — sem TELEGRAM_BOT_TOKEN no clip-processor.**

## Performance

- **Duration:** ~35 min (incluindo verificação full suite 240s)
- **Started:** 2026-06-19T20:43:00Z
- **Completed:** 2026-06-19T21:18:06Z
- **Tasks:** 2 (ambas auto)
- **Files modified:** 4 (3 do clip-processor + docker-compose.yml raiz)

## Accomplishments

- **`telegram_notifier.notify()` implementado**: POST best-effort para `N8N_NOTIFY_URL` com JSON `{event, payload}`. Captura `requests.RequestException` e retorna `False`; retorna `True` para `status_code < 400`. Nunca propaga.
- **publisher.py integrado**: import `from src.telegram_notifier import notify` + chamada `notify('upload_published', {clip_id, youtube_video_id, youtube_url, title})` após `_mark_clip_published` e `quota_manager.record_upload`. Posição garante que a notificação só dispara em sucesso do DB.
- **pipeline_runner.py integrado**: import + 3 chamadas `notify('pipeline_failure', {stage, error_msg})` — uma em cada `except` dos estágios `poll_all_channels`, `_download_pending_videos`, `publish_pending_clips`. Stage nomeado por string literal (mais legível que variável dinâmica).
- **docker-compose.yml raiz** (`/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml`): novo serviço `cloudflared` (`cloudflare/cloudflared:latest`) com `command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}`, `networks: [internal]`, `depends_on: [n8n]`.
- **n8n service ampliado** no mesmo compose: 4 novas env vars (`WEBHOOK_URL=${N8N_WEBHOOK_URL}`, `N8N_HOST=${N8N_HOST}`, `N8N_PROTOCOL=https`, `N8N_PORT=5678`) — outros vars (GENERIC_TIMEZONE, TZ, N8N_ENCRYPTION_KEY) preservados intactos.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implementar telegram_notifier.notify() + integrar em publisher.py e pipeline_runner.py** — `bf23e0c` (feat)
2. **Task 2: Adicionar serviço cloudflared + env vars n8n ao docker-compose raiz** — sem commit git (arquivo `/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml` está fora de qualquer repositório git — mudança aplicada diretamente no FS, validada via `docker compose config`)

_Plan metadata commit segue após este SUMMARY._

## Files Created/Modified

### Modified

- `clip-processor/src/telegram_notifier.py` — Substituído stub por implementação real: try/except + status_code check + logs `[NOTIFY] warn:` para falhas
- `clip-processor/src/publisher.py` — Adicionado import `from src.telegram_notifier import notify` + chamada após `_mark_clip_published` com payload `{clip_id, youtube_video_id, youtube_url, title}`
- `clip-processor/src/pipeline_runner.py` — Adicionado import + 3 chamadas `notify('pipeline_failure', {stage: '<nome>', error_msg: str(exc)[:500]})` nos 3 estágios críticos
- `/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml` — Serviço `cloudflared` novo + 4 env vars adicionadas ao serviço `n8n` (WEBHOOK_URL, N8N_HOST, N8N_PROTOCOL, N8N_PORT)

### Created

Nenhum arquivo criado neste plan (todos os stubs e arquivos de teste foram criados em Plan 06-01).

## Decisions Made

- **Eventos disparados por este plan**: `upload_published` (publisher), `pipeline_failure` (pipeline_runner — 3 pontos). Outros eventos `clip_warn_expiry`/`clip_expired` ficam por conta do `ttl_worker` (Plan 06-05, já implementado) que chama `requests.post` direto sem passar pelo notifier — isolamento por design.
- **Default URL em `os.getenv('N8N_NOTIFY_URL', 'http://n8n:5678/webhook/notify')`**: usa rede docker interna; operador só precisa setar `N8N_NOTIFY_URL` no `.env` se quiser apontar para outro endpoint. Default seguro e pronto-para-prod no docker-compose.
- **`notify` retorna `bool` (True/False)**: callers podem logar/decidir, mas nenhum dos call-sites atuais usa o valor. Future-proof — permite que callers futuros tratem retry/fallback se necessário.
- **3 chamadas separadas no pipeline_runner.py (uma por estágio)** em vez de 1 chamada genérica no `try/except` mais externo: cada estágio nomeia seu próprio `stage`, payload mais informativo para debug.
- **publisher.py NÃO notifica `clip_ready`**: clip_ready (após cutting) é responsabilidade de outro estágio (Phase 4 video_processor), fora do escopo deste plan. CTRL-06 cobre `upload_published` + `pipeline_failure` apenas (decisão CONTEXT do RESEARCH).
- **`error_msg` truncado em 500 chars** (`str(exc)[:500]`): mensagem do Telegram tem limite; tracebacks completos ficam só no log do clip-processor.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] 3 chamadas `notify('pipeline_failure', ...)` em pipeline_runner.py em vez de 1**

- **Found during:** Task 1, ao localizar o ponto de integração
- **Issue:** Plan original sugeriu 1 chamada no "except Exception mais externo do orquestrador". Mas o `pipeline_runner.py` atual (estabelecido em Phase 5) já tem 3 try/except separados por estágio (poll, download, publish) — não há um catch-all externo. Falhar só em 1 lugar geraria notificação ambígua (`stage='unknown'`).
- **Fix:** Adicionada 1 chamada `notify('pipeline_failure', {stage: '<nome-literal>', error_msg: str(exc)[:500]})` em CADA um dos 3 except — `stage='poll_all_channels'`, `stage='download_pending_videos'`, `stage='publish_pending_clips'`.
- **Files modified:** `clip-processor/src/pipeline_runner.py`
- **Verification:** grep confirmou 3 ocorrências de `notify('pipeline_failure'` no arquivo; testes de pipeline_runner (11/11) seguem GREEN
- **Committed in:** `bf23e0c` (Task 1 commit)
- **Por que Rule 2 (missing critical, não 1 ou 4):** sem notificação por estágio, observability do operador fica cega — não saberia onde o pipeline travou. Não é mudança arquitetural (não criou novo módulo nem mudou fluxo de controle); apenas instrumentação correta dos handlers existentes.

**2. [Rule 1 - Bug Fix] payload de `upload_published` inclui `youtube_video_id` E `youtube_url` (não só url)**

- **Found during:** Task 1, ao redigir o payload
- **Issue:** Plan original sugeriu payload `{clip_id, youtube_url, title}`. Mas o caller `_mark_clip_published(conn, clip_id, youtube_video_id)` já tem `youtube_video_id` como variável local — passar só `youtube_url` desperdiça informação que o n8n pode usar para extrair só o ID (mais barato para o bot do que regex).
- **Fix:** Payload final = `{clip_id, youtube_video_id, youtube_url: f'https://www.youtube.com/watch?v={id}', title}`. n8n recebe ambos, decide como formatar.
- **Files modified:** `clip-processor/src/publisher.py`
- **Verification:** `test_telegram_notifier.py::test_success_event` GREEN; integração visual confirmada via grep
- **Committed in:** `bf23e0c` (Task 1 commit)
- **Por que Rule 1 (correctness improvement):** payload mais rico não custa nada e evita parsing redundante no n8n.

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 correctness improvement)
**Impact on plan:** Ambos os auto-fixes mantêm o escopo do plan (notifier + integração) — só ajustam a forma de cumprir o objetivo. Nenhum scope creep, nenhum módulo novo, nenhuma dependência adicionada.

## Issues Encountered

- **`docker-compose.yml` raiz não está em repositório git**: arquivo em `/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml` foi modificado diretamente no FS. Validação via `CLOUDFLARE_TUNNEL_TOKEN=placeholder docker compose -f /Users/alessandrobm1/develop/server/wordpress/docker-compose.yml config >/dev/null` retornou exit 0 (CONFIG VALID). Sem commit git para Task 2 — não é regressão, é característica do projeto. Plano original já mencionava "arquivo fora de canaldecortes/".

- **Implementação já existia ao iniciar este executor**: ao ler o estado inicial, todo o código da Task 1 e Task 2 já estava aplicado (commit `bf23e0c` feito na Wave 2 paralela com o Plan 06-05). Não foi necessário re-aplicar — apenas verificar (testes + grep + docker compose config) e gerar este SUMMARY + atualizar STATE/ROADMAP. Reaplicar com Edit teria criado diff vazio.

## User Setup Required

**Sim — pendência operacional para Plan 07 (ativação do Tunnel CF):**

1. Operador cria Tunnel no [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com) → Networks → Tunnels → Create a tunnel
2. Configura DNS público (ex.: `n8n.canaldecortes.com.br`) apontando o Tunnel para o serviço interno `http://n8n:5678`
3. Copia o token gerado e preenche `.env`:
   ```
   CLOUDFLARE_TUNNEL_TOKEN=<token-do-CF>
   N8N_WEBHOOK_URL=https://n8n.canaldecortes.com.br
   N8N_HOST=n8n.canaldecortes.com.br
   ```
4. Sobe os serviços: `cd /Users/alessandrobm1/develop/server/wordpress && docker compose up -d cloudflared n8n` (n8n precisa reload para carregar as novas env vars)

**NÃO foi feito por este executor**: subir o serviço cloudflared. n8n está com workflows ativos de Phase 5 — reload sem o token correto deixaria o serviço com `WEBHOOK_URL` apontando para placeholder. Esse é checkpoint manual de Plan 06-07 (workflow router) ou de uma sessão operacional dedicada.

## Next Phase Readiness

- **Plan 06-07 desbloqueado**: agora o clip-processor publica 2 eventos no webhook do n8n (`upload_published`, `pipeline_failure`). Plan 06-07 vai criar o workflow n8n que consome `/webhook/notify` (Switch por `event_type`) e dispara mensagens formatadas no Telegram.
- **Cloudflared no compose pronto para subir**: assim que operador criar Tunnel no CF e preencher `.env`, `docker compose up -d cloudflared n8n` ativa o tunnel sem mais código.
- **Risco operacional**: enquanto Tunnel não estiver ativo, eventos `upload_published` e `pipeline_failure` farão POST que falha silenciosamente (best-effort retorna False, log `[NOTIFY] warn`). Pipeline continua funcionando sem notificação. Operador deve ativar o Tunnel ANTES de aprovar o primeiro clip via Telegram para evitar "publicou mas não recebi notificação".
- **Nenhum impacto em Phases 1-5**: notifier é opcional puro; falha de rede não derruba publisher nem pipeline_runner.

## Self-Check: PASSED

Verificações realizadas:

- `clip-processor/src/telegram_notifier.py`: FOUND — implementação real (não stub) com try/except + status_code check
- `clip-processor/src/publisher.py`: FOUND — contém `notify('upload_published'` exatamente 1 vez
- `clip-processor/src/pipeline_runner.py`: FOUND — contém `notify('pipeline_failure'` exatamente 3 vezes (uma por estágio)
- `/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml`: FOUND — contém `cloudflared:`, `CLOUDFLARE_TUNNEL_TOKEN`, `WEBHOOK_URL`, `N8N_PROTOCOL=https`
- Commit `bf23e0c`: FOUND in `git log --oneline -10`
- `docker exec clip-processor pytest tests/test_telegram_notifier.py -x`: 2/2 PASSED
- `docker exec clip-processor pytest tests/test_publisher.py tests/test_pipeline_runner.py -x`: 21/21 PASSED (sem regressão)
- `docker exec clip-processor pytest tests/`: 104/104 PASSED (full suite GREEN)
- `CLOUDFLARE_TUNNEL_TOKEN=placeholder docker compose -f /Users/alessandrobm1/develop/server/wordpress/docker-compose.yml config`: exit 0 (parseável)

---
*Phase: 06-controle-manual-n8n-telegram*
*Completed: 2026-06-19*
