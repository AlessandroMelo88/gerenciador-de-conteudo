---
phase: 08-painel-laravel-filament
plan: 06
subsystem: filament-resource+pipeline
tags: [filament, laravel, python, oauth, refresh-error, badge, tdd-green]

# Dependency graph
requires:
  - phase: 08-painel-laravel-filament
    plan: 02
    provides: oauth_expired_flag column migration, test_uploader_expired.py RED test
  - phase: 08-painel-laravel-filament
    plan: 03
    provides: DestinationChannel Model + oauth_status accessor (already GREEN) + DestinationChannelResourceTest/DestinationChannelOauthStatusTest RED tests
provides:
  - uploader.py._load_credentials captures google.auth.exceptions.RefreshError, persists oauth_expired_flag=TRUE, re-raises
  - uploader.py.upload_clip self-healing reset of oauth_expired_flag=FALSE on successful upload
  - DestinationChannelResource (Filament) — CRUD canais-destino with explicit niche Select + OAuth badge (authorized/expired/missing) + copy-paste OAuth instruction block
  - POST /admin/destination-channels REST route (routes/web.php) for direct form submission contract
affects: [08-08-destination-channel-approval-widgets, 08-09-dashboard-widgets]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "uploader.py: RefreshError caught around creds.refresh() only, best-effort MySQL UPDATE via db_connect() with try/except Exception (never masks the original RefreshError)"
    - "_flag_expired/_clear_expired skip silently when channel_slug is None — legacy single-token /app/token.json flow untouched"
    - "Filament Resource without --generate: Select::make('niche')->options([...]) explicit, TextColumn::make('oauth_status')->badge()->color(match) — same pattern established by SourceChannelResource (Plan 08-05)"
    - "REST route in routes/web.php alongside Filament Resource — Filament 5 only registers GET/HEAD; Livewire handles actual form submit. Direct POST/PATCH tests (Plan 08-03 contract) require an explicit route reusing the same Model, mirrors Plan 08-05 pattern for SourceChannelResource"

key-files:
  created:
    - painel/app/Filament/Resources/DestinationChannelResource.php
    - painel/app/Filament/Resources/DestinationChannelResource/Pages/ListDestinationChannels.php
    - painel/app/Filament/Resources/DestinationChannelResource/Pages/CreateDestinationChannel.php
    - painel/app/Filament/Resources/DestinationChannelResource/Pages/EditDestinationChannel.php
  modified:
    - clip-processor/src/uploader.py
    - painel/routes/web.php
    - .planning/phases/08-painel-laravel-filament/deferred-items.md

key-decisions:
  - "db_connect imported at module top of uploader.py (from src.db import get_db_connection as db_connect) — matches test_uploader_expired.py contract patch('src.uploader.db_connect')"
  - "_clear_expired() called immediately after video_id is confirmed non-null in upload_clip, before the thumbnail upload block — self-healing runs even if thumbnail step later fails"
  - "POST /admin/destination-channels added to routes/web.php (not in plan's files_modified) — same architectural pattern already established and documented by Plan 08-05 for source-channels; Filament Resources only expose GET/HEAD routes"

requirements-completed: [PANEL-02]

# Metrics
duration: ~25min
completed: 2026-07-02
---

# Phase 8 Plan 06: uploader.py RefreshError capture + DestinationChannelResource Summary

**`uploader.py._load_credentials` now catches `google.auth.exceptions.RefreshError`, persists `destination_channels.oauth_expired_flag=TRUE` for the failing channel, and re-raises; `upload_clip` self-heals the flag back to `FALSE` on successful upload. `DestinationChannelResource` (Filament) provides full CRUD for `destination_channels` with an explicit `niche` Select, a 3-color OAuth badge (authorized/expired/missing), and a copy-paste OAuth authorization command block.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2/2 completed
- **Files created/modified:** 7 (1 Python file modified, 4 Filament files created, 1 routes file modified, 1 deferred-items.md updated)

## Accomplishments

