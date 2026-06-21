# Pitfalls Research: Canal de Cortes v2.0

**Researched:** 2026-06-21
**Scope:** v2.0 additions — multi-channel YouTube publishing, Laravel/Filament panel, Telegram bot webhook, copyright protection, Mac Docker to dedicated server migration.
**Note:** v1.0 pitfalls (disk space, Whisper timeout, subtitle format, prompt calibration) are documented separately in the original PITFALLS.md. This document covers ONLY the v2.0 additions.

---

## Multi-Channel YouTube Publishing

### Pitfall: Quota Cega — Two Channels Share One Pool

**Risk:** CRITICAL. Multiple OAuth tokens authenticating through the same Google Cloud project all draw from the same 10,000-unit/day quota. With 2 channels at 3 uploads/day each = 6 uploads = 9,600 units. Any additional API call (video.list for status checks, thumbnails.set) pushes you over the limit and blocks ALL uploads for the rest of the day on BOTH channels.

**Why it happens:** Quota belongs to the GCP project, not to the OAuth credential or the YouTube channel. This is counterintuitive — creating a second OAuth client ID inside the same project gives you zero additional quota.

**Prevention:**
- Create a separate Google Cloud Project per YouTube channel (`canal-futebol-project`, `canal-podcasts-project`).
- Each project gets its own independent 10,000 units/day.
- Store each project's `client_secret.json` and `token.json` with the channel ID in the filename: `token_UC1234.json`.
- The Python publisher must select the correct token file based on which channel the clip belongs to (`destination_channel_id` field in `generated_clips`).

**Warning signs:** HTTP 403 `quotaExceeded` errors appearing mid-day while both channels have remaining upload slots — this signals shared quota exhaustion.

**Phase to address:** Phase 7 (Multi-canal) — must be resolved before any second channel goes live.

---

### Pitfall: OAuth App in Testing Mode Breaks Weekly

**Risk:** HIGH. Refresh tokens for OAuth apps still in "Testing" mode (not verified by Google for production) expire after 7 days. The automation stops uploading silently every Monday morning until someone manually re-runs the OAuth flow.

**Why it happens:** Google's OAuth policy restricts unverified apps to short-lived tokens specifically for `youtube.upload` scope, which is classified as a sensitive scope requiring verification.

**Prevention:**
- Submit Google Cloud Project for "Production" verification BEFORE going live with automation. Required documents: privacy policy URL, OAuth consent screen description, demo video of the auth flow.
- Timeline: 2–4 weeks for Google review. Start the verification request immediately when the first channel is set up.
- Apps created after July 28, 2020 that haven't passed a compliance audit can ONLY upload videos as private — this will silently break the pipeline since videos appear to upload successfully but are never public.
- Interim: Add a Redis key `oauth_authorized_at:<channel_id>` and a daily check that alerts via Telegram if token age > 5 days.

**Warning signs:** Upload calls return HTTP 200, MySQL status becomes `published`, but the video is actually private on YouTube. Requires checking `video.status.privacyStatus` after upload.

**Phase to address:** Phase 7 setup — handle before any automated public upload.

---

### Pitfall: Routing Clip to Wrong Channel Destroys Niche

**Risk:** HIGH. A podcast clip published on the futebol channel (or vice versa) alienates the audience, tanks watch time, and damages the channel's algorithmic positioning. With automation running at night, this can happen for 3 clips before anyone notices.

**Why it happens:** The `source_channels` table in v1.0 has no `niche` or `destination_channel_id` column. When Python publisher selects `WHERE status='approved' LIMIT 3`, all clips compete in the same queue regardless of niche.

**Prevention:**
- Add `niche ENUM('futebol', 'podcasts_variedades')` to `source_channels`.
- Add `destination_channel_id VARCHAR(50)` to `generated_clips` (populated when the clip is created, inherited from source channel's niche mapping).
- The publisher must filter: `WHERE status='approved' AND destination_channel_id = ?` and run a separate pass per channel.
- The Filament panel's channel creation form must require selecting a niche before saving.

**Warning signs:** Mix of clip titles in one channel's dashboard (a futebol clip appearing in a podcast channel's uploads).

**Phase to address:** Phase 7 — must be part of the DB migration that extends `source_channels` and `generated_clips`.

