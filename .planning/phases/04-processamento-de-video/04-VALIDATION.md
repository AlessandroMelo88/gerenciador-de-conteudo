---
phase: 4
slug: processamento-de-video
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-18
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-mock |
| **Config file** | `clip-processor/pytest.ini` |
| **Quick run command** | `cd clip-processor && python3 -m pytest tests/test_video_processor.py tests/test_metadata_generator.py tests/test_clip_pipeline.py -v --tb=short` |
| **Full suite command** | `cd clip-processor && python3 -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~240 seconds because existing downloader retry tests sleep |

---

## Sampling Rate

- **After every task commit:** Run `cd clip-processor && python3 -m pytest tests/test_video_processor.py tests/test_metadata_generator.py tests/test_clip_pipeline.py -v --tb=short`
- **After every plan wave:** Run `cd clip-processor && python3 -m pytest tests/ -v --tb=short`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 240 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 0 | VID-01, VID-02, VID-03 | unit stubs | `python3 -m pytest tests/test_video_processor.py -v --tb=short` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 0 | VID-04 | unit stubs | `python3 -m pytest tests/test_metadata_generator.py -v --tb=short` | ❌ W0 | ⬜ pending |
| 4-01-03 | 01 | 0 | VID-01, VID-02, VID-03, VID-04 | integration stubs | `python3 -m pytest tests/test_clip_pipeline.py -v --tb=short` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | VID-01 | unit | `python3 -m pytest tests/test_video_processor.py::TestVideoProcessor::test_cut_clip_uses_ffmpeg_with_exact_timestamps -x` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 1 | VID-01 | unit | `python3 -m pytest tests/test_video_processor.py::TestVideoProcessor::test_cut_clip_outputs_1080x1920_filter -x` | ❌ W0 | ⬜ pending |
| 4-02-03 | 02 | 1 | VID-02 | unit | `python3 -m pytest tests/test_video_processor.py::TestSubtitles::test_srt_contains_shifted_segment_times -x` | ❌ W0 | ⬜ pending |
| 4-02-04 | 02 | 1 | VID-02 | unit | `python3 -m pytest tests/test_video_processor.py::TestSubtitles::test_burn_subtitles_uses_force_style -x` | ❌ W0 | ⬜ pending |
| 4-02-05 | 02 | 1 | VID-03 | unit | `python3 -m pytest tests/test_video_processor.py::TestVideoProcessor::test_thumbnail_extracted_from_clip -x` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 1 | VID-04 | unit | `python3 -m pytest tests/test_metadata_generator.py::TestMetadataGenerator::test_generate_metadata_returns_title_description_tags -x` | ❌ W0 | ⬜ pending |
| 4-03-02 | 03 | 1 | VID-04 | unit | `python3 -m pytest tests/test_metadata_generator.py::TestMetadataGenerator::test_title_is_trimmed_to_100_chars -x` | ❌ W0 | ⬜ pending |
| 4-03-03 | 03 | 1 | VID-04 | unit | `python3 -m pytest tests/test_metadata_generator.py::TestMetadataPersistence::test_update_clip_metadata_persists_fields -x` | ❌ W0 | ⬜ pending |
| 4-04-01 | 04 | 2 | VID-01, VID-02, VID-03, VID-04 | integration | `python3 -m pytest tests/test_clip_pipeline.py -v --tb=short` | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `clip-processor/src/video_processor.py` — skeleton with public interfaces
- [ ] `clip-processor/src/metadata_generator.py` — skeleton with public interfaces
- [ ] `clip-processor/tests/test_video_processor.py` — RED tests for VID-01, VID-02, VID-03
- [ ] `clip-processor/tests/test_metadata_generator.py` — RED tests for VID-04
- [ ] `clip-processor/tests/test_clip_pipeline.py` — RED tests for daemon integration

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual subtitle readability on real football footage | VID-02 | Unit tests verify command/style, not visual legibility across backgrounds | Run one real clip through Phase 4, inspect MP4 at desktop and phone size |
| FFmpeg output is accepted as YouTube Shorts-compatible media | VID-01 | Requires rendered media metadata and practical upload constraints | Run `ffprobe` on output and confirm width=1080, height=1920, video codec h264, audio aac |
| Thumbnail looks usable and not blank/transition frame | VID-03 | Frame quality is visual | Open generated `.jpg` and inspect |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 240s
- [ ] `nyquist_compliant: true` set in frontmatter after execution proves coverage

**Approval:** pending
