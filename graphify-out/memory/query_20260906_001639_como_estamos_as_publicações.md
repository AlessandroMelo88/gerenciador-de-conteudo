---
type: "query"
date: "2026-09-06T00:16:39.918955+00:00"
question: "Como estamos as publicações ?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["publisher.py", "QuotaManager", "publish_pending_clips()", "GeneratedClip"]
---

# Q: Como estamos as publicações ?

## Answer

Expanded from original query via graph vocab: [published, publishing, publisher, upload, uploads, quota, shorts, video, youtube, channel, status]. Runtime verification: Hacker Libertário has 0 uploads today and 0 in the last 24 hours; last upload was 2026-09-04 01:32 America/Sao_Paulo. Pipeline has no publishable artifact: generated clip 205 is pending but has no title or rendered clip path. There are 67 pending source videos; 10 retain local media/transcripts while status is pending, so downloader counts them as active occupancy and AI only selects later-stage statuses, creating a queue deadlock. Historical 18 short uploads failed with YouTube daily upload-limit HTTP 400.

## Outcome

- Signal: useful

## Source Nodes

- publisher.py
- QuotaManager
- publish_pending_clips()
- GeneratedClip