---

### Pitfall: Per-Channel Upload Counter Not Isolated

**Risk:** MEDIUM. The v1.0 Redis counter `clips:upload_count` is a single global counter. With 2 channels, the counter hits 6 and blocks all further uploads even if one channel has only uploaded 1 clip and has 2 more slots available.

**Prevention:**
- Change Redis key to `clips:upload_count:<channel_id>` (e.g., `clips:upload_count:UCfutebol123`).
- Reset logic must reset ALL per-channel keys at midnight BRT, not a single global key.
- Publish quota at 3/day per channel, enforced independently.

**Phase to address:** Phase 7 — Redis key naming change required in `publisher.py`.

---

## Laravel + Existing Python DB

### Pitfall: Filament Auto-Generated Resources Break on ENUM Columns

**Risk:** HIGH. The `generated_clips.status` ENUM and `source_videos.status` ENUM are the central state machine for the entire pipeline. Running `php artisan make:filament-resource GeneratedClip --generate` silently skips ENUM columns — they appear as blank text inputs in Filament forms, allowing operators to type arbitrary invalid strings that corrupt the pipeline state.

**Why it happens:** Documented Filament limitation: `--generate` does not handle ENUM columns. It generates a plain `TextInput` or skips the field entirely.

**Prevention:**
- Never use `--generate` for tables with ENUMs; build the Filament resource manually.
- Use `Forms\Components\Select::make('status')->options([...])` with the exact ENUM values.
- Add a MySQL-level CHECK constraint or application-level validation to reject values outside the ENUM set from Laravel.
- For the dashboard, use a read-only `TextColumn` with color badges (`->badge()->color(fn($state) => match($state) { 'published' => 'success', 'failed' => 'danger', ... })`).

**Warning signs:** Filament form saves a clip with `status = "Published"` (capital P) instead of `"published"`, which is invisible in the UI but invisible to the Python pipeline's `WHERE status='approved'` query.

**Phase to address:** Phase 8 (Laravel/Filament panel) — resource definitions must be hand-crafted for all tables.

---

### Pitfall: Laravel Eloquent Assumes `updated_at` and Laravel Timestamps — Python Doesn't Write Them

**Risk:** MEDIUM. Laravel Eloquent automatically manages `created_at` and `updated_at`. The existing Python pipeline uses raw SQL (`UPDATE generated_clips SET status=... WHERE id=?`) without touching `updated_at`. When Filament displays records, sorting by `updated_at` or showing "last updated" will show incorrect stale timestamps for records Python modified.

**Why it happens:** Python's SQLAlchemy raw queries don't trigger Laravel's Eloquent ORM timestamp management. They are completely separate applications.

**Prevention:**
- In Python's SQL updates, explicitly include `updated_at = NOW()` in every UPDATE statement: `UPDATE generated_clips SET status='published', updated_at=NOW() WHERE id=?`.
- Review all UPDATE statements in `publisher.py`, `pipeline_runner.py`, and any other Python modules that write to these tables.
- In Filament models, use `$timestamps = true` (default) but verify the column names match (`updated_at`, not `modified_at` or `last_updated_at`).

**Phase to address:** Phase 8 — audit all Python UPDATE queries before connecting Filament.

---

### Pitfall: Laravel Writes Conflict with Python Pipeline Mid-Transaction

**Risk:** MEDIUM. A Filament operator approves a clip (Laravel writes `status='approved'`) while the Python pipeline is simultaneously reading pending clips in a SELECT loop. If the Python worker picks up the clip before the approval is committed, or worse, updates the same row, the status can flip back to `pending` or `failed` depending on race conditions.

**Why it happens:** Two separate processes (PHP/Laravel and Python) writing to the same MySQL rows with no distributed lock.

**Prevention:**
- Python publisher must use `SELECT ... FOR UPDATE` (pessimistic lock) when claiming a clip for uploading, inside a transaction: `BEGIN; SELECT id FROM generated_clips WHERE status='approved' LIMIT 1 FOR UPDATE; UPDATE ... SET status='uploading'; COMMIT;`.
- Laravel Filament should use `lockForUpdate()` when changing status from the panel: `GeneratedClip::lockForUpdate()->find($id)->update(['status' => 'approved'])`.
- Define a state machine rule: only the Python publisher transitions `approved → uploading → published`. Laravel/operator can only transition `pending → approved` or `pending → rejected`. Document this boundary clearly.

