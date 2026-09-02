---
phase: 07-schema-multi-canal-python-pipeline
plan: "07"
subsystem: clip-processor/youtube-oauth
tags: [oauth, multi-canal, branding, watermark, MCAN-01, COPY-01]
dependency_graph:
  requires: [07-06]
  provides: [youtube_oauth_helper, branding_volume]
  affects: [publisher, uploader, video_processor]
tech_stack:
  added: [google-auth-oauthlib CLI pattern]
  patterns: [argparse CLI, token per channel slug, bind mount read-only]
key_files:
  created:
    - clip-processor/src/youtube_oauth.py
    - branding/.gitkeep
    - branding/.gitignore
  modified:
    - /Users/alessandrobm1/develop/server/wordpress/docker-compose.yml (outside git repo)
decisions:
  - youtube_oauth.py exposes generate_token() as testable function separate from main() — allows unit testing without subprocess
  - YOUTUBE_CLIENT_SECRETS env var override enables multi-canal without code change
  - branding/ .gitignore excludes *.png assets (private per canal) but tracks directory via .gitkeep
metrics:
  duration: "~1min (partial — stopped at checkpoint)"
  completed_date: "2026-06-22"
  tasks_completed: 1
  tasks_total: 2
  files_changed: 3
---

# Phase 7 Plan 7: YouTube OAuth CLI + Branding Volume Summary

**One-liner:** CLI youtube_oauth.py gera token-{slug}.json por canal-destino via InstalledAppFlow com suporte a YOUTUBE_CLIENT_SECRETS env var; volume branding montado read-only no container.

## Status

PAUSED — Stopped at checkpoint:human-verify (Task 2). Task 1 complete and committed.

## Tasks Completed

### Task 1: Criar youtube_oauth.py e atualizar docker-compose.yml com volume branding

**Commit:** 8ebb510

**Files created/modified:**
- `clip-processor/src/youtube_oauth.py` — CLI helper com `--channel` obrigatório, gera `/app/youtube/token-{slug}.json`
- `branding/.gitkeep` — garante diretório no git
- `branding/.gitignore` — exclui *.png/*.jpg/*.jpeg do git (assets privados)
- `/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml` — volume `./canaldecortes/branding:/app/branding:ro` adicionado ao serviço clip-processor (fora do repo git)

**Done criteria met:**
- `clip-processor/src/youtube_oauth.py` existe com `--channel` como argumento obrigatório
- `docker-compose.yml` tem `./canaldecortes/branding:/app/branding:ro` nos volumes do clip-processor
- Diretório `branding/` existe com `.gitkeep` e `.gitignore`

## Tasks Pending (awaiting human verification)

### Task 2: Checkpoint — Verificação Visual e Funcional Completa

Tipo: `checkpoint:human-verify`

Requer que o operador execute as 5 verificações descritas no plano (pytest, schema DB, watermark visual, roteamento, blacklist guard).

## Deviations from Plan

None — Task 1 executed exactly as written.

**Note:** `generate_token()` extracted as separate testable function (beyond plan spec) — minor improvement for testability, no behavioral change.

## Self-Check
