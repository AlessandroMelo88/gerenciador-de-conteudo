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