**Warning signs:** `published` clips reappearing as `pending` in the dashboard, or clips stuck in `uploading` status permanently (Python crashed after taking the lock).

**Phase to address:** Phase 8 — must be addressed in both Python and Laravel code simultaneously.

---

### Pitfall: Filament Admin Panel Exposed Without Auth on Production Server

**Risk:** CRITICAL. Laravel Filament, when installed with `php artisan filament:install --panels`, creates an `/admin` route that by default requires a `User` model with the `FilamentUser` interface. If the User table is empty (no admin user seeded) or the auth guard is misconfigured, the panel may be accessible without credentials in some configurations.

**Why it happens:** Filament delegates auth to Laravel's guard. If the Laravel `users` table is in a different database than `clips_automation`, or the connection config is wrong, auth falls back silently.

**Prevention:**
- Run `php artisan make:filament-user` during Phase 8 setup to seed the admin user before deploying to server.
- Add nginx-level basic auth as a second layer: protect `/admin` with HTTP basic auth in nginx before the request even reaches PHP.
- Use `AllowedIPs` middleware in `FilamentServiceProvider` to restrict panel access to the server's LAN IP only.
- Never expose Filament on port 80/443 to the public internet without both application auth AND network-level restriction.

**Phase to address:** Phase 8 and Deployment phase — must be done before the panel is accessible on the production server.

---

### Pitfall: Python File Paths in MySQL are Docker-Relative, Laravel Sees a Different Filesystem

**Risk:** MEDIUM. The Python pipeline stores absolute paths in MySQL: `clip_path = '/clips/UC123/clip_45.mp4'`. These are Docker volume paths inside the `clip-processor` container. When Laravel/Filament tries to render a preview or download link, it uses a different container (or host path) and the file is not found at that path.

**Why it happens:** Docker volume mounts are container-scoped. `/clips/` inside `clip-processor` maps to `./docker/clips/` on the host, but Laravel (in its own container) doesn't have that mount unless explicitly configured.

**Prevention:**
- Mount the same clip/thumbnail volumes to the Laravel container (read-only): `volumes: - ./docker/clips:/var/www/html/storage/app/clips:ro`.
- In Filament, construct public URLs via a Laravel route that streams the file, not via direct filesystem path from the database.
- Store paths as relative (`clips/UC123/clip_45.mp4`) in MySQL, not absolute. Both Python and Laravel construct the absolute path from a configured base directory.

**Phase to address:** Phase 8 — define the shared volume strategy in `docker-compose.yml` during Laravel setup.

---

## Telegram Bot Webhook

### Pitfall: Webhook Receives Duplicate Updates on Server Errors

**Risk:** HIGH. If Laravel returns HTTP 500 (or takes > 60 seconds to process a command) on a webhook call, Telegram retries the update. The bot will process the same `/aprovar 45` command twice, resulting in two notifications being sent. If the command has side effects (status change, file deletion), running it twice can corrupt state.

**Why it happens:** Telegram webhook delivery guarantee is "at least once." Any non-2xx response or timeout triggers exponential backoff retries, eventually stopping updates entirely after repeated failures.

**Prevention:**
- Store processed `update_id` values in a `telegram_updates` table (or Redis SET) and check before processing: `if (Redis::sIsMember('telegram:processed_updates', $update->updateId)) return response('OK', 200);`.
- Always return HTTP 200 immediately, then process asynchronously via Laravel Queue: `ProcessTelegramUpdate::dispatch($update)->onQueue('telegram')`.
- Set webhook timeout in the `setWebhook` call: `max_connections=1` for a single-user bot to prevent Telegram from opening parallel connections.
- Monitor the Laravel queue worker — if the worker crashes, updates accumulate in the queue and Telegram eventually stops retrying (silent failure).

**Warning signs:** Operator receives the same notification twice, or clip status is `rejected` when it was approved (double command execution with conflicting operations).

**Phase to address:** Phase 9 (Telegram bot no Laravel) — idempotency must be built in from day one, not added later.

---

### Pitfall: Webhook Registration Breaks When IP Changes on Server

