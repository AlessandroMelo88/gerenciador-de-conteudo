---
phase: 08-painel-laravel-filament
plan: 02
subsystem: api
tags: [flask, mysql, pytest, sidecar, internal-http, oauth]

# Dependency graph
requires:
  - phase: 07-schema-multi-canal-python-pipeline
    provides: destination_channels table, uploader.py YouTubeUploader, rejeitar.py
provides:
  - Migration idempotente adicionando oauth_expired_flag em destination_channels
  - Skeleton Flask (internal_api.py) com contrato HTTP para resolve-channel e reject-clip
  - Testes RED que definem o contrato GREEN dos Plans 08-06 (uploader RefreshError) e 08-07 (internal_api)
affects: [08-06-uploader-refresh-error, 08-07-internal-api-implementation, 08-05-laravel-http-client]

# Tech tracking
tech-stack:
  added: [flask]
  patterns:
    - "Sidecar HTTP interno em vez de docker exec/docker.sock — Pattern 3 do 08-RESEARCH.md"
    - "RED skeleton: imports no topo do módulo, corpo levantando NotImplementedError, endpoints Flask já roteados"

key-files:
  created:
    - mysql/init/07-panel-oauth-flag-migration.sql
    - clip-processor/src/internal_api.py
    - clip-processor/tests/test_internal_api.py
    - clip-processor/tests/test_uploader_expired.py
    - .planning/phases/08-painel-laravel-filament/deferred-items.md
  modified:
    - clip-processor/requirements.txt

key-decisions:
  - "oauth_expired_flag como coluna BOOLEAN NOT NULL DEFAULT FALSE em destination_channels (não Redis/cache) — self-healing via reset no próximo upload bem-sucedido"
  - "internal_api.py mantém import de src.rejeitar no topo do módulo (não lazy) para expor patch alvo aos testes (src.internal_api.rejeitar)"
  - "Testes de test_internal_api.py assumem que Plan 08-07 vai importar subprocess dentro de internal_api.py — patch('src.internal_api.subprocess.run') falha hoje com AttributeError, que é o RED esperado (mesmo padrão do Pitfall documentado no plan)"

patterns-established:
  - "Sidecar HTTP interno (Flask) roda dentro do próprio container clip-processor, rede docker internal, sem porta publicada no host — elimina necessidade de montar /var/run/docker.sock no container php compartilhado"

requirements-completed: [PANEL-01, PANEL-02, PANEL-04]

# Metrics
duration: ~35min
completed: 2026-07-01
---

# Phase 8 Plan 02: Wave 0 Python (SQL migration + internal_api skeleton + testes RED) Summary

**Migration idempotente `oauth_expired_flag` aplicada em `destination_channels`, skeleton Flask `internal_api.py` com 2 endpoints internos (resolve-channel, reject-clip) levantando `NotImplementedError`, e 7 testes RED cobrindo o contrato HTTP do sidecar e a captura pendente de `RefreshError` no uploader.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-07-01T15:59:00-03:00 (aprox.)
- **Completed:** 2026-07-01T16:10:00-03:00 (aprox.)
- **Tasks:** 3/3 completed
- **Files modified:** 5 (2 criados diretamente para o sidecar, 2 testes, 1 requirements.txt, 1 migration SQL, 1 deferred-items.md)

## Accomplishments
- Coluna `oauth_expired_flag` (BOOLEAN NOT NULL DEFAULT FALSE) criada em `destination_channels` via migration idempotente verificada com dupla execução (segunda rodada sem erro).
- Skeleton `clip-processor/src/internal_api.py` importável dentro do container, expondo `app` (Flask), `resolve_channel`, `reject_clip`, `INTERNAL_TOKEN` e 2 rotas POST já registradas em `app.url_map`.
- 7 testes RED criados (`test_internal_api.py` com 6, `test_uploader_expired.py` com 1) — coleta sem `ImportError`/`ModuleNotFoundError`; execução confirma 5 falhas RED e 2 passes (testes de auth, já cobertos pelo skeleton).
- Zero regressão introduzida pelas mudanças deste plano: suite completa (127 passed) — as 3 falhas observadas em `test_quota_manager.py` são pré-existentes e não relacionadas (ver Deviations).

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar SQL migration idempotente `07-panel-oauth-flag-migration.sql`** - `78f75c8` (feat)
2. **Task 2: Criar `internal_api.py` skeleton + adicionar flask a requirements.txt** - `c2b729d` (feat)
3. **Task 3: Escrever testes RED — test_internal_api.py + test_uploader_expired.py** - `afe515b` (test)

