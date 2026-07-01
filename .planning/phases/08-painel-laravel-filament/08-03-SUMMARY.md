---
phase: 08-painel-laravel-filament
plan: 03
subsystem: models-tests
tags: [eloquent, factories, pest, phpunit, mysql, tdd-red]

# Dependency graph
requires:
  - phase: 08-painel-laravel-filament
    plan: 01
    provides: Laravel 13 + Filament 5.4 + Pest 4 funcional em painel/, .env conectado a clips_automation
provides:
  - 4 Eloquent Models (SourceChannel, DestinationChannel, SourceVideo, GeneratedClip) apontando para tabelas do pipeline Python sem migration Laravel
  - Accessor DestinationChannel::oauth_status (expired/authorized/missing) — GREEN, coberto por tests/Unit/DestinationChannelOauthStatusTest.php
  - 4 Factories (SourceChannelFactory, DestinationChannelFactory, SourceVideoFactory, GeneratedClipFactory) com cascata de FKs
  - phpunit.xml apontando para MySQL clips_automation real (DatabaseTransactions, não RefreshDatabase)
  - Migrations Laravel nativas (users/cache/jobs) aplicadas em clips_automation
  - 6 test files RED (5 Feature + 1 Unit) definindo o contrato de comportamento dos Plans 08-04..08-08