- `_load_credentials()` wraps `creds.refresh(Request())` in `try/except RefreshError`, calling `self._flag_expired()` (best-effort `UPDATE destination_channels SET oauth_expired_flag=TRUE WHERE slug=%s`) before re-raising — the exception itself is never swallowed, only the persistence side-effect is defensive (`except Exception` around the DB call, logged, does not replace the RefreshError).
- `upload_clip()` calls `self._clear_expired()` immediately after `video_id` is confirmed valid (before the thumbnail block) — resets `oauth_expired_flag=FALSE` for the channel, self-healing the badge back to `authorized` on the next panel poll.
- Both `_flag_expired`/`_clear_expired` are no-ops when `self.channel_slug` is `None` — preserves the legacy single-token `/app/token.json` flow used before multi-canal (Phase 7).
- `DestinationChannelResource` created with `Select::make('niche')->options(['futebol'=>'Futebol','podcast'=>'Podcast'])` (zero `--generate`, zero inferred ENUM), `TextColumn::make('oauth_status')->badge()->color(...)` mapping `authorized→success`, `expired→danger`, `missing→gray`, and a `Placeholder` rendering the copy-paste command `docker exec -it clip-processor python -m src.youtube_oauth --channel {slug}` on the edit form.
- 3 Pages created (`ListDestinationChannels`, `CreateDestinationChannel`, `EditDestinationChannel`) mirroring the structure already established by `SourceChannelResource` (Plan 08-05) — single-file Resource + `Pages\` namespace, not the `Schemas/`+`Tables/` convention auto-generated by `make:filament-resource`.
- `routes/web.php` gained `POST /admin/destination-channels` (protected by `web`+`auth` middleware) — same architectural necessity already documented in Plan 08-05: Filament Resources only register `GET|HEAD` routes; the RED test (`DestinationChannelResourceTest`, Plan 08-03) posts directly to the REST endpoint.

## Task Commits

1. **Task 1: uploader.py — capturar RefreshError + persistir oauth_expired_flag + self-healing** - `7abb073` (feat)
2. **Task 2: Criar DestinationChannelResource + 3 Pages com Select niche explícito, badge OAuth e bloco copy-paste** - `f13827b` (feat)

## Testes GREEN — confirmação explícita

### `clip-processor/tests/test_uploader_expired.py` + `test_uploader.py` (Python)
```
$ docker exec clip-processor pytest tests/test_uploader_expired.py tests/test_uploader.py -v --no-header
tests/test_uploader_expired.py::test_load_credentials_catches_refresh_error_and_flags_channel PASSED
tests/test_uploader.py::TestUploadClip (9 tests) PASSED
tests/test_uploader.py::TestYouTubeUploaderChannelSlug (3 tests) PASSED
13 passed in 0.30s
```

### `painel/tests/Feature/DestinationChannelResourceTest.php` + `Unit/DestinationChannelOauthStatusTest.php` (Laravel)
```
$ docker exec php bash -c "cd /var/www/html/painel && php artisan test --filter='DestinationChannel'"
Tests\Unit\DestinationChannelOauthStatusTest
  ✓ it returns expired when oauth_expired_flag is true
  ✓ it returns missing when no token file exists and flag is false
  ✓ it returns authorized when token file exists and flag is false
Tests\Feature\DestinationChannelResourceTest
  ✓ it creates a destination_channel with niche via Select field
  ✓ it renders OAuth status badge in the resource table