**Risk:** HIGH. Telegram webhook is registered once with `setWebhook(url='https://alessandromelo.com.br/telegramcanal')`. If the dedicated server gets a new IP (ISP change, server migration, DHCP), the webhook URL must still resolve. But if the SSL certificate is issued for the old IP or the DNS hasn't propagated, Telegram stops delivering updates silently with no alert.

**Why it happens:** Telegram does not notify the bot owner when webhook delivery fails — it silently stops after max retries. The bot appears to be running but receives no updates.

**Prevention:**
- Use a domain name (`alessandromelo.com.br`) with Let's Encrypt, not a bare IP address, for the webhook URL. Domain-based certificates survive IP changes if DNS is updated.
- Add a `/healthcheck` route in Laravel that checks webhook status via `getWebhookInfo` and alerts if `last_error_date` is recent.
- Set up a cron job that calls `getWebhookInfo` daily and sends a Telegram notification if `pending_update_count > 50` (sign of accumulation).
- Keep the `setWebhook` command in a deployment script so re-registration is one command, not a manual curl.

**Warning signs:** Operator sends `/status` and gets no response; `getWebhookInfo` shows `last_error_message: "SSL error"` or `last_error_date` is recent.

**Phase to address:** Phase 9 — include webhook health check in the deployment runbook.

---

### Pitfall: Telegram API 7.2 Requires TLS 1.3 — Old Server Configs Fail

**Risk:** MEDIUM. Telegram API 7.2 (October 2025) may enforce TLS 1.3 minimum for webhooks. A server with OpenSSL 1.0 or an nginx config specifying only `ssl_protocols TLSv1.2` will cause Telegram to reject the webhook with an SSL error.

**Prevention:**
- Nginx SSL config must include: `ssl_protocols TLSv1.2 TLSv1.3;` (allow both for compatibility, TLS 1.3 preferred).
- Test webhook acceptance with: `openssl s_client -tls1_3 -connect alessandromelo.com.br:443`.
- Use Let's Encrypt (Certbot) which defaults to modern TLS configs.
- Verify the Common Name (CN) or Subject Alternative Name (SAN) of the certificate matches the webhook domain exactly.

**Phase to address:** Deployment phase — nginx config must be validated before webhook registration.

---

### Pitfall: n8n Still Running Telegram Bot in Parallel After Migration

**Risk:** MEDIUM. The v1.0 system uses Cloudflare Tunnel + n8n for the Telegram bot. If the n8n webhook for Telegram is not explicitly deleted before the Laravel webhook is registered, BOTH will receive updates. Telegram delivers each update to only one webhook, but if n8n is still registered, the Laravel bot will never receive updates.

**Why it happens:** `setWebhook` replaces the existing webhook atomically, but if n8n's Telegram trigger node is in polling mode (not webhook), both systems may attempt to consume updates simultaneously.

**Prevention:**
- Explicitly call `deleteWebhook` (or `setWebhook` with the new URL) to deregister n8n.
- Disable the n8n Telegram trigger workflow BEFORE setting up the Laravel webhook.
- Verify via `getWebhookInfo` that the registered URL is the new Laravel endpoint.
- Document the migration sequence: (1) disable n8n workflow, (2) deploy Laravel, (3) register webhook, (4) test with `/ajuda`.

**Phase to address:** Phase 9 — migration from n8n bot to Laravel bot requires explicit deregistration.

---

## Copyright Protection

### Pitfall: Content ID Claim Despite Watermark — Revenue Goes to Original Creator

**Risk:** HIGH. Adding a watermark to a clip does NOT prevent Content ID matches. YouTube's Content ID system fingerprints audio and visual content independently. A clip with 30+ seconds of audio from a Globo Sports broadcast will receive a Content ID claim regardless of any visual watermark. The revenue from that video is then redirected to Globo, not the channel.

**Why it happens:** Content ID claims are based on audio/visual fingerprinting at the file level, before YouTube even displays the video. Transformations (crop, watermark, speed change) can sometimes evade Content ID but are not reliable against major rights holders with robust fingerprint databases.

