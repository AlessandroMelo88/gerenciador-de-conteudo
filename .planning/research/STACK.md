# Stack Research: Canal de Cortes v2.0

**Researched:** 2026-06-21
**Domain:** Laravel admin panel, Filament, Telegram Bot SDK, multi-channel YouTube OAuth, FFmpeg watermark
**Scope:** NEW additions only — existing Python pipeline (yt-dlp, Groq, Claude, FFmpeg, PyMySQL, APScheduler) is validated and unchanged.

---

## New Stack Additions

### Laravel + Filament

#### Laravel Version: 13 (not 11)

**Why 13, not 11:**
- Laravel 11 reached EOL on March 12, 2026 — no more security patches.
- Laravel 12 receives security fixes only until February 24, 2027.
- Laravel 13 (released March 17, 2026) receives bug fixes through Q3 2027 and security patches until March 2028 — the longest coverage available.
- Zero breaking changes from Laravel 12 to 13 (10-minute upgrade path).
- PHP 8.3 minimum (better performance, no legacy support burden).
- PROJECT.md listed "Laravel 11" but that is EOL. Use 13 instead.

**Confidence:** HIGH (verified via laravelversions.com and eosl.date/laravel)

#### Filament Version: 5.x

**Why 5, not 3:**
- Filament v5 (released January 16, 2026) is the current stable version.
- Filament v5 requires `illuminate/contracts ^11.28|^12.0` — also tested with Laravel 13 (multiple confirmed reports on answeroverflow and qadrlabs.com tutorials).
- Filament v5 = Filament v4 + Livewire v4 support. No API changes. New features continue to land in both v4 and v5.
- PROJECT.md specified "Filament 3" but v3 is superseded. Use v5 for Livewire v4 and forward compatibility.

**PHP requirement:** ^8.2 (Laravel 13 requires ^8.3, so PHP 8.3+ is the effective floor)

**Confidence:** HIGH (verified via filamentphp.com, laravel-news.com, packagist)

#### Core Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `laravel/framework` | `^13.0` | Framework base |
| `filament/filament` | `^5.0` | Admin panel (panels, resources, widgets, forms, tables) |
| `livewire/livewire` | `^4.0` | Reactive UI layer (Filament v5 dependency) |

**Installation:**
```bash
composer create-project laravel/laravel laravel-admin
composer require filament/filament:"^5.0"
php artisan filament:install --panels
```

#### Laravel Application Structure for This Project

```
laravel-admin/
├── app/
│   ├── Filament/
│   │   ├── Resources/
│   │   │   ├── SourceChannelResource.php    # CRUD canais-fonte
│   │   │   ├── DestinationChannelResource.php  # CRUD canais-destino
│   │   │   └── GeneratedClipResource.php    # Read-only pipeline dashboard
│   │   └── Widgets/
│   │       └── PipelineStatusWidget.php     # Contagens por status
│   ├── Models/
│   │   ├── SourceChannel.php    # maps source_channels table
│   │   ├── SourceVideo.php      # maps source_videos table
│   │   └── GeneratedClip.php   # maps generated_clips table
│   └── Http/Controllers/
│       └── TelegramWebhookController.php
├── config/
│   └── database.php   # connection "clips_automation" pointing to shared MySQL
└── routes/
    └── web.php        # POST /telegramcanal  (webhook, CSRF excluded)
```

**Confidence:** HIGH (standard Filament/Laravel structure)

---

### Telegram Bot (Laravel)

**Package:** `irazasyed/telegram-bot-sdk` `^3.16`

**Version note:** v3.16.0 (released March 23, 2026) explicitly adds Laravel 13 support. The SDK namespace remains `irazasyed/telegram-bot-sdk` at v3.x. Starting from v4.x the package moves to `telegram-bot-sdk/telegram-bot-sdk` + `telegram-bot-sdk/laravel`, but v4 is still WIP/in-development as of June 2026. Use v3.16 which is stable and Laravel 13 compatible.