**Plan metadata:** (this commit — docs: complete plan)

_Note: Task 2 e Task 3 foram marcadas `tdd="true"` no plano mas como skeleton/RED puro (sem ciclo GREEN neste plano — GREEN vem nos Plans 08-06/08-07), então cada uma resultou em um único commit `feat`/`test`._

## Files Created/Modified
- `mysql/init/07-panel-oauth-flag-migration.sql` - Migration idempotente (INFORMATION_SCHEMA guard) adicionando `oauth_expired_flag`
- `clip-processor/requirements.txt` - Adicionada dependência `flask` (última linha)
- `clip-processor/src/internal_api.py` - Skeleton Flask: `app`, `resolve_channel`, `reject_clip`, `INTERNAL_TOKEN`, 2 rotas POST
- `clip-processor/tests/test_internal_api.py` - 6 testes RED cobrindo auth, resolve success/fail, reject success + exit codes
- `clip-processor/tests/test_uploader_expired.py` - 1 teste RED cobrindo captura de `RefreshError` + persistência de `oauth_expired_flag`
- `.planning/phases/08-painel-laravel-filament/deferred-items.md` - Documentação de falhas pré-existentes fora de escopo

## Testes RED — lista explícita

### `clip-processor/tests/test_internal_api.py` (6 testes, 4 falham RED)
| Teste | Resultado | O que cobre |
|---|---|---|
| `test_resolve_channel_requires_auth` | PASS (já coberto pelo skeleton) | 401 sem header `X-Internal-Token` |
| `test_resolve_channel_returns_channel_data` | **FAIL (RED)** | Contrato de saída `resolve_channel` — `channel_id`/`channel_name`/`channel_handle` extraídos do JSON yt-dlp; falha hoje porque `src.internal_api` ainda não importa `subprocess` (AttributeError no patch) |
| `test_resolve_channel_returns_422_on_ytdlp_failure` | **FAIL (RED)** | Resposta 422 com `error: 'yt-dlp failed'` quando yt-dlp retorna exit != 0; mesmo motivo RED acima |
| `test_reject_clip_requires_auth` | PASS (já coberto pelo skeleton) | 401 sem header `X-Internal-Token` |
| `test_reject_clip_calls_rejeitar_and_returns_exit_code` | **FAIL (RED)** | Endpoint deve chamar `rejeitar(clip_id)` diretamente (sem subprocess) e retornar `exit_code`; falha hoje porque `reject_clip` levanta `NotImplementedError` (endpoint retorna 501 em vez de 200) |
| `test_reject_clip_propagates_exit_code_1` | **FAIL (RED)** | Mesmo motivo acima — contrato de propagação de exit_code=1 (clip não existe) |

### `clip-processor/tests/test_uploader_expired.py` (1 teste, RED)
| Teste | Resultado | O que cobre |
|---|---|---|
| `test_load_credentials_catches_refresh_error_and_flags_channel` | **FAIL (RED)** | `_load_credentials()` deve capturar `RefreshError` e persistir `UPDATE destination_channels SET oauth_expired_flag=TRUE` para o slug atual; falha hoje porque `src.uploader` não define `db_connect` (AttributeError no patch — `_load_credentials()` hoje só propaga `RefreshError` sem side-effect no MySQL) |

