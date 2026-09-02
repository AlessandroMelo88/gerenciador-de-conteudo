---
phase: 3
slug: ia-transcri-o-e-sele-o
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-18
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-mock (já instalados) |
| **Config file** | `clip-processor/pytest.ini` |
| **Quick run command** | `cd clip-processor && pytest tests/test_transcriber.py tests/test_selector.py -v --tb=short` |
| **Full suite command** | `cd clip-processor && pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd clip-processor && pytest tests/test_transcriber.py tests/test_selector.py -v --tb=short`
- **After every plan wave:** Run `cd clip-processor && pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | AI-01, AI-02, AI-03 | schema | `mysql -u root -p < mysql/init/03-schema-migration.sql` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | AI-01 | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_transcription_returns_segments -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | AI-01 | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_transcript_saved_to_disk -x` | ❌ W0 | ⬜ pending |
| 3-02-03 | 02 | 1 | AI-01 | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_transcript_path_updated_in_db -x` | ❌ W0 | ⬜ pending |
| 3-02-04 | 02 | 1 | AI-01 | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_large_file_audio_extraction -x` | ❌ W0 | ⬜ pending |
| 3-02-05 | 02 | 1 | AI-01 | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_api_failure_marks_video_failed -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 1 | AI-02 | unit | `pytest tests/test_selector.py::TestSelectMoments::test_returns_moments_list -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 1 | AI-02 | unit | `pytest tests/test_selector.py::TestSelectMoments::test_transcript_formatted_with_timestamps -x` | ❌ W0 | ⬜ pending |
| 3-03-03 | 03 | 1 | AI-03 | unit | `pytest tests/test_selector.py::TestInsertMoments::test_score_7_inserted -x` | ❌ W0 | ⬜ pending |
| 3-03-04 | 03 | 1 | AI-03 | unit | `pytest tests/test_selector.py::TestInsertMoments::test_score_6_discarded -x` | ❌ W0 | ⬜ pending |
| 3-03-05 | 03 | 1 | AI-03 | unit | `pytest tests/test_selector.py::TestInsertMoments::test_overlap_keeps_higher_score -x` | ❌ W0 | ⬜ pending |
| 3-03-06 | 03 | 1 | AI-03 | unit | `pytest tests/test_selector.py::TestInsertMoments::test_max_3_moments -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `clip-processor/tests/test_transcriber.py` — stubs para AI-01 (5 testes)
- [ ] `clip-processor/tests/test_selector.py` — stubs para AI-02 e AI-03 (6 testes)
- [ ] `mysql/init/03-schema-migration.sql` — ADD COLUMN `transcript_path VARCHAR(500)` em `source_videos`, ALTER ENUM para incluir `pending_cut` em `generated_clips`, ADD COLUMN `reason TEXT` em `generated_clips`
- [ ] `clip-processor/src/transcriber.py` — módulo principal AI-01 (skeleton com interface)
- [ ] `clip-processor/src/selector.py` — módulo principal AI-02 + AI-03 (skeleton com interface)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Groq API processa MP4 real de podcast >25MB via extração de áudio | AI-01 | Requer arquivo real e chamada de API externa | Baixar vídeo de teste 1h, executar transcriber com arquivo >25MB, verificar log de extração de áudio |
| Claude Haiku retorna JSON válido com momentos para transcrição PT-BR real | AI-02 | Requer chamada real à API Anthropic com conteúdo PT-BR | Executar selector com transcrição de teste, verificar formato JSON da resposta |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
