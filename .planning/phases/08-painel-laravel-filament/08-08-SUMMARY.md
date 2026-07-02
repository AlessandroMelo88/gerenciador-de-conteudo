---
phase: 08-painel-laravel-filament
plan: 08
subsystem: filament-widgets
tags: [filament, laravel, redis, livewire-polling, dashboard, tdd-green]

# Dependency graph
requires:
  - phase: 08-painel-laravel-filament
    plan: 03
    provides: GeneratedClip/DestinationChannel Models + ClipApprovalActionTest/DashboardPollingTest RED tests
  - phase: 08-painel-laravel-filament
    plan: 05
    provides: ClipProcessorClient::rejectClip (POST /internal/reject-clip wrapper)
  - phase: 08-painel-laravel-filament
    plan: 07
    provides: internal_api.py GREEN (sidecar HTTP real, não mockado)
provides:
  - 4 widgets Filament no dashboard /admin (QuotaTodayWidget, PendingApprovalWidget, RecentUploadsWidget, RecentFailuresWidget), todos com poll('5s')/CanPoll nativo e $isLazy=false
  - POST /admin/clips/{id}/approve (UPDATE guard status=pending) e POST /admin/clips/{id}/reject (ClipProcessorClient::rejectClip + session flash error) em routes/web.php
  - Migration mysql/init/05-controle-manual-migration.sql (já existente no repo desde Phase 6) finalmente aplicada nesta instância MySQL — ENUM generated_clips.status agora inclui approved/rejected
affects: [09-bot-telegram-laravel]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Filament 5 widgets são lazy por padrão (Filament\\Support\\Concerns\\CanBeLazy::$isLazy=true) — renderizam via x-intersect/AJAX após o primeiro paint, então wire:poll/conteúdo NÃO aparece no HTML de uma requisição de teste síncrona. Widgets que precisam estar visíveis/pollable imediatamente (dashboard) devem declarar protected static bool $isLazy = false;"
    - "Filament\\Widgets\\Concerns\\CanPoll já define $pollingInterval='5s' como propriedade de INSTÂNCIA (não static) — nunca redeclarar como 'protected static ?string $pollingInterval' em subclasse (FatalError: Cannot redeclare non static ... as static)"
    - "Filament\\Tables\\Table::applyQueryScopes() exige Illuminate\\Database\\Eloquent\\Builder — um DB::table(...)->unionAll(...) (Query Builder puro) quebra em runtime mesmo passando por ->query(fn () => ...). Widgets de tabela sobre múltiplas fontes sem FK comum devem usar um Eloquent Builder único como base e expor a segunda fonte via ->description() ou uma coluna calculada, não via UNION"
    - "Rotas REST em routes/web.php ao lado de Resources/Widgets Filament — mesmo padrão já estabelecido nos Plans 08-05/08-06: Filament só expõe GET/HEAD (submit real via Livewire), testes RED (Plan 08-03) exigem POST direto"

key-files:
  created:
    - painel/app/Filament/Widgets/QuotaTodayWidget.php
    - painel/app/Filament/Widgets/PendingApprovalWidget.php
    - painel/app/Filament/Widgets/RecentUploadsWidget.php
    - painel/app/Filament/Widgets/RecentFailuresWidget.php
  modified:
    - painel/app/Providers/Filament/AdminPanelProvider.php
    - painel/routes/web.php

key-decisions:
  - "$isLazy=false em todos os 4 widgets — sem essa flag, Filament 5 renderiza apenas um placeholder via x-intersect na resposta inicial do servidor; wire:poll.5s e o conteúdo (Cota, fila, etc.) só aparecem depois de uma chamada AJAX disparada pelo browser, o que quebra tanto o teste (assertSee síncrono) quanto a UX real (operador veria skeleton vazio até o JS rodar)"
  - "RecentFailuresWidget usa GeneratedClip::query()->where('status','failed') como fonte Eloquent única (não UNION ALL de source_videos+generated_clips) — fallback já previsto no PLAN.md porque Filament\\Tables\\Table::applyQueryScopes() rejeita Query\\Builder puro; contagem de source_videos falhados exposta via ->description() no cabeçalho da tabela"
  - "Migration 05-controle-manual-migration.sql (Phase 6, já commitada) aplicada diretamente nesta instância MySQL — o ENUM real de generated_clips.status nunca havia recebido approved/rejected neste ambiente, apesar do arquivo de migration existir no repo desde Phase 6. Mudança de schema apenas, sem novo arquivo criado"
  - "AdminPanelProvider mantém discoverWidgets(Filament/Widgets) e NÃO lista os 4 widgets novos em ->widgets([...]) — discoverWidgets já os registra automaticamente; listar os dois causaria duplicação visual no dashboard"

