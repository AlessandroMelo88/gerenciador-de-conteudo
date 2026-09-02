---
phase: 08-painel-laravel-filament
plan: 07
subsystem: api
tags: [flask, sidecar, internal-http, yt-dlp, threading]

# Dependency graph
requires:
  - phase: 08-painel-laravel-filament
    plan: 02
    provides: internal_api.py skeleton + 6 testes RED (test_internal_api.py), oauth_expired_flag migration
provides:
  - Implementação GREEN de resolve_channel (yt-dlp subprocess) e reject_clip (chamada direta a src.rejeitar.rejeitar)
  - Thread daemon Flask iniciada em main.py, disponível imediatamente no boot do container (antes do ciclo inicial do pipeline)
  - CLIP_PROCESSOR_INTERNAL_TOKEN propagado ao container clip-processor via docker-compose.yml
affects: [08-05-laravel-http-client, 08-08-panel-approval-rejection-action]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sidecar HTTP interno em thread daemon iniciada ANTES do primeiro ciclo do pipeline (não depois) — garante disponibilidade imediata para o painel Laravel sem esperar minutos de download/transcrição"

key-files:
  created: []
  modified:
    - clip-processor/src/internal_api.py
    - clip-processor/src/main.py
    - /Users/alessandrobm1/develop/server/wordpress/docker-compose.yml (fora do repo git — aplicado direto no FS)
    - /Users/alessandrobm1/develop/server/wordpress/.env (fora do repo git — token real gerado)
    - .env.example
    - painel/.env (fora do repo git via .gitignore — token real gerado)

key-decisions:
  - "Thread daemon do sidecar Flask posicionada ANTES de run_pipeline_once() no boot (não depois, como o snippet literal do plano sugeria) — o ciclo inicial do pipeline pode levar minutos (download+transcrição+corte); o painel precisa do sidecar disponível assim que o container sobe, não após o primeiro ciclo completo"
  - "CLIP_PROCESSOR_INTERNAL_TOKEN documentado em canaldecortes/.env.example (não em painel/README.md) — evita contenção de merge com outros plans da Wave 3 que tocam painel/"
  - "docker-compose.yml real consumido pelo Docker Compose é wordpress/.env (não canaldecortes/.env) — token real gerado com openssl rand -hex 32 e propagado nos DOIS arquivos (wordpress/.env para o clip-processor via docker-compose.yml, painel/.env para o Laravel) para consistência"

requirements-completed: [PANEL-01, PANEL-04]

# Metrics
duration: ~25min
completed: 2026-07-01
---

# Phase 8 Plan 07: GREEN internal_api.py + wiring main.py + docker-compose Summary

**Substituída a "ponte docker exec" pelo sidecar HTTP interno real: `resolve_channel` roda `yt-dlp --dump-single-json` via subprocess e `reject_clip` chama `src.rejeitar.rejeitar` diretamente; thread Flask daemon inicia em `main.py` antes do ciclo do pipeline; `CLIP_PROCESSOR_INTERNAL_TOKEN` propagado ponta-a-ponta e validado com 401 real via container `php`.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-07-01T22:20:00-03:00 (aprox.)
- **Completed:** 2026-07-01T22:35:00-03:00 (aprox.)
- **Tasks:** 2/2 completed
- **Files modified:** 2 no repo git (internal_api.py, main.py) + 1 doc (.env.example) + 3 fora do repo (docker-compose.yml, wordpress/.env, painel/.env)

## Accomplishments

