---
phase: 07-schema-multi-canal-python-pipeline
plan: "05"
subsystem: video-processing
tags: [ffmpeg, watermark, overlay, metadata, credits, tdd, python]

# Dependency graph
requires:
  - phase: 07-02
    provides: publisher multi-canal com destination_channel_id e channel_handle

provides:
  - overlay_watermark(input_path, watermark_path, output_path) -> str em video_processor.py
  - append_credits(description, credit_template, channel_handle) -> str em metadata_generator.py

affects:
  - 07-06-PLAN (integracao de overlay_watermark e append_credits no fluxo de publicacao)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "FFmpeg com dois inputs usa -filter_complex (nao -vf) — clip primeiro, watermark segundo"
    - "Graceful degradation: funçao retorna input sem efeito colateral quando dependencia ausente"
    - "append_credits: str.format nativo com {channel_handle} como slot — sem f-string de template"

key-files:
  created: []
  modified:
    - clip-processor/src/video_processor.py
    - clip-processor/src/metadata_generator.py

key-decisions:
  - "overlay_watermark usa -filter_complex overlay=W-w-20:20 com margem de 20px no canto superior direito — clip ANTES watermark nos -i args para que W/H referencie o clip"
  - "Graceful degradation em overlay_watermark: se watermark_path nao existe, retorna input_path sem chamar FFmpeg — comportamento identico ao burn_subtitles pattern existente"
  - "append_credits nao modifica descricao existente quando template ou handle vazios — guard duplo (not credit_template or not channel_handle) garante idempotencia"
  - "NÃO integrar overlay_watermark/append_credits em process_clip() ainda — Plan 07-06 tem destination_channel_slug disponivel para resolver o canal correto"

patterns-established:
  - "FFmpeg dual-input pattern: -i clip -i watermark -filter_complex overlay — para qualquer overlay compositing futuro"
  - "Graceful-degradation pattern: verificar arquivo existe antes de FFmpeg, retornar input_path se ausente"

requirements-completed:
  - COPY-01
  - COPY-02

# Metrics
duration: 2min
completed: 2026-06-22
---

# Phase 7 Plan 05: Watermark FFmpeg overlay e append_credits para COPY-01/COPY-02

**overlay_watermark() com FFmpeg -filter_complex overlay=W-w-20:20 e append_credits() com str.format — ambas exportadas e com testes GREEN, prontas para integração no Plan 07-06**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-22T20:37:53Z
- **Completed:** 2026-06-22T20:39:04Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `overlay_watermark()` implementada em `video_processor.py` com FFmpeg dual-input, graceful degradation e 2 novos testes GREEN
- `append_credits()` implementada em `metadata_generator.py` com str.format e guard duplo (template ou handle vazio = sem modificação), 3 novos testes GREEN
- Suíte total: 16/16 PASSED (9 video_processor + 7 metadata_generator), zero regressões

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: overlay_watermark() em video_processor (COPY-01)** - `02328d2` (feat)
2. **Task 2: append_credits() em metadata_generator (COPY-02)** - `298929e` (feat)

**Plan metadata:** (este commit docs)

_Nota: Tasks TDD — RED state (testes) já existia de Wave 2; Wave 3 implementou GREEN._

## Files Created/Modified

- `clip-processor/src/video_processor.py` — Adicionada `overlay_watermark()` e atualizado docstring do módulo
- `clip-processor/src/metadata_generator.py` — Adicionada `append_credits()` e atualizado docstring do módulo

## Decisions Made

- FFmpeg dual-input obriga uso de `-filter_complex` (não `-vf`) — clip é o primeiro `-i`, watermark o segundo, garantindo que `W`/`H` na expressão `overlay=W-w-20:20` referencie as dimensões do clip.
- Graceful degradation em `overlay_watermark`: arquivo ausente retorna `input_path` sem chamar FFmpeg — consistente com comportamento defensivo do projeto (sem crash em ausência de asset).
- `append_credits` guard duplo `not credit_template or not channel_handle`: basta um estar vazio para não adicionar créditos — previne linhas de crédito malformadas.
- Integração com `process_clip()` e publisher deliberadamente adiada para Plan 07-06 onde `destination_channel_slug` e `credit_template` estarão disponíveis via schema multi-canal.

## Deviations from Plan

None — plano executado exatamente como escrito.

## Issues Encountered

None.

## User Setup Required

None — nenhuma configuração externa necessária.

## Next Phase Readiness

- `overlay_watermark()` pronta para ser chamada no publisher com `watermark_path` resolvido via `channel_slug`
- `append_credits()` pronta para ser chamada no publisher com `credit_template` e `channel_handle` vindos da tabela `destination_channels`
- Plan 07-06 integra ambas no fluxo de publicação multi-canal

---
*Phase: 07-schema-multi-canal-python-pipeline*
*Completed: 2026-06-22*