requirements-completed: [PANEL-03, PANEL-04]

# Metrics
duration: ~55min
completed: 2026-07-02
---

# Phase 8 Plan 08: Dashboard Widgets + Aprovar/Rejeitar Summary

**4 widgets Filament (Cota Redis pipeline, Fila de aprovação com Aprovar/Rejeitar inline, Últimos uploads, Últimas falhas) com polling nativo de 5s, mais as rotas REST `POST /admin/clips/{id}/approve|reject` que fecham o loop UI → banco (Aprovar) e UI → sidecar Python → banco+filesystem (Rejeitar) — resolvendo um FatalError de tipo de propriedade e um bug de lazy-loading do Filament 5 no caminho.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-07-02T05:15:00Z (aprox.)
- **Completed:** 2026-07-02T05:37:24Z
- **Tasks:** 2/2 completed
- **Files created/modified:** 6 (4 widgets criados, `AdminPanelProvider.php` + `routes/web.php` modificados)

## Accomplishments

- `QuotaTodayWidget`: Stats widget lendo `Redis::connection('pipeline')->get("youtube_uploads:{$channel->youtube_channel_id}:{$date}")` com `Carbon::now('America/Sao_Paulo')` — não a conexão Redis default (Pitfall 3/4 do RESEARCH), não `destination_channels.id` interno.
- `PendingApprovalWidget`: `TableWidget` com `->recordActions([...])` (namespace `Filament\Actions\Action`, Filament 5) — Aprovar faz `UPDATE generated_clips SET status='approved' WHERE id=? AND status='pending'` (guard atômico); Rejeitar chama `ClipProcessorClient::rejectClip()` e reage aos exit codes 0/1/2 com `Notification` + `session()->flash('error', ...)`.
- `RecentUploadsWidget`: últimos 10 clips `status='published'` com link `https://youtu.be/{youtube_video_id}` clicável.
- `RecentFailuresWidget`: falhas de `generated_clips` (Eloquent) + contagem de `source_videos` falhados exposta na descrição do cabeçalho — fallback documentado no PLAN.md acionado porque `Filament\Tables\Table::applyQueryScopes()` rejeita `DB::table()->unionAll()` (Query Builder puro, não Eloquent).
- Todos os 4 widgets registrados via `discoverWidgets(in: app_path('Filament/Widgets'))` já presente desde o Plan 08-01 — nenhuma listagem manual duplicada em `->widgets([...])`.
- Rotas `POST /admin/clips/{id}/approve` e `POST /admin/clips/{id}/reject` em `routes/web.php`, protegidas por `middleware(['web', 'auth'])`, reusando exatamente a mesma lógica de negócio das Actions do widget.
- **4/4 `ClipApprovalActionTest` GREEN, 2/2 `DashboardPollingTest` GREEN, suite Laravel completa 25/25 GREEN (0 failed).**

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar 4 widgets Filament (Quota, PendingApproval, RecentUploads, RecentFailures)** - `dfc7289` (feat)
2. **Task 2: Registrar widgets no AdminPanelProvider + rotas REST approve/reject + rodar suite completa** - `11bae4f` (feat)

## Files Created/Modified

- `painel/app/Filament/Widgets/QuotaTodayWidget.php` - Stats widget de cota YouTube por canal-destino (Redis pipeline DB 0)
- `painel/app/Filament/Widgets/PendingApprovalWidget.php` - TableWidget da fila de aprovação com Actions Aprovar/Rejeitar inline
- `painel/app/Filament/Widgets/RecentUploadsWidget.php` - TableWidget dos últimos 10 uploads publicados
- `painel/app/Filament/Widgets/RecentFailuresWidget.php` - TableWidget de falhas (generated_clips + contador de source_videos falhados)
- `painel/app/Providers/Filament/AdminPanelProvider.php` - comentário documentando que `discoverWidgets` já cobre os 4 widgets novos
- `painel/routes/web.php` - rotas `POST /admin/clips/{id}/approve` e `POST /admin/clips/{id}/reject`

