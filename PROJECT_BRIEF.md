# PROJECT_BRIEF — Canal de Cortes

> Baseado no código real (as-built), lido em 18/07/2026. Referência primária: `ARCHITECTURE.md` (doc as-built, commit `dca6e44`), `mysql/init/*.sql`, `clip-processor/src/*`, `painel/app/*`. Onde há incerteza, marcado como **(a confirmar)**.

---

## 1. Visão geral

Pipeline automatizado que monitora canais de futebol no YouTube, corta os melhores momentos com IA e republica os clips em canais próprios. O fluxo padrão é **100% automático** — da descoberta via RSS até o upload, sem intervenção humana. O painel web existe para o operador **observar e corrigir**, não para operar o fluxo normal.

Dois formatos de saída, decididos automaticamente pela duração do vídeo fonte:

- **`curto`** — vídeo fonte < 10 min → até 3 shorts verticais 1080x1920 (15 s a 3 min cada).
- **`longo`** — vídeo fonte ≥ 10 min → **um único** corte horizontal contínuo de 10–20 min (`scale=-2:1080`).

O sistema é dividido em dois serviços com uma fronteira de responsabilidade rígida (ver §3): o **`clip-processor`** (daemon Python, dono do pipeline) e o **`painel`** (Laravel + React, observação e correção).

---

## 2. Stack

**Pipeline (`clip-processor/`)** — Python 3.12 (`python:3.12-slim` + ffmpeg no Dockerfile):
- Orquestração: **APScheduler** (`BlockingScheduler`, tz `America/Sao_Paulo`)
- Aquisição: **yt-dlp**, **feedparser** (RSS)
- IA: **anthropic** (Claude Haiku — seleção de momentos + metadata), **groq** (Whisper `whisper-large-v3-turbo` para transcrição; LLaMA `llama-3.3-70b-versatile` como fallback de seleção)
- Vídeo: **FFmpeg** (corte, SRT, legenda queimada, watermark, thumbnail)
- Upload: **google-api-python-client / google-auth / google-auth-oauthlib** (YouTube Data API, OAuth por canal)
- Dados: **pymysql** (MySQL), **redis** (dedup + cota)
- Sidecar HTTP interno: **Flask** (porta 8090, sem porta publicada)
- Testes: **pytest / pytest-mock**

**Painel (`painel/`)** — confirmado em `composer.json` / `package.json`:
- **Laravel `^13.8`** (PHP `^8.3`) + **Inertia Laravel `^3.1`**
- **React `^19.2`** + **@inertiajs/react `^3.6`** + **shadcn/ui** + **Tailwind 4** + **Vite 8** + **TypeScript** *(Vite 8 / TS via devDeps — a confirmar versões exatas)*
- UI libs: radix-ui, lucide-react, @tanstack/react-table, recharts, sonner, zod, ziggy-js, @dnd-kit
- Testes: **Pest 4** (`pestphp/pest ^4.7`)
- **Filament foi removido por completo** no commit `dca6e44` — não está em `composer.json`/`composer.lock`/`vendor/`. Qualquer menção a Filament nos READMEs é resíduo.

**Infra compartilhada:** nginx (vhost), PHP-FPM, MySQL 8.4, Redis (alpine). Docker Compose fica um nível acima do projeto.

---

## 3. Arquitetura e decisões-chave

### 3.1 A fronteira entre os dois serviços (decisão central)
- **Para ler**, o painel vai **direto na fonte** (MySQL, Redis, disco).
- **Para agir sobre disco/processo** (apagar arquivo, resolver canal via yt-dlp, enfileirar URL, purgar vídeos), o painel **nunca** toca o filesystem do pipeline — chama o **sidecar HTTP** do `clip-processor`. Isso substituiu o padrão anterior de `docker exec` / socket Docker (registrado em `painel/config/services.php:38-39`).
- **Exceção:** transições de status simples o painel escreve direto no MySQL (ex.: `approve()` → `UPDATE generated_clips SET status='approved' WHERE status='pending'`).

