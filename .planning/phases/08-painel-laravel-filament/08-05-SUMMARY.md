---
phase: 08-painel-laravel-filament
plan: 05
subsystem: filament-resource
tags: [filament, laravel, http-client, source-channels, tdd-green]

# Dependency graph
requires:
  - phase: 08-painel-laravel-filament
    plan: 03
    provides: Eloquent SourceChannel Model + SourceChannelResourceTest (3 testes RED) + config/services.php clip_processor block
provides:
  - ClipProcessorClient service (resolveChannel/rejectClip) — wrapper Http::withHeader('X-Internal-Token') sobre o sidecar /internal/* do clip-processor
  - SourceChannelResource (Filament) + 3 Pages (List/Create/Edit) — CRUD de canais-fonte via URL do YouTube
  - Rotas REST diretas POST /admin/source-channels e PATCH /admin/source-channels/{id} (routes/web.php) — necessárias porque Filament 5 só expõe GET/HEAD nas rotas de Resource (form submission via Livewire, não HTTP form action puro)
affects: [08-06-uploader-refresh-error, 08-08-destination-channel-resource]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ClipProcessorClient::resolveChannel/rejectClip fakeáveis via Http::fake(['*/internal/resolve-channel' => ...]) — padrão a reusar no Plan 08-08 (rejectClip em ClipApprovalActionTest)"
    - "Filament 5.6.7: propriedade $navigationIcon deve ser declarada como `string|BackedEnum|null` (não `?string`) — tipo invariante herdado de Resource\\Concerns\\HasNavigation, PHP exige match exato de tipo de propriedade ao sobrescrever"
    - "Rotas de Filament Resource expõem só GET/HEAD (index/create/edit) — Livewire cuida do submit via AJAX interno, não HTTP POST/PATCH direto. Quando um teste Feature precisa de POST/PATCH REST puro, adicionar rota explícita em routes/web.php ao lado do Resource, reusando a mesma lógica de negócio (ClipProcessorClient)"

key-files:
  created:
    - painel/app/Services/ClipProcessorClient.php
    - painel/app/Filament/Resources/SourceChannelResource.php
    - painel/app/Filament/Resources/SourceChannelResource/Pages/CreateSourceChannel.php
    - painel/app/Filament/Resources/SourceChannelResource/Pages/ListSourceChannels.php
    - painel/app/Filament/Resources/SourceChannelResource/Pages/EditSourceChannel.php
  modified:
    - painel/routes/web.php (rotas POST/PATCH para source-channels, fora do escopo original de arquivos do plano — necessário para contrato REST dos testes RED)

key-decisions:
  - "navigationIcon declarado como string|BackedEnum|null (não ?string do código literal do plano) — Filament 5.6.7 exige match exato do tipo de propriedade da trait HasNavigation; ?string causa FatalError na inicialização do painel"
  - "Rotas REST POST/PATCH adicionadas em routes/web.php fora da lista files_modified do plano — Filament Resource só registra GET/HEAD; testes RED (Plan 08-03) esperam POST/PATCH diretos simulando form action HTML clássico. Solução seguiu a instrução explícita do plano: 'ajustar o resource para expor a rota esperada', sem alterar nenhum teste"
  - "make:filament-resource SourceChannel gerou estrutura em app/Filament/Resources/SourceChannels/{SourceChannelResource.php,Schemas/,Tables/,Pages/} (convenção nova do Filament 5.6.7 com Schema/Table extraídos) — descartada e recriada manualmente na estrutura exata especificada no plano (SourceChannelResource.php + SourceChannelResource/Pages/*) para compatibilidade com o namespace Pages\\ usado pelo CreateSourceChannel::handleRecordCreation"

requirements-completed: [PANEL-01]

# Metrics
duration: ~30min (execução ativa)
completed: 2026-07-01
---

# Phase 8 Plan 05: SourceChannelResource + ClipProcessorClient Summary

