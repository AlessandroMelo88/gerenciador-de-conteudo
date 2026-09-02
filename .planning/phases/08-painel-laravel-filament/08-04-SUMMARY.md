---
phase: 08-painel-laravel-filament
plan: 04
subsystem: auth
tags: [filament, laravel-prompts, artisan, eloquent, pest]

# Dependency graph
requires:
  - phase: 08-painel-laravel-filament
    plan: 01
    provides: Laravel 13 + Filament 5.4 + Pest 4 funcional em painel/, AdminPanelProvider com ->login() base
  - phase: 08-painel-laravel-filament
    plan: 03
    provides: AuthGuardTest.php (3 asserções já GREEN via Filament nativo), migrations users/cache/jobs aplicadas
provides:
  - "php artisan painel:create-user — cria operador via Laravel Prompts (email+senha interativa, bcrypt), rejeita email duplicado"
  - "php artisan painel:reset-password {email} — reseta senha de usuário existente, exit 1 se não encontrado"
  - "AdminPanelProvider::panel() com ->profile() — /admin/profile expõe form nativo Filament (currentPassword/password/passwordConfirmation)"
  - "User implementa Filament\\Models\\Contracts\\FilamentUser::canAccessPanel() — corrige bloqueio de acesso em produção (app.env != local)"
affects: [09-bot-telegram-laravel]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Comandos artisan interativos usam Laravel\\Prompts\\text()/password() com validate closure inline — senha nunca ecoa, testável via ->expectsQuestion() (fallback automático de Prompts em ambiente não-interativo de teste)"
    - "Model que precisa acessar painel Filament DEVE implementar Filament\\Models\\Contracts\\FilamentUser::canAccessPanel() — sem essa interface, Filament\\Http\\Middleware\\Authenticate só libera acesso quando config('app.env')==='local', bloqueando qualquer ambiente de staging/produção mesmo com login válido"

key-files:
  created:
    - painel/app/Console/Commands/CreatePainelUser.php
    - painel/app/Console/Commands/ResetPainelPassword.php
    - painel/tests/Feature/CreatePainelUserCommandTest.php
    - painel/tests/Feature/ResetPainelPasswordCommandTest.php
    - painel/tests/Feature/AdminProfilePageTest.php
  modified:
    - painel/app/Providers/Filament/AdminPanelProvider.php (adicionado ->profile())
    - painel/app/Models/User.php (implements FilamentUser, canAccessPanel() => true)

key-decisions:
  - "canAccessPanel() sempre retorna true (single-user, sem roles/permissões) — qualquer linha em `users` foi criada via painel:create-user pelo próprio operador, não há cadastro público (rota /register inexistente)"
  - "routes/web.php e routes/auth.php NÃO foram tocados — o projeto foi bootstrapado apenas com `filament:install --panels` (Plan 08-01), nunca instalou Laravel Breeze, logo nunca existiu rota /register para desabilitar; PANEL-05 já estava satisfeito nesse ponto antes deste plano"
  - "Testes de comandos artisan interativos usam $this->artisan(...)->expectsQuestion(label, resposta) — Laravel Prompts detecta ambiente de teste (não-TTY) e cai automaticamente no fallback do Symfony Console question helper, compatível com as asserções padrão do Artisan test"

requirements-completed: [PANEL-05]

# Metrics
duration: ~20min
completed: 2026-07-02
---

# Phase 8 Plan 04: Autenticação — Comandos Artisan + Perfil Summary

**2 comandos artisan (`painel:create-user`/`painel:reset-password`) via Laravel Prompts com senha nunca ecoada, `->profile()` habilitado no AdminPanel com form nativo de troca de senha, e correção de um bug real de autorização (`User` sem `FilamentUser::canAccessPanel()` bloquearia o operador em qualquer ambiente que não fosse `local`).**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2/2 completed
- **Files modified/created:** 7 (2 comandos, 3 test files novos, AdminPanelProvider.php, User.php)

## Accomplishments