### 3.2 Sidecar interno (`clip-processor/src/internal_api.py`)
- Flask em `0.0.0.0:8090`, thread daemon, **sem porta publicada** (só rede docker `internal`).
- Auth por token compartilhado no header `X-Internal-Token` vs `CLIP_PROCESSOR_INTERNAL_TOKEN`. **Fail-closed:** env var vazia ⇒ toda rota responde 401. Sem rota de health check.
- Rotas (POST): `/internal/resolve-channel`, `/internal/process-url`, `/internal/reject-clip`, `/internal/delete-source-video`, `/internal/purge-old-videos`.
- **Caminho inverso:** `telegram_notifier.py` → `POST /internal/pipeline-event` no painel (mesmo token). Eventos: `upload_published`, `pipeline_failure`, `clip_ttl_warning`, `daily_summary`. Best-effort: falha nunca propaga para o pipeline.

### 3.3 Agendamento (APScheduler, `src/main.py`)
No boot: recupera downloads travados (`downloading` → `pending`), sobe o sidecar e roda um ciclo completo síncrono. Depois:

| Job | Função | Intervalo |
|---|---|---|
| `ingest_cycle` | `run_ingest_cycle` | 20 min |
| `publish_cycle` | `run_publish_only` | 20 min |
| `clip_pending_ttl` | `run_ttl_once` | 1 h |

Todos com `coalesce=True, max_instances=1, misfire_grace_time=900`. **Ingestão e publicação são jobs separados** (o ciclo completo só roda no boot).

### 3.4 Etapas do pipeline
1. **Descoberta** (`poll_all_channels`, `rss_poller.py`): RSS por `source_channel` ativo e não-blacklistado → dedup (Redis `SET NX`, TTL 30d, fallback MySQL) → filtro de título (bloqueia aposta/cassino) → detecção de formato (yt-dlp; falha ⇒ assume `curto`) → `INSERT status='pending'`.
2. **Download** (`pipeline_runner.py`): janela por formato que não se canibaliza — até **6 `curto`** e **4 `longo`** ocupando disco simultaneamente; baixa só o déficit. Só vídeos das últimas 24h (`FRESHNESS_DAYS=1`), `published_at DESC`. yt-dlp 720p, 3 tentativas, aborta se restar < 2 GB.
3. **Transcrição**: Groq Whisper (pt). Arquivo > 24 MB → MP3 antes.
4. **Seleção de momentos** (`selector.py`): Claude Haiku, score 0–10. Prompt varia por formato (`longo`: 1 segmento 600–1200 s, 20k chars; `curto`: até 3 momentos, 8k chars).
5. **Corte/pós** (`video_processor.py`): FFmpeg corta → SRT → legenda queimada → watermark → thumbnail. `curto` = crop 1080x1920; `longo` = `scale=-2:1080`.
6. **Metadata** (`metadata_generator.py`): Claude Haiku gera título, descrição e tags.
7. **Publicação** (`publisher.py`): cota + janela horária + round-robin.

> ⚠️ Nomenclatura enganosa: `rss_poller.py` também roda transcrição+seleção+corte, não só polling. Cada etapa em `try/except` isolado → `notify('pipeline_failure', ...)`; uma falha não derruba o scheduler.

### 3.5 Fallbacks de IA
| Chamada | Fallback |
|---|---|
| Seleção (Claude) | Groq LLaMA `llama-3.3-70b-versatile`; sem key vai direto no Groq; Groq falhando ⇒ nenhum momento |
| Metadata (Claude) | **Determinístico** (título = título original, descrição = `reason`, tags fixas); não cai para Groq |
| Transcrição (Whisper) | **Nenhum** → vídeo `failed` |
| Dedup (Redis) | `SELECT` no MySQL |
| Cota (Redis) | **Nenhum** → publicação para |