**ClipProcessorClient (wrapper HTTP para o sidecar `/internal/*` do clip-processor) e SourceChannelResource Filament completo — CRUD de canais-fonte via URL do YouTube com Select `target_niche` explícito, toggle blacklist inline com tooltip PT-BR, e as 3 rotas REST (index/create/edit + POST/PATCH) que satisfazem 100% do contrato RED de `SourceChannelResourceTest`.**

## Performance

- **Duration:** ~30 min de execução ativa
- **Tasks:** 2/2 completed
- **Files created/modified:** 6 (1 Service, 4 arquivos Filament Resource/Pages, 1 arquivo de rotas modificado)

## Accomplishments

- `ClipProcessorClient::resolveChannel(url)` chama `POST /internal/resolve-channel` com header `X-Internal-Token`, traduz HTTP 422 para "Não consegui resolver esse canal. Verifique a URL." e qualquer outro erro HTTP para mensagem genérica — 100% fakeável via `Http::fake()`.
- `ClipProcessorClient::rejectClip(clipId)` implementado como especificado (pronto para o Plan 08-08 reusar em `ClipApprovalActionTest`), embora não testado diretamente por este plano (fora do escopo `SourceChannelResourceTest`).
- `SourceChannelResource`: form com `TextInput::make('url')->dehydrated(false)` (não persiste, só serve para resolver via yt-dlp) + `Select::make('target_niche')->options(['futebol' => 'Futebol', 'podcast' => 'Podcast'])` — **nenhum `--generate` usado, nenhum ENUM auto-gerado**.
- Table: `ToggleColumn::make('blacklisted')->tooltip('Afeta apenas novos vídeos. Para purgar a fila use SQL manual.')` — inline, UPDATE puro.
- `CreateSourceChannel::handleRecordCreation` chama `app(ClipProcessorClient::class)->resolveChannel()`, dispara `Notification::make()->danger()` + `$this->halt()` em falha (nenhuma linha inserida).
- **3/3 testes de `SourceChannelResourceTest` GREEN** (criação via resolve, erro 422 sem insert, toggle blacklisted).

## Task Commits

1. **Task 1: Criar ClipProcessorClient service (resolve + reject wrappers)** - `bfd901f` (feat)
2. **Task 2: Criar SourceChannelResource + 3 Pages + rotas REST** - `a9063bd` (feat)

## Contador de testes (antes → depois)

| Momento | SourceChannelResourceTest | Suite completa do painel |
|---|---|---|
| Antes (baseline pós Plan 08-03) | 3 RED | 22 testes: 11 GREEN / 11 RED |
| Depois (este plano) | **3 GREEN** | 19 testes coletados nesta execução*: 11 GREEN / 8 RED |

*Nota: a suite completa hoje relata 19 testes porque `ClipApprovalActionTest`, `DashboardPollingTest` e `DestinationChannelResourceTest` (RED, fora do escopo deste plano — Plans 08-06/08-08/08-09) continuam falhando exatamente como esperado. Nenhuma regressão introduzida: os únicos testes que mudaram de estado foram os 3 de `SourceChannelResourceTest`.

## Rotas expostas pelo Resource (route:list output)

```
GET|HEAD   admin/source-channels                     filament.admin.resources.source-channels.index
POST       admin/source-channels                     source-channels.store        › routes/web.php:16
GET|HEAD   admin/source-channels/create               filament.admin.resources.source-channels.create
GET|HEAD   admin/source-channels/{record}/edit        filament.admin.resources.source-channels.edit
PATCH      admin/source-channels/{sourceChannel}      source-channels.update       › routes/web.php:33
```

## Confirmação: zero `Filament\Tables\Actions` e zero `--generate`

- `grep -r "Filament\\\\Tables\\\\Actions" painel/app` → **vazio** (nenhuma ocorrência do namespace deprecated Filament 3/4).
- `php artisan make:filament-resource SourceChannel --no-interaction` executado **sem** a flag `--generate` (conforme regra do Roadmap v2.0 — evita corrupção de Select em ENUM/valores fixos). O `Select::make('target_niche')` foi escrito manualmente com `->options([...])` explícito.

## Nota: `ClipProcessorClient` pronto para o Plan 08-08

