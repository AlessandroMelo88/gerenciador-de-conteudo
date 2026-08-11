# Sistema — `clip-processor`

Referência **módulo a módulo** do daemon Python. Para a visão conceitual (fluxo, máquina de estados, decisões de arquitetura), ler [`../ARCHITECTURE.md`](../ARCHITECTURE.md) seções 4 e 5 primeiro — este documento é o mapa de "qual arquivo faz o quê".

Última atualização: **11/08/2026** · 21 módulos, ~4.200 linhas em `clip-processor/src/`

---

## O que é

Container Docker único (`container_name: clip-processor`), sem porta publicada, rodando `python -m src.main`. Faz **todo** o trabalho do pipeline: descobre vídeos, baixa, transcreve, escolhe momentos com IA, corta, legenda e publica no YouTube.

Dentro dele também roda o **sidecar HTTP** (Flask, thread daemon, porta 8090 interna) que o painel chama para ações que tocam disco ou processo.

**Consequência operacional:** parar o container para o pipeline **e** derruba o sidecar. O painel continua abrindo, mas "Apagar arquivo", "Purgar antigos" e "Processar URL" passam a falhar.

**Editar código exige rebuild.** Não há bind mount para `src/` — a imagem embute o código no build:
```bash
docker compose build clip-processor && docker compose up -d clip-processor
```

---

## Mapa dos módulos

### Orquestração

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Entrypoint. Recovery no boot, sobe o sidecar em thread, roda um ciclo síncrono e entrega ao APScheduler (`ingest_cycle` 20 min, `publish_cycle` 20 min, `clip_pending_ttl` 1 h) |
| `pipeline_runner.py` | Descoberta e **download**. Janela por formato (6 `curto` + 4 `longo` ocupando disco), filtro de frescor `FRESHNESS_DAYS=1`. Desde 11/08/2026 chama `cleanup_stale_downloads()` antes de baixar |
| `rss_poller.py` | **Nome enganoso:** além do polling RSS, executa o estágio de IA (transcrição + seleção) e dispara o corte. `poll_all_channels` é o coração do ciclo |

### Aquisição

| Arquivo | Responsabilidade |
|---|---|
| `downloader.py` | yt-dlp 720p, 3 tentativas, disk guard de 2 GB, abort por pause. `_cleanup_partial` (por download) e `cleanup_stale_downloads` (varredura de órfãos, 6h+) |
| `dedup.py` | "Já vi esse vídeo?" via Redis `SET NX` (TTL 30 dias) com fallback para MySQL. `mark_failed_redis` está definida mas **nunca é chamada** |
| `transcriber.py` | Groq Whisper `whisper-large-v3-turbo`, pt. Converte para MP3 se o arquivo passar de 24 MB. **Sem fallback** — falhou, o vídeo vira `failed` |

### Inteligência

| Arquivo | Responsabilidade |
|---|---|
| `selector.py` | Escolhe os momentos com score 0–10. Claude Haiku → fallback Groq LLaMA 3.3-70b. Prompt e truncagem variam por formato (`longo`: 1 segmento de 600–1200 s, 20k chars; `curto`: até 3 momentos, 8k chars) |
| `metadata_generator.py` | Título, descrição e tags. Claude → Groq → título bruto do vídeo original. O fallback Groq foi adicionado em 27/07/2026; antes disso, key vazia produzia 3 clips com título idêntico |

### Produção de vídeo

| Arquivo | Responsabilidade |
|---|---|
| `video_processor.py` | FFmpeg. `cut_clip` (curto = crop 1080x1920; longo = `scale=-2:1080`), `generate_srt`, `burn_subtitles`, `overlay_watermark`, `extract_thumbnail`, e o orquestrador `process_clip`. **Deixa `_raw.mp4` para trás — bug 2** |

### Publicação

| Arquivo | Responsabilidade |
|---|---|
| `publisher.py` | Decide o que publicar: cota, janela 19h–22h (SP), round-robin por canal fonte, reserva de slot para `longo`. Ao final, apaga o raw do vídeo fonte quando nenhum clip dele está em estado não-terminal |
| `quota_manager.py` | Contadores Redis `youtube_uploads:*`, TTL até a meia-noite local. `MAX_UPLOADS_PER_DAY` é **clampado em [0,6]** no código |
| `uploader.py` | `videos.insert` + `thumbnails().set`. Um token OAuth por canal-destino; refresh falhando marca `oauth_expired_flag`. **A thumbnail não tem try/except próprio — bug 3** |
| `youtube_oauth.py` | CLI interativo que gera `/app/youtube/token-{slug}.json` |
| `ttl_worker.py` | Auto-rejeita clip `pending` com mais de 48h; avisa uma vez em 24h (idempotente via Redis) |