- `resolve_channel(url)` implementado: `subprocess.run(['yt-dlp', '--flat-playlist', '--skip-download', '--dump-single-json', url], ...)`, mapeia `id`→`channel_id`, `channel`/`title`→`channel_name`, `uploader_id`/`channel_id`→`channel_handle` com prefixo `@` normalizado. `RuntimeError` em exit code != 0, capturado na rota e retornado como 422.
- `reject_clip(clip_id)` implementado: chama `rejeitar(int(clip_id))` diretamente (sem subprocess), preservando 100% dos side-effects (remoção do MP4) e exit codes (0/1/2) já documentados em `rejeitar.py` (Plan 06-03).
- `main.py` ganhou `threading.Thread(target=_start_internal_api, daemon=True, name='internal-api').start()` — **posicionada ANTES de `run_pipeline_once()`** (desvio deliberado do snippet literal do plano — ver Deviations), garantindo que o sidecar HTTP responda imediatamente após o boot do container, sem depender da duração do primeiro ciclo do pipeline (download+transcrição+corte, que pode levar minutos).
- `docker-compose.yml` (fora do repo git `canaldecortes/`, aplicado direto no FS conforme padrão já estabelecido nas Phases 6/8-01) recebeu `CLIP_PROCESSOR_INTERNAL_TOKEN=${CLIP_PROCESSOR_INTERNAL_TOKEN}` no serviço `clip-processor`.
- Token real gerado via `openssl rand -hex 32` e propagado em `wordpress/.env` (arquivo real consumido pelo Docker Compose, diferente de `canaldecortes/.env`) e em `canaldecortes/painel/.env` — os dois lados batem.
- `canaldecortes/.env.example` documentado com instrução copy-paste `openssl rand -hex 32` e nota explícita de que o mesmo valor deve ir em `painel/.env`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implementar `resolve_channel` e `reject_clip` em `internal_api.py`** - `4418c55` (feat)
2. **Task 2: Wire `internal_api.app` em thread daemon no `main.py` + documentar `CLIP_PROCESSOR_INTERNAL_TOKEN`** - `e35a5f8` (feat)

_Nota: `docker-compose.yml`, `wordpress/.env` e `canaldecortes/painel/.env` ficam fora do repo git `canaldecortes/` (o primeiro por estar em `wordpress/`, os dois últimos por `.gitignore`) — alterações aplicadas direto no filesystem, sem commit, seguindo o padrão já documentado em `08-01-SUMMARY.md` e `06-06-SUMMARY.md`._

## Confirmação de 401 (auth) — comando real executado

```
$ docker exec php curl -s -o /dev/null -w '%{http_code}' -X POST http://clip-processor:8090/internal/reject-clip -H 'Content-Type: application/json' -d '{"clip_id":1}'
401
```

```
$ docker exec php curl -s -o /dev/null -w "%{http_code}\n" -X POST http://clip-processor:8090/internal/resolve-channel -H "Content-Type: application/json" -d '{}'
401
```

Ambos confirmam: o sidecar está no ar na rede docker `internal` (alcançável a partir do container `php`, que hospeda o painel Laravel), e a autenticação por `X-Internal-Token` está ativa e rejeitando requests sem header/token correto.

## Confirmação de porta 8090 NÃO publicada no host

```
$ docker port clip-processor
(vazio)
$ docker port clip-processor | grep -c 8090
0
```

Nenhuma porta publicada — o sidecar só é alcançável de dentro da rede docker `internal`, nunca do host local ou de fora do stack Docker.

## Instruções copiáveis para o operador (setup do token)

```bash
# 1. Gerar o token uma única vez
openssl rand -hex 32

# 2. Colar o MESMO valor em DOIS lugares:
#    - wordpress/.env (arquivo real lido pelo docker-compose.yml, propaga ao container clip-processor)
#      CLIP_PROCESSOR_INTERNAL_TOKEN=<hex>
#    - canaldecortes/painel/.env (Laravel envia esse valor no header X-Internal-Token)
#      CLIP_PROCESSOR_INTERNAL_TOKEN=<hex>

# 3. Recriar o container clip-processor para aplicar a env var
docker compose -f /Users/alessandrobm1/develop/server/wordpress/docker-compose.yml up -d --force-recreate clip-processor
```

Documentado também em `canaldecortes/.env.example` para referência futura.

## Testes RED do 08-02 agora GREEN

```
$ docker exec clip-processor pytest tests/test_internal_api.py -v --no-header
tests/test_internal_api.py::test_resolve_channel_requires_auth PASSED
tests/test_internal_api.py::test_resolve_channel_returns_channel_data PASSED
tests/test_internal_api.py::test_resolve_channel_returns_422_on_ytdlp_failure PASSED
tests/test_internal_api.py::test_reject_clip_requires_auth PASSED
tests/test_internal_api.py::test_reject_clip_calls_rejeitar_and_returns_exit_code PASSED
tests/test_internal_api.py::test_reject_clip_propagates_exit_code_1 PASSED
6 passed in 0.11s
```

