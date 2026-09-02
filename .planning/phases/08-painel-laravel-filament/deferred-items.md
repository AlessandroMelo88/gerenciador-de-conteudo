# Deferred Items — Phase 08

## Plan 08-02

### Pre-existing test failures unrelated to this plan's scope

**Found during:** Task 3 regression check (`pytest tests/ --ignore=tests/test_internal_api.py --ignore=tests/test_uploader_expired.py`).

**Failures:**
- `tests/test_quota_manager.py::TestCanUpload::test_before_window_start`
- `tests/test_quota_manager.py::TestCanUpload::test_after_window_end`
- `tests/test_quota_manager.py::TestCanUpload::test_outside_window_midnight`

**Root cause:** `clip-processor/src/quota_manager.py` has an uncommitted change (present in working tree before this plan started, not modified by Plan 08-02) that adds an `UPLOAD_WINDOW_BYPASS` env var check in `_is_upload_window()`. The `wordpress/.env` file has `UPLOAD_WINDOW_BYPASS=true`, which makes `can_upload()` always return `True` regardless of the hour, breaking the 3 window-boundary tests.

**Scope decision:** Out of scope for Plan 08-02 (SQL migration + internal_api skeleton + RED tests). Not caused by any file this plan modifies (`mysql/init/07-panel-oauth-flag-migration.sql`, `clip-processor/requirements.txt`, `clip-processor/src/internal_api.py`, `clip-processor/tests/test_internal_api.py`, `clip-processor/tests/test_uploader_expired.py`). Left unfixed per SCOPE BOUNDARY rule.

**Other uncommitted pre-existing working-tree changes observed at plan start** (also out of scope, not touched):
- `clip-processor/src/pipeline_runner.py`
- `clip-processor/src/rss_poller.py`
- `clip-processor/src/selector.py`
- `clip-processor/src/transcriber.py`
- `clip-processor/src/uploader.py` (removed `youtube.readonly` scope — unrelated to `_load_credentials`/RefreshError work targeted by Plan 08-06)
- `clip-processor/src/youtube_oauth.py`
- `.planning/REQUIREMENTS.md`

**Recommendation:** Operator/next plan should review and either commit or discard these pre-existing changes before Plan 08-06/08-07 touch the same files, to avoid conflating unrelated diffs.

## Plan 08-06

### Pre-existing Laravel test failures unrelated to this plan's scope

**Found during:** Task 2 full-suite regression check (`docker exec php bash -c "cd /var/www/html/painel && php artisan test"`).

**Failures (6, all pre-existing — none caused by files this plan touched):**
- `Tests\Feature\ClipApprovalActionTest` — 4 tests (404 on `/admin/clips/{id}/approve|reject` — routes don't exist yet, drives Plan 08-08)
- `Tests\Feature\DashboardPollingTest` — 2 tests (no `wire:poll.5s` / quota widget rendered yet — drives Plan 08-09)

**Root cause:** These routes/widgets are not in scope of Plan 08-06 (uploader RefreshError + DestinationChannelResource). They are explicitly assigned to Plans 08-08 (clip approval/rejection action) and 08-09 (dashboard widgets) per `08-RESEARCH.md`/`08-VALIDATION.md`.

**Scope decision:** Out of scope for Plan 08-06. Confirmed unchanged before/after this plan's commits — `DestinationChannelResourceTest` (2/2) and `DestinationChannelOauthStatusTest` (3/3) are the only tests that flipped state (RED→GREEN). `SourceChannelResourceTest` (3/3) remains GREEN with zero regression.

### Python full-suite confirmation (post Plan 08-06)

`docker exec clip-processor pytest tests/ --ignore=tests/test_internal_api.py -q` → **3 failed, 128 passed** (the 3 failures are the same pre-existing `test_quota_manager.py::TestCanUpload` failures documented above under Plan 08-02 — unrelated to `uploader.py`/`RefreshError` work). `test_uploader_expired.py` is included in the 128 passed.

## Plan 08-08

### `ClipApprovalActionTest`/`DashboardPollingTest` now resolved

The 6 pre-existing failures documented above under Plan 08-06 (4 `ClipApprovalActionTest` + 2 `DashboardPollingTest`) are **resolved by this plan**: 4 widgets created, registered via `discoverWidgets`, and `POST /admin/clips/{id}/approve|reject` routes added. Full Laravel suite: **25 passed, 0 failed**.

### Python full-suite confirmation (post Plan 08-08)

`docker exec clip-processor pytest tests/ -q` → **3 failed, 134 passed**. The 3 failures are the same pre-existing `test_quota_manager.py::TestCanUpload` failures documented above under Plan 08-02 (`UPLOAD_WINDOW_BYPASS=true` in `wordpress/.env`) — no file touched by Plan 08-08 affects `quota_manager.py`. Zero regression attributable to this plan.

### Applied pre-existing migration `mysql/init/05-controle-manual-migration.sql` (Rule 3 — blocking)

**Found during:** Task 2, first run of `ClipApprovalActionTest` — the `approve` route failed with `SQLSTATE[01000]: Data truncated for column 'status'` because the live `clips_automation.generated_clips.status` ENUM in this environment only had `('pending_cut','pending','cutting','publishing','published','failed')`, missing `approved`/`rejected` (added by Phase 6's `05-controle-manual-migration.sql`, which exists in the repo but had never been applied to this MySQL instance/volume).

**Fix:** Applied the existing, already-committed migration file directly: `docker exec -i mysql mysql -u clips_user -p${CLIPS_DB_PASSWORD} clips_automation < mysql/init/05-controle-manual-migration.sql`. No new SQL file created — the migration was already correct and idempotent (`MODIFY COLUMN` with the full target ENUM); it just hadn't been run against this database instance/volume.

**Verification:** `SHOW COLUMNS FROM generated_clips LIKE 'status'` now shows the full 8-value ENUM including `approved`/`rejected`. `ClipApprovalActionTest` 4/4 GREEN afterward.

**Impact:** Database schema change only, no code file modified — not committed (matches the established pattern for out-of-repo/infra-only changes in this phase, e.g. `08-01-SUMMARY.md`/`06-06-SUMMARY.md`).