**Prevention:**
- The blacklist (`blacklist` table or `source_channels.is_blacklisted`) is more important than the watermark. Channels with Content ID registered content (Globo, SBT, Band, ESPN, Liga de Futebol, Conmebol) should NEVER be in `source_channels`.
- Prioritize podcast channels where hosts own their content and explicitly allow or encourage clips (common in Brazilian podcast culture — Podpah, Flow, etc. actively encourage cortes).
- For any channel not explicitly whitelisted, require operator approval before the first clip is published (not just before clips from that video are published).
- The watermark protects YOUR channel's content from others clipping YOU, not from original rights holders claiming your clips.

**Warning signs:** Revenue share claim appearing in YouTube Studio within hours of publishing a clip from a specific channel. Add that channel to the blacklist immediately.

**Phase to address:** Phase 10 (copyright protection) — blacklist logic must be implemented BEFORE copyright watermark, not after.

---

### Pitfall: Blacklist Check Happens Too Late in the Pipeline

**Risk:** HIGH. If the blacklist is only checked at publication time (in the publisher), the pipeline still downloads the full video, transcribes it with Groq, processes it with Claude, and cuts the clips — all before discovering the source channel is blacklisted. This wastes significant compute time and API credits.

**Why it happens:** v1.0 pipeline adds any channel in `source_channels` to the download queue. A blacklist added as a phase 10 afterthought might be enforced at the wrong step.

**Prevention:**
- Enforce blacklist at the EARLIEST step: the RSS monitor. When inserting a new video into `source_videos`, JOIN with `source_channels` and check `is_blacklisted = FALSE`. Never insert videos from blacklisted channels.
- Also check in the download step as a safety net (defense in depth).
- The Filament panel's source channel form should show a prominent warning if adding a channel that matches known high-risk patterns (major sports leagues, TV networks).

**Phase to address:** Phase 10 — modify the RSS monitor step first, then add UI affordance in Filament.

---

### Pitfall: "Fair Use" Defense Does Not Work in Brazil the Same Way as in the US

**Risk:** MEDIUM. Brazilian copyright law (Lei 9.610/1998) does not have a "Fair Use" doctrine equivalent to the US. Brazil uses "uso justo" exceptions that are much narrower: quotation for criticism and journalistic coverage are allowed, but general "transformative use" as a defense is not codified. YouTube applies US DMCA rules globally for takedowns, but in practice Brazilian rights holders (Globo, Band, ESPN Brasil) have departments dedicated to DMCA filing internationally.

**Prevention:**
- The safest legal position is: only clip content from creators who have explicitly authorized clips (opt-in authorization, not "they haven't complained yet" as implicit consent).
- Include in the description: "Corte autorizado do canal [NOME]. Acesse o conteúdo original: [link]" — this signals good faith and is required for the DMCA counter-notice defense.
- Keep clips under 60 seconds — longer clips have higher risk because they replace viewing the original.
- Avoid clips from any channel owned by or distributed through Globoplay, TVBrasil, ESPN Brasil, TNT Sports Brasil — these have active Content ID and DMCA programs.

**Phase to address:** Phase 10 — these are operational rules, not code. Must be documented in the operator runbook alongside the blacklist.

---

### Pitfall: Watermark Positioned in a Corner Gets Cropped on Some Mobile Players

**Risk:** LOW-MEDIUM. YouTube Shorts player on mobile overlays UI elements (title, description, like/comment buttons) on the right side and bottom of the video. A watermark in the bottom-right or top-right corner of a 9:16 video may be partially obscured by YouTube's own overlay UI, making it invisible for copyright attribution purposes.

**Prevention:**
- Position the watermark at top-left (x=20, y=20) or bottom-left (x=20, h-logo_h-20) — these are the least-obscured positions in the Shorts player.
- Use semi-transparent overlay (opacity 0.6-0.7) — opaque watermarks feel aggressive and may hurt watch time.
- Test on an actual phone before finalizing the FFmpeg filter parameters.
- FFmpeg example for top-left logo: `ffmpeg -i clip.mp4 -i logo.png -filter_complex "overlay=20:20" output.mp4`.

**Phase to address:** Phase 10 — test on device before production deployment.

---

## Deployment (Local Mac Docker → Dedicated Server)

### Pitfall: File Permissions Differ Between Mac Docker and Linux Docker

