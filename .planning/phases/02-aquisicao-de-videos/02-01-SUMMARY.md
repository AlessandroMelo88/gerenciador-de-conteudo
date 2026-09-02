---
phase: 02-aquisicao-de-videos
plan: "01"
subsystem: testing
tags: [pytest, pytest-mock, tdd, redis, pymysql, yt-dlp, rss, deduplication]

# Dependency graph
requires:
  - phase: 01-infraestrutura-base
    provides: schema MySQL com source_videos/source_channels, clip-processor container stub

provides:
  - pytest.ini configurado com testpaths=tests
  - tests/__init__.py tornando diretório pacote Python
  - conftest.py com 4 fixtures: mock_redis, mock_db_conn, sample_rss_xml, sample_video_id
  - test_rss_poller.py: 3 testes ACQU-01 em RED state
  - test_downloader.py: 5 testes ACQU-02 em RED state
  - test_dedup.py: 5 testes ACQU-03 em RED state
  - test_db.py: 4 testes ORC-02 em RED state

affects:
  - 02-02-PLAN (implementação src/rss_poller.py, src/dedup.py — testes definidos aqui)
  - 02-03-PLAN (implementação src/downloader.py — testes definidos aqui)
  - 02-04-PLAN (implementação src/db.py — testes definidos aqui)

# Tech tracking
tech-stack:
  added:
    - pytest 9.1.0
    - pytest-mock 3.15.1
    - redis (python client, adicionado ao requirements.txt)
    - feedparser (adicionado ao requirements.txt)
    - apscheduler (adicionado ao requirements.txt)
  patterns:
    - "TDD RED-GREEN-REFACTOR: testes criados antes da implementação com imports diretos que causam ModuleNotFoundError"
    - "Fixtures pytest em conftest.py compartilhadas por todos os módulos de teste"
    - "Mock de context managers pymysql via __enter__/__exit__ no MagicMock"
    - "Permanent vs transient errors no downloader: keywords 'private', 'deleted', 'unavailable' → 1 tentativa; outros → 3 tentativas"

key-files:
  created:
    - clip-processor/pytest.ini
    - clip-processor/tests/__init__.py
    - clip-processor/tests/conftest.py
    - clip-processor/tests/test_rss_poller.py
    - clip-processor/tests/test_downloader.py
    - clip-processor/tests/test_dedup.py
    - clip-processor/tests/test_db.py
  modified:
    - clip-processor/requirements.txt (adicionado pytest, pytest-mock, redis, feedparser, apscheduler)

key-decisions:
  - "Imports de src.* no topo dos arquivos de teste (não dentro das funções) — coleta falha com ModuleNotFoundError = RED state correto e mais simples"
  - "test_dedup.py inclui test_redis_fallback_mysql_miss como teste adicional além do especificado — garante cobertura completa do caminho redis-falhou+mysql-falhou"
  - "requirements.txt atualizado com redis, feedparser, apscheduler antecipando necessidades dos Planos 02-04"

patterns-established:
  - "Fixture mock_db_conn: cursor como context manager com __enter__/__exit__ — padrão para todos os testes de DB"
  - "Fixture mock_redis: set() retorna True (NX sucesso) por padrão — testes que precisam de 'hit' sobreescrevem com return_value=None"
  - "sample_rss_xml: feed Atom completo com namespace yt: — reutilizável por qualquer teste que precise de XML RSS YouTube"

requirements-completed:
  - ACQU-01
  - ACQU-02
  - ACQU-03
  - ORC-02

# Metrics
duration: 3min
completed: 2026-06-18
---

# Phase 2 Plan 01: Infraestrutura de Testes pytest (Wave 0) Summary

**pytest scaffold com 17 testes em RED state cobrindo ACQU-01/02/03 e ORC-02 — define contratos de comportamento antes da implementação via TDD**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-18T14:18:33Z
- **Completed:** 2026-06-18T14:20:51Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- pytest.ini configurado e diretório tests/ transformado em pacote Python
- conftest.py com 4 fixtures reutilizáveis (mock_redis, mock_db_conn, sample_rss_xml, sample_video_id)
- 17 testes distribuídos em 4 arquivos cobrindo todos os requirements da Phase 2 — todos em RED state (ModuleNotFoundError esperado)

## Task Commits

1. **Task 1: pytest.ini e pacote de testes** — `3b6792a` (chore)
2. **Task 2: conftest.py com fixtures compartilhadas** — `31d236b` (test)
3. **Task 3: Scaffolds de testes failing (RED state)** — `e94cc0e` (test)

## Files Created/Modified

- `clip-processor/pytest.ini` — configuração pytest com testpaths=tests, addopts=-v --tb=short
- `clip-processor/tests/__init__.py` — torna tests/ um pacote Python
- `clip-processor/tests/conftest.py` — 4 fixtures compartilhadas para todos os testes
- `clip-processor/tests/test_rss_poller.py` — 3 testes ACQU-01 (poll, skip, empty feed)
- `clip-processor/tests/test_downloader.py` — 5 testes ACQU-02 (success, disk guard, cleanup, permanent, retry)
- `clip-processor/tests/test_dedup.py` — 5 testes ACQU-03 (redis hit, miss, fallback, mark failed)
- `clip-processor/tests/test_db.py` — 4 testes ORC-02 (update_status, update_with_path, recover_stuck, insert_video)
- `clip-processor/requirements.txt` — adicionado pytest, pytest-mock, redis, feedparser, apscheduler

## Decisions Made

- Imports de `src.*` no topo dos arquivos de teste — coleta pytest falha com ModuleNotFoundError, que é o RED state correto e mais limpo que try/except ou xfail
- test_dedup.py inclui `test_redis_fallback_mysql_miss` (não estava explicitamente no plano) como cobertura adicional do caminho redis-falhou+mysql-também-falhou
- requirements.txt atualizado antecipando dependências dos Planos 02-04

## Deviations from Plan

**1. [Rule 2 - Missing Critical] test_redis_fallback_mysql_miss adicionado em test_dedup.py**
- **Found during:** Task 3 (scaffolds de testes)
- **Issue:** O plano especificava `test_redis_fallback` (redis cai, MySQL encontra) mas não cobria o caso redis cai + MySQL também não encontra
- **Fix:** Adicionado `test_redis_fallback_mysql_miss` — cobertura completa do fallback path
- **Files modified:** clip-processor/tests/test_dedup.py
- **Verification:** Arquivo criado com 5 testes em dedup (plan especificava 4)
- **Committed in:** e94cc0e

---

**Total deviations:** 1 auto-adição (Rule 2 — cobertura de caso de teste crítico faltando)
**Impact on plan:** Sem impacto negativo — teste adicional, sem mudança de interface ou arquitetura.

## Issues Encountered

- pip3 no macOS bloqueado por PEP 668 — resolvido com `--break-system-packages` para instalação local de pytest/pytest-mock para verificação
- python3 não disponível como `python` no PATH — todos os comandos usam `python3` explicitamente

## User Setup Required

Nenhum — infraestrutura de testes é código puro, sem serviços externos.

## Next Phase Readiness

- Testes em RED state prontos para Plano 02-02 implementar src/rss_poller.py e src/dedup.py
- Testes em RED state prontos para Plano 02-03 implementar src/downloader.py
- Testes em RED state prontos para Plano 02-04 implementar src/db.py
- Executar `pytest clip-processor/tests/ -x -q` dentro do container após cada plano de implementação para validar GREEN state

---
*Phase: 02-aquisicao-de-videos*
*Completed: 2026-06-18*
