# Desenvolvimento

> Tipo: referência as-built · Atualizado: 2026-08-26
> Índice: [`README.md`](README.md) · regras: [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

## Toolchain

Versões fixadas em [`../.tool-versions`](../.tool-versions):

| Runtime | Versão |
|---|---:|
| Python | 3.12.14 |
| Node.js | 22.23.2 |
| PHP | 8.4.4 |

O projeto exige PHP 8.3+ no `composer.json`. PostgreSQL, Redis e FFmpeg são fornecidos
pelo Docker.

## Setup

~~~bash
make setup-asdf
make setup
make hooks
make help
~~~

- `setup-asdf`: instala runtimes com asdf;
- `setup-python`: cria `clip-processor/.venv` e instala dependências;
- `setup-panel`: executa `composer install` e `npm ci`;
- `hooks`: instala pre-commit.

Requisitos do host: asdf com plugins Python/Node/PHP, Composer, Docker, shellcheck e
`python` 3.12+. `hadolint` é opcional no host.

## Comandos

~~~bash
make lint
make format
make test-python
make test-php
make test
make types-python
make compose-check
make ci
~~~

`make format` altera arquivos; revise o diff. `make lint` é somente leitura.
`make ci` reúne lint Python/tipos, testes Python, validação Compose, lint de infraestrutura
e build frontend; testes PHP são executados separadamente.

## Gates

| Área | Ferramentas | Configuração |
|---|---|---|
| Python | Ruff check/format, mypy, pytest + piso de cobertura (68%), affiliate-worker (85%) | `clip-processor/pyproject.toml`, `affiliate-worker/pytest.ini` |
| PHP | Pint, PHPStan/Larastan, Pest | `painel/pint.json`, `phpstan.neon.dist` |
| Frontend | TypeScript, oxlint, Prettier, Vitest (jsdom), Vite | `painel/package.json`, `painel/vitest.config.ts` |
| E2E | Playwright (Chromium desktop + mobile), lento | `painel/playwright.config.ts`, `painel/e2e/` |
| Shell/YAML/Docker | shellcheck, yamllint, hadolint, Compose config | arquivos de config da raiz |

O PHPStan usa baseline existente; a regra é reduzir a baseline, nunca atualizá-la para esconder erro
novo. Avisos do oxlint que representam dívida já conhecida permanecem documentados no próprio config
e no TODO.

## CI

O workflow está em `.github/workflows/ci.yml` e roda em push/PR conforme sua configuração.
Ele valida:

- Python 3.12: Ruff + mypy + pytest com piso de cobertura;
- affiliate-worker: pytest com piso de cobertura;
- PHP: Pint + PHPStan;
- PHP integrado: Pest com PostgreSQL/Redis descartáveis;
- frontend: typecheck, oxlint, Prettier, Vitest com cobertura e Vite build;
- e2e: Playwright contra o painel real (PostgreSQL descartável, `E2ESeeder`); relatório/vídeo/trace
  sobem como artefato se falhar;
- infraestrutura: shellcheck, hadolint, yamllint e `docker compose config`;
- **`CI gate`**: job final que só passa se todos os anteriores passaram. É o único check a exigir na
  branch protection da `master` (Settings → Branches → *Require status checks* → `CI gate`).

No commit, o `pre-commit` roda pytest (clip-processor e affiliate-worker) e Vitest além dos linters;
no push, tsc, mypy e PHPStan. Instalar: `make hooks`.

## Testes

Python:

~~~bash
cd clip-processor
.venv/bin/pytest -q
~~~

PHP:

~~~bash
make test-php
~~~

Frontend (Vitest) e E2E (Playwright, lento, ~120 testes — login, 12 telas, fila de aprovação
(aprovar/rejeitar/lote/reprocessar), vídeos e fila do processor, canais fonte/destino, ofertas do
rascunho ao redirect rastreável, configurações, processar vídeo, transcrições, acesso anônimo e
viewport mobile). O clip-processor é substituído por `e2e/support/mock-processor.mjs`, que grava as
chamadas `/internal/*` para os testes conferirem; o painel é o real:

~~~bash
cd painel
npm test                  # unitários
npm run e2e:install       # uma vez: baixa o Chromium
# banco descartável migrado + seed fixo, depois:
php artisan db:seed --class=E2ESeeder   # recusa rodar em produção
npm run build && npm run e2e            # sobe `php -S` sozinho na :8099
E2E_BASE_URL=http://host:porta npm run e2e   # ou aponta para um servidor já de pé
~~~

Os testes consomem a massa do seeder (aprovam, rejeitam e apagam clips): **rode o `E2ESeeder` antes de
cada execução local** para voltar ao cenário inicial. No CI o banco já nasce limpo.

O painel usa PostgreSQL e as migrations do projeto. Rode testes somente contra banco local/
descartável. A fila Laravel padrão é `database` e não deve apontar para produção.

## Fluxo de mudança

1. leia [`../CLAUDE.md`](../CLAUDE.md) e o subsistema relevante;
2. altere código e teste;
3. rode o gate proporcional;
4. atualize [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md) se estados mudarem;
5. atualize documentação e crie fragmento em `../CHANGELOG.d/` quando relevante;
6. revise `git diff --check` e o status antes do commit.

O Compose atual monta `clip-processor/src` no sidecar e em cada worker: depois de alterar Python,
recrie `clip-processor` e os seis serviços `clip-*` do pipeline. Rebuild fica para mudanças no
Dockerfile, dependências ou pacotes do sistema.

## Versionamento

O formato é `v0.MINOR.PATCH`. O changelog é composto por fragmentos:

~~~bash
make changelog-preview
make changelog-release VERSION=v0.2.0
~~~

Não edite `CHANGELOG.md` manualmente antes do release. Tipos de fragmento:
`novidade`, `melhoria`, `correcao` e `tecnico`.

## Referências

- arquitetura: [`../ARCHITECTURE.md`](../ARCHITECTURE.md);
- operação: [`RUNBOOK.md`](RUNBOOK.md);
- contribuições: [`../CONTRIBUTING.md`](../CONTRIBUTING.md);
- decisões: [`ADR/README.md`](ADR/README.md);
- auditoria histórica: [`TODO-REFATORACAO.md`](TODO-REFATORACAO.md).
