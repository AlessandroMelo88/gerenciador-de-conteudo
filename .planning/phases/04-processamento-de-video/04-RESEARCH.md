# Phase 4: Processamento de Video - Research

**Researched:** 2026-06-18
**Domain:** FFmpeg video processing, subtitle burn-in, thumbnail extraction, Claude Haiku metadata generation
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| VID-01 | FFmpeg corta o clip nos timestamps selecionados pela IA e faz resize para 9:16 1080x1920 | `ffmpeg -ss {start} -to {end} -i input -vf scale/crop/pad/fps -c:v libx264 -c:a aac` |
| VID-02 | Legendas geradas pelo Whisper sao queimadas no clip final com fonte legivel e bordas | Gerar `.srt` filtrado pelos segmentos do transcript e usar `subtitles=...:force_style='Fontsize=...,Outline=...'` |
| VID-03 | Thumbnail automatica e extraida de frame do clip | `ffmpeg -ss {middle_or_best_second} -i clip.mp4 -frames:v 1 thumbnail.jpg` |
| VID-04 | Claude Haiku gera titulo, descricao e tags otimizados para YouTube SEO futebol/PT-BR | Novo modulo `metadata_generator.py` com structured outputs e update de `generated_clips.title/description/tags` |
</phase_requirements>

---

## Summary

Phase 4 consumes rows from `generated_clips` created by Phase 3 with `status = 'pending_cut'`. Each row already has `source_video_id`, `start_time`, `end_time`, `score`, and `reason`. The source video path and transcript path are available by joining `generated_clips.source_video_id` to `source_videos.id`.

The phase should create two focused modules:

- `video_processor.py`: cuts video, converts to Shorts format, creates SRT from transcript segments, burns subtitles, extracts thumbnail, updates `clip_path` and `thumbnail_path`.
- `metadata_generator.py`: asks Claude Haiku for title, description, and tags using the clip reason, transcript excerpt, source title, score, and timestamps; updates existing columns in `generated_clips`.

Integration should happen after Phase 3 processing in `rss_poller.py`, keeping the current daemon model: one scheduled poll runs acquisition, AI selection, then processing for pending clips. This preserves the simple linear pipeline and avoids a second scheduler.

No schema migration is required for Phase 4 because `generated_clips` already has `clip_path`, `thumbnail_path`, `title`, `description`, and `tags`.

---

## Standard Stack

| Tool/Library | Purpose | Status |
|--------------|---------|--------|
| FFmpeg CLI | Cut, resize, crop/pad, subtitle burn-in, thumbnail extraction | Already used by `transcriber.py` through `subprocess.run` |
| Python stdlib `subprocess` | Execute FFmpeg commands with `check=True` and `capture_output=True` | Available |
| Python stdlib `json`, `os`, `pathlib` | Transcript loading and output paths | Available |
| `anthropic` | Claude Haiku metadata generation | Already in `requirements.txt` |
| `pytest` + `pytest-mock` | Unit tests with subprocess and API mocks | Already configured |

---

## Architecture Patterns

### Pattern 1: Patchable Directories

Use module constants for output folders so tests can patch them.

```python
VIDEOS_DIR = '/app/videos'
CLIPS_DIR = '/app/clips'
THUMBNAILS_DIR = '/app/thumbnails'
```

The implementation should call `os.makedirs(..., exist_ok=True)` before writing output.

### Pattern 2: FFmpeg Shorts Transform

For landscape source videos, use a center crop/pad chain that always produces 1080x1920:

```text
scale=1080:1920:force_original_aspect_ratio=increase,
crop=1080:1920,
setsar=1
```

This creates a full-frame vertical crop. A blurred background layout could preserve more context, but the simpler crop is deterministic and easier to validate in v1.

Recommended base command:

```bash
ffmpeg -ss START -to END -i input.mp4 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1" \
  -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 128k -movflags +faststart output.mp4 -y
```

### Pattern 3: Subtitle Burn-In

Generate a temporary `.srt` file from transcript segments overlapping the clip interval. Shift each segment time relative to `start_time`.

SRT cue formatting:

```text
1
00:00:00,000 --> 00:00:03,200
Texto da legenda
```

Burn-in command:

```bash
ffmpeg -i raw_clip.mp4 \
  -vf "subtitles=subtitles.srt:force_style='Fontname=Arial,Fontsize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=160'" \
  -c:v libx264 -preset veryfast -crf 23 -c:a copy final_clip.mp4 -y
```

Tests should assert command construction and SRT generation, not run real FFmpeg for every unit test.

### Pattern 4: Idempotent Clip Processing

`process_clip(conn, clip_id)` should:

1. Lookup clip + source video + transcript by `generated_clips.id`.
2. Set `generated_clips.status = 'cutting'`.
3. Cut/resize/burn subtitles/extract thumbnail.
4. Update `clip_path`, `thumbnail_path`.
5. Generate and persist metadata.
6. Set status to `pending` (ready for Phase 5 publishing).

On failure, set `generated_clips.status = 'failed'` and do not propagate exception to the poll loop.

### Pattern 5: Metadata Structured Outputs

Use the same Anthropic pattern established in `selector.py`: `messages.create(..., output_config=json_schema)`.

Schema:

```json
{
  "title": "string <= 100 chars",
  "description": "string",
  "tags": ["string"]
}
```

Persist `tags` as a comma-separated string because the current schema has `tags TEXT`.

---

## Validation Architecture

Phase 4 needs Wave 0 tests before implementation. The fastest reliable feedback loop is:

- `test_video_processor.py`: verify command construction, SRT generation, path updates, failure status.
- `test_metadata_generator.py`: verify structured-output call, title trimming to 100 chars, tags persistence.
- `test_clip_pipeline.py`: verify `poll_all_channels()` triggers pending-cut clip processing and isolates failures.

Unit tests should mock `subprocess.run`, file I/O where practical, and Anthropic clients. Manual verification should run FFmpeg against a real short local fixture only at the checkpoint because video rendering is slower and environment-dependent.

---

## Anti-Patterns to Avoid

- Do not use real API calls in tests.
- Do not run real FFmpeg in ordinary unit tests; mock `subprocess.run` and inspect arguments.
- Do not add a new scheduler for cutting; integrate with the existing daemon flow unless Phase 5 later changes orchestration.
- Do not mark source video as `published` or delete raw files in Phase 4; that belongs to Phase 5.
- Do not store tags as Python list in MySQL; serialize to comma-separated text or JSON string consistently.

---

*Phase: 04-processamento-de-video*
*Research complete: 2026-06-18*