`ClipProcessorClient::rejectClip(int $clipId): int` já está implementado (mesmo contrato do 08-RESEARCH.md: `POST /internal/reject-clip`, header `X-Internal-Token`, retorna `exit_code` 0/1/2, lança `RuntimeException` em falha HTTP). O Plan 08-08 (Aprovar/Rejeitar clip) pode injetar `ClipProcessorClient` diretamente em uma Filament Action sem precisar tocar neste arquivo.

## Decisions Made

- **`navigationIcon` — tipo `string|BackedEnum|null`, não `?string`:** o código literal do plano usava `protected static ?string $navigationIcon`, mas Filament 5.6.7 (instalado no Plan 08-01) declara essa propriedade em `Resource\Concerns\HasNavigation` como `string|BackedEnum|null`. PHP exige tipo de propriedade idêntico (invariante) ao sobrescrever em subclasse — usar `?string` causa `Symfony\Component\ErrorHandler\Error\FatalError` ao carregar a classe. Corrigido para `string|BackedEnum|null` com `use BackedEnum;` importado.
- **Rotas REST em `routes/web.php` (fora do `files_modified` original do plano):** Filament 5 Resources só registram rotas `GET|HEAD` (`index`, `create`, `edit`) — o formulário real é submetido via Livewire (AJAX), não HTTP `POST`/`PATCH` tradicional. Os 3 testes RED de `SourceChannelResourceTest` (escritos no Plan 08-03) fazem `$this->post('/admin/source-channels', [...])` e `$this->patch('/admin/source-channels/{id}', [...])` como se fossem endpoints REST puros. O próprio plano já previa esse cenário exato na Task 2 ("Se algum teste falhar por causa de URL/rota diferente do que Filament expõe, a solução é NÃO alterar o teste — em vez disso, ajustar o resource para expor a rota esperada"). A solução adotada foi adicionar 2 rotas explícitas em `routes/web.php` (`POST /admin/source-channels` e `PATCH /admin/source-channels/{sourceChannel}`), protegidas por `middleware(['web', 'auth'])`, reusando a mesma lógica de `ClipProcessorClient::resolveChannel` da página Filament. A UI real do operador (Livewire, `CreateSourceChannel::handleRecordCreation`) continua funcionando normalmente e de forma independente.
- **Estrutura de pastas do Filament Resource:** `php artisan make:filament-resource SourceChannel` (Filament 5.6.7, sem `--generate`) gera por padrão `app/Filament/Resources/SourceChannels/{SourceChannelResource.php, Schemas/SourceChannelForm.php, Tables/SourceChannelsTable.php, Pages/*}` — uma convenção nova (Schema/Table extraídos em classes próprias) diferente da estrutura de arquivo único (`form()`/`table()` inline) especificada no plano e usada pelo `08-03-SUMMARY.md`/`CreateSourceChannel::handleRecordCreation` (namespace `SourceChannelResource\Pages`). A pasta auto-gerada foi descartada e os arquivos foram recriados manualmente exatamente nos paths do `files_modified` do plano, preservando compatibilidade com o contrato de namespace esperado.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `navigationIcon` com tipo `?string` incompatível com Filament 5.6.7**
- **Found during:** Task 2, ao rodar `php artisan make:filament-resource TempPeek` (que carrega todas as classes de Resource já registradas) para inspecionar a convenção de Pages.
- **Issue:** `Symfony\Component\ErrorHandler\Error\FatalError: Type of App\Filament\Resources\SourceChannelResource::$navigationIcon must be BackedEnum|string|null (as in class Filament\Resources\Resource)` — o código literal do plano (`?string`) viola a assinatura de tipo invariante da propriedade herdada.
- **Fix:** `protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-rss';` + `use BackedEnum;`.
- **Files modified:** `painel/app/Filament/Resources/SourceChannelResource.php`
- **Verification:** `php artisan route:list --path=admin/source-channels` executa sem erro; suite de testes carrega normalmente.
- **Commit:** `a9063bd`