### 3.6 Cota, janela e round-robin (`quota_manager.py` + `publisher.py`)
- Chave Redis `youtube_uploads:{channel_id}:{data}` (+ contador `:longo`), tz SP, TTL até meia-noite local.
- `MAX_UPLOADS_PER_DAY` **clampado em [0, 6]** — teto rígido de 6/dia por canal no código, independente da env var.
- `MAX_LONGO_UPLOADS_PER_DAY` reserva parte da cota para `longo`; `curto` só tem o teto total.
- **Janela horária 19h–22h (SP)**, bypass via `UPLOAD_WINDOW_BYPASS=true`.
- **Round-robin por canal FONTE** (`_round_robin_by_source_channel`): clips saem `created_at ASC`, intercalados por origem.
- Roteamento fonte→destino por **nicho**: `source_channels.target_niche` casa com `destination_channels.niche`.
- Guard de corrida (`_transition_to_publishing`): só avança se o `UPDATE ... WHERE status=?` afetar linha.
- Vídeo fonte sem clip não-terminal e com ≥1 publicado ⇒ `.mp4` apagado, vídeo vira `published` com `local_path=NULL`.

### 3.7 OAuth do YouTube
Um token por canal-destino em `/app/youtube/token-{slug}.json`, gerado por CLI interativo `youtube_oauth.py`. Refresh falhando ⇒ `destination_channels.oauth_expired_flag=TRUE` (painel mostra badge); upload OK limpa a flag (self-healing).

---

## 4. Modelos / Schema principais (`clips_automation`)

**As tabelas do pipeline NÃO são geridas por migrations Laravel.** Nascem de SQL bruto em `mysql/init/01..07`, aplicado **manualmente** via `docker exec`. O painel apenas as mapeia com Eloquent (`$table` explícito). Consequências: `migrate:fresh` não reconstrói o schema do pipeline; `RefreshDatabase` está desligado (`tests/Pest.php`), testes usam `DatabaseTransactions`.

### `source_channels` (`mysql/init/01` + `06`)
`id PK`, `youtube_channel_id VARCHAR(64) UNIQUE NOT NULL`, `channel_name`, `target_niche VARCHAR(50) NULL`, `channel_handle VARCHAR(100) NULL`, `blacklisted BOOL NOT NULL DEFAULT FALSE` (com `INDEX idx_blacklisted`), `rss_url VARCHAR(512)`, `active BOOL DEFAULT TRUE`, `created_at`.

### `source_videos` (`01` + `03`)
`id PK`, `youtube_video_id VARCHAR(64) UNIQUE NOT NULL`, `channel_id INT NOT NULL`, `title`, `published_at`, `status ENUM(...)`, `local_path VARCHAR(1024)`, `transcript_path VARCHAR(500)`, `format ENUM('curto','longo') NOT NULL DEFAULT 'curto'`, `created_at`, `updated_at`.
- **FK** `fk_source_videos_channel`: `channel_id` → `source_channels(id)`.
- **ENUM status:** `pending, downloading, downloaded, transcribing, selecting, cutting, publishing, published, failed`.
- Eloquent `SourceVideo`: `belongsTo(SourceChannel, 'channel_id')`, `hasMany(GeneratedClip, 'source_video_id')`.

### `generated_clips` (`01` + `03`/`04`/`05`/`06`)
`id PK`, `source_video_id INT NOT NULL`, `destination_channel_id INT NULL`, `clip_path`, `thumbnail_path`, `title VARCHAR(200)`, `description TEXT`, `tags TEXT`, `score TINYINT`, `reason TEXT`, `start_time FLOAT`, `end_time FLOAT`, `youtube_video_id VARCHAR(64)`, `published_at TIMESTAMP NULL`, `scheduled_for TIMESTAMP NULL`, `upload_error TEXT NULL`, `status ENUM(...)`, `created_at`, `updated_at`.
- **FK** `fk_generated_clips_video`: `source_video_id` → `source_videos(id)`.
- **FK** `fk_generated_clips_destination_channel`: `destination_channel_id` → `destination_channels(id)`.
- **ENUM status:** `pending_cut, pending, cutting, publishing, published, failed, approved, rejected` (default `pending_cut`).
- Eloquent `GeneratedClip`: `belongsTo(SourceVideo)`, `belongsTo(DestinationChannel)`.