- `painel:create-user` cria o operador via `text()`/`password()` do Laravel Prompts, valida email (`FILTER_VALIDATE_EMAIL`) e senha (mínimo 10 caracteres), grava `Hash::make()` em `users.password`, e rejeita duplicata sem persistir (exit `FAILURE`).
- `painel:reset-password {email}` localiza usuário existente, pede nova senha interativamente e atualiza `users.password`; retorna exit `FAILURE` (1) se o email não existe.
- Confirmado via `php artisan list` que ambos comandos são auto-descobertos com descrições em português.
- `AdminPanelProvider::panel()` ganhou `->profile()` — rota `/admin/profile` agora existe (`filament.admin.auth.profile`), servindo o `Filament\Auth\Pages\EditProfile` nativo com os campos `currentPassword`, `password`, `passwordConfirmation`.
- **Bug real encontrado e corrigido (Rule 1):** `App\Models\User` não implementava `Filament\Models\Contracts\FilamentUser`. O middleware `Filament\Http\Middleware\Authenticate` só permite acesso a usuários autenticados sem essa interface quando `config('app.env') === 'local'` — em qualquer outro ambiente (staging, produção) o operador logado receberia `403 Forbidden` ao acessar `/admin` ou `/admin/profile`, mesmo com credenciais corretas. Corrigido implementando `canAccessPanel(Panel $panel): bool { return true; }` (single-user, sem roles).
- `/register` confirmado inexistente (`php artisan route:list --path=register` → "nenhuma rota") — o projeto nunca instalou Laravel Breeze (só `filament:install --panels` no Plan 08-01), logo não havia rota a desabilitar.
- 3/3 `AuthGuardTest` + 2/2 `AdminProfilePageTest` (novo) GREEN.

## Task Commits

1. **Task 1a (RED): testes de `painel:create-user`/`painel:reset-password`** - `1ae7a7d` (test)
2. **Task 1b (GREEN): implementar os 2 comandos artisan** - `dabe601` (feat)
3. **Task 2a (RED): teste de `/admin/profile`** - `022ad0f` (test)
4. **Task 2b (GREEN): `->profile()` + `FilamentUser::canAccessPanel()`** - `b1b6727` (feat)

## Configuração final do AdminPanelProvider (trecho relevante)

```php
return $panel
    ->default()
    ->id('admin')
    ->path('admin')
    ->login()
    ->profile()
    ->colors([
        'primary' => Color::Amber,
    ])
    // ... discoverResources/Pages/Widgets inalterados
    ->authMiddleware([
        Authenticate::class,
    ]);
```

Nenhuma referência a `->registration()` em nenhum ponto do arquivo.

## Prova das rotas de registro desabilitadas

```
$ php artisan route:list --path=register
 ERROR  Your application doesn't have any routes matching the given criteria.

$ php artisan route:list --path=admin
  GET|HEAD   admin ................................. filament.admin.pages.dashboard
  GET|HEAD   admin/login ........................... filament.admin.auth.login
  POST       admin/logout .......................... filament.admin.auth.logout
  GET|HEAD   admin/profile ......................... filament.admin.auth.profile
  GET|HEAD   admin/source-channels ................. filament.admin.resources.source-channels.index
  POST       admin/source-channels ................. source-channels.store
  GET|HEAD   admin/source-channels/create .......... filament.admin.resources.source-channels.create
  GET|HEAD   admin/source-channels/{record}/edit ... filament.admin.resources.source-channels.edit
  PATCH      admin/source-channels/{sourceChannel} . source-channels.update
```

## Contador de testes (antes → depois deste plano)

| Métrica | Antes (Plan 08-03/05/07) | Depois (Plan 08-04) |
|---|---|---|
| Total de testes | 19 | 25 |
| GREEN | 11 | 17 |
| RED (fora de escopo — Plans 08-06/08-08/08-09) | 8 | 8 (inalterado) |

**+6 GREEN novos nesta plan:** 2 (`CreatePainelUserCommandTest`) + 2 (`ResetPainelPasswordCommandTest`) + 2 (`AdminProfilePageTest`). `AuthGuardTest` (3/3) já era GREEN antes deste plano (Filament nativo, confirmado no Plan 08-03) e permanece GREEN sem regressão.

Os 8 testes RED remanescentes (`ClipApprovalActionTest` x4, `DashboardPollingTest` x2, `DestinationChannelResourceTest` x2) são estritamente fora do escopo de PANEL-05/deste plano — pertencem aos contratos RED fixados no Plan 08-03 para os Plans 08-06/08-08/08-09, ainda não executados. Nenhum deles foi tocado.

## Files Created/Modified

- `painel/app/Console/Commands/CreatePainelUser.php` - comando `painel:create-user`
- `painel/app/Console/Commands/ResetPainelPassword.php` - comando `painel:reset-password {email}`
- `painel/tests/Feature/CreatePainelUserCommandTest.php` - 2 testes (happy path + duplicata)
- `painel/tests/Feature/ResetPainelPasswordCommandTest.php` - 2 testes (happy path + email inexistente)
- `painel/tests/Feature/AdminProfilePageTest.php` - 2 testes (redirect sem auth + form visível autenticado)
- `painel/app/Providers/Filament/AdminPanelProvider.php` - `->profile()` adicionado
- `painel/app/Models/User.php` - `implements FilamentUser` + `canAccessPanel()`

