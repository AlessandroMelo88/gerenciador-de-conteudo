---
type: "query"
date: "2026-09-06T05:51:02.709885+00:00"
question: "A musica no final do video esta ficando muito baixinha. Ela começa baxinha 30 segundos antes do video acabar, e vai aumentando, pra quando terminar de fato ja estar no volume do video."
contributor: "graphify"
outcome: "useful"
source_nodes: ["_mix_music()", "compose_media()", "media_composer.py", "test_compose_media_normalizes_segments_and_mixes_music()"]
---

# Q: A musica no final do video esta ficando muito baixinha. Ela começa baxinha 30 segundos antes do video acabar, e vai aumentando, pra quando terminar de fato ja estar no volume do video.

## Answer

Expanded via graph vocabulary: [audio, music, volume, mix, composer, crossfade, xfade]. The root cause was media_composer.py limiting canonical filesystem music to 0.12 with a 1.20 gain, so final gain was only 0.144, and music lasted 15 seconds. Updated _mix_music to use 30 seconds, start at 8 percent of target, ramp for 28 seconds, hold full target for 2 seconds, normalize music to -16 LUFS, and limit the final mix to avoid clipping. Canonical/default target is now 1.0. Runtime FFmpeg validation measured -36.8 dB at entry, -22.8 dB mid-ramp, and -18.2 dB at the end. 329 Python tests and frontend typecheck/lint/format passed.

## Outcome

- Signal: useful

## Source Nodes

- _mix_music()
- compose_media()
- media_composer.py
- test_compose_media_normalizes_segments_and_mixes_music()