### `destination_channels` (`06` + `07`)
`id PK`, `slug VARCHAR(50) UNIQUE NOT NULL`, `name VARCHAR(120)`, `niche VARCHAR(50) NOT NULL`, `youtube_channel_id VARCHAR(50) UNIQUE NOT NULL`, `credit_template TEXT`, `active BOOL DEFAULT TRUE`, `oauth_expired_flag BOOL NOT NULL DEFAULT FALSE`, `created_at`, `updated_at`.
- Seed: `futebol-em-cortes` e `podcast-cortes` com `youtube_channel_id` **placeholder** (`UC_PLACEHOLDER_FUTEBOL` / `UC_PLACEHOLDER_PODCAST`).

### `niches` (**única tabela do pipeline via migration Laravel** — `2026_07_14_010214`)
Fonte de verdade dos selects do painel; seeda `futebol` e `podcast`.
> **Sem FK** ligando `source_channels.target_niche` / `destination_channels.niche` a `niches` — seguem VARCHAR livre.

### Tabelas Laravel padrão (mesmo database)
`users`, `sessions`, `cache`, `jobs` — migrations `0001_01_01_*`.

### Máquinas de estado
- **`source_videos.status`**: `pending → downloading → downloaded → transcribing → selecting → published` (ramos `→ failed`). `selecting` é o estado final de sucesso do ramo de IA; o publisher move para `published` depois. `cutting` existe no ENUM mas **nenhum código o escreve** em `source_videos`.
- **`generated_clips.status`**: `pending_cut → cutting → pending → publishing → published` (`→ failed`). `approved` **só o painel escreve**; `rejected` via painel/TTL. O que é publicável depende de `MANUAL_APPROVAL_REQUIRED` (`true` = só `approved`; `false` default = publica `pending` direto). `ttl_worker` auto-rejeita `pending` > `CLIP_PENDING_TTL_HOURS` (48h), avisa 1× no Telegram (idempotente via `clip_warned:{id}`).

---

## 5. Infra e deploy

- **Topologia:** `docker-compose.yml` fica **um nível acima**, em `/server/wordpress/`, **compartilhado** com outros projetos (kelnab, feeb, placebeads, riodelux, gringo). O compose lê o `.env` da raiz `wordpress/` — **não** o `canaldecortes/.env` (que está defasado).

| Serviço | Dono | Portas host | Papel |
|---|---|---|---|
| `clip-processor` | exclusivo | nenhuma | Daemon Python: pipeline + sidecar 8090 |
| `nginx` | compartilhado | 80 | Vhost `canaldecortes.local` |
| `php` | compartilhado | 9000 interno | PHP-FPM do painel |
| `mysql:8.4` | compartilhado | 3306 | Database `clips_automation` |
| `redis:alpine` | compartilhado | 6379 | Dedup + cota (db 0 = pipeline, db 1 = painel) |