## Decisions Made

- `canAccessPanel()` retorna sempre `true`: não há roles/permissões nesta fase (single-user, decisão já registrada em CONTEXT.md).
- Nenhuma edição em `routes/web.php`/`routes/auth.php`: o plano previu essa possibilidade caso o projeto usasse Laravel Breeze, mas o bootstrap real (Plan 08-01) usou apenas `filament:install --panels`, que nunca gera rota `/register`. `files_modified` do plano incluía esses 2 arquivos preventivamente; nenhuma mudança foi necessária neles.
- Testes de comandos interativos usam `expectsQuestion()` (fallback nativo de Laravel Prompts em ambiente de teste) em vez de `Prompt::fake()` com key-presses — mais simples e legível para o caso de uso (perguntas sequenciais simples, sem navegação por setas).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `User` sem `FilamentUser::canAccessPanel()` bloquearia acesso ao painel fora de `app.env=local`**
- **Found during:** Task 2, ao rodar o teste RED de `/admin/profile` autenticado — resposta `403` inesperada mesmo com `->profile()` já habilitado e usuário autenticado corretamente.
- **Issue:** `Filament\Http\Middleware\Authenticate::authenticate()` só permite acesso a um usuário autenticado que não implementa `FilamentUser` quando `config('app.env') === 'local'` (código-fonte do próprio middleware, comentado como "Security: ... In production, implement FilamentUser with canAccessPanel()"). Em qualquer ambiente diferente de `local` (staging, produção — que é exatamente onde o operador realmente usará o painel), o acesso seria negado com `403` mesmo com login válido, quebrando PANEL-05 na prática.
- **Fix:** `App\Models\User implements Filament\Models\Contracts\FilamentUser` com `canAccessPanel(Panel $panel): bool { return true; }` — decisão consistente com o modelo single-user já documentado no CONTEXT.md (nenhuma role/permissão a verificar).
- **Files modified:** `painel/app/Models/User.php`
- **Verification:** `AdminProfilePageTest` (2/2 GREEN) + `AuthGuardTest` (3/3 GREEN, sem regressão) + `php artisan test` completo sem novas falhas.
- **Committed in:** `b1b6727` (parte do commit da Task 2)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug de autorização que bloquearia produção)
**Impact on plan:** Correção estritamente necessária para que PANEL-05 funcione fora de ambiente `local` — sem essa mudança, o painel seria inutilizável em produção mesmo após todo o resto da fase estar pronto. Nenhuma mudança arquitetural ou de escopo.

## Issues Encountered

Nenhum issue não resolvido. Os 8 testes RED remanescentes na suite completa (`ClipApprovalActionTest`, `DashboardPollingTest`, `DestinationChannelResourceTest`) são contratos intencionais de plans futuros (08-06/08-08/08-09) e não foram tocados, conforme scope boundary.

## User Setup Required

None — nenhuma configuração externa manual necessária para este plano específico. No setup real do operador (fora do escopo desta execução), rodar uma vez:
```
docker exec -it php bash -c "cd /var/www/html/painel && php artisan painel:create-user"
```
usando o email já documentado em CONTEXT.md (`alessandrobm1988@gmail.com`) e uma senha forte digitada interativamente (nunca gravada em arquivo).

## Next Phase Readiness

- PANEL-05 100% satisfeito: autenticação básica funcional em qualquer ambiente (não só `local`), comandos de criação/reset de senha prontos, página de perfil com troca de senha nativa.
- Nenhum bloqueio identificado para os Plans 08-06 (uploader RefreshError — já coberto pelo Plan 08-02), 08-08 (DestinationChannelResource) e 08-09 (dashboard widgets), que seguem seus próprios contratos RED já fixados no Plan 08-03.
- Bind mount `./canaldecortes/youtube:ro` no serviço `php` (concern já registrado no Plan 08-03) permanece pendente para o Plan 08-08 — não afeta este plano.

---
*Phase: 08-painel-laravel-filament*
*Completed: 2026-07-02*

## Self-Check: PASSED

All 5 created files verified present on disk (`CreatePainelUser.php`, `ResetPainelPassword.php`, `CreatePainelUserCommandTest.php`, `ResetPainelPasswordCommandTest.php`, `AdminProfilePageTest.php`). All 4 task commits (`1ae7a7d`, `dabe601`, `022ad0f`, `b1b6727`) confirmed present in git log. `AdminPanelProvider.php` and `User.php` modifications confirmed via `git diff` and passing tests (`AuthGuardTest` 3/3, `AdminProfilePageTest` 2/2, `CreatePainelUserCommandTest` 2/2, `ResetPainelPasswordCommandTest` 2/2).
