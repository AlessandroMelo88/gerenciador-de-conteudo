---
phase: 1
slug: infraestrutura-base
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-17
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash/shell scripts + docker compose commands |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `docker compose ps --format json` |
| **Full suite command** | `bash .planning/phases/01-infraestrutura-base/verify-phase1.sh` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker compose ps --format json`
- **After every plan wave:** Run `bash .planning/phases/01-infraestrutura-base/verify-phase1.sh`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | INFRA-01 | integration | `docker compose ps \| grep n8n` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | INFRA-01 | integration | `docker compose ps \| grep clip-processor` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | INFRA-01 | integration | `docker compose ps \| grep whisper` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | INFRA-02 | integration | `mysql -u root -e "SHOW TABLES FROM clips_automation"` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 1 | INFRA-03 | manual | N/A — YouTube channel creation | N/A | ⬜ pending |
| 1-04-01 | 04 | 1 | INFRA-04 | integration | `docker compose config \| grep -c API_KEY` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `verify-phase1.sh` — shell script with all automated checks for phase 1
- [ ] Docker external network pre-created before service start

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| YouTube channel created with verified account, banner and bio | INFRA-03 | Requires browser + Google account interaction; no API to create channel | Log into YouTube Studio and confirm channel details are filled |
| YouTube OAuth token.json generated | INFRA-04 | One-time browser OAuth flow required | Run `python oauth_setup.py`, complete browser flow, confirm token.json exists |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
