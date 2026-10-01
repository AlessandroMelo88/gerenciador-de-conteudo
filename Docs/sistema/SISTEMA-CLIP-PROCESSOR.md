# Sistema — `clip-processor`

Mapa de **qual arquivo faz o quê** no daemon Python. Cada subsistema tem documento próprio, linkado na
tabela; aqui é só o índice de módulos e o que é comum a todos.

Última atualização: **13/08/2026** · 21 módulos, ~4.450 linhas em `clip-processor/src/`

---

## O que é

Container Docker único (`container_name: clip-processor`), sem porta publicada, rodando
`python -m src.main`. Faz **todo** o trabalho do pipeline: descobre vídeos, baixa, transcreve, escolhe
momentos com IA, corta, legenda e publica no YouTube.

Dentro dele também roda o **sidecar HTTP** (Flask, thread daemon, porta 8090 interna) que o painel chama
para ações que tocam disco ou processo.

**Consequência operacional:** parar o container para o pipeline **e** derruba o sidecar. O painel
continua abrindo, mas "Apagar arquivo", "Purgar antigos" e "Processar URL" passam a falhar.

### Editar código exige rebuild

Não há bind mount para `src/` — o Dockerfile faz `COPY src/ src/` e a imagem embute o código no build.
Editar no host e reiniciar **não** aplica a mudança.

```bash
docker compose build clip-processor && docker compose up -d clip-processor
```