Tests: 5 passed (8 assertions)
```

## Contador de regressão Python (antes/depois)

- **Antes deste plano (baseline Plan 08-07):** `pytest tests/ -q` → 4 failed, 133 passed (3 pré-existentes em `test_quota_manager.py` + 1 RED de `test_uploader_expired.py`, este último no escopo deste plano).
- **Depois deste plano:** `docker exec clip-processor pytest tests/ --ignore=tests/test_internal_api.py -q` → **3 failed, 128 passed** (diferença de contagem total vs `tests/test_internal_api.py` sendo ignorado nesta execução, não incluído no antes). As 3 falhas remanescentes são as mesmas `test_quota_manager.py::TestCanUpload` já documentadas em `deferred-items.md` (Plan 08-02) — pré-existentes, fora de escopo, causadas por `UPLOAD_WINDOW_BYPASS=true` já presente no `wordpress/.env` antes deste plano.
- **`test_uploader_expired.py`:** RED → **GREEN** (1 teste, incluído nos 128 passed).
- **Conclusão:** zero regressão atribuível a este plano.

## Contador de regressão Laravel (painel)

- `docker exec php bash -c "cd /var/www/html/painel && php artisan test"` → **6 failed, 19 passed** no total da suite.
- Os 6 falhas são **pré-existentes e fora de escopo**: 4 em `ClipApprovalActionTest` (rotas `/admin/clips/{id}/approve|reject` não existem — Plan 08-08) e 2 em `DashboardPollingTest` (widgets de dashboard não implementados — Plan 08-09). Documentado em `deferred-items.md`.
- Os únicos testes que mudaram de estado neste plano: `DestinationChannelResourceTest` (2 RED → 2 GREEN) e `DestinationChannelOauthStatusTest` (já era 3 GREEN desde Plan 08-03, sem mudança, apenas confirmado ainda GREEN).
- `SourceChannelResourceTest` (3/3) permanece GREEN — zero regressão nos testes já GREEN de planos anteriores.

## Confirmação de Select explícito (print grep)

```
$ grep -c "Select::make('niche')" painel/app/Filament/Resources/DestinationChannelResource.php
1
$ grep -c "options(\[" painel/app/Filament/Resources/DestinationChannelResource.php
1
$ grep -r "Filament\\Tables\\Actions" painel/app | wc -l
0
```

## Diff resumido do `uploader.py`

- **Import novo:** `from src.db import get_db_connection as db_connect` (topo do módulo).
- **Import novo:** bloco `try/except ModuleNotFoundError` para `google.auth.exceptions.RefreshError` (fallback local para ambientes sem a dependência instalada, mesmo padrão já usado para `Credentials`/`MediaFileUpload`/`googleapiclient.errors`).
- **`__init__`:** `self.channel_slug = channel_slug` armazenado (antes não era guardado como atributo).
- **`_load_credentials`:** `creds.refresh(Request())` agora dentro de `try/except RefreshError: self._flag_expired(); raise`.
- **Métodos novos:** `_flag_expired()` e `_clear_expired()` — ambos fazem `UPDATE destination_channels SET oauth_expired_flag={TRUE|FALSE} WHERE slug=%s` via `db_connect()`, com guard de `channel_slug is None` (skip) e `except Exception` defensivo (log, não propaga — nunca mascara o `RefreshError` original).
- **`upload_clip`:** chamada `self._clear_expired()` inserida logo após a validação de `video_id`, antes do bloco de thumbnail.

## Decisions Made

- `db_connect` importado no topo do módulo (não lazy dentro do método) — necessário para que `patch('src.uploader.db_connect')` no teste funcione, e consistente com o padrão já estabelecido em `internal_api.py` (Plan 08-02) para `src.rejeitar`.
- `_clear_expired()` chamado antes do upload de thumbnail (não no final do método) — garante que o self-healing rode mesmo que a etapa de thumbnail falhe depois.
- Rota REST `POST /admin/destination-channels` adicionada em `routes/web.php` fora do `files_modified` original do plano — mesma decisão arquitetural já documentada e justificada em `08-05-SUMMARY.md` para `source-channels`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Filament Resource só expõe GET/HEAD — teste RED exigia POST direto**
- **Found during:** Task 2, ao rodar `DestinationChannelResourceTest` pela primeira vez (`it creates a destination_channel with niche via Select field` fazia `$this->post('/admin/destination-channels', [...])`).
- **Issue:** Idêntico ao já documentado em `08-05-SUMMARY.md` para `SourceChannelResource` — Filament 5 só registra rotas `GET|HEAD` para `index`/`create`/`edit`; o submit real do formulário é via Livewire (AJAX), não HTTP `POST` tradicional.
- **Fix:** Adicionada rota `POST /admin/destination-channels` em `routes/web.php`, protegida por `middleware(['web', 'auth'])`, criando o registro diretamente via `DestinationChannel::create()` (sem chamada a `ClipProcessorClient` — canais-destino não precisam de resolução via yt-dlp, diferente de canais-fonte).
- **Files modified:** `painel/routes/web.php`
- **Verification:** `php artisan test --filter=DestinationChannelResourceTest` → 2/2 GREEN.
- **Commit:** `f13827b`

**2. [Rule 3 - Blocking] Container `clip-processor` não reflete `src/uploader.py` sem `docker cp`**
- **Found during:** Task 1, ao rodar os testes pela primeira vez após a edição — `_load_credentials` no container ainda era a versão antiga (arquivo copiado no build da imagem, não bind-mounted).
- **Issue:** Mesmo padrão já documentado em `08-02-SUMMARY.md`/`08-07-SUMMARY.md` — `src/` só é sincronizado via `docker cp` ou rebuild de imagem, não bind mount.
- **Fix:** `docker cp clip-processor/src/uploader.py clip-processor:/app/src/uploader.py` e `docker cp clip-processor/tests/. clip-processor:/app/tests/` antes de rodar a suíte.
- **Files modified:** Nenhum arquivo de código adicional — apenas sincronização de ambiente local.
- **Verification:** `docker exec clip-processor python -c "import src.uploader"` → sem erro; suíte roda com o código atualizado.
- **Committed in:** N/A (operação de infraestrutura local)

---

**Total deviations:** 2 auto-fixed (ambos Rule 3 - Blocking, um de arquitetura de rotas já estabelecido em Plan 08-05, outro de sincronização de ambiente Docker local já estabelecido em Plans 08-02/08-07).
**Impact on plan:** Nenhum impacto de escopo ou arquitetura — ambos os desvios seguem padrões já documentados e aprovados em plans anteriores desta mesma phase.

## Issues Encountered

Nenhum issue não resolvido. 6 falhas pré-existentes em `ClipApprovalActionTest`/`DashboardPollingTest` (Laravel) e 3 em `test_quota_manager.py` (Python) confirmadas fora de escopo e documentadas em `deferred-items.md`.

## User Setup Required

None — nenhuma ação manual externa necessária para este plano.

## Next Phase Readiness

- PANEL-02 completo: CRUD de canais-destino + badge OAuth com 3 estados observáveis (authorized/expired/missing), incluindo o produtor real do estado `expired` (`uploader.py`).
- `ClipProcessorClient` (Plan 08-05) não precisou de extensão — o badge OAuth é resolvido inteiramente pelo accessor `DestinationChannel::oauth_status` (Model + arquivo de token + flag MySQL), sem chamada HTTP ao sidecar.
- Plans 08-08 (ClipApprovalAction) e 08-09 (Dashboard widgets) têm seus contratos RED intactos e documentados como fora de escopo deste plano.
- Nenhum bloqueio identificado.

---
*Phase: 08-painel-laravel-filament*
*Completed: 2026-07-02*

## Self-Check: PASSED

All 4 created files verified present on disk (DestinationChannelResource.php + 3 Pages). Both task commits (`7abb073`, `f13827b`) confirmed present in git log.
