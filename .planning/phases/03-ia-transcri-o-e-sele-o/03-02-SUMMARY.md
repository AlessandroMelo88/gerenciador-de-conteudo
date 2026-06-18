---
phase: 03-ia-transcri-o-e-sele-o
plan: 02
subsystem: ai
tags: [groq, whisper, transcription, ffmpeg, python, tdd]

# Dependency graph
requires:
  - phase: 03-01
    provides: transcriber.py skeleton com 5 testes RED (NotImplementedError), VIDEOS_DIR constante, assinaturas de interface

provides:
  - transcribe_video(): transcrição via Groq Whisper verbose_json com timestamps por segmento
  - save_transcript(): salva JSON em disco e atualiza transcript_path no banco
  - _prepare_audio(): extração MP3 via ffmpeg para vídeos >24MB
  - 5 testes GREEN em tests/test_transcriber.py

affects: [03-03, selector, pipeline-orchestration]

# Tech tracking
tech-stack:
  added: [groq SDK (production client), subprocess ffmpeg]
  patterns: [injeção de dependência groq_client=None, try/except retorna None sem propagar exception, cleanup finally block para arquivo temporário]

key-files:
  created: []
  modified:
    - clip-processor/src/transcriber.py

key-decisions:
  - "try/except Exception amplo em transcribe_video: captura qualquer falha de API e retorna None — chamador responsável por marcar vídeo como failed"
  - "Cleanup de audio_path temporário no bloco finally: garante remoção mesmo se exception ocorrer durante transcrição"
  - "_prepare_audio() retorna tuple (path, bool) para sinalizar ao chamador se deve deletar arquivo — extensível para casos futuros"

patterns-established:
  - "Groq Whisper: whisper-large-v3-turbo + verbose_json + timestamp_granularities=['segment'] + language='pt' + temperature=0.0"
  - "Threshold de tamanho de arquivo: 24_000_000 bytes (24MB) para acionar extração de áudio"
  - "SQL direto para transcript_path: UPDATE source_videos SET transcript_path=%s WHERE youtube_video_id=%s (sem função helper)"

requirements-completed: [AI-01]

# Metrics
duration: 6min
completed: 2026-06-18
---

# Phase 03 Plan 02: transcriber.py — Transcrição Groq Whisper com timestamps (AI-01) Summary

**transcribe_video() e save_transcript() implementados via Groq Whisper verbose_json com injeção de dependência, ffmpeg para arquivos >24MB e retorno None em falha de API**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-18T17:35:00Z
- **Completed:** 2026-06-18T17:41:00Z
- **Tasks:** 1 (TDD GREEN)
- **Files modified:** 1

## Accomplishments

- transcribe_video() chama Groq Whisper com verbose_json e retorna dict com video_id, text, segments serializados
- save_transcript() salva JSON em disco como {video_id}_transcript.json e executa UPDATE source_videos SET transcript_path
- _prepare_audio() extrai MP3 via ffmpeg (16kHz, mono, 32kbps) para arquivos >24MB com cleanup no finally
- 5/5 testes em test_transcriber.py passando; 22/28 testes totais (6 RED em selector são Wave 0 intencional de Plan 03)

## Task Commits

1. **GREEN: implement transcriber.py** - `fd7c08a` (feat)

**Plan metadata:** (a ser adicionado)

_Note: TDD plan com Wave 0 confirmado RED no Plan 01. Este plan executa apenas a fase GREEN._

## Files Created/Modified

- `clip-processor/src/transcriber.py` - Implementação completa: transcribe_video, save_transcript, _prepare_audio

## Decisions Made

- try/except amplo captura qualquer falha Groq e retorna None — sem propagar exception ao chamador
- Cleanup de audio_path temporario no bloco finally garante remoção mesmo em caso de exception durante transcrição
- _prepare_audio retorna tuple (path, bool) onde bool sinaliza se chamador deve deletar o arquivo

## Deviations from Plan

None - plan executado exatamente como escrito.

## Issues Encountered

None.

## User Setup Required

None - nenhuma configuração externa requerida. GROQ_API_KEY já configurada no .env (Phase 01 Plan 03).

## Next Phase Readiness

- AI-01 (transcriber.py) completo e testado
- Plan 03-03 (selector.py GREEN) pode iniciar imediatamente — 6 testes RED já existem em test_selector.py
- Pipeline de transcrição pronto para integração com o daemon de aquisição (Phase 02)

---
*Phase: 03-ia-transcri-o-e-sele-o*
*Completed: 2026-06-18*