### Interface com o painel

| Arquivo | Responsabilidade |
|---|---|
| `internal_api.py` | Sidecar Flask 8090. Auth por `X-Internal-Token`, **fail-closed** (env vazia ⇒ 401 em tudo). Rotas: `resolve-channel`, `process-url`, `reject-clip`, `delete-source-video`, `purge-old-videos`. Sem health check |
| `queue_controls.py` | Pause / resume / reorder / prioritize da fila. `can_delete_raw` é o guard de "arquivo em uso" |
| `telegram_notifier.py` | Caminho inverso: `POST /internal/pipeline-event` no Laravel, que centraliza o token do Telegram. Best-effort — falha nunca propaga |

### Entrada manual

| Arquivo | Responsabilidade |
|---|---|
| `processar.py` | Enfileira URL avulsa como `pending`. Não bypassa o pipeline |
| `rejeitar.py` | Rejeita clip, apaga o MP4 final e **preserva** o raw do vídeo fonte (decisão explícita, para permitir recorte futuro) |
| `transcription_job.py` | Feature isolada "Transcrição Local": baixa só o áudio e roda whisper.cpp local, sem Groq e sem cota. Progresso persistido em `transcription_jobs` |
| `db.py` | Conexão pymysql e helpers de status. `recover_stuck_downloads` (`:112`) e `recover_stuck_selecting` — **não cobrem `cutting` nem `publishing`, bug 4** |

---

## Artefatos em disco

Saber quais existem importa: metade dos incidentes de disco veio de classificar artefato vivo como lixo, ou o contrário.

| Padrão | Onde | Está no banco? | Ciclo de vida |
|---|---|---|---|
| `<youtube_id>.mp4` | `videos/` | `source_videos.local_path` | Apagado pelo publisher quando todos os clips terminam |
| `<youtube_id>_transcript.json` | `videos/` | `source_videos.transcript_path` | Permanente |
| `<clip_id>.mp4` | `videos/clips/` | `generated_clips.clip_path` | Permanente até rejeição ou limpeza manual |
| `<clip_id>.jpg` | `videos/thumbnails/` | `generated_clips.thumbnail_path` | Idem |
| `<clip_id>.srt` | `videos/clips/` | **não** | Nunca apagado |
| `<clip_id>_raw.mp4` | `videos/clips/` | **não** | **Nunca apagado — bug 2** |
| `<clip_id>_subtitled.mp4` | `videos/clips/` | **não** | Apagado no caminho feliz; sobra se o processo morrer |
| `.part`, `.ytdl`, `.temp.mp4`, `.fNNN.*` | `videos/` | **não** | Desde 11/08/2026, varridos após 6h |

**A regra que sai daí:** ao cruzar banco × disco, filtrar pelo **id** (prefixo numérico antes de `.` ou `_`), nunca pelo nome do arquivo. Comparar nomes contra as colunas marca `.srt` e `_raw.mp4` como órfãos e apaga arquivo de clip vivo. Detalhe do incidente em [`../CLAUDE.md`](../CLAUDE.md).

---

## O que o Redis guarda (e o que não guarda)

**A fila NÃO mora no Redis.** Fila = MySQL (`source_videos`, `generated_clips`). O Redis tem só:

- `video:<id>` (TTL 30 dias) — marca "vídeo já visto", para dedup
- `youtube_uploads:<data>` e variantes `:<canal>` / `:<formato>` — cota diária
- `clip_warned:<id>` — idempotência do aviso de TTL

Consequência que morde: apagar as chaves `video:*` faz os vídeos deletados **voltarem** no próximo poll RSS. Nunca `FLUSHALL` achando que "reseta a fila".

---

## Testes

`clip-processor/tests/`, pytest. Rodar dentro do container — o host não tem as dependências do sidecar (`flask`), o que faz `test_pipeline_runner.py::test_scheduler_compatible_coalesce` falhar por ambiente, não por código. Ver bug 7.