**Why this over alternatives:**
- Already specified in PROJECT.md Key Decisions: "irazasyed/telegram-bot-sdk."
- Most mature PHP Telegram SDK with Laravel service provider, facade, and webhook handling built in.
- v3.x requires `illuminate/support` 9–13 (v3.16 confirmed Laravel 13 support).
- Handles: webhook registration, command routing, sendMessage, sendPhoto, inline keyboards.

**Alternative considered:** `telegram-bot-sdk/laravel ^4.0` — skip for now, still WIP.

**Confidence:** MEDIUM-HIGH (v3.16 Laravel 13 support confirmed via GitHub release; v4 status is WIP per github.com/telegram-bot-sdk/telegram-bot-sdk)

**Installation:**
```bash
composer require irazasyed/telegram-bot-sdk:"^3.16"
php artisan vendor:publish --provider="Telegram\Bot\Laravel\TelegramServiceProvider"
```

**Webhook setup:**
```php
// routes/web.php
Route::post('/telegramcanal', [TelegramWebhookController::class, 'handle'])
    ->withoutMiddleware([\App\Http\Middleware\VerifyCsrfToken::class]);
```

```php
// TelegramWebhookController.php
use Telegram\Bot\Laravel\Facades\Telegram;

public function handle(Request $request): Response
{
    $update = Telegram::commandsHandler(true);
    return response('OK');
}
```

Register webhook once on deploy:
```bash
php artisan tinker
Telegram::setWebhook(['url' => 'https://alessandromelo.com.br/telegramcanal']);
```

**SSL requirement:** Telegram requires HTTPS on port 443. The nginx proxy at `alessandromelo.com.br` covers this per PROJECT.md.

**Confidence:** HIGH for webhook pattern (verified via telegram-bot-sdk.com docs and hostman.com tutorial)

---

### YouTube Multi-Channel

**Approach: one token file per destination channel, no new library**

The existing `google-api-python-client` + `google-auth` + `google-auth-oauthlib` stack already handles OAuth 2.0. No new Python library needed.

**Pattern:**
- One-time CLI authorization per channel: run the OAuth flow in a browser once per Google account, store result as `tokens_{channel_id}.json`.
- At upload time, load the token file matching the destination channel.
- The `destination_channel_id` column in the new `destination_channels` table drives which token file to load.

**Token storage convention:**
```
/app/credentials/
├── client_secret.json           # shared OAuth client (one Google Cloud project)
├── tokens_UCfutebol123.json     # channel 1 refresh token
└── tokens_UCpodcasts456.json    # channel 2 refresh token
```

**Python snippet pattern (existing publisher.py extended):**
```python
def get_youtube_service(destination_channel_id: str):
    token_path = f'/app/credentials/tokens_{destination_channel_id}.json'
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # save updated token back
        with open(token_path, 'w') as f:
            f.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)
```

**Quota per channel:** Each destination channel has its own YouTube Data API quota (10,000 units/day per OAuth project, or create separate GCP projects for full independence). Quota tracking in Redis already uses a key per upload — extend key to include `channel_id`: `quota:{date}:{channel_id}`.

**DB change needed:** Add `destination_channels` table (see Integration Points below).

**Confidence:** HIGH — standard Google OAuth pattern, confirmed by Google's own documentation and woodyrush.com multi-channel guide.

---

### FFmpeg Watermark

**No new library.** FFmpeg already available in the clip-processor Docker container. This is a new step in `video_processor.py` between `burn_subtitles()` and `extract_thumbnail()`.

**Approach:** `filter_complex` with `overlay` filter on the already-subtitled clip.

**Key design choices:**
- Watermark is a PNG with alpha transparency (RGBA). Store at `/app/assets/watermark.png`.
- Scale watermark to ~15% of video height relative to video dimensions using `scale2ref`.
- Position: bottom-right corner with 20px margin (safe for vertical 9:16 frame).
- Apply AFTER subtitle burning so watermark sits above subtitles.
- Opacity: 70% (`colorchannelmixer=aa=0.7`) — visible but not intrusive.

**filter_complex pattern:**
```bash
ffmpeg -i subtitled_clip.mp4 -i /app/assets/watermark.png \
  -filter_complex \
    "[1]format=rgba,colorchannelmixer=aa=0.7[wm]; \
     [wm][0]scale2ref=oh*mdar:ih*0.15[wm_scaled][base]; \
     [base][wm_scaled]overlay=W-w-20:H-h-20" \
  -c:v libx264 -preset veryfast -crf 23 -c:a copy \
  watermarked_clip.mp4 -y
```