**Confirmação de RED state:** `pytest tests/test_internal_api.py tests/test_uploader_expired.py -v` → **5 failed, 2 passed** (os 2 passes são os testes de auth já cobertos 100% pelo skeleton — comportamento esperado e correto, não uma falha de plano).

## Confirmação de zero regressão

- **Antes/depois deste plano:** nenhum teste existente foi modificado. Contagem `pytest tests/ -q --ignore=tests/test_internal_api.py --ignore=tests/test_uploader_expired.py` → **127 passed, 3 failed**.
- As 3 falhas (`TestCanUpload::test_before_window_start`, `test_after_window_end`, `test_outside_window_midnight` em `test_quota_manager.py`) são **pré-existentes**, causadas por uma mudança já presente no working tree antes do início deste plano (`UPLOAD_WINDOW_BYPASS` em `quota_manager.py` + `.env` com `UPLOAD_WINDOW_BYPASS=true`) — não relacionadas a nenhum arquivo tocado por este plano. Documentado em `deferred-items.md` (fora de escopo, SCOPE BOUNDARY rule).
- **Conclusão:** zero regressão atribuível a este plano.

## Contrato JSON dos endpoints (para Plans 08-05/08-07 consumirem)

### POST /internal/resolve-channel
- Header: `X-Internal-Token: {CLIP_PROCESSOR_INTERNAL_TOKEN}` (obrigatório)
- Body JSON: `{"url": "https://youtube.com/@handle"}`
- Response 200: `{"channel_id": "UCxxx", "channel_name": "Nome", "channel_handle": "@handle"}`
- Response 422: `{"error": "yt-dlp failed", "stderr": "..."}` (URL inválida ou canal inexistente)
- Response 401: `{"error": "unauthorized"}` (token inválido/ausente)

### POST /internal/reject-clip
- Header: `X-Internal-Token: {CLIP_PROCESSOR_INTERNAL_TOKEN}` (obrigatório)
- Body JSON: `{"clip_id": 42}`
- Response 200: `{"exit_code": 0}` (sucesso) OU `{"exit_code": 1}` (clip não existe) OU `{"exit_code": 2}` (status inválido)
- Response 401: `{"error": "unauthorized"}`

### Coluna nova em `destination_channels`
```sql
oauth_expired_flag BOOLEAN NOT NULL DEFAULT FALSE
-- Producer: uploader.py._load_credentials() ao capturar google.auth.exceptions.RefreshError (Plan 08-06)
-- Consumer: Laravel DestinationChannel model (accessor oauth_status) (Plan 08-04/08-05)
-- Self-healing: uploader.py reseta para FALSE em upload bem-sucedido (Plan 08-06)
```

## Decisions Made
- `oauth_expired_flag` implementado como coluna MySQL simples (não Redis/cache Laravel) — decisão já direcionada pelo 08-RESEARCH.md e confirmada no plan.
- `internal_api.py` importa `src.rejeitar.rejeitar` no topo do módulo (não dentro de `reject_clip`) para que os testes possam usar `patch('src.internal_api.rejeitar')` diretamente no namespace do módulo.
- Container `clip-processor` foi rebuilded (`docker compose build clip-processor && up -d`) para que o novo `src/internal_api.py` e a dependência `flask` fossem refletidos na imagem — Dockerfile só faz `COPY src/ src/`, sem bind mount de `src/` (padrão já documentado nas Phases 2 e 6). Diretório `tests/` também não é copiado para a imagem — usado `docker cp` para rodar a suite de testes dentro do container, seguindo o mesmo padrão documentado em `06-04-SUMMARY.md`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Comando `docker exec -T` incompatível com a versão local do Docker CLI**
- **Found during:** Task 2 (verificação de import do skeleton)
- **Issue:** O plano especifica `docker exec -T clip-processor ...`, mas a flag `-T` não é reconhecida pelo `docker exec` (versão 20.10.21 instalada) — é uma flag de `docker compose exec`, não de `docker exec` puro. Comando falhava com `unknown shorthand flag: 'T'`.
- **Fix:** Todos os comandos de verificação foram executados como `docker exec clip-processor ...` (sem `-T`), que é equivalente para comandos não-interativos.
- **Files modified:** Nenhum arquivo de código — apenas ajuste de comando de verificação nesta sessão.
- **Verification:** Todos os comandos `docker exec` (sem `-T`) executaram como esperado.
- **Committed in:** N/A (não gera artefato de código)

