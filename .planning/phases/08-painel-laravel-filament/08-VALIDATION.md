---
phase: 8
slug: painel-laravel-filament
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-01
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pest 3.x / phpunit 11.x (Laravel side) + pytest 7.x (Python HTTP sidecar) |
| **Config file** | `panel/phpunit.xml` (Laravel) · `clip-processor/pytest.ini` (Python) |
| **Quick run command** | `docker exec -T php php artisan test --filter=Panel --parallel` |
| **Full suite command** | `docker exec -T php php artisan test && docker exec -T clip-processor pytest tests/test_internal_api.py -v` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `{quick run command}`
- **After every plan wave:** Run `{full suite command}`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

*Populated by planner — one row per task with automated verification command. Rows referencing Wave 0 files use `❌ W0` in "File Exists" column until Wave 0 completes.*

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 8-XX-XX | XX | N | PANEL-XX | unit/feature | `{command}` | ✅ / ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `panel/tests/Feature/AuthGuardTest.php` — stubs for PANEL-01 (redirect-to-login on unauthenticated requests)
- [ ] `panel/tests/Feature/SourceChannelResourceTest.php` — stubs for PANEL-02 (form creates row in `source_channels`)
- [ ] `panel/tests/Feature/DestinationChannelResourceTest.php` — stubs for PANEL-02/PANEL-03 (form + OAuth status badge)
- [ ] `panel/tests/Feature/DashboardPollingTest.php` — stubs for PANEL-04 (polling wired to 5s)
- [ ] `panel/tests/Feature/ClipApprovalActionTest.php` — stubs for PANEL-05 (approve/reject writes to `generated_clips`)
- [ ] `panel/tests/Pest.php` + `panel/phpunit.xml` — Pest/PHPUnit bootstrap for panel/
- [ ] `clip-processor/tests/test_internal_api.py` — stubs for internal HTTP sidecar (resolve-channel, reject-clip)
- [ ] `clip-processor/tests/test_uploader_expired.py` — stubs for `RefreshError` → `oauth_expired` flag

*Wave 0 installs Pest/PHPUnit under `panel/` and creates all stub files above before Wave 1 executes.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Login page renders correctly in browser and rejects wrong password | PANEL-01 | Visual + browser session cookie behavior | 1) `docker compose up` 2) Open `https://canaldecortes.test/admin` 3) Confirm redirect to `/admin/login` 4) Enter wrong password → error message 5) Enter correct → dashboard |
| Dashboard actually re-renders every 5s without page reload | PANEL-04 | Livewire polling is a runtime browser behavior; unit tests can only assert the polling attribute is set | 1) Open dashboard 2) In another tab insert row into `source_videos` via `docker exec -T mysql mysql -e "..."` 3) Observe dashboard update within 5s 4) Confirm no full-page reload (network tab shows Livewire XHR only) |
| OAuth badge transitions authorized → expired after real token revocation | PANEL-03 | Requires real Google OAuth token revocation flow | 1) Authorize a destination channel via `youtube_oauth` CLI 2) Confirm badge = authorized 3) Revoke access at `myaccount.google.com` 4) Trigger an upload attempt 5) Confirm badge flips to expired within one poll cycle |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
