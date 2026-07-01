---
phase: 08-painel-laravel-filament
plan: 01
subsystem: infra
tags: [laravel, filament, pest, docker, nginx, mysql, redis, composer]

# Dependency graph
requires:
  - phase: 07-schema-multi-canal-python-pipeline
    provides: tabelas destination_channels/source_channels/generated_clips/source_videos em clips_automation, Redis DB 0 usado pelo pipeline Python
provides:
  - Projeto Laravel 13 + Filament 5.4 + Pest 4 funcional em canaldecortes/painel/, servido em http://canaldecortes.local via container php/nginx compartilhados
  - Bind mounts no wordpress/docker-compose.yml (painel/ no php, vhost no nginx) sem tocar mounts de outros projetos
  - config/database.php com conexão Redis nomeada 'pipeline' (DB 0) isolada da conexão default (DB 1)
  - config/services.php com bloco clip_processor (url/token) pronto para Plan 08-05/08-07/08-08
  - Imagem wordpress-php reconstruída para PHP 8.3 (pré-requisito de Laravel 13, ausente antes desta execução)
affects: [08-03-eloquent-models, 08-04-auth-user-commands, 08-05-source-channel-resource, 08-07-internal-api-http-client, 08-08-destination-channel-resource, 08-09-dashboard-widgets]

# Tech tracking
tech-stack:
  added: [laravel/framework 13.18.0, filament/filament 5.6.7, pestphp/pest 4.7.4, pestphp/pest-plugin-laravel 4.1.0]
  patterns:
    - "painel/ é um projeto Laravel isolado dentro de canaldecortes/, montado no container php compartilhado via bind mount único — não introduz container novo"
    - "Conexão Redis 'pipeline' (config/database.php) separada da conexão 'default' de session/cache — nunca usar Redis::get() direto para ler chaves do pipeline Python"

key-files:
  created:
    - painel/ (projeto Laravel completo: app/, config/, database/, tests/, public/, etc.)
    - painel/app/Providers/Filament/AdminPanelProvider.php
    - painel/tests/Pest.php
    - painel/README.md
    - docker/nginx/canaldecortes.conf
  modified:
    - painel/config/database.php (conexão redis 'pipeline' adicionada)
    - painel/config/services.php (bloco clip_processor adicionado)
    - painel/.env / painel/.env.example (APP_URL, DB_*, REDIS_*, CLIP_PROCESSOR_INTERNAL_*)
    - wordpress/docker-compose.yml (fora do repo git — 2 linhas de bind mount adicionadas, sem commit)
    - wordpress/Dockerfile (fora do repo git — nenhuma edição de conteúdo; apenas rebuild da imagem para alinhar com FROM php:8.3-fpm já declarado)

key-decisions:
  - "Imagem wordpress-php estava rodando PHP 8.2.29 apesar do Dockerfile já declarar `FROM php:8.3-fpm` com comentário 'alinhada ao Kelnab (composer exige ^8.3)' — rebuild feito via `docker compose build php` + `docker compose up -d --no-deps php nginx` (Rule 3: blocking issue, corrige drift do próprio Dockerfile, não é mudança arquitetural nova)"
  - "`.env.example` do painel recebe os mesmos campos de infra do `.env` real (DB_HOST=mysql, REDIS_HOST=redis, REDIS_DB=1) mas com senha/token sempre vazios — nunca versionar CLIPS_DB_PASSWORD nem CLIP_PROCESSOR_INTERNAL_TOKEN"
  - "wordpress/docker-compose.yml e wordpress/Dockerfile ficam fora do repo git canaldecortes/ (mesmo padrão já registrado na Phase 6) — mudanças aplicadas direto no filesystem, validadas via `docker compose config` e `docker exec php php -v`, sem commit"

patterns-established:
  - "Bootstrap de novo projeto Laravel dentro do container php compartilhado: composer create-project no bind mount + filament:install --panels (padrão default, guard web, path /admin) + pestphp/pest com `vendor/bin/pest --init` (não `artisan pest:install`, que não existe no Pest 4)"

requirements-completed: [PANEL-05]

# Metrics
duration: ~65min (execução ativa; grande parte do tempo foi rebuild de PHP 8.2->8.3 com compilação de extensões a partir do código-fonte, ~6min de build + composer installs do Laravel/Filament/Pest)
completed: 2026-07-01
---

# Phase 8 Plan 01: Bootstrap Laravel/Filament/Pest Summary

**Painel Laravel 13.18.0 + Filament 5.6.7 + Pest 4.7.4 criado em `canaldecortes/painel/`, servido via container `php`/`nginx` compartilhados em `http://canaldecortes.local`, conectado a `clips_automation` (MySQL) e Redis DB 1, com conexão Redis `pipeline` (DB 0) isolada para leitura de cota do pipeline Python.**

## Performance

