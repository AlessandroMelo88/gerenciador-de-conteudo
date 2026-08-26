# Sistema — `clip-processor`

Mapa de **qual arquivo faz o quê** no daemon Python. Cada subsistema tem documento próprio, linkado na
tabela; aqui é só o índice de módulos e o que é comum a todos.

Última atualização: **26/08/2026** · módulos do daemon em `clip-processor/src/`

---

## O que é

Container Docker único (nome gerenciado pelo Compose), sem porta publicada, rodando
`python -m src.main`. Faz **todo** o trabalho do pipeline: descobre vídeos, baixa, transcreve, escolhe
momentos com IA, corta, aplica pós-produção específica do formato e publica no YouTube.

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
[`RUNBOOK.md`](RUNBOOK.md#o-container-está-rodando-código-velho).

---

## Mapa dos módulos

### Orquestração — [`PIPELINE-E-SCHEDULER.md`](PIPELINE-E-SCHEDULER.md)

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Entrypoint. Recovery no boot, sobe o sidecar em thread, roda um ciclo síncrono e entrega ao APScheduler. Jobs: `ingest_cycle` 20 min, `publish_cycle` 20 min, `clip_pending_ttl` 1 h, `state_recovery` **30 min** |
| `pipeline_runner.py` | Descoberta de vaga e **download**. Janela por formato (6 `curto` + 4 `longo`), `FRESHNESS_DAYS=365` por default, `_discard_failed_download` |
| `rss_poller.py` | **Nome enganoso:** além do polling RSS, executa o estágio de IA (transcrição + seleção) e dispara o corte. `poll_all_channels` é o coração do ciclo |

### Aquisição — [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md)

| Arquivo | Responsabilidade |
|---|---|
| `downloader.py` | yt-dlp 720p, 3 tentativas, disk guard de 2 GB, abort por pause. `_cleanup_partial` (por download) e `cleanup_stale_downloads` (varredura de órfãos, **1 h+**) |
| `dedup.py` | "Já vi esse vídeo?" via Redis `SET NX` (TTL 30 dias) com fallback para PostgreSQL. `mark_failed_redis` é helper de compatibilidade para retries explícitos |
| `processar.py` | Enfileira URL avulsa como `pending`. Não bypassa o pipeline |

### Inteligência — [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md), [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md)

| Arquivo | Responsabilidade |
|---|---|
| `transcriber.py` | Tenta legendas do YouTube (manual/automática) em pt antes do Groq Whisper `whisper-large-v3-turbo`; converte para MP3 acima de 24 MB no fallback |
| `selector.py` | Escolhe os momentos com score 0–10. Claude Haiku → fallback Groq LLaMA 3.3-70b. Prompt e limites variam por formato (`curto`: até 3 momentos de **30**–180 s; `longo`: 1 segmento de 420–1200 s) |
| `metadata_generator.py` | Título, descrição e tags para SEO; `generate_thumbnail_text` usa um prompt dedicado para uma chamada literal da thumb. O provider é escolhido pela configuração e não há fallback determinístico |
| `transcription_job.py` | Feature isolada "Transcrição Local": baixa só o áudio e roda whisper.cpp local, sem Groq e sem cota. Progresso em `transcription_jobs` |

### Produção de vídeo — [`SISTEMA-VIDEO.md`](SISTEMA-VIDEO.md)

| Arquivo | Responsabilidade |
|---|---|
| `video_processor.py` | FFmpeg. `cut_clip` (curto = vertical 1080x1920; longo = `scale=-2:1080`), `generate_srt`/`burn_subtitles` somente para Shorts, overlays de watermark e texto da thumbnail, `extract_thumbnail`, e o orquestrador `process_clip` |

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
| `db.py` | Conexão psycopg2 e helpers de status. `recover_stuck_downloads`, `recover_stuck_selecting`, `recover_stuck_publishing` e `recover_cutting_on_boot` ([`db.py`](../clip-processor/src/db.py)) |

Schema e colunas em [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md); estados e transições em
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
| Roteamento de IA | Seleção legada usa Anthropic → Groq; metadata e thumbnail usam o provider configurado. Resposta inválida ou ausente falha de forma explícita |

> **`ANTHROPIC_API_KEY` está vazia na operação normal.** O código tenta Claude primeiro, mas o provider
> que roda de fato em produção é o **Groq LLaMA 3.3-70b**, na seleção, metadata e chamada da thumbnail. Ao
> depurar qualidade de corte ou de título, o prompt que importa é o que o Groq recebe.

---

## O que o Redis guarda (e o que não guarda)

**A fila NÃO mora no Redis.** Fila = PostgreSQL (`source_videos`, `generated_clips`). O Redis tem só:

| Chave | Conteúdo | TTL |
|---|---|---|
| `video:<id>` | "vídeo já visto", para dedup | 30 dias |
| `youtube_uploads:<canal>:<data>` e `:longo` | cota diária | até a meia-noite local |
| `clip_warned:<id>` | idempotência do aviso de TTL | — |

Consequência que morde: apagar as chaves `video:*` faz os vídeos deletados **voltarem** no próximo poll
RSS. Nunca `FLUSHALL` achando que "reseta a fila" — isso ressuscita todo o backlog e zera a cota junto.

---

## Configuração

As env vars do runtime são injetadas pelo `docker-compose.yml` deste repositório, que lê o `.env` da
raiz do projeto.

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
| `ASSETS_DIR` | raiz dos assets canônicos | `/app/assets` |
| `LARAVEL_NOTIFY_URL` / `LARAVEL_HOST_HEADER` | endpoint de eventos e Host para o roteamento nginx | `http://nginx/internal/pipeline-event` / `canaldecortes.local` |
| `CLIP_PENDING_TTL_HOURS` / `CLIP_PENDING_WARN_HOURS` | TTL de auto-rejeição | 48 / 24 (constantes) |

**Não declaradas no compose** (valem os defaults do código): `DOWNLOAD_WINDOW_CURTO` (6),
`DOWNLOAD_WINDOW_LONGO` (4), `WHISPER_CPP_BIN`, `WHISPER_MODEL_PATH` (vêm do `ENV` do Dockerfile).

Armadilha de drift: o default de `MAX_UPLOADS_PER_DAY` é `:-1` no `clip-processor` e `:-2` no serviço
`php`. Só não morde porque a var está setada no `.env` da raiz.

Volumes: `youtube/` (read-write, tokens), `videos/` (read-write), `assets/` (**read-only**, assets
canônicos por canal e faixas completas), `branding/` (**read-only** aqui, read-write no `php`, usado
por marcas d'água e pelo fallback legado de `media_assets`).

---

## Testes

`clip-processor/tests/`, pytest (quantidade verificada pelo comando abaixo). Dois jeitos de rodar:

```bash
# no container (reproduz produção)
docker exec clip-processor python -m pytest tests/ -q

# no host, via venv com requirements-dev.txt (make setup-python uma vez)
make test-python
```

Lint e formatação: `make lint-python` (ruff) e `make format-python`; mypy bloqueante em
`make types-python`. Detalhes em `DESENVOLVIMENTO.md`. O bug 7 (falhas por ambiente no host)
deixou de reproduzir com o venv.
