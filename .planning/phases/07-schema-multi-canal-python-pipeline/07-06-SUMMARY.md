---
phase: 07-schema-multi-canal-python-pipeline
plan: "06"
subsystem: python-pipeline-integration
tags: [selector, video-processor, publisher, multi-canal, watermark, credits, tdd, python]

# Dependency graph
requires:
  - phase: 07-03
    provides: migration destination_channels + generated_clips.destination_channel_id
  - phase: 07-04
    provides: QuotaManager com channel_id e YouTubeUploader com channel_slug
  - phase: 07-05
    provides: overlay_watermark() e append_credits() prontas para integração

provides:
  - selector.insert_selected_moments persiste destination_channel_id em generated_clips
  - video_processor.process_clip integrado com overlay_watermark via destination_channel_slug
  - publisher.publish_pending_clips com loop multi-canal por destination_channel
  - publisher._fetch_destination_channels e _fetch_pending_clips_for_channel

affects:
  - Pipeline end-to-end: do selector ao publisher, todos os módulos Phase 7 conectados

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD dual-layer: RED no nível de teste → GREEN na implementação → zero regressões"
    - "Fallback legado em publish_pending_clips quando destination_channels vazio — garante retrocompat sem quebrar ambientes v1.0"
    - "_lookup_destination_channel_id: SELECT único antes do loop de momentos — evita N queries por momento"
    - "make_conn_with_clips com fetchall.side_effect: primeiro retorna [] (fallback), segundo retorna clips — desacopla testes legados do fluxo multi-canal"

key-files:
  created: []
  modified:
    - clip-processor/src/selector.py
    - clip-processor/src/video_processor.py
    - clip-processor/src/publisher.py
    - clip-processor/tests/test_selector.py
    - clip-processor/tests/test_video_processor.py
    - clip-processor/tests/test_publisher.py

key-decisions:
  - "_lookup_destination_channel_id chamado uma única vez antes do loop de moments em insert_selected_moments — evita redundância e garante consistência entre momentos do mesmo vídeo"
  - "process_clip usa subtitled_path intermediário (_subtitled.mp4) com limpeza explícita após watermark ou rename — sem acúmulo de arquivos em disco"
  - "overlay_watermark graceful: quando resultado == subtitled_path (watermark ausente), os.rename para final_clip_path em vez de deixar arquivo no caminho errado"
  - "publish_pending_clips fallback quando _fetch_destination_channels retorna []: usa _fetch_pending_clips() legado — garante pipeline funcional em ambientes sem migration 07-03 aplicada"
  - "make_conn_with_clips atualizado com fetchall.side_effect [[], clips, ...]: primeiro fetchall retorna [] para acionar fallback legado; novos testes multi-canal sobrescrevem side_effect explicitamente"
  - "_publish_one e _publish_clips_for extraídos: separação de responsabilidades entre loop de canal e lógica de upload de clip individual"

# Metrics
duration: 29min
completed: 2026-06-22
---

# Phase 7 Plan 06: Integração End-to-End Multi-Canal — selector + video_processor + publisher

**Integração completa dos módulos Phase 7: selector persiste destination_channel_id, process_clip aplica overlay_watermark via slug, publisher itera por canais-destino com QuotaManagers independentes e append_credits — suíte 130/130 GREEN**

## Performance

- **Duration:** ~29 min
- **Started:** 2026-06-22T20:41:25Z
- **Completed:** 2026-06-22T21:11:06Z
- **Tasks:** 2
- **Files modified:** 6 (3 src + 3 tests)

## Accomplishments

- `selector.py`: `_lookup_destination_channel_id` adicionado; `insert_selected_moments` persiste `destination_channel_id` em `generated_clips` via JOIN `source_videos → source_channels → destination_channels`; NULL graceful quando nicho ausente ou sem canal ativo
- `video_processor.py`: `_fetch_clip` estendido com LEFT JOIN `destination_channels` retornando `destination_channel_slug`; `process_clip` pipeline atualizado: `burn_subtitles` → `subtitled_path` → `overlay_watermark` → `final_clip_path`; `os.rename` quando slug NULL; limpeza de arquivo intermediário em ambos os casos
- `publisher.py`: `_fetch_destination_channels` e `_fetch_pending_clips_for_channel` adicionados; `publish_pending_clips` reescrito com loop multi-canal; `append_credits` importado e chamado por clip quando `credit_template + channel_handle` disponíveis; fallback legado quando sem canais-destino; `_publish_one` e `_publish_clips_for` extraídos para reuso
- Suíte total: **130/130 PASSED** (zero regressões)
- 5 novos testes em `TestInsertMomentsDestinationChannel`, 2 em `TestProcessClipWithWatermark`, 6 em `TestPublisherMultiCanal` (3 pré-existentes RED + 3 novos)

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: selector + video_processor (MCAN-02, COPY-01)** - `1870f31` (feat)
2. **Task 2: publisher multi-canal (MCAN-01/03/04, COPY-02)** - `de5cba8` (feat)