- `postgres`, `minio`, `minio-init` pertencem a outros projetos (sem relação).
- **Acesso HTTP:** não há rota `/painel` no nginx — é só caminho no filesystem. Acesso por vhost `canaldecortes.local` → `docker/nginx/canaldecortes.conf` → root `/var/www/html/painel/public` → `fastcgi_pass php:9000`.
- **Serviços mortos** (comentados no compose só por histórico): **n8n** e **cloudflared**. n8n substituído pelo APScheduler (pipeline) + `Schedule::call()` do Laravel (`painel/routes/console.php`, resumo diário 18h BRT). Workflow n8n está `"active": false`.
- **Schema do pipeline aplicado à mão** (`docker exec` dos `mysql/init/*.sql`), não por migration. Operador do painel criado por `php artisan painel:create-user` (não há registro público); reset por `painel:reset-password {email}`.
- **Config sensível** vive no `.env` da raiz `wordpress/`: `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `CLIPS_DB_PASSWORD`, `CLIP_PROCESSOR_INTERNAL_TOKEN` (mesmo valor nos dois lados), `MANUAL_APPROVAL_REQUIRED`, `MAX_UPLOADS_PER_DAY`/`MAX_LONGO_UPLOADS_PER_DAY`, `UPLOAD_WINDOW_BYPASS`, `YOUTUBE_PRIVACY_STATUS` (default `private`), `CLIP_PENDING_TTL_HOURS`/`WARN_HOURS`, `LARAVEL_NOTIFY_URL`/`LARAVEL_HOST_HEADER`. `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID_ALLOWED` vivem no `painel/.env`.

---

## 6. Estado atual e limitações conhecidas

**Estado:** sistema funcional e em operação; pipeline automático da descoberta ao upload, com painel de observação/correção. Diretório `videos/` já tem ~130 subitens (uso real).

### Documentação desatualizada
- Ambos os READMEs (`README.md`, `painel/README.md`) ainda dizem "Filament" — **errado** desde `dca6e44` (painel é Inertia + React). `README.md` também não menciona a tabela `niches`.
- `.planning/research/ARCHITECTURE.md` é pesquisa de junho/2026 (planeja migração do bot para n8n e painel Filament — nenhum válido hoje). **Não usar como referência do estado atual.**
- `n8n/workflows/README.md` manda importar workflows num container que não existe mais.

### Código morto / dívida técnica
- `painel/app/Filament/Pages/Dashboard.php` — órfão da limpeza do Filament, `extends` classe inexistente no autoloader. `composer dump-autoload -o` com classmap authoritative daria fatal error. **Deve ser deletado.**
- `app-sidebar.tsx` — flag `external` / branch `<a>` eram só para rotas Filament; dead code.
- `scripts/validate-infra.sh` — checa n8n na 5678, termina com `exit 1`; **nunca passa**.
- `scripts/validate-phase6-n8n.py` — aponta para `telegram-n8n/` (inexistente); explode ao rodar.
- `dedup.mark_failed_redis` definida mas nunca chamada: download falho deixa `video:{id}` no Redis por 30d ⇒ RSS não re-ingere o vídeo.
- Nomes de teste ainda dizem "Resource" (`SourceChannelResourceTest`), conteúdo já é Inertia.
- `cutting` no ENUM de `source_videos` nunca é escrito (guard "arquivo em uso" nunca dispara por ele).

### Armadilhas de configuração
- **`env()` fora de config** em `DashboardController` (`MAX_UPLOADS_PER_DAY`, `MANUAL_APPROVAL_REQUIRED`): com `config:cache` ativo, `env()` retorna `null` e cai nos defaults silenciosamente — painel mostra número diferente do publisher.
- **Drift de default do `MAX_UPLOADS_PER_DAY`:** `:-2` no serviço `php`, `:-1` no `clip-processor` (só não morde porque a var está no `.env`).
- **`ANTHROPIC_API_KEY` vazia = falha silenciosa:** selector degrada limpo para Groq, mas `metadata_generator` instancia `anthropic.Anthropic()` sem key ⇒ exceção ⇒ **sempre** fallback determinístico (clip publicado com título bruto, sem erro visível).
- **Senha inconsistente:** `painel:create-user` exige ≥10 chars; reset pela UI (`SettingsController`) exige só 8.
- **`destination_channels` seedados com `youtube_channel_id` placeholder** — inválidos até o operador trocar no banco.
- `docker/nginx_conf/canaldecortes.conf` na raiz `wordpress/` tem 0 bytes (vestigial, sobrescrito pelo bind-mount).

### Cobertura de testes
- Painel: 35 testes, 13 arquivos (Pest 4). Cobrem comandos Telegram, aprovação/rejeição, eventos de pipeline, guards de auth, CRUD de canais, accessor OAuth, comandos Artisan.
- **Sem cobertura:** `SettingsController`, `ProcessVideoController`, `SourceVideoController`, `NicheController`, rota `clips.preview`. **Nenhum teste de frontend.**
- Pipeline Python: há suíte pytest em `clip-processor/tests/` — **cobertura exata a confirmar**.