## Decisions Made

- `$isLazy = false` em todos os 4 widgets (ver Deviations — necessário para o dashboard mostrar conteúdo/polling imediatamente, tanto para os testes quanto para a UX real do operador).
- `RecentFailuresWidget` usa fallback de fonte única Eloquent (`generated_clips`) + descrição com contador de `source_videos` falhados, em vez do UNION originalmente esboçado no PLAN.md — decisão já prevista como "Plano B" no próprio texto do plano.
- Migration `05-controle-manual-migration.sql` (já existente desde Phase 6) aplicada diretamente no MySQL desta instância — não era um problema de código, era um gap de setup de ambiente que bloqueava literalmente qualquer transição para `status='approved'`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `QuotaTodayWidget::$pollingInterval` redeclarado como `static` causa FatalError**
- **Found during:** Task 1, primeira execução de `DashboardPollingTest` após criar os 4 widgets
- **Issue:** O código literal do PLAN.md declarava `protected static ?string $pollingInterval = '5s';` em `QuotaTodayWidget`, mas `Filament\Widgets\Concerns\CanPoll` (trait usado por `StatsOverviewWidget` nesta versão do Filament 5.6.7) já define `$pollingInterval` como propriedade de **instância** (não static) com default `'5s'`. PHP recusa redeclarar uma propriedade herdada não-static como static em subclasse — `Symfony\Component\ErrorHandler\Error\FatalError: Cannot redeclare non static Filament\Widgets\StatsOverviewWidget::$pollingInterval as static App\Filament\Widgets\QuotaTodayWidget::$pollingInterval`.
- **Fix:** Removida a redeclaração — o widget herda `$pollingInterval='5s'` do trait automaticamente, comportamento idêntico ao pretendido pelo plano.
- **Files modified:** `painel/app/Filament/Widgets/QuotaTodayWidget.php`
- **Verification:** `php -l` limpo; `DashboardPollingTest` deixa de dar FatalError.
- **Committed in:** `dfc7289`

**2. [Rule 1 - Bug] Widgets Filament 5 são `$isLazy=true` por padrão — `wire:poll`/conteúdo não aparecem no HTML inicial**
- **Found during:** Task 1, após corrigir o FatalError acima — `DashboardPollingTest` continuava RED (`assertSee('wire:poll.5s')` e `assertSee('Cota')` falhando) mesmo com os widgets registrados e sem erro de servidor.
- **Issue:** Investigação via dump do HTML renderizado (`response->getContent()`) mostrou que os 4 widgets eram montados como componentes Livewire com `"lazyLoaded":false,"lazyIsolated":true` e um `x-intersect="$wire.__lazyLoad(...)"` — ou seja, apenas um placeholder é enviado na resposta HTTP inicial; o conteúdo real (stats, tabela, atributo `wire:poll`) só é buscado via AJAX quando o elemento entra no viewport do browser (Intersection Observer). Isso é o comportamento padrão de `Filament\Support\Concerns\CanBeLazy::$isLazy = true`, não documentado explicitamente no PLAN.md/RESEARCH.md (achado genuinamente novo desta versão do Filament).
- **Fix:** Adicionado `protected static bool $isLazy = false;` aos 4 widgets — força renderização síncrona completa (stats/tabela/poll attribute) na primeira resposta HTTP, sem esperar JS/AJAX do browser.
- **Files modified:** `painel/app/Filament/Widgets/QuotaTodayWidget.php`, `PendingApprovalWidget.php`, `RecentUploadsWidget.php`, `RecentFailuresWidget.php`
- **Verification:** Dump do HTML pós-fix mostra `wire:poll.5s` 4x (3 TableWidgets com `->poll('5s')` + 1 StatsOverviewWidget herdando `$pollingInterval` do `CanPoll`) e `"Cota"` 2x. `DashboardPollingTest` 2/2 GREEN.
- **Committed in:** `dfc7289`