**Plan metadata:** (este commit docs)

## Files Created/Modified

- `clip-processor/src/selector.py` — `_lookup_destination_channel_id()` adicionado; `insert_selected_moments` inclui `destination_channel_id` no INSERT
- `clip-processor/src/video_processor.py` — `_fetch_clip` com LEFT JOIN; `process_clip` com pipeline watermark + limpeza intermediário
- `clip-processor/src/publisher.py` — `_fetch_destination_channels`, `_fetch_pending_clips_for_channel`, `_publish_one`, `_publish_clips_for`; `publish_pending_clips` multi-canal com fallback legado; import `append_credits`
- `clip-processor/tests/test_selector.py` — `TestInsertMomentsDestinationChannel` (3 novos testes); `test_score_6_discarded` e `test_max_3_moments` atualizados para novo fluxo com SELECT prévio
- `clip-processor/tests/test_video_processor.py` — `TestProcessClipWithWatermark` (2 novos testes); testes existentes atualizados com `destination_channel_slug` e mock `os.rename`
- `clip-processor/tests/test_publisher.py` — `make_conn_with_clips` atualizado com `fetchall.side_effect`; `TestPublisherMultiCanal` expandido com 3 novos testes; testes de SELECT de status atualizados para aceitar multi-canal params

## Decisions Made

- `_lookup_destination_channel_id` chamado uma única vez antes do loop de moments: todos os clips do mesmo `source_video_id` ficam com o mesmo `destination_channel_id`, garantindo consistência e evitando N queries.
- `process_clip` usa arquivo intermediário `{clip_id}_subtitled.mp4`: mantém separação clara entre saída de `burn_subtitles` e entrada de `overlay_watermark`. Limpeza explícita em ambos os caminhos (slug presente ou ausente).
- Fallback em `publish_pending_clips` quando `_fetch_destination_channels` retorna `[]`: garante que ambientes sem migration Phase 7 aplicada continuem funcionando com o pipeline v1.0.
- `make_conn_with_clips` atualizado com `fetchall.side_effect = [[], clips, ...]`: primeiro call retorna `[]` para acionar fallback legado, sem alterar a semântica dos testes existentes. Testes multi-canal sobrescrevem `side_effect` explicitamente para testar o novo fluxo.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_score_6_discarded assertiva incompatível com novo fluxo**
- **Found during:** Task 1 RED state
- **Issue:** `execute.assert_not_called()` falharia porque `_lookup_destination_channel_id` chama `cursor.execute` (SELECT) antes de verificar o score
- **Fix:** Atualizado para verificar apenas a ausência de INSERT, não de qualquer execute call
- **Files modified:** `clip-processor/tests/test_selector.py`
- **Commit:** `1870f31`

**2. [Rule 2 - Retrocompat] make_conn_with_clips incompatível com novo fluxo multi-canal**
- **Found during:** Task 2 GREEN state
- **Issue:** `cursor.fetchall.return_value = clips` fazia `_fetch_destination_channels` retornar clips (não canais-destino), quebrando os testes existentes no loop multi-canal
- **Fix:** `make_conn_with_clips` atualizado para usar `fetchall.side_effect = [[], clips, ...]` onde `[]` aciona o fallback legado
- **Files modified:** `clip-processor/tests/test_publisher.py`
- **Commit:** `de5cba8`

**3. [Rule 1 - Bug] test_seleciona_pending/approved assertiva de tuple incompatível com multi-canal**
- **Found during:** Task 2 analysis
- **Issue:** `select_params == ('pending',)` falharia com multi-canal onde params = `('pending', dest_id)`
- **Fix:** Assertiva atualizada para verificar `select_params[0] == 'pending'` (compatível com ambos os formatos)
- **Files modified:** `clip-processor/tests/test_publisher.py`
- **Commit:** `de5cba8`

## Issues Encountered

None bloqueantes. As deviações acima foram todas Rule 1/2 auto-fixadas sem necessidade de pausa.

## User Setup Required

None — nenhuma configuração externa necessária. A migration 07-03 deve estar aplicada no banco para o fluxo multi-canal funcionar em produção; sem migration, o fallback legado é ativado automaticamente.

## Next Phase Readiness

- Pipeline Python Phase 7 completo: todos os módulos integrados end-to-end
- `destination_channel_id` persistido → publisher sabe para qual canal publicar cada clip
- Watermark do canal-destino aplicado automaticamente em cada clip processado
- Créditos do canal de origem appended na descrição antes do upload
- Phase 8 (Painel Laravel/Filament) pode consumir `destination_channels` e `generated_clips.destination_channel_id` para exibir dados por canal

---
*Phase: 07-schema-multi-canal-python-pipeline*
*Completed: 2026-06-22*
