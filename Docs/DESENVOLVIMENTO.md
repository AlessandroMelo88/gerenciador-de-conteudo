# Desenvolvimento — ambiente, ferramentas de qualidade e fluxo

Como preparar o host, o que cada ferramenta verifica, o que bloqueia e o que é só informativo.
Atualizado em **25/08/2026**. Decisões por trás disto: [`ADR/0005-ferramentas-de-qualidade.md`](ADR/0005-ferramentas-de-qualidade.md).

---

## 1. Setup do host (uma vez)

```bash
make setup            # = setup-python + setup-panel
make hooks            # pre-commit install (exige `pip install pre-commit`)
make help             # lista todos os alvos
```

| Alvo | O que faz | Pré-requisito |
|---|---|---|
| `setup-python` | cria `clip-processor/.venv` e instala `requirements-dev.txt` (ruff, mypy, pytest, yamllint + deps de produção) | Python **3.12+** no host (`python3` ou `PYTHON=...`) |
| `setup-panel` | `composer install` + `npm ci` em `painel/` | PHP 8.3+ com `intl mbstring pdo_mysql redis bcmath zip`; Node 22 |

Ferramentas que o `make` procura no venv podem ser sobrescritas: `make lint-python RUFF=ruff`,
`make lint-yaml YAMLLINT=yamllint`. `shellcheck` vem do sistema (`brew install shellcheck`);
`hadolint` é opcional (`brew install hadolint`).

**Testes Python no host agora funcionam** — antes só dentro do container porque o host não tinha
`flask` etc. (bug 7). O container continua sendo o caminho canônico para reproduzir produção:
`docker exec clip-processor python -m pytest tests/ -q`.

---

## 2. Comandos do dia a dia

```bash
make lint             # tudo, sem alterar arquivo: python + php + js + shell + yaml
make format           # aplica autofix/formatação em tudo (ruff, pint, prettier, oxlint --fix)
make test-python      # pytest do clip-processor (~4 min: há sleeps reais não mockados — TODO-REFATORACAO)
make test-php         # Pest do painel — exige MySQL e Redis, ver §5
make types-python     # mypy, informativo
make ci               # o mesmo que o GitHub Actions roda, menos os testes PHP
make compose-check    # docker compose config -q
make changelog-preview
```

Cada `lint-*` e `format-*` também existe isolado (`make lint-php`, `make format-js`...).

---

## 3. O que cada ferramenta cobre

### clip-processor (Python) — `clip-processor/pyproject.toml`

| Ferramenta | Bloqueia? | Configuração |
|---|---|---|
| **ruff check** | sim | regras `E W F I B UP C4 SIM RUF`; ignora `E501` (linha longa fica com o formatter), `RUF001-003` (unicode em prompts pt-BR), `SIM105/SIM108` (estilo); `E402` só em `src/rss_poller.py` (código antes dos imports — TODO-REFATORACAO) |
| **ruff format** | sim | aspas simples, 100 colunas, `target-version = py312` |
| **mypy** | **não** (informativo) | `check_untyped_defs`, `ignore_missing_imports`; 12 erros em 6 arquivos em 25/08/2026 |
| **pytest** | sim | `[tool.pytest.ini_options]` (substituiu o `pytest.ini`); 186 testes |

`requirements.txt` continua com `pytest`/`pytest-mock` porque a suíte também roda no container.

### painel — PHP

| Ferramenta | Bloqueia? | Configuração |
|---|---|---|
| **Laravel Pint** | sim | `pint.json`, preset `laravel` |
| **PHPStan + Larastan** | sim | `phpstan.neon.dist`, **nível 5**, paths `app bootstrap/app.php config database routes tests`; `config/database.php` excluído enquanto está em migração |
| **Pest** | sim no CI (`php-tests`) | `phpunit.xml`; ver §5 |

`phpstan-baseline.neon` guarda os **87 erros pré-existentes** (25/08/2026). Regra: a baseline
**só encolhe**. Nunca regenerar para esconder erro novo; ao corrigir código que estava na baseline,
rode `vendor/bin/phpstan analyse --generate-baseline phpstan-baseline.neon` e commite a redução.

### painel — TypeScript/React (`painel/resources/js`)

