# Makefile — atalhos de qualidade do Canal de Cortes.
# Tudo roda no host. Pré-requisitos e explicação de cada ferramenta:
# Docs/DESENVOLVIMENTO.md.  `make help` lista os alvos.
SHELL := /bin/bash
.DEFAULT_GOAL := help

PY_DIR    := clip-processor
PANEL_DIR := painel
VENV      ?= .venv                      # relativo a clip-processor/
RUFF      ?= $(VENV)/bin/ruff
MYPY      ?= $(VENV)/bin/mypy
PYTEST    ?= $(VENV)/bin/pytest
YAMLLINT  ?= $(PY_DIR)/$(VENV)/bin/yamllint  # relativo à raiz
PYTHON    ?= python3

.PHONY: help setup setup-python setup-panel hooks \
        lint lint-python lint-php lint-js lint-shell lint-yaml lint-docker \
        format format-python format-php format-js \
        test test-python test-php types-python types-js \
        compose-check changelog-preview changelog-release ci

help: ## Lista os alvos disponíveis
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------------ setup
setup: setup-python setup-panel ## Instala dependências de dev (venv Python, composer, npm)

setup-python: ## Cria clip-processor/.venv com requirements-dev.txt
	cd $(PY_DIR) && $(PYTHON) -m venv $(VENV) && $(VENV)/bin/pip install -q -r requirements-dev.txt

setup-panel: ## composer install + npm ci no painel
	cd $(PANEL_DIR) && composer install --no-interaction --prefer-dist && npm ci

hooks: ## Instala os hooks do pre-commit (pip install pre-commit antes)
	pre-commit install --install-hooks

# ------------------------------------------------------------------- lint
lint: lint-python lint-php lint-js lint-shell lint-yaml ## Todos os linters, sem alterar arquivos

lint-python: ## ruff check + ruff format --check (clip-processor)
	cd $(PY_DIR) && $(RUFF) check . && $(RUFF) format --check .

lint-php: ## Pint --test + PHPStan nível 5 com baseline (painel)
	cd $(PANEL_DIR) && vendor/bin/pint --test && vendor/bin/phpstan analyse --memory-limit=1G --no-progress

lint-js: ## oxlint + prettier --check + tsc --noEmit (painel/resources)
	cd $(PANEL_DIR) && npm run lint && npm run format:check && npm run typecheck

lint-shell: ## shellcheck nos scripts bash (severidade warning+)
	shellcheck -S warning scripts/*.sh manual-workflow/*.sh docker/php/bootstrap-panel

lint-yaml: ## yamllint em compose, CI e configs (roda da raiz; ignora node_modules/vendor)
	$(YAMLLINT) -c .yamllint.yml .

lint-docker: ## hadolint nos Dockerfiles (opcional: brew install hadolint)
	@command -v hadolint >/dev/null || { echo "hadolint não instalado — brew install hadolint"; exit 0; }; \
	hadolint $(PY_DIR)/Dockerfile docker/php/Dockerfile docker/nginx/Dockerfile

# ----------------------------------------------------------------- format
format: format-python format-php format-js ## Aplica formatação/autofix em tudo

format-python: ## ruff check --fix + ruff format
	cd $(PY_DIR) && $(RUFF) check --fix . && $(RUFF) format .

format-php: ## Laravel Pint
	cd $(PANEL_DIR) && vendor/bin/pint

format-js: ## prettier --write + oxlint --fix
	cd $(PANEL_DIR) && npm run format && npm run lint:fix

# ------------------------------------------------------------------ types
types-python: ## mypy (informativo: não bloqueia CI ainda)
	cd $(PY_DIR) && $(MYPY)

types-js: ## tsc --noEmit
	cd $(PANEL_DIR) && npm run typecheck

# ------------------------------------------------------------------- test
test: test-python test-php ## Suítes Python e PHP

test-python: ## pytest do clip-processor (host, via venv)
	cd $(PY_DIR) && $(PYTEST) -q

test-php: ## Pest do painel (exige MySQL/Redis acessíveis — ver DESENVOLVIMENTO.md)
	cd $(PANEL_DIR) && php artisan test

# ------------------------------------------------------------------ infra
compose-check: ## Valida docker-compose.yml com o .env atual
	docker compose config -q && echo "compose OK"

# -------------------------------------------------------------- changelog
changelog-preview: ## Monta a seção [Unreleased] a partir de CHANGELOG.d/
	$(PYTHON) scripts/changelog.py preview

changelog-release: ## make changelog-release VERSION=v0.2.0 — move fragmentos para o CHANGELOG.md
	@test -n "$(VERSION)" || { echo "uso: make changelog-release VERSION=vX.Y.Z"; exit 2; }
	$(PYTHON) scripts/changelog.py release $(VERSION)

# --------------------------------------------------------------------- ci
ci: lint test-python ## O que o GitHub Actions roda (sem os testes PHP, que precisam de banco)
