---
phase: quick-1
plan: 01
subsystem: ui
tags: [whisper-cpp, laravel, inertia, react, flask, mysql, shadcn]

requires: []
provides:
  - "Tabela transcription_jobs (MySQL) — fonte única de status/progresso de transcrições locais"
  - "Endpoint POST /internal/transcribe no clip-processor (whisper-cpp local em thread daemon)"
  - "Página /painel/transcricoes: formulário de URL + lista de jobs com Progress bar (shadcn) + download do .srt"
affects: []

tech-stack:
  added: [whisper.cpp (build from source, modelo ggml-small), progress.tsx (shadcn)]
  patterns:
    - "Worker de background em thread daemon Python que abre sua própria conexão pymysql (nunca compartilha conexão entre threads)"
    - "UPDATE dinâmico (update_job) montando SET só com campos não-None — evita sobrescrever colunas não informadas"

key-files:
  created:
    - painel/database/migrations/2026_07_30_000000_create_transcription_jobs_table.php
    - painel/app/Models/TranscriptionJob.php
    - clip-processor/src/transcription_job.py
    - clip-processor/tests/test_transcription_job.py
    - painel/app/Http/Controllers/TranscriptionController.php
    - painel/resources/js/pages/TranscricaoLocal.tsx
    - painel/resources/js/components/ui/progress.tsx
  modified:
    - painel/app/Services/ClipProcessorClient.php
    - clip-processor/src/internal_api.py
    - clip-processor/Dockerfile
    - painel/routes/web.php
    - painel/resources/js/components/app-sidebar.tsx

key-decisions:
  - "Modelo whisper-cpp 'small' multilíngue (funciona com -l pt) — mesmo tamanho recomendado no plano"
  - "Progresso via milestones grosseiros (10%/50%/100%), não % real do whisper — whisper-cpp não expõe progresso incremental fácil de parsear entre versões"
  - "Binário confirmado como whisper-cli (não main) — versão atual do whisper.cpp já usa esse nome, sem necessidade de ajustar o Dockerfile"
  - "Dockerfile precisou de curl adicional (Rule 3 - blocking): download-ggml-model.sh do whisper.cpp requer wget2/curl/wget, ausente na imagem base python:3.12-slim"

requirements-completed: [QUICK-1]

duration: ~35min
completed: 2026-07-30
---

# Quick Task 1: Transcrição Local Summary

**Sessão "Transcrição Local" no painel: URL do YouTube → download de áudio + whisper-cpp local em thread de background no clip-processor, com progresso persistido em `transcription_jobs` (MySQL) e Progress bar (shadcn) que sobrevive a reload.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 3
- **Files modified:** 12 (7 criados, 5 modificados)

## Accomplishments

- Tabela `transcription_jobs` isolada (nunca toca `source_videos`/`generated_clips`) com model Eloquent e método `ClipProcessorClient::transcribe()`
- Worker `transcription_job.py` no clip-processor: `create_transcription_job`/`update_job`/`process_transcription_job`/`start_transcription_job`, com endpoint `POST /internal/transcribe` protegido por `X-Internal-Token`, cobertos por 23 testes (TDD RED→GREEN)
- Imagem `clip-processor` reconstruída com whisper-cpp compilado (binário `whisper-cli`) e modelo `ggml-small.bin` (487MB) baixado; container rodando
- Página `TranscricaoLocal.tsx` no painel: formulário de URL, lista de jobs com `Progress` (shadcn), polling via `router.reload` a cada 3s, download de `.srt` habilitado só quando `status === 'done'`; item na sidebar

## Task Commits

Each task was committed atomically:

1. **Task 1: Contrato de dados — migration + model + ClipProcessorClient::transcribe()** - `1186b10` (feat)
2. **Task 2: Worker de transcrição local (whisper-cpp + thread + endpoint)** - `4e90418` (test) → `59c21c5` (feat)
3. **Task 3: Página "Transcrição Local" no painel** - `310e394` (feat)