- **Duration:** ~65 min (dominado por rebuild de imagem PHP 8.2→8.3 com compilação de extensões C — intl, gd, pdo_mysql, mysqli, zip, exif, pcntl, bcmath — e instalação composer do Laravel/Filament/Pest)
- **Tasks:** 2
- **Files modified/created:** 96 (94 novos em `painel/` + `docker/nginx/canaldecortes.conf` + `painel/README.md`; mais 2 linhas em `wordpress/docker-compose.yml`, fora do repo git)

## Accomplishments
- Vhost nginx `canaldecortes.conf` criado seguindo o padrão do `kelnab.conf`, servindo `canaldecortes.local` via `php:9000`
- `wordpress/docker-compose.yml` ganhou exatamente 2 linhas novas (bind mount `painel/` no `php`, bind mount do vhost no `nginx`) — nenhum mount de outro projeto (kelnab, feeb, riodelux, gringo, placebeads) foi tocado
- Imagem `wordpress-php` reconstruída para PHP 8.3.31 (pré-requisito não documentado do Laravel 13 que estava pendente desde antes desta fase)
- Laravel 13.18.0 + Filament 5.6.7 + Pest 4.7.4 instalados e funcionais dentro de `canaldecortes/painel/`
- `.env`/`.env.example` configurados para `clips_automation` (MySQL) e Redis compartilhado (DB 1 para Laravel, DB 0 reservado para o pipeline Python via conexão nomeada `pipeline`)
- `config/services.php` pronto com bloco `clip_processor` para a ponte HTTP interna dos Plans 08-05/08-07/08-08

## Task Commits

1. **Task 1: Adicionar bind mounts no docker-compose.yml raiz e criar vhost nginx** - `59edacc` (feat)
2. **Task 2: Bootstrap Laravel 13 + Filament 5.4 + Pest 4 e configurar .env/database.php/services.php** - `9ca25be` (feat)

_Nota: `wordpress/docker-compose.yml` e `wordpress/Dockerfile` ficam fora do repositório git `canaldecortes/` (mesmo padrão já estabelecido na Phase 6 Plan 06-06) — as mudanças nesses arquivos foram aplicadas diretamente no filesystem e validadas via `docker compose config`, sem commit git._

## Files Created/Modified
- `docker/nginx/canaldecortes.conf` - vhost nginx para `canaldecortes.local`, root `/var/www/html/painel/public`, fastcgi para `php:9000`
- `painel/README.md` - setup local, URL de acesso, instrução de preview de MP4 sem player HTML5
- `painel/` (94 arquivos) - projeto Laravel 13 completo gerado por `composer create-project`, com Filament 5 (`AdminPanelProvider`) e Pest 4 (`tests/Pest.php`) instalados
- `painel/config/database.php` - conexão Redis `pipeline` (DB 0) adicionada, isolada da `default` (DB 1)
- `painel/config/services.php` - bloco `clip_processor` (url/token) adicionado
- `painel/.env` / `painel/.env.example` - `APP_NAME`, `APP_URL`, `DB_*`, `REDIS_*`, `CLIP_PROCESSOR_INTERNAL_*` configurados (senha e token sempre vazios no `.env.example`)
- `wordpress/docker-compose.yml` (fora do repo) - 2 linhas de bind mount adicionadas (serviços `php` e `nginx`)

## Decisions Made
- Imagem `wordpress-php` precisou de rebuild para PHP 8.3 antes de instalar Laravel 13 (composer bloqueia platform requirement em PHP 8.2.29) — o próprio `Dockerfile` já declarava `FROM php:8.3-fpm` com um comentário explicando a necessidade por causa do Kelnab, mas a imagem em uso ainda não tinha sido reconstruída. Tratado como Rule 3 (blocking issue) por já ser a intenção documentada do próprio arquivo, não uma mudança arquitetural nova.
- `.env.example` recebeu os mesmos valores de infraestrutura do `.env` real (host/porta/banco) mas manteve senha e token vazios, seguindo a regra "nunca gravar senha nem token em arquivo versionado" do CONTEXT.md.
- `php artisan pest:install` não existe no Pest 4 (o plano original citava esse comando); usado `./vendor/bin/pest --init` no lugar, que produz o mesmo resultado (`tests/Pest.php` criado).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Imagem PHP desatualizada (8.2.29) impedia instalação de Laravel 13 (exige PHP >=8.3)**
- **Found during:** Task 2, antes de rodar `composer create-project laravel/laravel . '^13.0'`
- **Issue:** O container `php` compartilhado rodava PHP 8.2.29, mas `wordpress/Dockerfile` já declarava `FROM php:8.3-fpm` (comentário: "alinhada ao Kelnab (composer exige ^8.3)") — a imagem em uso estava desatualizada em relação ao próprio Dockerfile, provavelmente por falta de rebuild após uma mudança anterior não relacionada a este plano.
- **Fix:** `docker compose build php` (rebuild completo, ~6min, recompilando intl/gd/pdo_mysql/mysqli/zip/exif/pcntl/bcmath/redis/xdebug para PHP 8.3) seguido de `docker compose up -d --no-deps php nginx` para recriar os containers com a nova imagem, preservando os demais serviços (mysql, redis, clip-processor, etc.) intocados.
- **Files modified:** Nenhum arquivo de conteúdo alterado (Dockerfile já estava correto); apenas rebuild de imagem Docker.
- **Verification:** `docker exec php php -v` → `PHP 8.3.31`; `kelnab` e `feeb` continuam montados e acessíveis (`docker exec php ls /var/www/html/kelnab`); `nginx -t` válido; `docker compose config` válido.
- **Committed in:** N/A (mudança de infraestrutura Docker, não de arquivo versionado)

