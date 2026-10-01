# Desenvolvimento — lint, testes e CI

> Tipo: referência as-built · Atualizado: 2026-09-30
> Índice: [`README.md`](../README.md) · regras de trabalho: [`../CLAUDE.md`](../../CLAUDE.md),
> [`../CONTRIBUTING.md`](../../CONTRIBUTING.md) · decisão: [ADR-0006](../adr/0006-ferramentas-de-qualidade.md)

Tudo roda **no host**, sem `docker compose` do projeto (o compose de `wordpress/` é compartilhado
com outros projetos — não mexa nele). Os alvos ficam no [`Makefile`](../../Makefile); `make help` lista.

## O que cada gate faz hoje

O código legado não segue o estilo das ferramentas, e **não foi reformatado**. Por isso cada
gate só reprova o que o código atual já respeita; a dívida conhecida é informativa ou fica em baseline.

| Área | Ferramenta | Reprova? | Configuração |
|---|---|---|---|
| Python | `ruff check` só com erros reais (`E9`, `F63`, `F7`, `F82`) | sim | `clip-processor/pyproject.toml` |
| Python | `pytest` + piso de cobertura 60 % (medido 66,5 %) | sim | `clip-processor/pytest.ini`, `pyproject.toml` |
| Python | `mypy` | não (23 erros herdados) | `pyproject.toml` |
| affiliate-worker | `pytest` + cobertura 85 % (medido 93 %) | sim | `affiliate-worker/pytest.ini` |
| PHP | Pint **só nos arquivos alterados** (`--diff=master`) | sim | `painel/pint.json` |
| PHP | PHPStan/Larastan nível 5 com baseline | sim | `painel/phpstan.neon.dist`, `phpstan-baseline.neon` |
| PHP | Pest (Postgres + Redis) | sim | `painel/phpunit.xml` |
| Frontend | `oxlint` (erros reprovam; regras herdadas ficam em aviso) | sim | `painel/.oxlintrc.json` |
| Frontend | `tsc --noEmit` | não (27 erros herdados) | `painel/tsconfig.json` |
| Frontend | `vite build` | sim | `painel/package.json` |
| Shell | `shellcheck -S error` | sim | — |
| Docker / YAML | `hadolint`, `yamllint` | sim | `.hadolint.yaml`, `.yamllint.yml` |

Regra da dívida: a baseline do PHPStan, os `ignored` do hadolint e as regras rebaixadas do oxlint
**só encolhem**. Para endurecer uma regra do ruff, limpe os achados e acrescente o prefixo em
`select` no `pyproject.toml`.

## Setup

~~~bash
make setup-python     # cria clip-processor/.venv com requirements-dev.txt (Python 3.12+)
make setup-panel      # composer install + npm ci no painel
make hooks            # opcional: instala o pre-commit
~~~

Requisitos do host: Python 3.12+, PHP 8.3+ com Composer, Node 22, Docker (só para o Postgres de
teste), `shellcheck` e `hadolint` (opcionais: o `make` avisa e segue se faltarem). Versões de
referência em [`../.tool-versions`](../../.tool-versions); PHP não é fixado lá porque a produção usa
`php:8.3` e o `composer.lock` é resolvido para 8.3 (`config.platform.php`).

## Como rodar

~~~bash
make lint             # todos os linters, sem alterar arquivo
make lint-python      # ruff check
make lint-php         # Pint (arquivos alterados vs master) + PHPStan
make lint-js          # oxlint
make types-python     # mypy (informativo)
make types-js         # tsc (informativo)
make test-python      # pytest do clip-processor (~4 min)
make test-php         # Pest contra o Postgres avulso (ver abaixo)
make ci               # lint + pytest + build do painel (o que o CI roda, sem o Pest)
~~~

`make format-python` e `make format-php` corrigem só o que o gate exige (`ruff check --fix` e Pint
nos arquivos alterados); revise o diff. Não rode formatação em massa fora de um lote `style:`.

### Testes PHP (Pest)

