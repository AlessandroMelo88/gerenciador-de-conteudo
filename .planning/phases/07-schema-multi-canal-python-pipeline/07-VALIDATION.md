---
phase: 7
slug: schema-multi-canal-python-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-22
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (com pytest-mock) |
| **Config file** | `clip-processor/pytest.ini` |
| **Quick run command** | `docker exec clip-processor python -m pytest tests/test_quota_manager.py tests/test_publisher.py tests/test_rss_poller.py tests/test_video_processor.py -x -q` |
| **Full suite command** | `docker exec clip-processor python -m pytest -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec clip-processor python -m pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `docker exec clip-processor python -m pytest -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 7-01-01 | 01 | 1 | MCAN-03 | unit | `pytest tests/test_quota_manager.py -x -k channel_id` | ❌ W0 | ⬜ pending |
| 7-01-02 | 01 | 1 | MCAN-01 | unit | `pytest tests/test_uploader.py -x -k channel_slug` | ❌ W0 | ⬜ pending |
| 7-02-01 | 02 | 1 | COPY-03 | unit | `pytest tests/test_rss_poller.py -x -k blacklist` | ❌ W0 | ⬜ pending |
| 7-02-02 | 02 | 1 | MCAN-02 | unit | `pytest tests/test_rss_poller.py -x -k target_niche` | ❌ W0 | ⬜ pending |
| 7-03-01 | 03 | 2 | COPY-01 | unit | `pytest tests/test_video_processor.py -x -k watermark` | ❌ W0 | ⬜ pending |
| 7-03-02 | 03 | 2 | COPY-01 | unit | `pytest tests/test_video_processor.py -x -k watermark_missing` | ❌ W0 | ⬜ pending |
| 7-04-01 | 04 | 2 | COPY-02 | unit | `pytest tests/test_metadata_generator.py -x -k credits` | ❌ W0 | ⬜ pending |
| 7-05-01 | 05 | 3 | MCAN-02 | unit | `pytest tests/test_publisher.py -x -k destination_channel` | ❌ W0 | ⬜ pending |
| 7-05-02 | 05 | 3 | MCAN-04 | unit | `pytest tests/test_publisher.py -x -k multi_canal` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_quota_manager.py` — adicionar testes com `channel_id` parameter (MCAN-03)
- [ ] `tests/test_uploader.py` — adicionar testes com `channel_slug` parameter (MCAN-01)
- [ ] `tests/test_publisher.py` — adicionar `destination_channel_id` ao `SAMPLE_CLIP` e testes multi-canal (MCAN-02, MCAN-04)
- [ ] `tests/test_video_processor.py` — adicionar testes de `overlay_watermark` com mocker de subprocess (COPY-01)
- [ ] `tests/test_metadata_generator.py` — adicionar testes de `append_credits()` (COPY-02)
- [ ] `tests/test_rss_poller.py` — adicionar testes de blacklist guard no SELECT (COPY-03)

*Todos são extensões de arquivos existentes — nenhum arquivo de teste novo necessário.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Watermark visível no vídeo MP4 final | COPY-01 | Verificação visual do overlay no vídeo gerado | Assistir o arquivo MP4 exportado e confirmar logo no canto superior direito |
| Clip de nicho 'futebol' publicado no canal correto | MCAN-02 | Requer canal YouTube real configurado + OAuth ativo | Verificar `destination_channel_id` na tabela `generated_clips` após execução real |
| Token OAuth por canal gera `token-{slug}.json` | MCAN-01 | Requer interação com Google OAuth consent screen | Executar `python -m src.youtube_oauth --channel futebol-em-cortes` e verificar arquivo gerado |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
