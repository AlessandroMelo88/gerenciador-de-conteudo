---
phase: 07-schema-multi-canal-python-pipeline
plan: "02"
subsystem: testing
tags: [tdd, pytest, multi-canal, quota-manager, youtube-uploader, publisher, video-processor, metadata-generator, rss-poller, watermark, blacklist, credits]

# Dependency graph
requires:
  - phase: 07-schema-multi-canal-python-pipeline
    plan: "01"
    provides: "Schema migration com destination_channels table e FK destination_channel_id em generated_clips"
provides:
  - "12 testes RED cobrindo MCAN-01/02/03/04 e COPY-01/02/03 em 6 arquivos de teste existentes"
  - "Contratos TDD para Wave 3-4: channel_slug, channel_id, _fetch_pending_clips_for_channel, overlay_watermark, append_credits, blacklist guard"
affects:
  - "07-03 (implementação Wave 3-4 deve passar todos esses testes)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Testes RED com import local (dentro do método) para evitar quebra de módulo ao importar símbolo inexistente"
    - "TestXxxMultiCanal / TestXxxChannelSlug como sufixo para novas classes TDD em Wave 2"

key-files:
  created: []
  modified:
    - "clip-processor/tests/test_quota_manager.py"
    - "clip-processor/tests/test_uploader.py"
    - "clip-processor/tests/test_publisher.py"
    - "clip-processor/tests/test_video_processor.py"
    - "clip-processor/tests/test_metadata_generator.py"
    - "clip-processor/tests/test_rss_poller.py"

key-decisions:
  - "Import de símbolos ainda não existentes (overlay_watermark, append_credits, _fetch_pending_clips_for_channel) feitos localmente dentro dos métodos de teste — evita ImportError ao nível de módulo que quebraria os testes existentes da mesma classe"
  - "SAMPLE_CLIP enriquecido com destination_channel_id e channel_handle — campos extras são ignorados pelos testes existentes que não os verificam"
  - "Retrocompat mantida como GREEN: QuotaManager(r) sem channel_id e YouTubeUploader() sem channel_slug continuam funcionando e seus testes passam"

patterns-established:
  - "RED import pattern: ao importar símbolo não implementado dentro do método de teste, o erro é isolado ao teste individual sem afetar coleta do módulo inteiro"

requirements-completed:
  - MCAN-01
  - MCAN-02
  - MCAN-03
  - MCAN-04
  - COPY-01
  - COPY-02
  - COPY-03

# Metrics
duration: 18min
completed: 2026-06-22
---

# Phase 07 Plan 02: RED Tests Multi-Canal e Copyright Summary

**12 testes RED em 6 arquivos cobrindo channel_slug/channel_id (MCAN-01/03/04), destination_channel_id (MCAN-02), overlay_watermark (COPY-01), append_credits (COPY-02) e blacklist guard (COPY-03)**

## Performance

- **Duration:** 18 min
- **Started:** 2026-06-22T20:00:41Z
- **Completed:** 2026-06-22T20:18:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Adicionou `TestQuotaManagerMultiCanal` (4 testes) e `TestYouTubeUploaderChannelSlug` (3 testes) em seus respectivos arquivos — cobrem MCAN-01, MCAN-03, MCAN-04
- Adicionou `TestPublisherMultiCanal` (3 testes), `TestOverlayWatermark` (2 testes), `TestAppendCredits` (3 testes) e `TestBlacklistGuard` (2 testes) — cobrem MCAN-02, COPY-01, COPY-02, COPY-03
- 57 testes existentes continuam PASS; 12 novos testes em RED state (TypeError, ImportError, AssertionError)

## Task Commits

1. **Task 1: test_quota_manager.py e test_uploader.py** - `0bdb935` (test)
2. **Task 2: test_publisher.py, test_video_processor.py, test_metadata_generator.py, test_rss_poller.py** - `fe30435` (test)

## Files Created/Modified

- `clip-processor/tests/test_quota_manager.py` - +TestQuotaManagerMultiCanal: _key() com channel_id, fallback sem channel_id, independência de quota entre canais
- `clip-processor/tests/test_uploader.py` - +TestYouTubeUploaderChannelSlug: token path derivado de channel_slug, retrocompat com DEFAULT_TOKEN_FILE e token_file explícito
- `clip-processor/tests/test_publisher.py` - SAMPLE_CLIP enriquecido com destination_channel_id/channel_handle; +TestPublisherMultiCanal: _fetch_pending_clips_for_channel, quota independente entre canais
- `clip-processor/tests/test_video_processor.py` - +TestOverlayWatermark: ffmpeg com -filter_complex overlay=W-w-20:20, skip sem subprocess quando watermark ausente
- `clip-processor/tests/test_metadata_generator.py` - +TestAppendCredits: template {channel_handle} substituição, template vazio e handle vazio retornam descrição inalterada
- `clip-processor/tests/test_rss_poller.py` - +TestBlacklistGuard: canal blacklisted=True não dispara insert_video, canal blacklisted=False chama normalmente

## Decisions Made

- Import de `overlay_watermark`, `append_credits` e `_fetch_pending_clips_for_channel` feito localmente dentro dos métodos de teste (não no topo do arquivo) — garante que apenas os novos testes falham, sem quebrar a coleta de pytest para os testes existentes do módulo.
- SAMPLE_CLIP enriquecido com `destination_channel_id: 1, channel_handle: '@sportv'` — campos extras em dicts Python são ignorados pelos testes existentes que não os verificam via mock.
- Retrocompat definida como GREEN intencional: `QuotaManager(r)` sem `channel_id` e `YouTubeUploader()` sem `channel_slug` têm testes que passam imediatamente porque o comportamento existente satisfaz o contrato.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Docker compose estava executando `stop` durante a sessão, tornando `docker exec` indisponível. Testes executados localmente via `python3 -m pytest` com resultado idêntico ao ambiente de container (mesmas dependências).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 6 arquivos de teste com 12 novos testes RED prontos para guiar implementação em Wave 3-4 (07-03)
- Contratos definidos: `QuotaManager(channel_id=)`, `YouTubeUploader(channel_slug=)`, `_fetch_pending_clips_for_channel(conn, dest_id=)`, `overlay_watermark()`, `append_credits()`, blacklist guard em `poll_all_channels`
- Sem bloqueadores para Wave 3

---
*Phase: 07-schema-multi-canal-python-pipeline*
*Completed: 2026-06-22*
