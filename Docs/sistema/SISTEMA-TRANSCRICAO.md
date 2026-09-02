# Transcrição

Duas transcrições **independentes** convivem no mesmo container e não se falam:

| | Pipeline principal | Transcrição Local |
|---|---|---|
| Módulo | [`transcriber.py`](../clip-processor/src/transcriber.py) | [`transcription_job.py`](../clip-processor/src/transcription_job.py) |
| Motor | Groq Whisper API (`whisper-large-v3-turbo`) | whisper.cpp local, modelo `ggml-small` |
| Custo | cota da API Groq | zero |
| Entrada | `.mp4` já baixado pelo pipeline | URL colada pelo operador no painel |
| Saída | `<id>_transcript.json` + `source_videos.transcript_path` | `.srt` + tabela `transcription_jobs` |
| Toca `source_videos`/`generated_clips`? | sim | **não** |

Verificado no código em **13/08/2026**.

---

## Pipeline principal — Groq Whisper

`transcribe_video` ([`transcriber.py:51`](../clip-processor/src/transcriber.py#L51)), chamado por
`_process_ai_pipeline` ([`rss_poller.py:116`](../clip-processor/src/rss_poller.py#L116)).

| Parâmetro | Valor | Onde |
|---|---|---|
| modelo | `whisper-large-v3-turbo` | [`:83`](../clip-processor/src/transcriber.py#L83) |
| `response_format` | `verbose_json`, `timestamp_granularities=['segment']` | [`:84`](../clip-processor/src/transcriber.py#L84) |
| idioma | `pt` fixo | [`:86`](../clip-processor/src/transcriber.py#L86) |
| `temperature` | `0.0` | [`:87`](../clip-processor/src/transcriber.py#L87) |

### Conversão para áudio acima de 24 MB

[`transcriber.py:72`](../clip-processor/src/transcriber.py#L72): arquivo maior que 24.000.000 bytes é
convertido por `_prepare_audio` ([`:25`](../clip-processor/src/transcriber.py#L25)) antes de subir —
`ffmpeg -vn -ar 16000 -ac 1 -b:a 32k` para `<video_path sem .mp4>_audio.mp3`. O temporário é apagado
no `finally` ([`:111`](../clip-processor/src/transcriber.py#L111)).

Vídeo de 720p com mais de ~1 minuto passa dos 24 MB, então na prática **quase todo** vídeo do
pipeline passa pela conversão.

### Sem fallback

`transcribe_video` retorna `None` em qualquer exceção
([`:105`](../clip-processor/src/transcriber.py#L105)) e `_process_ai_pipeline` marca o vídeo como
`failed` ([`rss_poller.py:119`](../clip-processor/src/rss_poller.py#L119)). **Não existe fallback**:
Groq fora do ar ⇒ vídeo perdido para o pipeline. É o único estágio de IA sem plano B — seleção e
metadata têm fallback Groq.

O `.mp4` bruto **permanece em disco** nesse caso, com `local_path` preenchido, ocupando vaga da
janela de download.

### Formato do transcript salvo

`save_transcript` ([`transcriber.py:116`](../clip-processor/src/transcriber.py#L116)) grava
`/app/videos/<video_id>_transcript.json`:

```json
{"video_id": "...", "text": "...", "segments": [{"start": 0.0, "end": 4.2, "text": "..."}]}
```

Os `segments` são consumidos por dois lugares: o seletor de momentos e `generate_srt`
([`video_processor.py:72`](../clip-processor/src/video_processor.py#L72)), que recorta as cues
relativas ao início do clip. **O JSON de transcript nunca é apagado** — nenhuma rotina de limpeza o
toca, e ele é pequeno (KB, não MB).

---

## Transcrição Local — whisper.cpp

Feature isolada, adicionada pelo commit `59c21c5` (30/07/2026). O operador cola uma URL no painel
(`/painel/transcricoes`), o sidecar chama `POST /internal/transcribe`
([`internal_api.py:332`](../clip-processor/src/internal_api.py#L332)) e o trabalho roda numa thread
daemon.

Não usa Groq, não consome cota do YouTube, e **nenhum job de transcrição local entra na fila de
aprovação de clips nem é enviado ao YouTube**.

### Binário e modelo

Compilados no build da imagem ([`clip-processor/Dockerfile:12-16`](../clip-processor/Dockerfile#L12)):
`git clone whisper.cpp` + `cmake --build`. É esse passo que faz o primeiro build demorar 10–20 min em
máquina ARM (relevante para o [`PLANO-ORACLE.md`](PLANO-ORACLE.md)).

| Env var | Default |
|---|---|
| `WHISPER_CPP_BIN` | `/opt/whisper.cpp/build/bin/whisper-cli` |
| `WHISPER_MODEL_PATH` | `/opt/whisper.cpp/models/ggml-small.bin` |

Nenhuma das duas está no `docker-compose.yml`; valem os `ENV` do Dockerfile
([`:18-19`](../clip-processor/Dockerfile#L18)).

### Chunking

| Constante | Valor | Onde |
|---|---|---|
| `CHUNK_THRESHOLD_SECONDS` | 1500 (25 min) | [`transcription_job.py:36`](../clip-processor/src/transcription_job.py#L36) |
| `MAX_CHUNKS` | 3 | [`:37`](../clip-processor/src/transcription_job.py#L37) |
| `WHISPER_TIMEOUT_SECONDS` | 3600 | [`:38`](../clip-processor/src/transcription_job.py#L38) |

Áudio acima de 25 min é dividido em até 3 pedaços (`_split_audio`,
[`:113`](../clip-processor/src/transcription_job.py#L113)), cada um transcrito separadamente, e os
`.srt` são remontados com os timestamps deslocados (`_shift_srt_timestamps`,
[`:150`](../clip-processor/src/transcription_job.py#L150); `_merge_srt_chunks`,
[`:165`](../clip-processor/src/transcription_job.py#L165)).

O teto de 3 pedaços é pedido explícito do operador — vídeo muito longo continua tendo pedaços longos
em vez de virar 10 chamadas.

### Progresso

Persistido em `transcription_jobs` (MySQL), nunca em memória, para sobreviver a reload da página.
whisper.cpp não expõe progresso incremental estável entre versões, então os valores são **milestones
grosseiros**: 10% ao iniciar o download, 50% ao iniciar a transcrição, 100% ao terminar. Não é o
progresso real do whisper.

Funções: `create_transcription_job` ([`:42`](../clip-processor/src/transcription_job.py#L42)),
`update_job` ([`:56`](../clip-processor/src/transcription_job.py#L56)),
`process_transcription_job` ([`:222`](../clip-processor/src/transcription_job.py#L222)),
`start_transcription_job` ([`:257`](../clip-processor/src/transcription_job.py#L257)).

Saída em `/app/videos/transcripts/` ([`:27`](../clip-processor/src/transcription_job.py#L27)).

> **Não confirmado:** se existe rotina de limpeza para os `.srt` e os áudios baixados por esta
> feature. Não encontrei nenhuma varredura que toque em `videos/transcripts/`.
