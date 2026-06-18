---
phase: 2
slug: aquisicao-de-videos
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-18
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-mock |
| **Config file** | `clip-processor/pytest.ini` — Wave 0 installs |
| **Quick run command** | `pytest clip-processor/tests/ -x -q` |
| **Full suite command** | `pytest clip-processor/tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest clip-processor/tests/ -x -q`
- **After every plan wave:** Run `pytest clip-processor/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-W0-01 | W0 | 0 | ACQU-01 | unit | `pytest clip-processor/tests/test_rss_poller.py -x` | ❌ W0 | ⬜ pending |
| 2-W0-02 | W0 | 0 | ACQU-02 | unit | `pytest clip-processor/tests/test_downloader.py -x` | ❌ W0 | ⬜ pending |
| 2-W0-03 | W0 | 0 | ACQU-02 | unit | `pytest clip-processor/tests/test_downloader.py::test_disk_space_guard -x` | ❌ W0 | ⬜ pending |
| 2-W0-04 | W0 | 0 | ACQU-02 | unit | `pytest clip-processor/tests/test_downloader.py::test_partial_cleanup -x` | ❌ W0 | ⬜ pending |
| 2-W0-05 | W0 | 0 | ACQU-03 | unit | `pytest clip-processor/tests/test_dedup.py::test_redis_hit -x` | ❌ W0 | ⬜ pending |
| 2-W0-06 | W0 | 0 | ACQU-03 | unit | `pytest clip-processor/tests/test_dedup.py::test_redis_fallback -x` | ❌ W0 | ⬜ pending |
| 2-W0-07 | W0 | 0 | ORC-02 | unit | `pytest clip-processor/tests/test_db.py::test_status_update -x` | ❌ W0 | ⬜ pending |
| 2-W0-08 | W0 | 0 | ORC-02 | unit | `pytest clip-processor/tests/test_db.py::test_recover_stuck_downloads -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `clip-processor/tests/__init__.py` — pacote de testes
- [ ] `clip-processor/tests/conftest.py` — fixtures compartilhadas (mock redis, mock pymysql, sample RSS feed XML)
- [ ] `clip-processor/tests/test_rss_poller.py` — cobre ACQU-01
- [ ] `clip-processor/tests/test_downloader.py` — cobre ACQU-02
- [ ] `clip-processor/tests/test_dedup.py` — cobre ACQU-03
- [ ] `clip-processor/tests/test_db.py` — cobre ORC-02
- [ ] `clip-processor/pytest.ini` — configuração do pytest
- [ ] `pytest` e `pytest-mock` adicionados ao `requirements.txt`

*Sem infraestrutura de testes existente — Wave 0 cria tudo do zero.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RSS feed real detecta vídeos novos dentro de 6h | ACQU-01 | Requer canal YouTube real com atividade | Adicionar canal a `source_channels`, aguardar poll, checar `source_videos` |
| Download 720p real de vídeo YouTube | ACQU-02 | Requer rede e conta YouTube | `docker logs clip-processor` após poll detectar vídeo pendente |
| `entry.yt_videoid` funciona com feed real | ACQU-01 | Campo feedparser namespace não testável sem feed real | Logar `entry.yt_videoid` em primeiro poll real, comparar com URL do vídeo |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