6/6 GREEN (eram 4 FAIL/2 PASS no estado RED do Plan 08-02).

## Confirmação de zero regressão

```
$ docker exec clip-processor pytest tests/ -q
4 failed, 133 passed in 242.38s
FAILED tests/test_quota_manager.py::TestCanUpload::test_before_window_start
FAILED tests/test_quota_manager.py::TestCanUpload::test_after_window_end
FAILED tests/test_quota_manager.py::TestCanUpload::test_outside_window_midnight
FAILED tests/test_uploader_expired.py::test_load_credentials_catches_refresh_error_and_flags_channel
```

As 4 falhas são **pré-existentes e fora de escopo deste plano** (SCOPE BOUNDARY):
- 3 em `test_quota_manager.py` — já documentadas como pré-existentes em `08-02-SUMMARY.md` (causadas por `UPLOAD_WINDOW_BYPASS` já presente no working tree antes deste plano).
- 1 em `test_uploader_expired.py` — pertence ao escopo do **Plan 08-06** (`uploader.py` ainda não captura `RefreshError`); nenhum arquivo tocado por este plano (08-07) afeta `uploader.py`.

**Conclusão:** zero regressão atribuível ao Plan 08-07. 133 testes passando incluem os 6 de `test_internal_api.py`.

## Files Created/Modified

- `clip-processor/src/internal_api.py` - GREEN: `resolve_channel` (subprocess yt-dlp) e `reject_clip` (chamada direta a `rejeitar`)
- `clip-processor/src/main.py` - `import threading` + `_start_internal_api()` + thread daemon iniciada antes do ciclo inicial do pipeline
- `.env.example` (canaldecortes/) - documentação de `CLIP_PROCESSOR_INTERNAL_TOKEN` com instrução `openssl rand -hex 32`
- `/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml` (fora do repo) - `CLIP_PROCESSOR_INTERNAL_TOKEN=${CLIP_PROCESSOR_INTERNAL_TOKEN}` no serviço `clip-processor`
- `/Users/alessandrobm1/develop/server/wordpress/.env` (fora do repo) - token real gerado
- `canaldecortes/painel/.env` (gitignored) - token real gerado (mesmo valor)

## Decisions Made

- Thread daemon do sidecar posicionada **antes** de `run_pipeline_once()`, não depois — ver Deviations abaixo.
- Documentação do token em `.env.example` do diretório raiz `canaldecortes/` (não em `painel/README.md`) para minimizar contenção de merge com Plans paralelos da Wave 3 (08-04/05/06) que tocam arquivos dentro de `painel/`.
- Token real gerado imediatamente (não deixado como placeholder vazio) para permitir validação end-to-end real do fluxo de autenticação (401/sucesso) durante a execução deste plano, não apenas nos testes unitários mockados.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Thread do sidecar posicionada antes do ciclo inicial do pipeline, não depois**
- **Found during:** Task 2, ao validar o boot do container após a primeira implementação seguindo literalmente o snippet do plano (thread iniciada logo antes de `scheduler.start()`, ou seja, DEPOIS de `run_pipeline_once()`)
- **Issue:** `run_pipeline_once()` executa download + transcrição + corte de vídeo de forma síncrona e pode levar vários minutos no primeiro ciclo. Com a thread do sidecar iniciando só depois dessa chamada, o painel Laravel ficaria sem conseguir resolver canais ou rejeitar clips durante todo esse tempo após qualquer restart do container — quebra a proposta central do plano ("sidecar sempre disponível para o painel").
- **Fix:** Thread daemon movida para logo após o bloco de recovery (`recover_stuck_downloads`) e ANTES de `run_pipeline_once()`. Ordem final no boot: recovery → start thread sidecar → log → ciclo inicial do pipeline → scheduler.start().
- **Files modified:** `clip-processor/src/main.py`
- **Verification:** `docker logs clip-processor` confirma `[ACQU] Sidecar HTTP interno iniciado em 0.0.0.0:8090 (thread daemon)` logo após o log de boot, antes de qualquer log de poll/download. Requests reais via `docker exec php curl` retornaram 401 (esperado, sem token) com o container recém-recriado, mesmo com o ciclo do pipeline ainda rodando em paralelo (visível nos logs de download simultâneo).
- **Committed in:** `e35a5f8`