| Ferramenta | Bloqueia? | Configuração |
|---|---|---|
| **tsc --noEmit** | sim | `tsconfig.json` (strict) — `npm run typecheck` |
| **oxlint** | sim (erros); avisos não | `.oxlintrc.json`: plugins `typescript react jsx-a11y import`; `react-hooks/*`, `import/no-cycle`. Rebaixadas a **aviso** por apontarem dívida já mapeada: `react/set-state-in-effect` (TODO React #9), `react/purity` (#18), `jsx-a11y/role-has-required-aria-props` e `*-interactions` (#17). Desligadas por decisão: `no-autofocus` (login), `media-has-caption` (legenda queimada no clip), `prefer-tag-over-role` (padrões shadcn/radix) |
| **Prettier** | sim | `.prettierrc`: aspas simples, 4 espaços, 120 colunas, plugins `organize-imports` + `tailwindcss` |

Por que **oxlint** e não ESLint: o painel usa `typescript@7`, e `typescript-eslint` exige
`typescript <6.1`. oxlint parseia TS/TSX nativamente, sem essa dependência, e cobre as regras que
importam aqui (hooks, a11y, ciclos de import). Quando `typescript-eslint` suportar TS 7, trocar é
uma mudança de config.

### Infra / repositório

| Ferramenta | Alvo |
|---|---|
| **shellcheck** `-S warning` | `scripts/*.sh`, `manual-workflow/*.sh`, `docker/php/bootstrap-panel` |
| **yamllint** | `.yamllint.yml` — compose, CI, pre-commit |
| **hadolint** | `.hadolint.yaml` — os três Dockerfiles (CI e pre-commit; no host só se instalado) |
| **docker compose config** | valida o compose com o `.env` atual |
| **EditorConfig** | `.editorconfig` na raiz (o de `painel/` refina o Laravel) |

---

## 4. pre-commit e CI

**Local:** `.pre-commit-config.yaml`. No `commit`: hooks genéricos (whitespace, EOF, YAML/JSON/TOML,
chave privada, arquivo > 512 KB), ruff, shellcheck, yamllint, hadolint, pint, prettier e oxlint —
todos só nos arquivos tocados. No `push`: `tsc` e `phpstan` (mais lentos). `pre-commit autoupdate`
atualiza as versões dos hooks.

**GitHub Actions:** `.github/workflows/ci.yml`, em push para `master`/`develop`/`release/**` e em PR.

| Job | Roda |
|---|---|
| `python` | ruff check/format + pytest (Python 3.12) |
| `php-static` | pint --test + phpstan |
| `php-tests` | Pest com serviços MySQL 8.4 + Redis 7; aplica `mysql/init/*.sql` na mesma ordem do entrypoint |
| `frontend` | tsc + oxlint + prettier --check + `vite build` (Node 22) |
| `infra` | shellcheck + hadolint + yamllint + `docker compose config` |

O workflow ainda **não foi executado no GitHub** (criado em 25/08/2026 sem push). A primeira
execução é o teste real dele — em especial `php-tests`, que depende do schema em `mysql/init`.

---

## 5. Testes PHP — cuidado com o banco

`phpunit.xml` aponta para `DB_HOST=mysql` / `clips_automation`, isto é, **o banco de produção do
stack local**, e `RefreshDatabase` está desligado (motivo em `SISTEMA-PAINEL.md`). Consequências:

- `make test-php` só funciona com o stack de pé e o host enxergando `mysql`/`redis` (por padrão o
  compose não publica essas portas — rode dentro do container `php`, ou exporte `DB_HOST`/`REDIS_HOST`).
- `tests/Feature/ExampleTest.php` **grava um usuário real** com senha `password` a cada execução
  (auditoria PHP, item A4 em `TODO-REFATORACAO.md`). Até isso ser corrigido, confira `users` depois de
  rodar a suíte contra o banco real.
- No CI o banco é descartável, então nada disso importa lá.

---

## 6. Políticas

1. **Formatação vem em commit próprio** (`style:`), nunca misturada com mudança de comportamento.
2. **Baseline só encolhe** (PHPStan). Não existe baseline para ruff: `ruff check` precisa passar limpo.
3. **Avisos não bloqueiam** (oxlint `warn`, mypy). Erros bloqueiam.
4. **Formatar ao tocar**: o pre-commit formata os arquivos do commit; não é preciso reformatar o
   repositório inteiro de novo.
5. **Toda mudança relevante tem fragmento em `CHANGELOG.d/`** (ver `CHANGELOG.d/README.md`).

---

## 7. Versionamento e release

Versões `v0.MINOR.PATCH` (semver; `v1.0.0` só em produção madura com muitos usuários). Ainda não
existe tag — a primeira será `v0.1.0`.

Fechar uma versão:

```bash
make changelog-preview                       # confere o que entra
make changelog-release VERSION=v0.2.0        # move CHANGELOG.d/ → CHANGELOG.md
# bump em painel/package.json (e composer.json se quiser); commitar:
git commit -am "chore(release): v0.2.0"
git tag -a v0.2.0 -m "v0.2.0"
```

O `CHANGELOG.md` segue o formato **Release Notes** (`### ✨ Novidades / 🎨 Melhorias / 🐛 Correções /
🔧 Técnico`, itens em checkbox, link de compare no cabeçalho). Detalhes em `CHANGELOG.d/README.md`.

---

## 8. Pendências conhecidas (25/08/2026)

- **13 arquivos do clip-processor** (`requirements.txt`, `src/db.py`, `dedup.py`, `internal_api.py`,
  `main.py`, `pipeline_runner.py`, `processar.py`, `publisher.py`, `queue_controls.py`, `rss_poller.py`,
  `transcriber.py`, `transcription_job.py`, `ttl_worker.py`) estavam em edição por outra frente
  (migração de banco) quando o ruff foi adotado; a formatação deles entra junto com esse trabalho.
  Rode `make format-python` antes de commitar essa frente.
- `src/rss_poller.py` mantém `E402` ignorado por arquivo até o item correspondente do TODO.
- mypy: 12 erros, informativo. Meta: zerar e promover a bloqueante.
- PHPStan: baseline de 87 erros no nível 5. Meta: encolher e subir para nível 6.
- Suíte Python leva ~4 min por `time.sleep` real em retries (TODO-REFATORACAO Python).