**Where it fits in process_clip():**
```
cut_clip()          → raw_clip.mp4
burn_subtitles()    → subtitled_clip.mp4
add_watermark()     → final_clip.mp4   ← NEW step
extract_thumbnail() → thumbnail.jpg    (from final_clip.mp4)
```

**New function signature:**
```python
def add_watermark(input_path: str, watermark_path: str, output_path: str) -> str:
    """Queima watermark PNG com transparência sobre o clip já legendado."""
```

**Environment variable for watermark path:**
```
WATERMARK_PATH=/app/assets/watermark.png
```
If `WATERMARK_PATH` is unset or file doesn't exist, skip the step (backward compatible).

**Confidence:** HIGH (FFmpeg overlay with scale2ref and colorchannelmixer is well-documented and stable API)

---

## Integration Points

### How Laravel Connects to clips_automation MySQL

Laravel is a separate application (separate Docker container or host process) but reads/writes the **same** MySQL instance. In `config/database.php`:

```php
'connections' => [
    'clips_automation' => [
        'driver'    => 'mysql',
        'host'      => env('CLIPS_DB_HOST', '127.0.0.1'),
        'port'      => env('CLIPS_DB_PORT', '3306'),
        'database'  => 'clips_automation',
        'username'  => env('CLIPS_DB_USER', 'clips_user'),
        'password'  => env('CLIPS_DB_PASSWORD'),
        'charset'   => 'utf8mb4',
        'collation' => 'utf8mb4_unicode_ci',
    ],
],
```

Each Eloquent model specifies `protected $connection = 'clips_automation';`.

**No separate Laravel database is needed** — all application state lives in clips_automation. No Laravel migrations needed for existing tables (add `$timestamps = false` or map `created_at`/`updated_at` explicitly where columns already exist).

### How Laravel Reads/Writes Each Table

| Table | Laravel Action | Python Pipeline Action |
|-------|---------------|----------------------|
| `source_channels` | INSERT/UPDATE/DELETE via Filament Resource | SELECT (reads rss_url, active flag) |
| `destination_channels` | INSERT/UPDATE/DELETE via Filament Resource | SELECT (reads channel_id, token path, quota) |
| `source_videos` | READ ONLY (pipeline status dashboard) | Owner: INSERT, UPDATE status |
| `generated_clips` | READ + UPDATE status (approve/reject) | Owner: INSERT, UPDATE status, UPDATE clip_path |

**Concurrency rule:** Laravel never writes to `source_videos` or `generated_clips.clip_path`. Python never writes to `source_channels` or `destination_channels`. Shared writes on `generated_clips.status` (approve/reject by Laravel, status transitions by Python) are safe because they target different ENUM values.

### New Table Required: destination_channels