**2. [Rule 3 - Blocking] `wordpress/.env` (não `canaldecortes/.env`) é o arquivo real lido pelo Docker Compose**
- **Found during:** Task 2, ao recriar o container e notar warning "CLIP_PROCESSOR_INTERNAL_TOKEN variable is not set" mesmo após editar `canaldecortes/.env`
- **Issue:** `docker-compose.yml` vive em `wordpress/` e o Docker Compose usa o `.env` do MESMO diretório do compose file (`wordpress/.env`), não `canaldecortes/.env`. O plano assumia implicitamente que bastava editar `canaldecortes/.env`.
- **Fix:** Token adicionado também em `wordpress/.env` (arquivo fora do repo git `canaldecortes/`, editado direto no FS, mesmo padrão de `docker-compose.yml`).
- **Files modified:** `/Users/alessandrobm1/develop/server/wordpress/.env` (fora do repo git)
- **Verification:** `docker exec clip-processor env | grep CLIP_PROCESSOR_INTERNAL_TOKEN` retornou o valor esperado após recriar o container.
- **Committed in:** N/A (arquivo fora do repo git, sem commit — consistente com padrão já estabelecido)

**3. [Rule 3 - Blocking] `docker exec -T` incompatível com a versão local do Docker CLI**
- **Found during:** Task 2, ao rodar o comando de verificação automatizada do plano
- **Issue:** Mesmo problema já documentado em `08-02-SUMMARY.md` — a flag `-T` de `docker exec` não é reconhecida pela versão local do Docker CLI (é uma flag de `docker compose exec`, não de `docker exec` puro).
- **Fix:** Comando de verificação executado como `docker exec php curl ...` (sem `-T`) — resultado idêntico para comandos não-interativos.
- **Files modified:** Nenhum arquivo de código — apenas ajuste de comando de verificação nesta sessão.
- **Committed in:** N/A (não gera artefato de código)

---

**Total deviations:** 3 (1 Rule 2 - funcionalidade crítica de disponibilidade do sidecar, 2 Rule 3 - ambiente Docker local)
**Impact on plan:** Nenhum impacto negativo no escopo — a mudança de posicionamento da thread (Deviation 1) é estritamente uma melhoria de robustez sobre o snippet literal do plano, mantendo 100% do contrato/interface especificado (mesmos endpoints, mesma auth, mesmo bind). As Deviations 2 e 3 são ajustes operacionais de ambiente local, sem alteração de código de produção além do já previsto.

## Issues Encountered

Nenhum issue bloqueante não coberto pelas Deviations acima.

## User Setup Required

**Ação já realizada nesta execução** (não pendente): token `CLIP_PROCESSOR_INTERNAL_TOKEN` gerado via `openssl rand -hex 32` e propagado em `wordpress/.env` + `canaldecortes/painel/.env`. Nenhuma ação manual adicional necessária para este plano — mas se o operador rotacionar o token no futuro, deve lembrar de atualizar AMBOS os arquivos (não apenas um) e recriar o container `clip-processor`.

## Next Phase Readiness

- Contrato HTTP `/internal/resolve-channel` e `/internal/reject-clip` está 100% implementado (GREEN) e validado end-to-end (não apenas com testes mockados) via `docker exec php curl` alcançando o container `clip-processor` pela rede `internal`.
- Plan 08-08 (Approval/Rejection action no painel) já pode consumir `ClipProcessorClient` (Plan 08-05) contra um backend real e funcional.
- Plan 08-06 (uploader `RefreshError`) permanece com seu teste RED (`test_uploader_expired.py`) intacto — não afetado por este plano.
- **Concern residual:** `wordpress/.env` e `wordpress/docker-compose.yml` continuam fora do controle de versão do repositório `canaldecortes/` — qualquer novo Plan que precise de env vars adicionais no `clip-processor` deve lembrar de editar `wordpress/.env` (não apenas `canaldecortes/.env`), como documentado nesta Deviation.

---
*Phase: 08-painel-laravel-filament*
*Completed: 2026-07-01*

## Self-Check: PASSED

All modified files verified present on disk (internal_api.py, main.py, .env.example, SUMMARY.md). Both task commits (`4418c55`, `e35a5f8`) verified present in git history.