**2. [Rule 1 - Bug] Comando `php artisan pest:install` do plano não existe no Pest 4**
- **Found during:** Task 2, etapa de instalação do Pest
- **Issue:** O plano especificava `php artisan pest:install --no-interaction`, mas essa Artisan command não é registrada pelo pacote `pestphp/pest` na versão instalada (4.7.4) — o comando correto é `./vendor/bin/pest --init`.
- **Fix:** Executado `docker exec php bash -c "cd /var/www/html/painel && ./vendor/bin/pest --init"`, que criou `tests/Pest.php` com sucesso (mesmo resultado esperado pelo plano).
- **Files modified:** `painel/tests/Pest.php` (criado)
- **Verification:** `php artisan test` executa e reporta 2 testes passando (Unit + Feature `ExampleTest`)
- **Committed in:** `9ca25be` (parte do commit da Task 2)

**3. [Rule 1 - Bug] `php artisan test --no-interaction` não é uma flag válida**
- **Found during:** Task 2, verificação final
- **Issue:** O plano pedia `php artisan test --no-interaction`, mas essa flag não existe para o comando `test` (que delega ao runner do Pest) — falha com "Unknown option".
- **Fix:** Executado `php artisan test` sem a flag (comportamento não-interativo já é o padrão ao rodar via `docker exec` sem TTY).
- **Files modified:** Nenhum
- **Verification:** `php artisan test` → `Tests: 2 passed (2 assertions)`
- **Committed in:** N/A (apenas comando de verificação, não gerou mudança de arquivo)

---

**Total deviations:** 3 auto-fixed (1 blocking de infraestrutura, 2 bugs de comando incorreto no plano)
**Impact on plan:** Nenhum desvio de escopo — todos os ajustes foram necessários para completar exatamente o que o plano pedia (Laravel 13 + Filament 5.4 + Pest 4 funcionais). Nenhuma feature nova ou mudança arquitetural foi introduzida.

## Issues Encountered
- Durante o rebuild da imagem PHP, dois processos `docker compose build php` concorrentes (lançados em background por mim, por precaução, antes de confirmar que o primeiro já estava rodando) competiram por CPU com um processo externo de teste (`pytest` no `clip-processor`, ~400% CPU, aparentemente iniciado por atividade concorrente no host fora desta sessão). Isso tornou o rebuild significativamente mais lento do que o esperado, mas ambos os builds concluíram com sucesso e produziram a mesma imagem final íntegra (`PHP 8.3.31` com `redis`, `xdebug`, `php.ini` customizado, `crontab` e `entrypoint` corretos).

## User Setup Required

None - nenhuma configuração externa manual necessária para este plano. O operador ainda precisará, no setup real:
- Preencher `painel/.env` com o `CLIPS_DB_PASSWORD` real (hoje vazio no arquivo, propositalmente) e com `CLIP_PROCESSOR_INTERNAL_TOKEN` quando o Plan 08-07 definir o valor
- Adicionar `127.0.0.1 canaldecortes.local` ao `/etc/hosts` local (documentado em `painel/README.md`)

## Next Phase Readiness
- Base Laravel/Filament/Pest pronta — Plans 08-03 (Eloquent Models sobre tabelas existentes), 08-04 (auth/user commands), 08-05/08-08 (Resources) e 08-09 (widgets) podem ser executados.
- `config/services.php` já expõe `clip_processor.url`/`token`, então o Plan 08-07 (cliente HTTP) não precisa criar essa config do zero.
- Nenhum bloqueio identificado. O Plan 08-02 (Python-side: migration `oauth_expired_flag`, skeleton `internal_api.py`) já havia sido executado anteriormente e é independente deste plano (`depends_on: []` em ambos).

---
*Phase: 08-painel-laravel-filament*
*Completed: 2026-07-01*

## Self-Check: PASSED

All created files verified present on disk (`docker/nginx/canaldecortes.conf`, `painel/README.md`, `painel/artisan`, `painel/tests/Pest.php`, `painel/config/database.php`, `painel/config/services.php`, `painel/app/Providers/Filament/AdminPanelProvider.php`, this SUMMARY.md). Both task commits (`59edacc`, `9ca25be`) confirmed present in git log.