```sql
CREATE TABLE IF NOT EXISTS destination_channels (
  id INT AUTO_INCREMENT PRIMARY KEY,
  youtube_channel_id VARCHAR(64) NOT NULL UNIQUE,
  channel_name VARCHAR(255) NOT NULL,
  niche VARCHAR(64) NOT NULL,           -- 'futebol', 'podcasts', etc.
  token_path VARCHAR(512) NOT NULL,     -- path to tokens_{id}.json inside container
  uploads_per_day TINYINT DEFAULT 3,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

And a migration to link `source_channels` to a niche (or directly to a `destination_channel_id`):

```sql
-- Add niche to source_channels for routing
ALTER TABLE source_channels ADD COLUMN niche VARCHAR(64) DEFAULT 'futebol';
```

### Whether Python Pipeline Needs Changes

**Python changes required (minimal):**

1. `video_processor.py` — add `add_watermark()` function and call it in `process_clip()`.
2. `publisher.py` — change `get_youtube_service()` to accept `destination_channel_id` and load the correct token file; update quota Redis key to include channel_id; SELECT `destination_channels` for routing.
3. No changes to: `rss_monitor.py`, `downloader.py`, `transcriber.py`, `selector.py`.

**Python does NOT need to know about Laravel** — they communicate only through the shared MySQL database.

---

## What NOT to Add

| What | Why Not |
|------|---------|
| Laravel migrations for existing tables | Tables already exist with data. Use Eloquent with `$table`, `$primaryKey`, `$timestamps` mapped manually. Running Laravel migrations against existing schema risks data loss or conflicts. |
| Separate Laravel database | All state is in clips_automation. A separate laravel database adds needless complexity and drift. |
| n8n for Telegram bot | PROJECT.md explicitly decided to replace n8n Telegram integration with Laravel SDK. No new n8n workflows for bot. n8n may remain for other orchestration but not for bot. |
| Filament v3 | EOL cycle — Filament v5 is current stable. v3 would require upgrading soon. |
| Laravel 11 or 12 | Laravel 11 is EOL. Laravel 12 is shorter-lived than 13. Use 13 for new project. |
| `telegram-bot-sdk/laravel ^4.0` | v4 is marked WIP/in-development on GitHub. Use stable v3.16. |
| `php-telegram-bot/core` or `nutgram/nutgram` | irazasyed/telegram-bot-sdk is already in scope per project decisions and is sufficient for notification + command use case. |
| Pusher / Laravel Echo / WebSockets | Dashboard "real-time" status can be achieved with Filament's built-in Livewire polling (every N seconds via `$refresh` or `getPollingInterval()`). No WebSocket server needed for this use case. |
| Laravel Horizon | Redis queue with Horizon adds complexity. The Python APScheduler daemon is the existing job runner. No Laravel queued jobs needed for this milestone. |
| Laravel Sanctum / Passport | No API consumers. Admin panel is internal, protected by Filament's built-in auth (email + password). |
| `google/apiclient` (PHP) | YouTube API is called from Python. Laravel only reads/writes DB, never calls YouTube API directly. |
| TikTok / Instagram libraries | Out of scope per PROJECT.md. |

---

## Confidence Summary

| Area | Level | Reason |
|------|-------|--------|
| Laravel 13 version choice | HIGH | EOL dates verified via official sources |
| Filament 5 version choice | HIGH | Packagist + Laravel News + community tutorials confirmed |
| irazasyed/telegram-bot-sdk v3.16 | MEDIUM-HIGH | v3.16.0 Laravel 13 support confirmed via GitHub release; v4 is WIP |
| Multi-channel OAuth pattern | HIGH | Standard Google OAuth 2.0 pattern, no new library |
| FFmpeg watermark filter_complex | HIGH | Stable FFmpeg API, well-documented pattern |
| Laravel connecting to existing MySQL | HIGH | Standard Laravel multi-connection config, widely used pattern |
| destination_channels schema design | MEDIUM | Logical inference from requirements; confirm column names with team |

**Research date:** 2026-06-21
**Valid until:** 2026-09-21 (90 days — Laravel/Filament major versions move slowly; SDK versions faster)

---

## Sources

- [Laravel EOL dates](https://endoflife.date/laravel) — version support timelines
- [Laravel 13 release notes](https://laravel.com/docs/13.x/releases) — official release
- [Filament v5 announcement](https://laravel-news.com/filament-5) — Laravel News
- [Filament v5 official introduction](https://filamentphp.com/insights/danharrin-filament-v5-blueprint) — Filament team
- [Filament + Laravel 13 install tutorial](https://qadrlabs.com/post/laravel-13-filament-5-crud-tutorial-build-a-blog-admin-panel-step-by-step) — confirmed install path
- [irazasyed/telegram-bot-sdk releases](https://github.com/irazasyed/telegram-bot-sdk/releases) — v3.16.0 Laravel 13 support
- [Telegram webhook + Nginx guide](https://pas7.com.ua/blog/en/telegram-bot-webhook-vps-nginx-ssl) — production setup pattern
- [FFmpeg watermark with filter_complex](https://www.mux.com/articles/add-watermarks-to-a-video-with-ffmpeg) — overlay + scale2ref patterns
- [YouTube OAuth multi-account guide](https://woodyrush.com/en/blog/youtube-oauth-setup-guide/) — token-per-channel pattern