**3. [Rule 1 - Bug] `RecentFailuresWidget` com UNION via `DB::table()` quebra `Filament\Tables\Table::applyQueryScopes()`**
- **Found during:** Task 1, ao rodar `ZZDebugDashboardTest` (teste temporário de diagnóstico, removido antes do commit) — `local ERROR: Filament\Tables\Table::applyQueryScopes(): Argument #1 ($query) must be of type Illuminate\Database\Eloquent\Builder, Illuminate\Database\Query\Builder given`.
- **Issue:** O código literal do plano usava `DB::table('source_videos')->unionAll(DB::table('generated_clips'))` retornado de `->query(fn () => ...)`. `Illuminate\Database\Query\Builder` (union de query builders puros) não é aceito por `Filament\Tables\Table`, que internamente chama `applyQueryScopes()` esperando um `Eloquent\Builder`. O próprio PLAN.md já previa esse risco ("Se `->query(fn () => ...)` não aceitar builder de union... fallback: exibir só `generated_clips` failed... + Stat separado com contador de `source_videos.failed`").
- **Fix:** `RecentFailuresWidget::table()` reescrito para usar `GeneratedClip::query()->where('status', 'failed')` (Eloquent Builder) como única fonte da tabela, com `->description(fn () => 'Vídeos-fonte com falha: '.SourceVideo::query()->where('status','failed')->count())` no cabeçalho para expor a segunda fonte sem precisar de um 5º widget dedicado.
- **Files modified:** `painel/app/Filament/Widgets/RecentFailuresWidget.php`
- **Verification:** Erro desaparece do log; widget renderiza normalmente; `DashboardPollingTest`/`ClipApprovalActionTest` GREEN sem exceções relacionadas.
- **Committed in:** `dfc7289`

**4. [Rule 3 - Blocking] ENUM `generated_clips.status` sem `approved`/`rejected` nesta instância MySQL**
- **Found during:** Task 2, primeira execução de `ClipApprovalActionTest::it_approves_a_pending_clip` após criar a rota `/admin/clips/{id}/approve` — `SQLSTATE[01000]: Data truncated for column 'status'` ao tentar `UPDATE ... SET status='approved'`.
- **Issue:** `mysql/init/05-controle-manual-migration.sql` (Phase 6, já commitado no repo há várias phases) estende o ENUM de `generated_clips.status` para incluir `approved`/`rejected`, mas esse arquivo nunca havia sido executado contra a instância/volume MySQL usada neste ambiente de desenvolvimento — o ENUM real ainda era `('pending_cut','pending','cutting','publishing','published','failed')`. Isso bloqueava literalmente qualquer transição para `approved`, tanto pela rota REST quanto pela Action do widget.
- **Fix:** `docker exec -i mysql mysql -u clips_user -p${CLIPS_DB_PASSWORD} clips_automation < mysql/init/05-controle-manual-migration.sql` — arquivo já existente e idempotente, apenas aplicado à instância real. Nenhum novo arquivo SQL criado.
- **Files modified:** Nenhum arquivo de código — apenas schema do banco `clips_automation` (mudança de ambiente, documentada em `.planning/phases/08-painel-laravel-filament/deferred-items.md`, mesmo padrão de mudanças out-of-repo já usado em Plans anteriores desta fase).
- **Verification:** `SHOW COLUMNS FROM generated_clips LIKE 'status'` retorna o ENUM completo de 8 valores; `ClipApprovalActionTest` 4/4 GREEN.
- **Committed in:** N/A (mudança de schema de banco, não de arquivo versionado)

---

**Total deviations:** 4 auto-fixed (2 Rule 1 - bugs de compatibilidade com a versão real do Filament 5.6.7, 1 Rule 1 - limitação de query builder documentada como risco pelo próprio plano, 1 Rule 3 - blocking de ambiente/schema pré-existente).
**Impact on plan:** Nenhuma mudança de escopo ou arquitetura. Todos os desvios foram necessários para que o dashboard funcionasse exatamente como especificado (widgets visíveis com polling real, Aprovar/Rejeitar funcionais) contra a versão real do Filament instalada e o schema real do MySQL desta instância. O achado #2 (lazy widgets) é o mais relevante para plans futuros que criem novos widgets Filament neste projeto.

## Issues Encountered

Nenhum issue não resolvido. Ver Deviations acima para os 4 problemas encontrados e corrigidos durante a execução.

## Contador de testes (estado final)

**Laravel (`php artisan test`):** 25 passed, 0 failed (48 assertions).

