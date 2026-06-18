---
phase: 03-ia-transcri-o-e-sele-o
plan: 01
subsystem: testing
tags: [python, pytest, tdd, mysql, groq, anthropic, whisper]

# Dependency graph
requires:
  - phase: 02-aquisicao-de-videos
    provides: db.py com get_db_connection/update_status, conftest.py com mock_db_conn e sample_video_id
provides:
  - Schema MySQL migrado com pending_cut, reason e transcript_path
  - Interface pública de transcriber.py (transcribe_video, save_transcript)
  - Interface pública de selector.py (select_moments, insert_selected_moments)
  - 11 testes em RED state prontos para GREEN na Wave 1
affects:
  - 03-ia-transcri-o-e-sele-o (plans 02-03 implementam as interfaces aqui definidas)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Skeleton pattern: módulos exportam interfaces com raise NotImplementedError — contratos definidos antes da implementação"
    - "TDD Wave 0: testes RED criados antes dos módulos — garante que falham por lógica, não por config"

key-files:
  created:
    - mysql/init/03-schema-migration.sql
    - clip-processor/src/transcriber.py
    - clip-processor/src/selector.py
    - clip-processor/tests/test_transcriber.py
    - clip-processor/tests/test_selector.py
  modified: []

key-decisions:
  - "VIDEOS_DIR = '/app/videos' definido como constante em transcriber.py — patchável nos testes via patch('src.transcriber.VIDEOS_DIR')"
  - "transcribe_video: groq_client=None cria cliente de produção; injetado em testes — padrão consistente com downloader.py"
  - "select_moments: anthropic_client=None cria cliente de produção; injetado em testes"
  - "insert_selected_moments: score >= 7 insere com status 'pending_cut'; score < 7 descarta sem INSERT"
  - "ENUM generated_clips.status: pending_cut como primeiro valor e novo default — todo clip Phase 3 começa em pending_cut"

patterns-established:
  - "Wave 0 TDD: criar skeletons com NotImplementedError antes de qualquer implementação garante RED state limpo"
  - "Injeção de dependência para clientes externos (groq_client, anthropic_client) permite testes sem API calls reais"

requirements-completed: [AI-01, AI-02, AI-03]

# Metrics
duration: 2min
completed: 2026-06-18
---

# Phase 3 Plan 01: IA Transcricao e Selecao — Wave 0 Summary

**Schema MySQL migrado para pending_cut/reason/transcript_path + 11 testes TDD em RED state com interfaces de transcriber.py e selector.py definidas**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-18T17:28:06Z
- **Completed:** 2026-06-18T17:30:05Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Schema migration SQL criado com os 3 ALTER TABLE para Phase 3 (pending_cut, reason, transcript_path)
- Skeletons transcriber.py e selector.py criados com interfaces públicas completas e raise NotImplementedError
- 11 testes em RED state confirmados: 5 para AI-01 (Groq Whisper), 6 para AI-02/AI-03 (Claude Haiku + inserção)
- Todas as falhas são NotImplementedError — zero ImportError — RED state limpo e correto

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Schema migration SQL** - `51b03d3` (feat)
2. **Task 2: Skeletons + testes RED** - `63197eb` (test)

## Files Created/Modified
- `mysql/init/03-schema-migration.sql` - 3 ALTER TABLE para Phase 3: transcript_path, ENUM pending_cut, coluna reason
- `clip-processor/src/transcriber.py` - Skeleton com transcribe_video() e save_transcript() — raise NotImplementedError
- `clip-processor/src/selector.py` - Skeleton com select_moments() e insert_selected_moments() — raise NotImplementedError
- `clip-processor/tests/test_transcriber.py` - 5 testes RED para AI-01 (Groq Whisper, extração de áudio, falha de API)
- `clip-processor/tests/test_selector.py` - 6 testes RED para AI-02 (formatação de timestamps) e AI-03 (score >= 7, overlap, max 3)

## Decisions Made
- `VIDEOS_DIR = '/app/videos'` definido como constante patchável nos testes — sem hardcode nos métodos
- Padrão de injeção de dependência: `groq_client=None` e `anthropic_client=None` — consistente com downloader.py da Phase 2
- Score >= 7 como threshold de inserção — definido na interface antes da implementação para garantir consistência nos testes

## Deviations from Plan

None — plano executado exatamente como especificado.

## Issues Encountered

`python` não disponível no PATH do macOS; usando `python3`. Sem impacto — testes rodaram corretamente com `python3 -m pytest`.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- Wave 0 completa: schema pronto, interfaces definidas, 11 testes RED aguardando implementação
- Plans 02 e 03 da Phase 3 podem implementar transcriber.py e selector.py diretamente, orientados pelos testes existentes
- Sem blockers — MySQL migration aplicada quando container subir; testes rodam em qualquer ambiente com Python 3.13

---
*Phase: 03-ia-transcri-o-e-sele-o*
*Completed: 2026-06-18*