Os testes **não** usam `RefreshDatabase`: dependem de um banco já migrado, e vários gravam e apagam
linhas. Rode **somente contra um banco descartável, nunca contra produção**.

~~~bash
scripts/dev-pgvector.sh                      # Postgres 17 + pgvector avulso em 127.0.0.1:5433
cd painel
APP_ENV=testing DB_CONNECTION=pgsql DB_HOST=127.0.0.1 DB_PORT=5433 \
  DB_DATABASE=clips_automation DB_USERNAME=clips_user DB_PASSWORD=clips_local_dev \
  php artisan migrate --force --no-interaction
cd .. && make test-php                       # recusa qualquer TEST_DB_HOST que não seja local
~~~

Detalhes que já morderam: sem `painel/.env` é preciso `APP_KEY` no ambiente (`cp .env.example .env
&& php artisan key:generate`); `APP_ENV=testing` evita que a migration do pgvector aborte como se
fosse produção; os testes de Telegram/estado usam Redis (extensão `phpredis` e um Redis local).
`TELEGRAM_BOT_TOKEN` e `CLIP_PROCESSOR_INTERNAL_TOKEN` de teste vêm do `phpunit.xml`/`make test-php`
(valores falsos).

## CI

[`../.github/workflows/ci.yml`](../../.github/workflows/ci.yml) roda em push na `master` e em PR:

~~~mermaid
flowchart LR
    PR[push / PR] --> py[python: ruff + pytest]
    PR --> aw[affiliate-worker: pytest]
    PR --> ps[php-static: Pint + PHPStan]
    PR --> pt[php-tests: Pest + Postgres 17 + Redis]
    PR --> fe[frontend: oxlint + build]
    PR --> in[infra: shellcheck + hadolint + yamllint]
    py & aw & ps & pt & fe & in --> gate{CI gate}
~~~

- **Só valida.** Não usa segredo e não faz deploy: o deploy continua manual (`./deploy.sh`, ver
  [`../DEPLOY.md`](../../DEPLOY.md) e [`sistema/CI-CD.md`](../planos/CI-CD.md)).
- `CI gate` é o job final; é o único check a exigir na proteção da `master`.
- Os testes PHP no CI usam PHP 8.3 e `pgvector/pgvector:pg17` com credenciais descartáveis.

## Fluxo de mudança

1. leia [`../CLAUDE.md`](../../CLAUDE.md) e o subsistema relevante;
2. branch com prefixo (Gitflow, skill `gitflow`), altere código e teste;
3. rode o gate proporcional (`make lint` + a suíte da área);
4. atualize a documentação no mesmo commit e acrescente um fragmento em
   [`../CHANGELOG.d/`](../../CHANGELOG.d/README.md) quando a mudança for percebida por quem usa;
5. `git diff --check` antes do commit.

Editar `clip-processor/src/` continua exigindo rebuild + restart do serviço (`docker compose build
clip-processor && docker compose up -d clip-processor`, só ele).

## Changelog

Fragmentos por mudança em `CHANGELOG.d/<slug>.<tipo>.md` (`novidade`, `melhoria`, `correcao`,
`tecnico`); não edite `CHANGELOG.md` à mão.

~~~bash
make changelog-preview
make changelog-release VERSION=v0.2.0
~~~

## Restaurar um backup do PostgreSQL

[`scripts/restore-postgres.sh`](../../scripts/restore-postgres.sh) restaura `.sql.gz` ou `.dump`
(`pg_dump -Fc`) no container `postgres`. Sobrescreve dados: exige
`CONFIRM_RESTORE=I_UNDERSTAND`, confere o `.sha256` ao lado do arquivo, e aceita
`POSTGRES_CONTAINER=` se o nome do container for outro. Tire um dump do estado atual antes
(`DEPLOY.md`) e pause o `clip-processor`.

## Referências

- arquitetura: [`../ARCHITECTURE.md`](../../ARCHITECTURE.md)
- operação: [`sistema/RUNBOOK.md`](RUNBOOK.md)
- decisões: [`adr/README.md`](../adr/README.md)