affects: [08-04-auth-user-commands, 08-05-source-channel-resource, 08-06-uploader-refresh-error, 08-07-internal-api-client, 08-08-destination-channel-resource, 08-09-dashboard-widgets]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eloquent Model com $table explícito e SEM Schema::create correspondente — schema já existe via mysql/init/*.sql, nunca rodar php artisan make:migration para essas tabelas"
    - "phpunit.xml usa MySQL real (clips_automation) + DatabaseTransactions por teste — não RefreshDatabase, que apagaria as tabelas do pipeline Python"
    - "tests/Pest.php estende Tests\\TestCase também em Unit (não só Feature) — necessário sempre que um teste Unit precisar do helper config()/app() sem tocar o banco"

key-files:
  created:
    - painel/app/Models/SourceChannel.php
    - painel/app/Models/DestinationChannel.php
    - painel/app/Models/SourceVideo.php
    - painel/app/Models/GeneratedClip.php
    - painel/database/factories/SourceChannelFactory.php
    - painel/database/factories/DestinationChannelFactory.php
    - painel/database/factories/SourceVideoFactory.php
    - painel/database/factories/GeneratedClipFactory.php
    - painel/tests/Feature/AuthGuardTest.php
    - painel/tests/Feature/SourceChannelResourceTest.php
    - painel/tests/Feature/DestinationChannelResourceTest.php
    - painel/tests/Feature/DashboardPollingTest.php
    - painel/tests/Feature/ClipApprovalActionTest.php
    - painel/tests/Unit/DestinationChannelOauthStatusTest.php
  modified:
    - painel/config/services.php (token_dir adicionado ao bloco clip_processor)
    - painel/.env / painel/.env.example (CLIP_PROCESSOR_TOKEN_DIR documentado; DB_PASSWORD preenchido no .env real)
    - painel/phpunit.xml (DB_CONNECTION=mysql, DB_HOST=mysql, DB_DATABASE=clips_automation, DB_USERNAME=clips_user)
    - painel/tests/Pest.php (Unit também estende Tests\TestCase)

key-decisions:
  - "DatabaseTransactions (não RefreshDatabase) em todos os testes Feature — RefreshDatabase apagaria/recriaria as tabelas do pipeline Python (source_channels, destination_channels, source_videos, generated_clips), que não têm migration Laravel"
  - "token_dir configurável via CLIP_PROCESSOR_TOKEN_DIR (default /var/www/html/painel/../youtube) — permite ao operador sobrescrever se o bind mount ./canaldecortes/youtube não estiver montado no container php (ver Concern abaixo)"
  - "tests/Pest.php: Unit também estende Tests\\TestCase — sem essa mudança, DestinationChannelOauthStatusTest falha com BindingResolutionException ao chamar config() (Container sem app Laravel bootado); mesmo padrão usado por Feature, só que sem RefreshDatabase/DatabaseTransactions (nenhum teste Unit toca o banco)"

requirements-completed: []

# Metrics
duration: ~40min
completed: 2026-07-01
---

# Phase 8 Plan 03: Wave 0 Laravel — Models, Factories, Testes RED Summary

**4 Eloquent Models sem migration apontando para as tabelas do pipeline Python, 4 Factories com cascata de FKs, phpunit.xml migrado para MySQL real com DatabaseTransactions, e 6 test files (5 RED + 1 GREEN) que fixam o contrato de comportamento dos Plans 08-04 a 08-08.**

## Performance

- **Duration:** ~40 min
- **Tasks:** 3/3 completed
- **Files created/modified:** 18 (4 Models, 4 Factories, 6 test files, phpunit.xml, config/services.php, .env/.env.example, tests/Pest.php)

## Accomplishments

- `SourceChannel`, `DestinationChannel`, `SourceVideo`, `GeneratedClip` criados com `$table` explícito, `$fillable`, casts de boolean/float/int e relationships (`sourceChannel`, `sourceVideo`, `destinationChannel`) — nenhuma migration Laravel foi criada para essas 4 tabelas (confirmado: `php artisan migrate:status` só lista `0001_01_01_*` nativas).
- `DestinationChannel::getOauthStatusAttribute()` implementado exatamente conforme o contrato do 08-03-PLAN.md (`expired` se flag TRUE; `authorized` se flag FALSE e arquivo de token existe; `missing` caso contrário) — confirmado via `php artisan model:show` (accessor `oauth_status` listado) e via os 3 testes Unit, todos GREEN.
- 4 Factories geram registros válidos via `Model::factory()->make()->toArray()` — `SourceVideoFactory`/`GeneratedClipFactory` encadeiam `SourceChannel::factory()`/`DestinationChannel::factory()` para preencher FKs automaticamente.
- `phpunit.xml` migrado de `DB_CONNECTION=sqlite`/`:memory:` para `mysql`/`clips_automation` — decisão de usar `DatabaseTransactions` (não `RefreshDatabase`) registrada em todos os 5 test files Feature, preservando o schema real do pipeline Python intacto entre execuções.
- 6 test files criados nos paths exatos do 08-VALIDATION.md: `AuthGuardTest`, `SourceChannelResourceTest`, `DestinationChannelResourceTest`, `DashboardPollingTest`, `ClipApprovalActionTest` (Feature) + `DestinationChannelOauthStatusTest` (Unit).

## Task Commits

1. **Task 1: Criar 4 Eloquent Models** - `10228ab` (feat)
2. **Task 2: Criar 4 Factories + configurar phpunit.xml para MySQL real** - `4494d6c` (feat)
3. **Task 3: Criar 6 test files RED (5 Feature + 1 Unit)** - `e99e193` (test)

## Contador de testes (estado final da suite `php artisan test`)

**Total: 22 testes | GREEN: 8 | RED: 11 | (+3 sem relação com este plano: `ExampleTest` x2 já existiam do bootstrap)**

| Test file | Testes | Resultado | Justificativa |
|---|---|---|---|
| `Tests\Unit\DestinationChannelOauthStatusTest` | 3 | **3 GREEN** | Accessor `oauth_status` já implementado nesta plan (Task 1) — contrato 100% satisfeito |
| `Tests\Feature\AuthGuardTest` | 3 | **3 GREEN** | Filament 5 já provê `/admin` → redirect `/admin/login`, `/admin/login` responde 200, e `/register` não é rota registrada (404) — comportamento nativo do bootstrap Plan 08-01, nenhuma implementação adicional necessária |
| `Tests\Feature\SourceChannelResourceTest` | 3 | **3 RED** | Nenhuma rota `/admin/source-channels` existe ainda — drives Plan 08-05 |
| `Tests\Feature\DestinationChannelResourceTest` | 2 | **2 RED** | Nenhuma rota `/admin/destination-channels` existe ainda — drives Plan 08-08 |
| `Tests\Feature\DashboardPollingTest` | 2 | **2 RED** | Nenhum widget com polling implementado — drives Plan 08-09 |
| `Tests\Feature\ClipApprovalActionTest` | 4 | **4 RED** | Nenhuma rota `/admin/clips/{id}/approve\|reject` existe ainda — drives Plans 08-07/08-08 |

Coleta 100% limpa (`php artisan test` sem `ImportError`/`SyntaxError`/erro de coleta). Confirmado via 2 execuções completas da suite.

## Confirmação: nenhuma migration Laravel para as 4 tabelas do pipeline

```
$ php artisan migrate:status (antes deste plano)
ERROR  Migration table not found.

$ php artisan migrate --force (rodado nesta execução — ver Deviations)
0001_01_01_000000_create_users_table ... DONE
0001_01_01_000001_create_cache_table ... DONE
0001_01_01_000002_create_jobs_table ... DONE
```

Apenas as 3 migrations nativas do Laravel (`users`, `cache`+`cache_locks`, `jobs`+`job_batches`+`failed_jobs`) foram aplicadas em `clips_automation`. `source_channels`, `destination_channels`, `source_videos`, `generated_clips` continuam 100% geridas por `mysql/init/*.sql` — confirmado via `Schema::getColumnListing()` no tinker antes de qualquer edição, e via `git diff` (nenhum arquivo em `mysql/init/` foi tocado por este plano).

## Notas sobre `DatabaseTransactions` (por que não `RefreshDatabase`)

`RefreshDatabase` roda `migrate:fresh` (ou equivalente) a cada suite, o que apagaria `source_channels`/`destination_channels`/`source_videos`/`generated_clips` — tabelas sem migration Laravel correspondente, geridas por SQL puro do pipeline Python. `DatabaseTransactions` envolve cada teste em uma transação revertida no `tearDown()`, preservando o schema (e quaisquer dados de produção/dev já presentes) intacto. Todos os 5 test files Feature usam `uses(DatabaseTransactions::class)`.

## Path final de `token_dir`

`config('services.clip_processor.token_dir')` = `env('CLIP_PROCESSOR_TOKEN_DIR', '/var/www/html/painel/../youtube')`, documentado em `painel/.env` e `painel/.env.example`. **Concern para o Plan 08-08:** o bind mount `./canaldecortes/youtube:/app/youtube:ro` hoje só existe no serviço `clip-processor` do `wordpress/docker-compose.yml` — o serviço `php` (que serve o painel) NÃO tem esse volume montado ainda. Isso não bloqueia este plano (os 3 testes Unit usam `config(['services.clip_processor.token_dir' => ...])` com diretórios temporários, não o volume real), mas o Plan 08-08 (DestinationChannelResource / badge OAuth em produção) precisará adicionar o bind mount `./canaldecortes/youtube:/var/www/html/painel/../youtube:ro` (ou path equivalente) no serviço `php` do `wordpress/docker-compose.yml`, fora do repo git conforme padrão já estabelecido (Phase 6 P06, Phase 8 P01).

## Decisions Made

- `oauth_status` implementado exatamente como especificado no plan (sem desvio de lógica).
- `DatabaseTransactions` confirmado como estratégia de isolamento em todos os 5 Feature tests.
- Unit tests em `tests/Pest.php` passaram a estender `Tests\TestCase` (ver Deviations) — decisão registrada como padrão a seguir em Unit tests futuros que precisem de `config()`/`app()`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `painel/.env` tinha `DB_PASSWORD` vazio, impedindo qualquer conexão real ao MySQL**
- **Found during:** Task 1, verificação inicial (`php artisan tinker` retornava `Access denied for user 'clips_user'@'...' (using password: NO)`)
- **Issue:** O `.env` do painel (criado no Plan 08-01) nunca recebeu a senha real do MySQL (`CLIPS_DB_PASSWORD` do `.env` raiz do projeto), deixando `DB_PASSWORD=` vazio.
- **Fix:** Copiado o valor de `CLIPS_DB_PASSWORD` do `.env` raiz (`canaldecortes/.env`) para `painel/.env` (`DB_PASSWORD=...`). `.env` real não é versionado (apenas `.env.example`, que mantém o campo vazio).
- **Files modified:** `painel/.env` (não commitado — fora do git por padrão do projeto)
- **Verification:** `php artisan tinker --execute='dump(Schema::getColumnListing("destination_channels"));'` → schema real retornado sem erro.
- **Committed in:** N/A (arquivo `.env` não versionado)

**2. [Rule 3 - Blocking] Tabelas nativas do Laravel (`users`, `cache`, `jobs`) nunca foram migradas em `clips_automation`**
- **Found during:** Task 3, ao rodar a suite pela primeira vez — todos os testes que chamam `User::factory()->create()` falhavam com `SQLSTATE[42S02]: Base table or view not found: 1146 Table 'clips_automation.users' doesn't exist`.
- **Issue:** O Plan 08-01 instalou o Laravel/Filament/Pest mas nunca rodou `php artisan migrate` contra o banco real `clips_automation` (só existiam migrations pendentes em `painel/database/migrations/`).
- **Fix:** `php artisan migrate --force`, que criou apenas as 3 migrations nativas (`users`, `cache`+`cache_locks`, `jobs`+`job_batches`+`failed_jobs`) — nenhuma tabela do pipeline Python foi tocada (confirmado via `Schema::getColumnListing` antes/depois idênticos para as 4 tabelas do pipeline).
- **Files modified:** Nenhum arquivo de código — apenas schema do banco `clips_automation` (tabelas Laravel nativas, exatamente o que o CONTEXT.md já previa: "Migrations Laravel novas: só as tabelas Laravel próprias... vivem no MESMO banco clips_automation").
- **Verification:** `php artisan migrate:status` lista as 3 migrations como `Ran`; testes com `User::factory()->create()` passam a inserir corretamente.
- **Committed in:** N/A (mudança de schema de banco, não de arquivo versionado)

**3. [Rule 1 - Bug] `tests/Unit/DestinationChannelOauthStatusTest.php` (código exato do plano) falhava com `BindingResolutionException: Target class [config] does not exist`**
- **Found during:** Task 3, ao rodar a suite completa — 2 dos 3 testes Unit falhavam ao chamar o helper `config()`.
- **Issue:** `tests/Pest.php` (gerado no Plan 08-01) só vincula `Tests\TestCase` (app Laravel bootado) aos testes em `Feature` — testes em `Unit` usam o `PHPUnit\Framework\TestCase` puro por padrão, sem container/app Laravel disponível, então o helper global `config()` não resolve.
- **Fix:** Adicionado um segundo bloco em `tests/Pest.php`: `pest()->extend(TestCase::class)->in('Unit')` — sem `RefreshDatabase`/`DatabaseTransactions` (nenhum teste Unit toca o banco), apenas para disponibilizar `config()`/`app()`.
- **Files modified:** `painel/tests/Pest.php`
- **Verification:** `php artisan test --filter=DestinationChannelOauthStatusTest` → `3 passed`.
- **Committed in:** `e99e193` (parte do commit da Task 3)

---

**Total deviations:** 3 auto-fixed (2 Rule 3 - blocking de infraestrutura/ambiente, 1 Rule 1 - bug no bootstrap de testes)
**Impact on plan:** Nenhum desvio de escopo ou arquitetura. Todos os ajustes foram necessários para que os artefatos exatamente especificados no plano (Models, Factories, testes) funcionassem como pretendido.

## Issues Encountered

Nenhum issue não resolvido. Ver Concern acima sobre o bind mount `youtube/` no serviço `php` (não bloqueia este plano, mas é pré-requisito para o Plan 08-08 em produção).

## User Setup Required

None — nenhuma ação manual externa necessária para este plano específico. O operador deverá, ao chegar no Plan 08-08, adicionar o bind mount `./canaldecortes/youtube:ro` ao serviço `php` do `wordpress/docker-compose.yml` (fora do repo git, mesmo padrão dos Plans 08-01/06-06) para que o badge OAuth funcione com o volume real.

## Next Phase Readiness

- Contrato de comportamento 100% fixado para os Plans 08-04 (auth/user commands), 08-05 (SourceChannelResource), 08-06 (uploader RefreshError — já coberto pelo Plan 08-02), 08-07 (internal API client), 08-08 (DestinationChannelResource) e 08-09 (dashboard widgets).
- `AuthGuardTest` já GREEN — Filament 5 nativo já satisfaz PANEL-05 sem código adicional (Plan 08-04 pode focar em `painel:create-user`/`painel:reset-password` em vez de guard/middleware).
- `DestinationChannelOauthStatusTest` já GREEN — Plan 08-08 não precisa reimplementar o accessor, só o Resource/Form/Table em cima dele.
- Nenhum bloqueio identificado para os próximos plans.

---
*Phase: 08-painel-laravel-filament*
*Completed: 2026-07-01*

## Self-Check: PASSED

All 14 created files verified present on disk (4 Models, 4 Factories, 6 test files). All 3 task commits (`10228ab`, `4494d6c`, `e99e193`) confirmed present in git log.