**2. [Rule 3 - Blocking] Container `clip-processor` não reflete mudanças em `src/`/`tests/` sem rebuild ou `docker cp`**
- **Found during:** Task 2 e Task 3 (verificação de import e coleta de testes)
- **Issue:** `docker-compose.yml` monta apenas `youtube/`, `videos/` e `branding/` no container `clip-processor` — `src/` e `tests/` são copiados via `Dockerfile` (`COPY src/ src/`) apenas no build da imagem, e `tests/` nem é copiado para a imagem em produção. Isso é um padrão já documentado em `06-04-SUMMARY.md` (Phase 6).
- **Fix:** `docker compose build clip-processor && docker compose up -d clip-processor` (para refletir `src/internal_api.py` + `flask` na imagem) e `docker cp clip-processor/tests/. clip-processor:/app/tests/` (para rodar a suite de testes RED dentro do container, sem persistir no Dockerfile — consistente com o padrão da Phase 6).
- **Files modified:** Nenhum arquivo de código adicional.
- **Verification:** `docker exec clip-processor python -c "from src import internal_api; ..."` → `SKELETON_OK`; `pytest --collect-only` → 7 itens coletados sem erro.
- **Committed in:** N/A (operação de infraestrutura local, não gera commit)

---

**Total deviations:** 2 auto-fixed (ambos Rule 3 - Blocking, relacionados a ambiente Docker local, não a código de produção)
**Impact on plan:** Nenhum impacto no escopo do plano. Ambos os desvios são operacionais (comandos de verificação/deploy local) e não alteraram nenhum arquivo além dos já especificados no plano.

## Issues Encountered
- 3 falhas pré-existentes e fora de escopo em `test_quota_manager.py` foram detectadas durante a checagem de regressão (Task 3). Documentadas em `deferred-items.md` — não corrigidas por estarem fora do escopo deste plano (mudança em `quota_manager.py` já presente no working tree antes do início da execução, não relacionada a `oauth_expired_flag`/`internal_api`).

## User Setup Required

None - nenhuma configuração externa necessária. A dependência `flask` já foi instalada na imagem Docker via rebuild; nenhuma ação manual pendente para este plano específico.

## Next Phase Readiness
- Contrato HTTP dos endpoints `/internal/resolve-channel` e `/internal/reject-clip` está estável e documentado — Plan 08-05 (Laravel `ClipProcessorClient`) e Plan 08-07 (implementação GREEN do sidecar) podem consumir/implementar contra ele sem ambiguidade.
- Coluna `oauth_expired_flag` pronta para o accessor `oauth_status` do Model Laravel `DestinationChannel` (Plan 08-04).
- Plan 08-06 tem o teste RED (`test_uploader_expired.py`) que define exatamente o comportamento esperado de `_load_credentials()` — implementação fica direta: capturar `RefreshError`, persistir a flag via `db_connect`/`get_db_connection`, reset em upload bem-sucedido.
- **Concern:** existem mudanças pré-existentes não commitadas em `clip-processor/src/uploader.py`, `pipeline_runner.py`, `rss_poller.py`, `selector.py`, `transcriber.py`, `youtube_oauth.py` (ver `deferred-items.md`). Recomenda-se revisão/commit ou descarte dessas mudanças antes do Plan 08-06 tocar `uploader.py` novamente, para evitar misturar diffs não relacionados.

---
*Phase: 08-painel-laravel-filament*
*Completed: 2026-07-01*

## Self-Check: PASSED

All 6 created files verified present on disk. All 3 task commits (`78f75c8`, `c2b729d`, `afe515b`) verified present in git history.
