---
phase: 02-aquisicao-de-videos
plan: "02"
subsystem: database
tags: [pymysql, mysql, docker, redis, python, pytest, tdd]

# Dependency graph
requires:
  - phase: 01-infraestrutura-base
    provides: MySQL schema clips_automation, docker-compose.yml base, clip-processor Dockerfile
  - phase: 02-aquisicao-de-videos plan 01
    provides: pytest.ini, conftest.py, test_db.py (RED state)

provides:
  - docker-compose clip-processor com volume ./canaldecortes/videos:/app/videos e vars Redis
  - requirements.txt completo com apscheduler, feedparser, redis, pytest, pytest-mock
  - 02-seed-channels.sql com 5 canais de futebol PT-BR reais (INSERT IGNORE idempotente)
  - db.py com 4 funções: get_db_connection, update_status, insert_video, recover_stuck_downloads
  - test_db.py passando 4/4 (GREEN)

affects:
  - 02-03 (rss_poller usa insert_video de db.py)
  - 02-04 (downloader usa update_status e get_db_connection de db.py)
  - 03-transcricao (usa get_db_connection e update_status para gerenciar estado)

# Tech tracking
tech-stack:
  added: [pymysql, apscheduler, feedparser, redis-py, pytest, pytest-mock]
  patterns:
    - "with conn.cursor() as cur: — context manager para cursor pymysql"
    - "INSERT IGNORE para idempotência em inserts de vídeos e canais"
    - "Quem chama é responsável por fechar a conexão (não fechar dentro das funções)"
    - "Logging via print com timestamp [YYYY-MM-DD HH:MM:SS] [MODULE] — sem biblioteca logging"

key-files:
  created:
    - clip-processor/src/db.py
    - mysql/init/02-seed-channels.sql
    - videos/.gitkeep
  modified:
    - clip-processor/requirements.txt (já atualizado em 02-01; sem diff neste plano)
    - docker-compose.yml (fora do git repo — parent dir /develop/server/wordpress/)

key-decisions:
  - "db.py: quem chama é responsável por fechar a conexão — padrão de uso do daemon"
  - "INSERT IGNORE em insert_video para idempotência — RSS pode re-publicar o mesmo item"
  - "recover_stuck_downloads captura apenas OperationalError para robustez, outros erros propagam"
  - "Seed inclui 5 canais reais PT-BR: SporTV, ge.globo, ESPN Brasil, Canal do Nicola, TNT Sports Brasil"

patterns-established:
  - "TDD: test_db.py commitado em 02-01 (RED), db.py commitado neste plano (GREEN)"
  - "Seed SQL: INSERT IGNORE + USE clips_automation para idempotência"

requirements-completed: [ORC-02, ACQU-01]

# Metrics
duration: 15min
completed: 2026-06-18
---

# Phase 2 Plan 02: Infraestrutura de Suporte do Daemon Summary

**pymysql db.py com 4 funções (get_db_connection, update_status, insert_video, recover_stuck_downloads) implementado e testado (4/4 GREEN), docker-compose com volume canaldecortes/videos e Redis vars, seed SQL com 5 canais PT-BR reais**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-06-18T14:18:45Z
- **Completed:** 2026-06-18T14:35:00Z
- **Tasks:** 3
- **Files modified:** 4 (db.py, 02-seed-channels.sql, videos/.gitkeep, docker-compose.yml fora do git)

## Accomplishments
- docker-compose.yml atualizado: volume /tmp/clips substituído por ./canaldecortes/videos:/app/videos, REDIS_HOST=redis, REDIS_PORT=6379 e redis em depends_on
- 5 canais de futebol PT-BR reais inseridos via 02-seed-channels.sql com INSERT IGNORE idempotente
- db.py implementado com 4 funções exportadas, padrão `with conn.cursor() as cur:`, commit explícito em cada função
- pytest clip-processor/tests/test_db.py: 4/4 passed GREEN

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: docker-compose e requirements.txt** - `66e54c1` (feat)
2. **Task 2: Seed SQL de canais de futebol** - `73ab8b8` (feat)
3. **Task 3: db.py — módulo de acesso ao MySQL (TDD GREEN)** - `9a01858` (feat)

## Files Created/Modified
- `clip-processor/src/db.py` — módulo pymysql com get_db_connection, update_status, insert_video, recover_stuck_downloads
- `mysql/init/02-seed-channels.sql` — seed idempotente com 5 canais PT-BR: SporTV, ge.globo, ESPN Brasil, Canal do Nicola, TNT Sports Brasil
- `videos/.gitkeep` — diretório para volume mount Docker ./canaldecortes/videos:/app/videos
- `docker-compose.yml` (fora do git) — volume atualizado + REDIS_HOST/PORT + depends_on redis

## Decisions Made
- db.py: quem chama é responsável por fechar a conexão (padrão do daemon, não das funções de acesso)
- INSERT IGNORE em insert_video para idempotência — RSS pode re-publicar o mesmo item entre polls
- recover_stuck_downloads captura apenas OperationalError para robustez; outros erros propagam normalmente
- Seed com 5 canais em vez do mínimo de 3 — maior cobertura de conteúdo desde o início

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] pymysql não instalado localmente**
- **Found during:** Task 3 (verificação pytest test_db.py)
- **Issue:** `ModuleNotFoundError: No module named 'pymysql'` ao rodar testes localmente
- **Fix:** `pip3 install pymysql --break-system-packages`
- **Files modified:** Nenhum (instalação de pacote local, não afeta requirements.txt)
- **Verification:** pytest 4/4 passou após instalação
- **Committed in:** 9a01858 (parte do Task 3 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Fix necessário apenas para execução local dos testes. Container Docker usa pip install -r requirements.txt normalmente.

## Issues Encountered
- docker-compose.yml está no diretório pai `/Users/alessandrobm1/develop/server/wordpress/` que não é um repositório git. A mudança foi aplicada no filesystem mas não pode ser commitada via git. O histórico do arquivo é mantido fora do controle de versão do projeto canaldecortes.

## Next Phase Readiness
- db.py pronto para uso pelos módulos rss_poller (02-03) e downloader (02-04)
- Canais-seed disponíveis no DB após próxima inicialização do MySQL com o arquivo de init
- Volume canaldecortes/videos/ configurado para armazenar vídeos baixados

---
*Phase: 02-aquisicao-de-videos*
*Completed: 2026-06-18*
