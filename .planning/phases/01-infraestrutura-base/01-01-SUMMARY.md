---
phase: 01-infraestrutura-base
plan: "01"
subsystem: infra
tags: [docker, docker-compose, n8n, whisper, ffmpeg, python, yt-dlp, anthropic]

# Dependency graph
requires: []
provides:
  - docker-compose.yml com n8n 2.27.0, clip-processor (build local) e whisper na rede internal
  - clip-processor/Dockerfile com python:3.12-slim + ffmpeg + dependências pip
  - clip-processor/requirements.txt com yt-dlp, google-api-python-client, anthropic, pymysql
  - clip-processor/src/main.py stub para manter container em execução
  - .env.example documentando N8N_ENCRYPTION_KEY, ANTHROPIC_API_KEY, CLIPS_DB_PASSWORD
  - .gitignore excluindo .env, token.json, client_secret.json, whisper/models/, n8n/data/
  - Estrutura de diretórios: youtube/, clip-processor/src/, n8n/data/, whisper/models/
affects:
  - 01-02 (MySQL clips_automation database setup)
  - 01-03 (YouTube OAuth token generation)
  - 01-04 (docker-compose up verification)

# Tech tracking
tech-stack:
  added:
    - n8n 2.27.0 (docker.n8n.io/n8nio/n8n:2.27.0)
    - faster-whisper-server (fedirz/faster-whisper-server:latest-cpu)
    - python:3.12-slim + ffmpeg
    - yt-dlp, google-api-python-client, google-auth-oauthlib, anthropic, pymysql
  patterns:
    - Serviços novos entram na rede 'internal' existente (não external network)
    - N8N usa SQLite default (não DB_TYPE=mysqldb, removido no n8n 2.0)
    - Secrets via ${VAR} do .env, nunca hardcoded
    - Volumes de dados ignorados no .gitignore, tracked com .gitkeep para git preservar dirs

key-files:
  created:
    - /Users/alessandrobm1/develop/server/wordpress/canaldecortes/.gitignore
    - /Users/alessandrobm1/develop/server/wordpress/canaldecortes/.env.example
    - /Users/alessandrobm1/develop/server/wordpress/canaldecortes/clip-processor/Dockerfile
    - /Users/alessandrobm1/develop/server/wordpress/canaldecortes/clip-processor/requirements.txt
    - /Users/alessandrobm1/develop/server/wordpress/canaldecortes/clip-processor/src/main.py
    - /Users/alessandrobm1/develop/server/wordpress/canaldecortes/youtube/.gitkeep
    - /Users/alessandrobm1/develop/server/wordpress/canaldecortes/youtube/token.json (placeholder {})
  modified:
    - /Users/alessandrobm1/develop/server/wordpress/docker-compose.yml

key-decisions:
  - "n8n usa SQLite default — DB_TYPE=mysqldb removido no n8n 2.0 causaria falha silenciosa"
  - "N8N_ENCRYPTION_KEY via ${N8N_ENCRYPTION_KEY} do .env — nunca hardcoded"
  - "Imagem n8n 2.27.0 pinada (não :latest) para evitar breaking changes em runtime"
  - "token.json placeholder {} criado para evitar falha do volume mount no clip-processor antes do Plan 03"

patterns-established:
  - "Secrets no .env referenciados via ${VAR} no docker-compose"
  - "Novos serviços na rede 'internal' existente sem external network"
  - "Diretórios de runtime (n8n/data, whisper/models) ignorados pelo .gitignore"

requirements-completed: [INFRA-01, INFRA-04]

# Metrics
duration: 2min
completed: 2026-06-17
---

# Phase 1 Plan 01: Infraestrutura Base — Definição dos Containers Summary

**docker-compose.yml estendido com n8n 2.27.0, clip-processor Python/FFmpeg e whisper na rede internal, com Dockerfile customizado e .env.example documentando todas as variáveis obrigatórias**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-17T16:31:10Z
- **Completed:** 2026-06-17T16:33:30Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- docker-compose.yml estendido com 3 novos serviços (n8n, clip-processor, whisper) sem alterar nginx/php/mysql/redis
- Dockerfile customizado do clip-processor com python:3.12-slim + ffmpeg + 5 dependências pip
- .env.example com todas as variáveis obrigatórias documentadas (N8N_ENCRYPTION_KEY, ANTHROPIC_API_KEY, CLIPS_DB_PASSWORD)
- .gitignore protegendo .env, token.json, client_secret.json e volumes de dados

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar estrutura de diretórios e .env.example** - `fdaa379` (chore)
2. **Task 2: Criar clip-processor Dockerfile e requirements.txt** - `759e2ed` (feat)
3. **Task 3: Estender docker-compose.yml com n8n, clip-processor e whisper** - `e892552` (feat)

## Files Created/Modified
- `canaldecortes/.gitignore` - Exclui .env, token.json, client_secret.json, whisper/models/, n8n/data/
- `canaldecortes/.env.example` - Template com N8N_ENCRYPTION_KEY, ANTHROPIC_API_KEY, CLIPS_DB_PASSWORD
- `canaldecortes/clip-processor/Dockerfile` - python:3.12-slim + ffmpeg + pip install requirements
- `canaldecortes/clip-processor/requirements.txt` - yt-dlp, google-api-python-client, google-auth-oauthlib, anthropic, pymysql
- `canaldecortes/clip-processor/src/main.py` - Stub mínimo com loop infinito para manter container em execução
- `canaldecortes/youtube/.gitkeep` - Mantém diretório no git
- `canaldecortes/youtube/token.json` - Placeholder {} para volume mount (gitignored, substituído em Plan 03)
- `/server/wordpress/docker-compose.yml` - Adicionados n8n, clip-processor, whisper (fora do git repo canaldecortes)

## Decisions Made
- n8n usa SQLite (default) — DB_TYPE=mysqldb foi removido no n8n 2.0 e causaria falha silenciosa
- Imagem n8n pinada em 2.27.0 em vez de :latest para estabilidade
- token.json placeholder {} criado (gitignored) para evitar falha do volume mount no clip-processor antes do OAuth ser configurado no Plan 03
- docker-compose.yml vive em /server/wordpress/ fora do git repo canaldecortes — mudança feita mas não trackeada em git nesta fase

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- docker-compose.yml está em `/server/wordpress/` (fora do git repo canaldecortes). A mudança foi aplicada com sucesso mas não é trackeada no git deste projeto. Será relevante para Plans futuros que executem `docker-compose up`.

## User Setup Required

Para executar os containers após este plano:

1. Copiar `.env.example` para `.env` em `/server/wordpress/canaldecortes/`:
   ```bash
   cp canaldecortes/.env.example canaldecortes/.env
   ```
2. Preencher valores no `.env`:
   - `N8N_ENCRYPTION_KEY`: `openssl rand -hex 32`
   - `ANTHROPIC_API_KEY`: obter em https://console.anthropic.com/settings/keys
   - `CLIPS_DB_PASSWORD`: senha para clips_user (você escolhe)

## Next Phase Readiness
- Estrutura de containers definida e pronta para `docker-compose up` após Plan 04
- Plan 02: criar banco de dados MySQL `clips_automation` com usuário `clips_user`
- Plan 03: gerar token.json do YouTube OAuth (substitui placeholder)
- Plan 04: executar `docker-compose up` e verificar todos os serviços online

---
*Phase: 01-infraestrutura-base*
*Completed: 2026-06-17*
