---
phase: 03-ia-transcri-o-e-sele-o
plan: 03
subsystem: ia-selection
tags: [python, pytest, tdd, anthropic, claude-haiku, structured-outputs, mysql]

# Dependency graph
requires:
  - phase: 03-ia-transcri-o-e-sele-o
    plan: 01
    provides: selector.py skeleton com NotImplementedError + 6 testes RED
affects:
  - clip-processor/src/selector.py
  - mysql generated_clips table

provides:
  - selector.py completo com select_moments + insert_selected_moments + _remove_overlaps
  - AI-02: análise de transcrição via Claude Haiku com output_config json_schema
  - AI-03: inserção filtrada em generated_clips com score >= 7 e limite de 3 momentos

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "output_config com json_schema para structured outputs do Claude Haiku 4.5 — sem prefill (HTTP 400 em modelos 4.x)"
    - "_remove_overlaps aplicado em insert_selected_moments além de select_moments — contrato explícito de deduplicação"
    - "TDD GREEN: implementação mínima guiada pelos 6 testes RED existentes"

key-files:
  created: []
  modified:
    - clip-processor/src/selector.py

key-decisions:
  - "_remove_overlaps aplicado também em insert_selected_moments além de select_moments — testes exigem que a função de inserção seja idempotente quanto a overlaps"
  - "output_config com format.type=json_schema — MOMENT_OUTPUT_SCHEMA segue padrão da RESEARCH.md para evitar HTTP 400"
  - "insert_selected_moments respeita limite de 3 paradas no loop, não em _remove_overlaps — permite mais de 3 na lista de entrada"

# Metrics
duration: ~5min
completed: 2026-06-18
---

# Phase 3 Plan 03: selector.py GREEN — Claude Haiku structured outputs com score >= 7 e remoção de overlap

**selector.py implementado em ciclo TDD GREEN: select_moments() via output_config json_schema + insert_selected_moments() com filtro score >= 7, remoção de overlap e limite de 3 momentos**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-18T17:33:11Z
- **Completed:** 2026-06-18T17:38:25Z
- **Tasks:** 1 (TDD GREEN)
- **Files modified:** 1

## Accomplishments

- SYSTEM_PROMPT definido como constante de módulo com instrução completa para futebol e podcasts
- MOMENT_OUTPUT_SCHEMA com json_schema via output_config — padrão correto para claude-haiku-4-5 (prefill retorna HTTP 400)
- select_moments(): formata segmentos com [Ns-Ns], chama Claude Haiku, aplica _remove_overlaps, trata exceções com []
- insert_selected_moments(): aplica _remove_overlaps nos momentos de entrada antes de iterar, filtra score >= 7, limita a 3 inserções
- _remove_overlaps(): ordena por score decrescente, descarta candidatos sobrepostos, retorna máx 3
- 6/6 testes GREEN: test_returns_moments_list, test_transcript_formatted_with_timestamps, test_score_7_inserted, test_score_6_discarded, test_overlap_keeps_higher_score, test_max_3_moments
- Suite completa: 28/28 passando (zero regressão)

## Task Commits

1. **Task 1: selector.py GREEN** - `4871ba9` (feat)

## Files Created/Modified

- `clip-processor/src/selector.py` - Implementação completa de AI-02 e AI-03: SYSTEM_PROMPT, MOMENT_OUTPUT_SCHEMA, select_moments, insert_selected_moments, _remove_overlaps

## Decisions Made

- `_remove_overlaps` aplicado dentro de `insert_selected_moments` (além de `select_moments`): o teste `test_overlap_keeps_higher_score` envia overlaps diretamente para insert — a função precisa ser robusta independente da origem dos momentos
- `output_config=MOMENT_OUTPUT_SCHEMA` em vez de prefill: seguindo padrão documentado na RESEARCH.md — modelos claude-haiku-4-5 retornam HTTP 400 com prefill de '['
- Params do SQL como tupla com 'pending_cut' literal: `(source_video_id, start, end, score, reason, 'pending_cut')` — teste verifica que 'pending_cut' aparece nos params

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] _remove_overlaps aplicado em insert_selected_moments**
- **Found during:** Task 1 (primeira execução dos testes)
- **Issue:** test_overlap_keeps_higher_score envia 2 momentos sobrepostos diretamente para insert_selected_moments e espera count == 1. A implementação inicial só aplicava _remove_overlaps em select_moments.
- **Fix:** Adicionado `filtered = _remove_overlaps(moments)` no início de insert_selected_moments antes do loop de inserção
- **Files modified:** clip-processor/src/selector.py
- **Commit:** 4871ba9

## Self-Check: PASSED

- clip-processor/src/selector.py: FOUND
- Commit 4871ba9: FOUND
- 6 testes selector: PASSED (confirmado)
- 28 testes suite completa: PASSED (confirmado — exit code 0)