Isso já causou horas perdidas: em 13/08/2026 o container rodava código de 01/08 enquanto o host tinha
commits de 12/08, e o comportamento observado não correspondia a nenhuma versão do código que se estava
lendo. **Conferir a data da imagem antes de investigar qualquer bug** —
[`RUNBOOK.md`](../operacao/RUNBOOK.md#o-container-está-rodando-código-velho).

---

## Mapa dos módulos

### Orquestração — [`PIPELINE-E-SCHEDULER.md`](PIPELINE-E-SCHEDULER.md)

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Entrypoint. Recovery no boot, sobe o sidecar em thread, roda um ciclo síncrono e entrega ao APScheduler. Jobs: `ingest_cycle` 20 min, `publish_cycle` 20 min, `clip_pending_ttl` 1 h, `state_recovery` **30 min** |
| `pipeline_runner.py` | Descoberta de vaga e **download**. Janela de 10 vídeos por canal destino ativo (`_niche_windows`), `FRESHNESS_DAYS`, `_discard_failed_download` |
| `rss_poller.py` | **Nome enganoso:** além do polling RSS, executa o estágio de IA (transcrição + seleção) e dispara o corte. `poll_all_channels` é o coração do ciclo |

### Aquisição — [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md)

| Arquivo | Responsabilidade |
|---|---|
| `downloader.py` | yt-dlp 720p, 3 tentativas, disk guard de 2 GB, abort por pause. `_cleanup_partial` (por download) e `cleanup_stale_downloads` (varredura de órfãos, **1 h+**) |
| `dedup.py` | "Já vi esse vídeo?" via Redis `SET NX` (TTL 30 dias) com fallback para MySQL. `mark_failed_redis` está definida mas **nunca é chamada** |
| `processar.py` | Enfileira URL avulsa como `pending`. Não bypassa o pipeline |

### Inteligência — [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md), [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md)

| Arquivo | Responsabilidade |
|---|---|
| `transcriber.py` | Groq Whisper `whisper-large-v3-turbo`, pt. Converte para MP3 acima de 24 MB. **Sem fallback** — falhou, o vídeo vira `failed` |
| `selector.py` | Escolhe os momentos com score 0–10. Claude Haiku → fallback Groq LLaMA 3.3-70b. Prompt e limites variam por formato (`curto`: até 3 momentos de **30**–180 s; `longo`: 1 segmento de 420–1200 s) |
| `metadata_generator.py` | Título, descrição e tags. Claude → **Groq** → título bruto do vídeo original. O fallback Groq foi adicionado em 27/07/2026 |
| `transcription_job.py` | Feature isolada "Transcrição Local": baixa só o áudio e roda whisper.cpp local, sem Groq e sem cota. Progresso em `transcription_jobs` |

### Produção de vídeo — [`SISTEMA-VIDEO.md`](SISTEMA-VIDEO.md)

| Arquivo | Responsabilidade |
|---|---|
| `video_processor.py` | FFmpeg. `cut_clip` (curto = crop 1080x1920; longo = `scale=-2:1080`), `generate_srt`, `burn_subtitles`, `overlay_watermark`, `extract_thumbnail`, e o orquestrador `process_clip`. Desde o Lote 7 há também `render_short_clip` (Short em passe único) e, ao lado dele, `video_quality.py` (modos de render), `media_contract.py` (contrato técnico do Short) e `subtitle_detector.py` (opt-in) — ver [seção Render](#render-de-qualidade-modos-de-encode-e-shorts-em-passe-único-lote-7) |

### Publicação — [`SISTEMA-PUBLICACAO.md`](SISTEMA-PUBLICACAO.md)

| Arquivo | Responsabilidade |
|---|---|
| `publisher.py` | Decide o que publicar: cota, janela 19h–22h (SP), round-robin por canal fonte, reserva de slot para `longo`. `_maybe_finalize_source_video` apaga raw, clips, `_raw`, `_subtitled` e thumbnails ao fechar o vídeo fonte |
| `quota_manager.py` | Contadores Redis `youtube_uploads:*`, TTL até a meia-noite local. `MAX_UPLOADS_PER_DAY` é **clampado em [0,6]** no código |
| `uploader.py` | `videos.insert` + `thumbnails().set`. Um token OAuth por canal-destino; refresh falhando marca `oauth_expired_flag`. **A thumbnail não tem try/except próprio — bug 3** |
| `youtube_oauth.py` | CLI interativo que gera `/app/youtube/token-{slug}.json` |
| `ttl_worker.py` | Auto-rejeita clip `pending` com mais de 48 h; avisa uma vez em 24 h (idempotente via Redis) |

### Interface com o painel — [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md)

| Arquivo | Responsabilidade |
|---|---|
| `internal_api.py` | Sidecar Flask 8090. Auth por `X-Internal-Token`, **fail-closed** (env vazia ⇒ 401 em tudo). 10 rotas. Sem health check |
| `queue_controls.py` | Pause / resume / reorder / prioritize da fila. `can_delete_raw` é o guard de "arquivo em uso" |
| `rejeitar.py` | Rejeita clip, apaga o MP4 final e **preserva** o raw do vídeo fonte (decisão explícita, permite recorte futuro) |
| `telegram_notifier.py` | Caminho inverso: `POST /internal/pipeline-event` no Laravel, que centraliza o token do Telegram. Best-effort — falha nunca propaga |

### Base

| Arquivo | Responsabilidade |
|---|---|
| `db.py` | Conexão agnóstica de banco de dados (`pymysql` para MySQL e `psycopg2` para PostgreSQL, chaveado via `DB_CONNECTION`), wrappers de cursor (`PostgresCursorWrapper`) e helpers de status. `recover_stuck_downloads` e `recover_stuck_selecting` adaptados dinamicamente para cada dialeto SQL |

Schema e colunas em [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md); rotinas de backup e recuperação em [`BANCO-DE-DADOS.md#rotinas-de-backup-e-recuperação-dbbackup-e-dbrestore`](BANCO-DE-DADOS.md#rotinas-de-backup-e-recuperação-dbbackup-e-dbrestore); estados e transições em
[`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md).


---

## Padrões comuns a todos os módulos

Vale conhecer antes de escrever código novo aqui — são consistentes no projeto inteiro:

| Padrão | Detalhe |
|---|---|
| Logging | `print` com timestamp e tag por módulo: `[ACQU]`, `[AI]`, `[VID]`, `[PUB]`, `[DB]`, `[QUEUE]`, `[DEDUP]`, `[NOTIFY]`. Sem biblioteca de logging |
| Injeção de dependência | `db_conn=None` / `redis_client=None` / `groq_client=None` significa "produção cria o cliente"; testes injetam |
| Ciclo de vida da conexão | Quem **abre** fecha. Funções que recebem `conn` nunca o fecham |
| Commit | Explícito em cada função (`autocommit=False`) |
| Isolamento de falha | Cada estágio em `try/except` próprio que loga e segue. Uma falha não derruba o scheduler |
| Fallback de IA | Anthropic → Groq. Qualquer caminho de IA novo deve nascer com fallback Groq — não replicar o buraco do `metadata_generator` |

> **`ANTHROPIC_API_KEY` está vazia na operação normal.** O código tenta Claude primeiro, mas o provider
> que roda de fato em produção é o **Groq LLaMA 3.3-70b**, tanto na seleção quanto na metadata. Ao
> depurar qualidade de corte ou de título, o prompt que importa é o que o Groq recebe.

---

## O que o Redis guarda (e o que não guarda)

**A fila NÃO mora no Redis.** Fila = MySQL (`source_videos`, `generated_clips`). O Redis tem só:

| Chave | Conteúdo | TTL |
|---|---|---|
| `video:<id>` | "vídeo já visto", para dedup | 30 dias |
| `youtube_uploads:<canal>:<data>` e `:longo` | cota diária | até a meia-noite local |
| `clip_warned:<id>` | idempotência do aviso de TTL | — |

Consequência que morde: apagar as chaves `video:*` faz os vídeos deletados **voltarem** no próximo poll
RSS. Nunca `FLUSHALL` achando que "reseta a fila" — isso ressuscita todo o backlog e zera a cota junto.

---

## Configuração

Todas as env vars são injetadas pelo `docker-compose.yml` da raiz `wordpress/`, que lê o `.env`
**daquela** raiz — não o `canaldecortes/.env`.

| Var | Serve para | Default no compose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude: seleção + metadata | — |
| `GROQ_API_KEY` | Whisper + fallback de seleção e metadata | — |
| `CLIPS_DB_PASSWORD` | senha do `clips_user` | — |
| `CLIP_PROCESSOR_INTERNAL_TOKEN` | token painel ↔ sidecar (mesmo valor nos dois lados) | — |
| `MANUAL_APPROVAL_REQUIRED` | `true` exige `approved`; `false` publica `pending` direto | `false` |
| `MAX_UPLOADS_PER_DAY` | cota diária por canal (**teto rígido de 6 no código**) | `1` |
| `MAX_LONGO_UPLOADS_PER_DAY` | teto de `longo` e reserva de slot | `2` |
| `UPLOAD_WINDOW_BYPASS` | ignora a janela 19h–22h | `false` |
| `YOUTUBE_PRIVACY_STATUS` | `privacyStatus` do upload | `private` |
| `YOUTUBE_CLIENT_SECRETS` | client secrets do OAuth | `/app/youtube/client_secret.json` |
| `LARAVEL_NOTIFY_URL` / `LARAVEL_HOST_HEADER` | endpoint de eventos e Host para o roteamento nginx | `http://nginx/internal/pipeline-event` / `canaldecortes.local` |
| `CLIP_PENDING_TTL_HOURS` / `CLIP_PENDING_WARN_HOURS` | TTL de auto-rejeição | 48 / 24 (constantes) |

**Não declaradas no compose** (valem os defaults do código): `DOWNLOAD_WINDOW_PER_CHANNEL` (10, vagas por
canal destino ativo), `WHISPER_CPP_BIN`, `WHISPER_MODEL_PATH` (vêm do `ENV` do Dockerfile).

Armadilha de drift: o default de `MAX_UPLOADS_PER_DAY` é `:-1` no `clip-processor` e `:-2` no serviço
`php`. Só não morde porque a var está setada no `.env` da raiz.

Volumes: `youtube/` (read-write, tokens), `videos/` (read-write), `branding/` (**read-only** aqui,
read-write no `php`).

---

## Testes

`clip-processor/tests/`, pytest. **Rodar dentro do container** — o host não tem as dependências do
sidecar (`flask`), o que faz teste falhar por ambiente e não por código. Ver bug 7.

```bash
docker exec clip-processor python -m pytest tests/ -q
```

---

## Render de qualidade, modos de encode e Shorts em passe único (Lote 7)

Portado seletivamente de `origin/release/rico` (feature `feature/render-qualidade-e-shorts`), sem o
`ruff format` do lote e sem trazer o que não é render (mídia por canal, meme editor, `worker.py`).

### O que mudou

| Peça | Comportamento |
|---|---|
| `video_quality.py` | Modos de encode escolhidos por `VIDEO_RENDER_MODE`, lidos **a cada chamada** (sem rebuild): `padrao` (default), `economia`, `quality`, `ultra` |
| `render_short_clip` | Short `curto` em **uma** recodificação: enquadra 1080x1920 (crop central, como antes) + legenda queimada + watermark no mesmo filtergraph. Antes eram 3 encodes (`cut_clip` → `burn_subtitles` → `overlay_watermark`), cada um perdendo qualidade |
| Áudio dinâmico | `loudnorm=I=-14:LRA=11:TP=-1.5` + fade in 80 ms / fade out 200 ms em `cut_clip` e `render_short_clip`. `AUDIO_LOUDNORM=0` desliga |
| `media_contract.py` | Depois do render, o Short precisa ser 9:16 e ter duração entre 5 s e o teto. Falhou → clip `failed` com `upload_error` |
| `subtitle_detector.py` | **Opt-in** (`BURNED_SUBTITLE_DETECTION=true`): OCR do rodapé do vídeo-fonte; se ele já traz legenda queimada que repete a fala, não queimamos a nossa por cima. Exige `tesseract-ocr-por` (agora no Dockerfile) |

Vídeo `longo` continua no caminho antigo (`cut_clip` com template/fundo + `burn_subtitles` + watermark
condicional). `SHORTS_SINGLE_PASS=0` volta o `curto` ao encadeamento de 3 passes.

### Modos de render (`VIDEO_RENDER_MODE`)

| Modo | x264 | Áudio | Uso |
|---|---|---|---|
| `padrao` (**default**, aliases `legacy`) | `ultrafast`, CRF 24, 1 thread | AAC 128k | O que a master já rodava; é o que a A1 (2 OCPU) sustenta |
| `economia` (`fast`) | `veryfast`, CRF 16, 2 threads | AAC 320k | Meio-termo opt-in |
| `quality` (`maximo`) | `slow`, CRF 14, 2 threads | AAC 320k | Qualidade máxima da rico; **opt-in** |
| `ultra` | `ultrafast`, CRF 18, 2 threads | AAC 320k | Rápido com CRF melhor |

Todos usam `-profile:v high -level 4.2 -pix_fmt yuv420p`. Ajuste fino sobrescreve o modo:
`FFMPEG_PRESET`, `FFMPEG_CRF`, `FFMPEG_THREADS`. As variáveis **não** estão no `docker-compose.yml` (a
raiz é compartilhada); para ligar na A1, incluí-las no `environment` do `clip-processor` quando for
decidido.

### Medição (corte de 30 s, fonte sintética 1920x1080 30 fps, legenda + watermark)

> **Medido em Mac (Apple Silicon) / Docker Desktop, limitado a `--cpus=2`, imagem `wordpress-clip-processor`
> arm64. NÃO foi medido na A1.** A máquina tinha outros containers ativos, então os números têm ruído
> (a repetição do mesmo caso variou até ~2x). A Neoverse N1 da A1 é bem mais lenta que um núcleo M-series:
> use os números como **razão** entre modos, não como tempo absoluto. Falta repetir na A1.

| Caso | Tempo (s) | Tamanho |
|---|---|---|
| 3 passes, `padrao` (encadeamento antigo) | 40,1 / 33,4 | 20,9 MB |
| **Passe único, `padrao`** | **24,1 / 12,8** | 22,4 MB |
| Passe único, `economia` (veryfast CRF 16) | 59,4 | 16,5 MB |
| Passe único, `quality` (slow CRF 14) | 88,5 | 19,7 MB |

Leitura: o passe único **reduz** o CPU do default (1 encode em vez de 3, ~2x mais rápido aqui);
`economia` custa ~2,5–4x o `padrao` e `quality` ~4–7x. Por isso o default fica em `padrao` e
qualidade máxima é opt-in até haver medição na A1 (render de 30 s hoje cabe folgado no intervalo do
ciclo; o gargalo seria empilhar clips com `quality` em 2 OCPU).

Descoberta na medição: `overlay=...:format=auto` com `format=rgba` no PNG do watermark fazia o Short
levar ~70–90 s; o `overlay=W-w-20:20` simples (o mesmo do `overlay_watermark` antigo) é o usado.

### Duração do Short: reconciliação com a regra da master

A rico exige **30–45 s** rígidos (`SHORTS_MIN/MAX_DURATION_SECONDS`) e recusa render fora disso.
A master tem regra editorial diferente, que **foi mantida**: o `selector` descarta momento < 15 s,
estica 15–30 s até 30 s (quando a transcrição permite) e limita a 180 s. Decisão de 30/09/2026:

- A política (15 / 30 / 180) continua **só no `selector`**; o render não a reimpõe.
- `media_contract` valida apenas o técnico: 9:16, piso absoluto de 5 s (o `selector` aceita clip curto
  quando a transcrição inteira é menor que 30 s) e teto = `SHORTS_MAX_DURATION_SECONDS` (default 180).
- Quem quiser a regra da rico: `SHORTS_MAX_DURATION_SECONDS=45` — o render corta o excedente e o
  contrato passa a rejeitar acima de 45 s. Não é o default.
- Preservados: 1 clip por corte, janela de 10 vídeos por canal, raw só apagado pelo sidecar, recoveries.

### O que ficou de fora do lote

- **Stage workers (`worker.py`)**: dependem de `poll_sources_only`, `process_downloaded_videos` e
  `process_pending_clips` públicos no `rss_poller`, que a master não tem, e o APScheduler do `main.py`
  já agenda essas etapas — subir os dois duplicaria o agendamento. Fica para um lote próprio de refactor.
- Enquadramento com fundo desfocado da rico (`SHORTS_VERTICAL_FILTER` blur): muda o visual dos Shorts;
  a master segue com crop central.
- `paths.py` (resolução de paths para workers nativos), `media_composer`/`meme_editor` (Lote 8).