**Risk:** HIGH. Docker Desktop on Mac runs containers inside a lightweight Linux VM, which masks Linux file ownership — files created as `root` in a container appear owned by your Mac user on the host. On Linux, the same container creates files owned by `root:root` with permissions `644` or `755`. The Python pipeline writes clip files, and if nginx (running as `www-data`) or Laravel needs to read them, permission errors appear only on the server, never during Mac development.

**Why it happens:** Docker Desktop on Mac abstracts filesystem via FUSE/VirtioFS. Native Linux Docker exposes raw UID/GID mapping.

**Prevention:**
- In the `clip-processor` Dockerfile, add: `RUN groupadd -g 1000 appgroup && useradd -u 1000 -g appgroup appuser` and run the service as `appuser`, not root.
- Set volume directories on the host to be owned by UID 1000 before starting containers: `chown -R 1000:1000 ./docker/clips ./docker/videos ./docker/thumbnails`.
- Explicitly test on a Linux VM or the target server before considering deployment "ready."
- Add to the deployment runbook: check `ls -la ./docker/clips` after first pipeline run to confirm permissions are as expected.

**Phase to address:** Deployment phase — add to the server setup checklist.

---

### Pitfall: MySQL Data Migration Leaves Inconsistent State

**Risk:** HIGH. The existing `clips_automation` database on the Mac development machine has data (source channels, processed videos, generated clips). A naive `mysqldump` during active pipeline operation can produce an inconsistent dump — for example, a video in status `transcribing` with its transcript file not yet written, or a clip in status `uploading` that never completes.

**Prevention:**
- Before the production migration dump: set `PIPELINE_PAUSED=true` (env var that the Python pipeline checks before starting new work), wait for any in-flight jobs to complete (max 30 minutes), THEN run `mysqldump`.
- After import on the server: manually set any clips stuck in transient states (`transcribing`, `uploading`, `downloading`) back to `pending` or `failed` — these represent interrupted jobs that must be retried.
- Run schema migrations FIRST (v2.0 column additions) before importing data, or run them after import but before starting the pipeline.

**Phase to address:** Deployment phase — must be in the migration runbook.

---

### Pitfall: Cron/Scheduler Runs on Both Mac and Server Simultaneously

**Risk:** HIGH. During the transition period (running pipeline on Mac while setting up the server), both the Mac and server may have active cron jobs or Python schedulers running. Both will monitor the same RSS feeds, insert duplicate entries (deduplication via Redis will fail if they use separate Redis instances), and attempt to upload to the same YouTube channels, burning quota on duplicates.

**Prevention:**
- The Mac local system must be explicitly STOPPED before the server pipeline starts. This is not a Docker concern — it's an operational procedure.
- Add a `PIPELINE_ACTIVE_INSTANCE` key in Redis (the production Redis, not a local one). Only one instance should hold this key at a time.
- Alternatively: make the dedicated server the ONLY environment that runs the Python pipeline. The Mac development environment should only run the pipeline in manual/test mode.
- Document a "cutover checklist": stop Mac Docker compose → export data → import on server → start server compose → verify first run manually.

**Phase to address:** Deployment phase — critical operational risk during the transition window.

---

### Pitfall: YouTube OAuth Tokens Generated on Mac Won't Work on Server (Redirect URI Mismatch)

**Risk:** MEDIUM. YouTube OAuth tokens are generated by running a local auth flow (opens browser → user logs in → returns token). The `redirect_uri` in the OAuth flow is typically `http://localhost:PORT/callback`. If the `client_secret.json` has `http://localhost:8080` as the only authorized redirect URI, you cannot run the auth flow on a headless server.

**Prevention:**
- Generate OAuth tokens on the Mac (which has a browser) and securely copy the `token_*.json` files to the server. Tokens are portable — the refresh token works from any IP.
- Add the server's domain to the authorized redirect URIs in Google Cloud Console as a fallback, in case re-authorization is ever needed from the server.
- Store tokens in a location that is NOT inside the Docker volume (to survive container rebuilds): `/etc/clips-automation/secrets/token_UC123.json` on the host, mounted read-only into the container.

**Phase to address:** Phase 7 (Multi-canal setup) and Deployment phase — the multi-channel OAuth flow must be designed for server-based operation from the start.

---