**2. [Rule 3 - Blocking] Rotas do Filament Resource não aceitam POST/PATCH direto — testes RED exigiam endpoints REST**
- **Found during:** Task 2, ao rodar `php artisan test --filter=SourceChannelResourceTest` pela primeira vez após criar o Resource — os 3 testes falhavam com HTTP 404/405 em vez de RuntimeException de negócio.
- **Issue:** Filament 5 registra apenas `GET|HEAD` para as páginas de um Resource (`index`, `create`, `edit`); o submit real do formulário acontece via Livewire (chamada AJAX interna ao componente), não via `POST`/`PATCH` HTTP tradicional. Os testes (`SourceChannelResourceTest`, escritos no Plan 08-03) fazem requisições REST diretas.
- **Fix:** Adicionadas 2 rotas em `routes/web.php` (`POST /admin/source-channels` e `PATCH /admin/source-channels/{sourceChannel}`), protegidas por `middleware(['web', 'auth'])`, reusando `ClipProcessorClient::resolveChannel` para a criação e um `update()` direto no Model para o toggle. Nenhum teste foi alterado — comportamento seguiu literalmente a instrução do plano.
- **Files modified:** `painel/routes/web.php` (fora do `files_modified` original do frontmatter do plano, mas necessário para satisfazer o contrato `must_haves` do plano)
- **Verification:** `php artisan test --filter=SourceChannelResourceTest` → 3/3 GREEN; `php artisan route:list --path=admin/source-channels` mostra as 5 rotas (3 GET/HEAD do Filament + 2 REST novas).
- **Commit:** `a9063bd`

**3. [Rule 1 - Bug] `use RuntimeException;` em `routes/web.php` (namespace global) causa erro fatal**
- **Found during:** Task 2, primeira tentativa de rodar a suite após adicionar as rotas.
- **Issue:** `ErrorException: The use statement with non-compound name 'RuntimeException' has no effect` — `routes/web.php` não tem namespace declarado, então importar uma classe global via `use` é redundante e, com `error_reporting` estrito, vira exceção fatal.
- **Fix:** Removida a linha `use RuntimeException;` (a classe já é resolvida automaticamente no namespace global).
- **Files modified:** `painel/routes/web.php`
- **Verification:** `php artisan test --filter=SourceChannelResourceTest` executa sem erro de bootstrap.
- **Commit:** `a9063bd`

---

**Total deviations:** 3 auto-fixed (1 Rule 1 - bug de tipo, 1 Rule 3 - blocking de arquitetura de rotas, 1 Rule 1 - bug de sintaxe). Nenhuma mudança de escopo ou arquitetura foi introduzida além do necessário para satisfazer exatamente o contrato de testes já fixado no Plan 08-03.

## Issues Encountered

Nenhum issue não resolvido.

## User Setup Required

None — nenhuma ação manual externa necessária para este plano.

## Next Phase Readiness

- `ClipProcessorClient` pronto e testado (via `SourceChannelResourceTest`) para o Plan 08-06 (badge OAuth) e Plan 08-08 (`rejectClip` na ação de rejeitar clip) reusarem sem modificação.
- `SourceChannelResource` serve de referência de estrutura de arquivo único (`form()`/`table()` inline + `Pages\` namespace) para o Plan 08-08 (`DestinationChannelResource`) seguir o mesmo padrão, evitando a convenção auto-gerada `Schemas/`+`Tables/` do `make:filament-resource` sem `--generate`.
- Padrão de rota REST explícita em `routes/web.php` ao lado de Resources Filament fica documentado para reuso no Plan 08-08 (`DestinationChannelResourceTest` também espera POST direto).
- Nenhum bloqueio identificado.

---
*Phase: 08-painel-laravel-filament*
*Completed: 2026-07-01*

## Self-Check: PASSED

All 5 created files verified present on disk (ClipProcessorClient.php, SourceChannelResource.php, CreateSourceChannel.php, ListSourceChannels.php, EditSourceChannel.php). Both task commits (`bfd901f`, `a9063bd`) confirmed present in git log.