_Nota: Task 2 seguiu TDD (RED com 23 testes falhando por ModuleNotFoundError → GREEN após implementação, sem etapa de refactor necessária)._

## Files Created/Modified

- `painel/database/migrations/2026_07_30_000000_create_transcription_jobs_table.php` - Tabela transcription_jobs
- `painel/app/Models/TranscriptionJob.php` - Model Eloquent isolado ($guarded = [])
- `painel/app/Services/ClipProcessorClient.php` - Método `transcribe(string $url): array`
- `clip-processor/src/transcription_job.py` - Worker completo (CRUD do job + download + whisper + thread)
- `clip-processor/src/internal_api.py` - Endpoint `POST /internal/transcribe`
- `clip-processor/tests/test_transcription_job.py` - 9 testes do worker + 3 testes do endpoint
- `clip-processor/Dockerfile` - Build whisper.cpp + curl + modelo small
- `painel/app/Http/Controllers/TranscriptionController.php` - index/store/download
- `painel/routes/web.php` - Rotas `/painel/transcricoes` (GET/POST) e `/painel/transcricoes/{job}/download`
- `painel/resources/js/pages/TranscricaoLocal.tsx` - Página completa com Progress bar e polling
- `painel/resources/js/components/ui/progress.tsx` - Componente shadcn Progress (novo no projeto)
- `painel/resources/js/components/app-sidebar.tsx` - Item "Transcrição Local" (AudioLinesIcon)

## Decisions Made

- Modelo whisper-cpp `small` (multilíngue, `-l pt`) — conforme especificado no plano
- Progresso por milestones grosseiros (10% download, 50% transcrevendo, 100% concluído) — limitação documentada, whisper-cpp não expõe % real de forma parseável entre versões
- `srt_path` gravado pelo Python como caminho absoluto do container clip-processor; Laravel sempre remonta via `basename()` + disco `clips-videos` (nunca usa o caminho absoluto diretamente)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adicionado `curl` ao Dockerfile do clip-processor**
- **Found during:** Task 2 (build da imagem clip-processor)
- **Issue:** `docker compose build clip-processor` falhou no build — `download-ggml-model.sh` do whisper.cpp requer `wget2`, `curl` ou `wget`, nenhum presente na imagem base `python:3.12-slim` + pacotes originalmente listados no plano (ffmpeg, git, build-essential, cmake)
- **Fix:** Adicionada linha `curl` à lista de pacotes `apt-get install` no Dockerfile
- **Files modified:** `clip-processor/Dockerfile`
- **Verification:** Rebuild subsequente completou com sucesso, modelo `ggml-small.bin` (487MB) baixado e confirmado via `ls` dentro do container
- **Committed in:** `59c21c5` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Correção necessária para o build completar; nenhum scope creep — resto do Dockerfile seguiu exatamente o plano, incluindo o nome do binário confirmado (`whisper-cli`, sem necessidade de ajuste do `WHISPER_CPP_BIN`).

## Issues Encountered

None além do deviation acima.

## User Setup Required

None - nenhuma configuração externa necessária. Rebuild/restart do `clip-processor` já executado (`docker compose build clip-processor && docker compose up -d clip-processor`), container `running`.

## Next Phase Readiness

- Feature isolada e funcional: nenhum job de transcrição local aparece em `generated_clips` nem nas telas de aprovação de clips
- Fluxo manual fim-a-fim (colar URL real, acompanhar pending→downloading→transcribing→done, baixar .srt) ainda não foi testado com vídeo real — recomendado como próximo passo de verificação do operador
- Suite Python completa rodada: 167 passed, 3 falhas pré-existentes em `test_quota_manager.py` (fora do escopo desta tarefa, documentadas em STATE.md)

---
*Phase: quick-1*
*Completed: 2026-07-30*

## Self-Check: PASSED

All created files verified present on disk; all task commit hashes (1186b10, 4e90418, 59c21c5, 310e394) verified present in git log.