### Pitfall: Let's Encrypt Certificate Renewal Breaks Telegram Webhook

**Risk:** LOW-MEDIUM. Let's Encrypt certificates expire every 90 days. Certbot auto-renews them, but the nginx reload after renewal can cause a brief (seconds) downtime. If Telegram sends an update during that window and gets a connection refused, it marks the webhook as failed and starts exponential backoff. After 15 minutes of repeated failures, Telegram stops delivering updates until the next successful delivery.

**Prevention:**
- Configure certbot's `--deploy-hook` to run `nginx -s reload` (not restart) — reload is graceful and handles existing connections.
- The idempotency system (deduplication by `update_id`) handles any duplicates from Telegram retries during brief outages.
- Monitor `getWebhookInfo.last_error_date` daily. If it's within the last 24 hours, send a Telegram alert immediately.

**Phase to address:** Deployment phase — add webhook health monitoring to the server setup.

---

## Cross-Cutting: Laravel ↔ Python Integration

### Pitfall: Filament "Delete" Button Deletes MySQL Row Without Deleting Files

**Risk:** HIGH. Filament's built-in resource management includes a delete action that by default calls `->delete()` on the Eloquent model, which removes the MySQL row. The associated files (`clip_path`, `thumbnail_path`) remain on disk, consuming space indefinitely. The Python pipeline may also attempt to process a clip whose MySQL record no longer exists, leading to orphaned file errors.

**Prevention:**
- Override the delete action in Filament to dispatch a Laravel job: `DeleteClipJob::dispatch($record)` which: (1) deletes the files, (2) deletes the MySQL row.
- Add a `GeneratedClip::deleting()` model observer that removes associated files before the row is deleted.
- For soft-deletes (recoverable deletions): use `softDeletes()` in the migration and `SoftDeletes` trait on the model. Python must check `deleted_at IS NULL` in all SELECT queries.

**Phase to address:** Phase 8 — critical to implement the observer before any operator uses the panel.

---

### Pitfall: Real-Time Pipeline Dashboard Shows Stale Data

**Risk:** MEDIUM. A Filament dashboard showing pipeline status ("5 clips pending, 1 uploading") that refreshes every page load gives a false sense of real-time monitoring. The Python pipeline can change clip status 10 times in a minute; the Filament table shows the state at the last browser refresh.

**Prevention:**
- Use Filament's built-in polling: `->poll('5s')` on the stats widget. This auto-refreshes the panel every 5 seconds without a full page reload.
- Do NOT implement WebSockets for v2.0 — overkill for a 2-channel pipeline. Polling every 5 seconds is sufficient.
- Show `updated_at` timestamp on each clip row so operators know when the status was last changed, even if they don't see the live transition.

**Phase to address:** Phase 8 — `->poll('5s')` is a one-line addition with significant UX value.

---

## Summary Risk Matrix

| Pitfall | Impact | Likelihood | Phase |
|---------|--------|------------|-------|
| Shared quota pool (two channels, one GCP project) | CRITICAL | HIGH | Ph 7 |
| OAuth app in Testing mode, tokens expire weekly | CRITICAL | HIGH | Ph 7 |
| Clips routed to wrong channel | HIGH | HIGH | Ph 7 |
| Filament breaks ENUM columns with --generate | HIGH | HIGH | Ph 8 |
| Laravel/Python race condition on clip status | MEDIUM | MEDIUM | Ph 8 |
| Telegram duplicate updates without idempotency | HIGH | HIGH | Ph 9 |
| n8n bot still active while Laravel bot registered | HIGH | MEDIUM | Ph 9 |
| Content ID claim despite watermark (blacklist missing) | HIGH | HIGH | Ph 10 |
| Fair use defense not valid in Brazil | MEDIUM | MEDIUM | Ph 10 |
| File permissions differ Mac vs Linux Docker | HIGH | HIGH | Deploy |
| Dual pipeline (Mac + server) running simultaneously | HIGH | MEDIUM | Deploy |
| OAuth redirect URI fails on headless server | MEDIUM | HIGH | Deploy |
| Filament delete leaves orphaned files | HIGH | MEDIUM | Ph 8 |
| Blacklist check happens too late in pipeline | HIGH | MEDIUM | Ph 10 |
