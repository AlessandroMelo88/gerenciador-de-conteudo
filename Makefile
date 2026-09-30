# Makefile — atalhos de qualidade do Canal de Cortes.
# Tudo roda no host, sem tocar no docker-compose (que é compartilhado com outros projetos).
# Pré-requisitos e explicação de cada ferramenta: Docs/DESENVOLVIMENTO.md.  `make help` lista os alvos.
SHELL := /bin/bash
.DEFAULT_GOAL := help

PY_DIR    := clip-processor
PANEL_DIR := painel
VENV      ?= .venv
RUFF      ?= $(VENV)/bin/ruff
MYPY      ?= $(VENV)/bin/mypy
PYTEST    ?= $(VENV)/bin/pytest
YAMLLINT  ?= $(PY_DIR)/$(VENV)/bin/yamllint
PYTHON    ?= python3.12
ASDF      ?= asdf
BASE      ?= master

# Banco dos testes PHP: o container avulso de scripts/dev-pgvector.sh (porta 5433).
# NUNCA aponte para produção: o alvo test-php recusa host que não seja local.
TEST_DB_HOST ?= 127.0.0.1
TEST_DB_PORT ?= 5433

.PHONY: help setup setup-asdf setup-python setup-panel hooks \
        lint lint-python lint-php lint-js lint-shell lint-yaml lint-docker \
        format-python format-php \
        test test-python test-php types-python types-js \
        changelog-preview changelog-release ci

help: ## Lista os alvos disponíveis
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------------ setup
setup: setup-python setup-panel ## Instala dependências de dev (venv Python, composer, npm)

setup-asdf: ## Instala as versões fixadas em .tool-versions
	@command -v $(ASDF) >/dev/null 2>&1 || { echo "asdf não encontrado — instale o asdf e os plugins python e nodejs"; exit 1; }
	$(ASDF) install

setup-python: ## Cria clip-processor/.venv com requirements-dev.txt
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else "Python 3.12+ é obrigatório; encontrado " + sys.version.split()[0])'
	cd $(PY_DIR) && $(PYTHON) -m venv $(VENV) && $(VENV)/bin/pip install -q -r requirements-dev.txt

setup-panel: ## composer install + npm ci no painel
	cd $(PANEL_DIR) && composer install --no-interaction --prefer-dist && npm ci

hooks: ## Instala os hooks do pre-commit (incluído no requirements-dev)
	cd $(PY_DIR) && $(VENV)/bin/pre-commit install --install-hooks -c ../.pre-commit-config.yaml

# ------------------------------------------------------------------- lint
# Os linters só reprovam o que o código atual já respeita (baselines em pyproject.toml,
# phpstan-baseline.neon, .oxlintrc.json). O estilo legado NÃO é reformatado em massa.
lint: lint-python lint-php lint-js lint-shell lint-yaml lint-docker ## Todos os linters, sem alterar arquivos

lint-python: ## ruff check (clip-processor)
	cd $(PY_DIR) && $(RUFF) check .

lint-php: ## Pint (só arquivos alterados vs $(BASE)) + PHPStan nível 5 com baseline
	cd $(PANEL_DIR) && vendor/bin/pint --test --diff=$(BASE) && vendor/bin/phpstan analyse --memory-limit=1G --no-progress

lint-js: ## oxlint (painel/resources/js)
	cd $(PANEL_DIR) && npm run lint

lint-shell: ## shellcheck nos scripts bash (só erros; avisos herdados ficam de fora)
	@command -v shellcheck >/dev/null || { echo "shellcheck não instalado — brew install shellcheck"; exit 0; }; \
	shellcheck -S error scripts/*.sh manual-workflow/*.sh

lint-yaml: ## yamllint em compose, CI e configs (roda da raiz; ignora node_modules/vendor)
	$(YAMLLINT) -c .yamllint.yml .

lint-docker: ## hadolint nos Dockerfiles (opcional: brew install hadolint)
	@command -v hadolint >/dev/null || { echo "hadolint não instalado — brew install hadolint"; exit 0; }; \
	hadolint --config .hadolint.yaml Dockerfile.php $(PY_DIR)/Dockerfile embedder/Dockerfile docker/postgres/Dockerfile

# ----------------------------------------------------------------- format
# Só formata arquivos que você está tocando; não rode em massa sem um lote "style" isolado.
format-python: ## ruff check --fix (clip-processor) — confira o diff antes de commitar
	cd $(PY_DIR) && $(RUFF) check --fix .

format-php: ## Pint apenas nos arquivos alterados vs $(BASE)
	cd $(PANEL_DIR) && vendor/bin/pint --diff=$(BASE)

# ------------------------------------------------------------------ types
types-python: ## mypy (informativo: 23 erros herdados)
	cd $(PY_DIR) && $(MYPY)

types-js: ## tsc --noEmit (informativo: 27 erros herdados)
	cd $(PANEL_DIR) && npm run typecheck

# ------------------------------------------------------------------- test
test: test-python test-php ## Suítes Python e PHP

test-python: ## pytest do clip-processor (host, via venv)
	cd $(PY_DIR) && $(PYTEST) -q

test-php: ## Pest do painel no host contra o Postgres avulso (scripts/dev-pgvector.sh)
	@case "$(TEST_DB_HOST)" in 127.0.0.1|localhost) ;; *) \
		echo "recusado: TEST_DB_HOST=$(TEST_DB_HOST) não é local — teste nunca roda contra outro banco"; exit 2;; esac
	cd $(PANEL_DIR) && DB_HOST=$(TEST_DB_HOST) DB_PORT=$(TEST_DB_PORT) \
		CLIP_PROCESSOR_INTERNAL_TOKEN=test-internal-token TELEGRAM_BOT_TOKEN=test-telegram-token \
		php artisan test

# -------------------------------------------------------------- changelog
# Dependem de scripts/changelog.py e de CHANGELOG.d/ (lote de documentação).
changelog-preview: ## Monta a seção [Unreleased] a partir de CHANGELOG.d/
	@test -f scripts/changelog.py || { echo "scripts/changelog.py ausente"; exit 1; }
	$(PYTHON) scripts/changelog.py preview

changelog-release: ## make changelog-release VERSION=v0.2.0 — move fragmentos para o CHANGELOG.md
	@test -n "$(VERSION)" || { echo "uso: make changelog-release VERSION=vX.Y.Z"; exit 2; }
	@test -f scripts/changelog.py || { echo "scripts/changelog.py ausente"; exit 1; }
	$(PYTHON) scripts/changelog.py release $(VERSION)

# --------------------------------------------------------------------- ci
ci: lint test-python ## O que o GitHub Actions roda (sem os testes PHP, que precisam de banco)
	cd $(PANEL_DIR) && npm run build