| Test file | Testes | Resultado |
|---|---|---|
| `Tests\Feature\ClipApprovalActionTest` | 4 | **4 GREEN** (era 4 RED antes deste plano) |
| `Tests\Feature\DashboardPollingTest` | 2 | **2 GREEN** (era 2 RED antes deste plano) |
| `Tests\Feature\AuthGuardTest` | 3 | 3 GREEN (sem regressão) |
| `Tests\Feature\AdminProfilePageTest` | 2 | 2 GREEN (sem regressão) |
| `Tests\Feature\CreatePainelUserCommandTest` | 2 | 2 GREEN (sem regressão) |
| `Tests\Feature\ResetPainelPasswordCommandTest` | 2 | 2 GREEN (sem regressão) |
| `Tests\Feature\SourceChannelResourceTest` | 3 | 3 GREEN (sem regressão) |
| `Tests\Feature\DestinationChannelResourceTest` | 2 | 2 GREEN (sem regressão) |
| `Tests\Unit\DestinationChannelOauthStatusTest` | 3 | 3 GREEN (sem regressão) |
| `Tests\Feature\ExampleTest` / `Tests\Unit\ExampleTest` | 2 | 2 GREEN (bootstrap) |

**Python (`pytest tests/ -q`):** 134 passed, 3 failed. As 3 falhas são pré-existentes e fora de escopo (`tests/test_quota_manager.py::TestCanUpload` — causadas por `UPLOAD_WINDOW_BYPASS=true` em `wordpress/.env`, documentadas desde o Plan 08-02, não relacionadas a nenhum arquivo tocado por este plano). Confirmação completa em `.planning/phases/08-painel-laravel-filament/deferred-items.md`.

## Confirmação `Redis::connection('pipeline')` no Quota widget

```
$ grep -q "connection('pipeline')" painel/app/Filament/Widgets/QuotaTodayWidget.php && echo OK
OK
```

## Confirmação `Filament\Actions\Action` (namespace v5) no PendingApprovalWidget

```
$ grep -q "Filament\\Actions\\Action" painel/app/Filament/Widgets/PendingApprovalWidget.php && echo OK
OK
```

## Descrição conceitual do dashboard renderizado

`GET /admin` (autenticado) mostra, em ordem: **Cota** (Stat cards por canal-destino ativo, formato `N/3`, cor verde/amarelo/vermelho conforme uso), **Fila de aprovação** (tabela full-width com colunas ID/Título/Vídeo-fonte/Destino/Score/Criado e botões Aprovar/Rejeitar por linha, com confirmação modal), **Últimos uploads** (tabela full-width com link direto pro YouTube) e **Últimas falhas** (tabela full-width de `generated_clips` falhados, com contador de `source_videos` falhados na descrição do cabeçalho). Todos os 4 widgets reconsultam o banco/Redis a cada 5 segundos via Livewire polling nativo, sem SSE/WebSockets.

## User Setup Required

None — nenhuma ação manual externa necessária para este plano. A migration `05-controle-manual-migration.sql` aplicada (Deviation #4) já está documentada e o comando de aplicação é idempotente caso precise ser reexecutado em outro ambiente (ex: produção).

## Next Phase Readiness

- PANEL-03 e PANEL-04 100% satisfeitos: dashboard com 4 widgets + polling 5s nativo, Aprovar/Rejeitar funcionais tanto via UI (widget Action) quanto via contrato REST testado.
- `deferred-items.md` atualizado com a confirmação final de que os 6 testes historicamente RED (`ClipApprovalActionTest` + `DashboardPollingTest`, documentados desde o Plan 08-06) estão resolvidos.
- Padrão `$isLazy = false` documentado em `tech-stack.patterns` para qualquer widget futuro (Phase 9 ou expansões deste painel) que precise de conteúdo/polling visível na primeira resposta HTTP.
- Nenhum bloqueio identificado para a Phase 9 (Bot Telegram no Laravel).

---
*Phase: 08-painel-laravel-filament*
*Completed: 2026-07-02*

## Self-Check: PASSED

All 6 created/modified files verified present on disk (4 widgets, `AdminPanelProvider.php`, `routes/web.php`). Both task commits (`dfc7289`, `11bae4f`) confirmed present in git log. `deferred-items.md` update confirmed present on disk.
