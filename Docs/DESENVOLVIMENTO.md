# Desenvolvimento — ambiente, ferramentas de qualidade e fluxo

Como preparar o host, o que cada ferramenta verifica e como reproduzir a validação local.
Atualizado em **26/08/2026**. Decisões por trás disto:
[`ADR/0008-gates-de-qualidade-bloqueantes.md`](ADR/0008-gates-de-qualidade-bloqueantes.md).

---

## 1. Setup do host (uma vez)

```bash
make setup-asdf       # instala os runtimes fixados em .tool-versions (uma vez)
make setup            # = setup-python + setup-panel
make hooks            # instala o pre-commit e os hooks locais
make help             # lista todos os alvos
```

### Runtimes com asdf

O arquivo [`.tool-versions`](../.tool-versions) é a fonte de verdade do ambiente local:
Node.js **22.23.2**, PHP **8.4.4** e Python **3.12.14**. Instale os plugins `nodejs`, `php` e
`python` no asdf e rode `make setup-asdf` antes do primeiro `make setup`.

O PHP 8.4.4 acompanha a imagem de runtime do Compose; o `composer.json` mantém PHP 8.3 como
versão mínima e a CI continua validando essa compatibilidade. PostgreSQL, Redis e FFmpeg são
fornecidos pelo Docker e não precisam ser instalados pelo asdf.

| Alvo | O que faz | Pré-requisito |
|---|---|---|
| `setup-asdf` | instala os runtimes declarados em `.tool-versions` | asdf com os plugins `python`, `nodejs` e `php` |
| `setup-python` | cria `clip-processor/.venv` e instala `requirements-dev.txt` (ruff, mypy, pytest, yamllint + deps de produção) | Python **3.12+** (`python` do asdf ou `PYTHON=...`) |
| `setup-panel` | `composer install` + `npm ci` em `painel/` | PHP 8.3+ com `intl mbstring pdo_pgsql redis bcmath zip`; Node 22 |

Ferramentas que o `make` procura no venv podem ser sobrescritas: `make lint-python RUFF=ruff`,
`make lint-yaml YAMLLINT=yamllint`. `shellcheck` vem do sistema (`brew install shellcheck`);
`hadolint` é opcional (`brew install hadolint`).

**Testes Python no host agora funcionam** — antes só dentro do container porque o host não tinha
`flask` etc. (bug 7). O container continua sendo o caminho canônico para reproduzir produção:
`docker exec clip-processor python -m pytest tests/ -q`.

---

## 2. Comandos do dia a dia

```bash
make lint             # tudo, sem alterar arquivo: tipos + linters + formatadores
make format           # aplica autofix/formatação em tudo (ruff, pint, prettier, oxlint --fix)
make test-python      # pytest do clip-processor (~4 min: há sleeps reais não mockados — TODO-REFATORACAO)
make test-php         # Pest do painel — exige PostgreSQL e Redis, ver §5
make types-python     # mypy bloqueante
make ci               # lint, tipos, testes Python, compose e build frontend
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
| **mypy** | sim | `check_untyped_defs`, `ignore_missing_imports`, `no_implicit_optional`; zero erros |
| **pytest** | sim | `[tool.pytest.ini_options]` (substituiu o `pytest.ini`); a suíte deve estar verde |

`requirements.txt` continua com `pytest`/`pytest-mock` porque a suíte também roda no container.

### painel — PHP

| Ferramenta | Bloqueia? | Configuração |
|---|---|---|
| **Laravel Pint** | sim | `pint.json`, preset `laravel` |
| **PHPStan + Larastan** | sim | `phpstan.neon.dist`, **nível 5**, paths `app bootstrap/app.php config database routes tests` |
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
| `php-tests` | Pest com serviços PostgreSQL 16 + Redis 7; aplica todas as migrations Laravel |
| `frontend` | tsc + oxlint + prettier --check + `vite build` (Node 22) |
| `infra` | shellcheck + hadolint + yamllint + `docker compose config` |

O workflow valida o mesmo contrato do host: o schema é criado por `php artisan migrate`, sem uma
segunda fonte de verdade em SQL de bootstrap.

---

## 5. Testes PHP — cuidado com o banco

`phpunit.xml` aponta para `DB_HOST=postgres` / `clips_automation`, isto é, **o banco do stack local**,
e a suíte usa `DatabaseTransactions`. Consequências:

- `make test-php` executa a suíte dentro do container `php`, onde `postgres`/`redis` são resolvidos
  pela rede interna do Compose.
- cada teste de feature roda dentro de `DatabaseTransactions`; mesmo assim, execute a suíte somente
  contra um banco local/descartável, nunca contra uma instância de produção.
- No CI o banco é descartável, então nada disso importa lá.

---

## 6. Políticas

1. **Formatação e comportamento podem compartilhar o commit** quando fazem parte da mesma entrega;
   o importante é que todos os gates passem e o changelog explique a mudança.
2. **Baseline só encolhe** (PHPStan). Não existe baseline para ruff: `ruff check` precisa passar limpo.
3. **Avisos não bloqueiam** (oxlint `warn`) somente quando já documentados como dívida técnica.
   Ruff, mypy, PHPStan, Pint, TypeScript, Prettier, shellcheck, yamllint, testes e Compose bloqueiam.
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

## 8. Pendências conhecidas (26/08/2026)

- `src/rss_poller.py` mantém `E402` ignorado por arquivo até o item correspondente do TODO.
- PHPStan: baseline histórica de 87 erros no nível 5; a baseline deve apenas diminuir.
- Suíte Python pode levar alguns minutos por `time.sleep` real em retries; substituir por injeção de
  clock/sleeper continua sendo uma melhoria futura.
