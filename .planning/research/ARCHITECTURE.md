# Architecture Research: Canal de Cortes v2.0

**Researched:** 2026-06-21
**Domain:** Laravel/Filament + Multi-canal YouTube + Telegram via webhook
**Confidence:** HIGH (código existente lido linha a linha; padrões de integração derivados da implementação real)

---

## Current Architecture (as-is)

```
Docker Compose (raiz: /server/wordpress/docker-compose.yml)
├── nginx          — proxy reverso, porta 80
├── php            — PHP-FPM para outros projetos do servidor
├── mysql:8.4      — DB compartilhado; clips_automation é database separado
├── redis:alpine   — quota counter + dedup SET
├── n8n:1.100.0    — orquestração: router Telegram + cron 18h BRT
├── cloudflared    — tunnel Cloudflare para webhook público do Telegram → n8n
└── clip-processor — daemon Python APScheduler, ciclo a cada 6h

clip-processor pipeline (pipeline_runner.py):
  poll_all_channels (rss_poller.py)
    → _download_pending_videos (downloader.py via yt-dlp)
    → _process_ai_pipeline (transcriber.py → selector.py)
    → _process_pending_clips (video_processor.py → metadata_generator.py)
    → publish_pending_clips (publisher.py → uploader.py)

Notificações:
  clip-processor POST → n8n /webhook/notify → Telegram API

Aprovação manual (Phase 6):
  Telegram → n8n execute command → rejeitar.py / processar.py / UPDATE SQL

Database: clips_automation
  source_channels (id, channel_name, rss_url, active)
  source_videos   (id, youtube_video_id, channel_id FK, status ENUM, title,
                   local_path, transcript_path, published_at, created_at)
  generated_clips (id, source_video_id FK, start_time, end_time, score, reason,
                   clip_path, thumbnail_path, title, description, tags,
                   status ENUM, youtube_video_id, published_at, upload_error, created_at)

status ENUM generated_clips:
  pending_cut | cutting | pending | approved | rejected | publishing | published | failed

OAuth: token único /app/token.json → um canal YouTube de destino
```

---

## New Components

### Laravel/Filament Container

**O que faz:**
- Painel web (Filament 3) para CRUD de source_channels, destination_channels e channel_blacklist sem SQL
- Dashboard de pipeline: lista source_videos e generated_clips com status em tempo real
- Gerenciamento de canais de destino: upload de token.json por canal, campo niche
- Bot Telegram via `irazasyed/telegram-bot-sdk`: recebe webhook POST em `/telegramcanal`, processa comandos, envia notificações
- Endpoint interno `/internal/pipeline-event`: recebe eventos do clip-processor (substitui n8n `/webhook/notify`)
- Cron scheduler do Laravel: resumo diário às 18h BRT (substitui cron n8n)
- Substitui n8n + cloudflared como destino para o bot Telegram

**Docker config sugerida:**
```yaml
laravel:
  build: ./canaldecortes/laravel
  container_name: laravel
  restart: unless-stopped
  environment:
    - APP_ENV=production
    - APP_KEY=${LARAVEL_APP_KEY}
    - DB_HOST=mysql
    - DB_DATABASE=clips_automation
    - DB_USERNAME=clips_user
    - DB_PASSWORD=${CLIPS_DB_PASSWORD}
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - TELEGRAM_CHAT_ID_ALLOWED=${TELEGRAM_CHAT_ID_ALLOWED}
    - REDIS_HOST=redis
    - REDIS_PORT=6379
  volumes:
    - ./canaldecortes/laravel:/var/www/html/laravel
    - ./canaldecortes/youtube/tokens:/app/tokens:ro
  networks:
    - internal
  depends_on:
    - mysql
    - redis
```

**nginx:** adicionar `location /telegramcanal` e `location /painel` apontando para `laravel:8000`.

---

### Tabela `destination_channels`

```sql
CREATE TABLE destination_channels (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    channel_name        VARCHAR(255) NOT NULL,
    youtube_channel_id  VARCHAR(50)  NOT NULL UNIQUE,
    niche               VARCHAR(100) NOT NULL,          -- 'futebol', 'podcasts', etc.
    token_file          VARCHAR(500) NOT NULL,           -- /app/tokens/futebol.json
    uploads_per_day     TINYINT UNSIGNED NOT NULL DEFAULT 3,
    active              TINYINT(1) NOT NULL DEFAULT 1,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

### Tabela `channel_blacklist`

```sql
CREATE TABLE channel_blacklist (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    pattern     VARCHAR(255) NOT NULL,  -- youtube_channel_id, channel_name ou keyword
    reason      VARCHAR(500),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

### Webhook Telegram no Laravel

- Rota: `POST /telegramcanal`
- Controller: `TelegramController@handle`
- Usa `irazasyed/telegram-bot-sdk` para parsear o Update e despachar comandos
- Comandos a migrar do n8n: `/status`, `/clipes`, `/aprovar`, `/rejeitar`, `/processar`, `/ajuda`
- Allowlist: verificar `$update->getMessage()->getChat()->getId() === TELEGRAM_CHAT_ID_ALLOWED`

---

## Integration Points (what changes in existing code)

### uploader.py

**Mudança:** `token_file` deixa de ter fallback global. Torna-se parâmetro obrigatório passado pelo publisher a partir de `destination_channels.token_file`.

```python
# ANTES
def __init__(self, token_file=None, ...):
    self.token_file = token_file or os.environ.get('YOUTUBE_TOKEN_FILE', DEFAULT_TOKEN_FILE)

# DEPOIS
def __init__(self, token_file: str, ...):
    self.token_file = token_file  # chamador é responsável; sem fallback global
```

---

### publisher.py

**Mudança 1 — fetch:** `_fetch_pending_clips` expande o SELECT para trazer `destination_channel_id`, `token_file` e `uploads_per_day` via JOIN com `destination_channels`.

```python
'SELECT gc.id, gc.source_video_id, gc.clip_path, gc.thumbnail_path, '
'gc.title, gc.description, gc.tags, sv.local_path AS source_local_path, '
'gc.destination_channel_id, dc.token_file, dc.uploads_per_day '
'FROM generated_clips gc '
'JOIN source_videos sv ON sv.id = gc.source_video_id '
'JOIN destination_channels dc ON dc.id = gc.destination_channel_id '
'WHERE gc.status = %s AND gc.clip_path IS NOT NULL AND gc.title IS NOT NULL '
'ORDER BY gc.created_at ASC'
```

**Mudança 2 — quota por canal:** `QuotaManager` recebe `channel_id` para usar chave Redis com escopo por canal: `youtube_uploads:{channel_id}:{date}`. `max_uploads_per_day` vem do banco, não de env var global.

**Mudança 3 — uploader por clip:** dentro do loop de publicação, criar `YouTubeUploader(token_file=clip['token_file'])` por iteração em vez de receber uploader fixo como parâmetro.

**Mudança 4 — assinatura:** remover parâmetro `uploader` de `publish_pending_clips` (ou torná-lo opcional e ignorado).

---

### rss_poller.py

**Mudança 1 — `assign_destination_channel` (nova função):** chamada dentro de `_process_ai_pipeline` após `insert_selected_moments`. Lê `source_channels.niche` para o canal-fonte, busca `destination_channels WHERE niche=? AND active=1 LIMIT 1` e faz UPDATE em `generated_clips.destination_channel_id`.

**Mudança 2 — blacklist:** antes de `insert_video`, verificar se `channel_name` ou `youtube_video_id` bate com algum `channel_blacklist.pattern`. Se sim, skip com log. Zero impacto no happy path.

**Mudança 3 — SELECT em `poll_all_channels`:** adicionar `niche` ao SELECT de `source_channels` (mudança trivial de string SQL).

---

### video_processor.py

**Nova função `burn_watermark`:**

```python
def burn_watermark(input_path: str, watermark_path: str, output_path: str) -> str:
    """Queima logo PNG no canto superior direito via FFmpeg overlay."""
    subprocess.run([
        'ffmpeg', '-i', input_path, '-i', watermark_path,
        '-filter_complex', 'overlay=W-w-20:20',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
        '-c:a', 'copy', output_path, '-y',
    ], check=True, capture_output=True)
    return output_path
```

**Integração em `process_clip`:** inserir `burn_watermark` entre `burn_subtitles` e `extract_thumbnail`. Sequência final:

```
cut_clip → burn_subtitles → burn_watermark → extract_thumbnail
```

O arquivo de watermark é `/app/watermark.png` (controlado por env var `WATERMARK_PATH`, com fallback para `/app/watermark.png`). Se o arquivo não existir, o step é pulado com log de aviso (não falha o pipeline).

---

### metadata_generator.py

**Mudança no SYSTEM_PROMPT:**
```python
SYSTEM_PROMPT = (
    "..."
    "A descrição deve incluir ao final: 'Créditos: [nome do canal original]'."
)
```

**Mudança no prompt em `generate_metadata`:**
```python
f"Canal original: {clip_context.get('source_channel', '')}\n"
```

---

### video_processor.py — `_fetch_clip` e `_build_clip_context`

Para passar `source_channel_name` ao metadata_generator, `_fetch_clip` precisa fazer JOIN com `source_channels`:

```python
'SELECT gc.id, gc.source_video_id, gc.start_time, gc.end_time, gc.score, gc.reason, '
'sv.youtube_video_id, sv.title AS source_title, sv.local_path, sv.transcript_path, '
'sc.channel_name AS source_channel_name '
'FROM generated_clips gc '
'JOIN source_videos sv ON sv.id = gc.source_video_id '
'JOIN source_channels sc ON sc.id = sv.channel_id '
'WHERE gc.id = %s'
```

`_build_clip_context` adiciona `'source_channel': clip.get('source_channel_name', '')`.

---

### telegram_notifier.py

**Mudança zero no código Python.** Apenas a variável de ambiente `N8N_NOTIFY_URL` (atualmente `http://n8n:5678/webhook/notify`) é substituída por uma nova env var apontando para o endpoint Laravel:

```
NOTIFY_URL=http://laravel:8000/internal/pipeline-event
```

O módulo `telegram_notifier.py` pode continuar como está se a leitura for mudada para `NOTIFY_URL`, ou pode ser renomeada internamente. O padrão best-effort (never propagate) permanece idêntico.

---

### pipeline_runner.py

**Mudança:** remover `uploader=YouTubeUploader()` da chamada a `publish_pending_clips` (linha 92 atual). O publisher passará a criar o uploader internamente por clip. Nenhuma outra mudança estrutural.

---

### quota_manager.py

**Mudança:** adicionar parâmetro `channel_id` ao construtor; usar na geração da chave Redis.

```python
def __init__(self, redis_client, channel_id: str, max_uploads_per_day: int | None = None):
    self.channel_id = channel_id
    ...

def _key(self, now: datetime) -> str:
    return f'youtube_uploads:{self.channel_id}:{now.strftime("%Y-%m-%d")}'
```

`ABSOLUTE_MAX_UPLOADS_PER_DAY = 6` permanece como teto global por canal (não total).

---

## Database Schema Changes

### Novas tabelas

```sql
-- 1. Canais de destino YouTube (multi-canal)
CREATE TABLE destination_channels (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    channel_name        VARCHAR(255) NOT NULL,
    youtube_channel_id  VARCHAR(50)  NOT NULL UNIQUE,
    niche               VARCHAR(100) NOT NULL,
    token_file          VARCHAR(500) NOT NULL,
    uploads_per_day     TINYINT UNSIGNED NOT NULL DEFAULT 3,
    active              TINYINT(1) NOT NULL DEFAULT 1,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Blacklist de canais-fonte
CREATE TABLE channel_blacklist (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    pattern     VARCHAR(255) NOT NULL,
    reason      VARCHAR(500),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Colunas adicionadas a tabelas existentes

```sql
-- source_channels: campo niche para roteamento
ALTER TABLE source_channels
    ADD COLUMN niche VARCHAR(100) NOT NULL DEFAULT 'futebol' AFTER channel_name;

-- generated_clips: FK para canal de destino selecionado
ALTER TABLE generated_clips
    ADD COLUMN destination_channel_id INT NULL AFTER source_video_id,
    ADD CONSTRAINT fk_gc_dest_channel
        FOREIGN KEY (destination_channel_id)
        REFERENCES destination_channels(id)
        ON DELETE SET NULL;
```

**Nota MySQL 8.4:** `ADD COLUMN IF NOT EXISTS` não é suportado. Usar migration com check via `INFORMATION_SCHEMA.COLUMNS` (padrão estabelecido na Phase 4 do projeto).

---

## Docker Compose Changes

### Novo serviço `laravel`

```yaml
laravel:
  build: ./canaldecortes/laravel
  container_name: laravel
  restart: unless-stopped
  environment:
    - APP_ENV=production
    - APP_KEY=${LARAVEL_APP_KEY}
    - DB_HOST=mysql
    - DB_DATABASE=clips_automation
    - DB_USERNAME=clips_user
    - DB_PASSWORD=${CLIPS_DB_PASSWORD}
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - TELEGRAM_CHAT_ID_ALLOWED=${TELEGRAM_CHAT_ID_ALLOWED}
    - REDIS_HOST=redis
    - REDIS_PORT=6379
  volumes:
    - ./canaldecortes/laravel:/var/www/html/laravel
    - ./canaldecortes/youtube/tokens:/app/tokens:ro
  networks:
    - internal
  depends_on:
    - mysql
    - redis
```

### Mudanças no serviço `clip-processor`

```yaml
# Volumes: substituir token único por diretório de tokens por canal
# REMOVER:
- ./canaldecortes/youtube/token.json:/app/token.json:ro

# ADICIONAR:
- ./canaldecortes/youtube/tokens:/app/tokens:ro
- ./canaldecortes/youtube/watermark.png:/app/watermark.png:ro

# Env vars: substituir N8N_NOTIFY_URL por NOTIFY_URL
# REMOVER implícito (não estava no compose, estava em telegram_notifier.py como default):
#   N8N_NOTIFY_URL=http://n8n:5678/webhook/notify

# ADICIONAR:
- NOTIFY_URL=http://laravel:8000/internal/pipeline-event
- WATERMARK_PATH=/app/watermark.png
```

### nginx

Adicionar dois `location` blocks no arquivo de configuração existente:

```nginx
location /telegramcanal {
    proxy_pass http://laravel:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

location /painel {
    proxy_pass http://laravel:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### `cloudflared`

Container permanece idêntico no docker-compose. Apenas o destino do tunnel muda: no Cloudflare Zero Trust dashboard, atualizar a URL de `http://n8n:5678` para `http://laravel:8000`. Operação manual.

### `n8n`

Container permanece no docker-compose para não quebrar estado existente. Workflows do bot Telegram são desativados após migração para o Laravel. O cron diário de 18h BRT migra para o Laravel Scheduler.

---

## Data Flow (novo)

### Fluxo completo com multi-canal

```
1. poll_all_channels()
   source_channels (niche='futebol', active=1) → RSS
   [blacklist check] → se canal na blacklist, skip
   → insert_video → source_videos (status=pending)

2. _download_pending_videos()
   source_videos (pending) → yt-dlp → source_videos (downloaded)

3. _process_ai_pipeline()
   source_videos (downloaded)
   → transcriber.py (Groq Whisper) → salva transcript JSON
   → selector.py (Claude Haiku) → insert_selected_moments
   → assign_destination_channel()    [NOVO]
       source_channels.niche='futebol'
       → SELECT destination_channels WHERE niche='futebol' AND active=1 LIMIT 1
       → UPDATE generated_clips SET destination_channel_id=<id>
   → generated_clips (status=pending_cut, destination_channel_id=X)

4. _process_pending_clips() → process_clip()
   generated_clips (pending_cut)
   → cut_clip        (FFmpeg: corta + resize 9:16)
   → burn_subtitles  (FFmpeg: legenda queimada)
   → burn_watermark  (FFmpeg: logo overlay)  [NOVO]
   → extract_thumbnail
   → generate_metadata (Claude Haiku + source_channel_name para créditos)  [MODIFICADO]
   → generated_clips (status=pending)

5. publish_pending_clips()
   Para cada clip (pending, destination_channel_id=X):
   → JOIN destination_channels → pega token_file, uploads_per_day
   → QuotaManager(channel_id=X, max=uploads_per_day).can_upload()  [MODIFICADO]
   → YouTubeUploader(token_file=dc.token_file).upload_clip(clip)   [MODIFICADO]
   → generated_clips (status=published)

Diagrama de roteamento:
  source_channel niche='futebol'   → destination_channels[id=1] → /app/tokens/futebol.json
  source_channel niche='podcasts'  → destination_channels[id=2] → /app/tokens/podcasts.json
```

### Fluxo de notificações (novo)

```
clip-processor → POST http://laravel:8000/internal/pipeline-event
    {'event': 'upload_published', 'payload': {...}}
    ↓
Laravel PipelineEventController
    → irazasyed/telegram-bot-sdk → sendMessage(chat_id, texto formatado)
    → Telegram API → operador
```

### Fluxo do bot Telegram (novo)

```
operador → Telegram → POST https://alessandromelo.com.br/telegramcanal
    ↓  (nginx proxy → laravel:8000)
TelegramController@handle
    → verificar allowlist chat_id
    ├── /status    → SELECT COUNT FROM generated_clips WHERE status='pending'
    ├── /clipes    → SELECT últimos 5 clips com status
    ├── /aprovar N → UPDATE generated_clips SET status='approved' WHERE id=N AND status='pending'
    ├── /rejeitar N → UPDATE + DELETE clip file  (lógica de rejeitar.py migrada para PHP)
    ├── /processar URL → yt-dlp metadata + upsert source_videos  (lógica de processar.py migrada)
    └── /ajuda     → mensagem de texto fixa
```

---

## Suggested Build Order

Numeração continua a partir da Phase 6 (Phase 6 assume concluída — checkpoints manuais Telegram/Cloudflare feitos).

---

### Phase 7: Schema Multi-Canal + Watermark + Copyright (Python puro)

**Goal:** Banco de dados pronto para multi-canal e copyright; pipeline Python atualizado. Verificável sem painel web.

**Dependências:** Phase 6 completa

**O que entra:**
- Migration SQL: `destination_channels`, `channel_blacklist`, `source_channels.niche`, `generated_clips.destination_channel_id`
- `quota_manager.py`: parâmetro `channel_id`, chave Redis por canal
- `uploader.py`: `token_file` como parâmetro obrigatório sem fallback
- `publisher.py`: fetch com JOIN, QuotaManager por canal, YouTubeUploader por clip
- `rss_poller.py`: `assign_destination_channel` + blacklist check
- `video_processor.py`: função `burn_watermark` + integração em `process_clip`; JOIN com `source_channels` em `_fetch_clip`
- `metadata_generator.py`: `source_channel` no context + créditos no SYSTEM_PROMPT
- `pipeline_runner.py`: remover `uploader=YouTubeUploader()` fixo
- Seed SQL: 2 registros em `destination_channels` (futebol + podcasts), `source_channels.niche` atualizado
- Watermark PNG placeholder em `canaldecortes/youtube/watermark.png`
- Diretório `canaldecortes/youtube/tokens/` com token(s) existente(s) renomeados

**Verificação:** rodar pipeline localmente; confirmar `destination_channel_id` preenchido nos clips, watermark visível, créditos na descrição.

---

### Phase 8: Laravel/Filament — Painel Base + Dashboard

**Goal:** Container Laravel funcionando com Filament 3 conectado ao MySQL existente. Operador consegue adicionar canais e ver status do pipeline sem abrir o terminal.

**Dependências:** Phase 7 (schema multi-canal já existe)

**O que entra:**
- Projeto Laravel 11 em `canaldecortes/laravel/`
- `Dockerfile` para container Laravel (php-fpm + nginx, ou `php artisan serve` simplificado para dev)
- Conexão ao banco `clips_automation` (não cria banco próprio)
- Models Eloquent: `SourceChannel`, `DestinationChannel`, `SourceVideo`, `GeneratedClip`, `ChannelBlacklist`
- Filament Resources: `SourceChannelResource`, `DestinationChannelResource`, `ChannelBlacklistResource`
- Filament Page: `PipelineDashboard` — tabela de `source_videos` + `generated_clips` com status e timestamps
- Upload de `token.json` por canal: Filament FileUpload salva em `/app/tokens/{slug}.json`
- docker-compose: serviço `laravel` adicionado
- nginx: `location /painel` ativo; `/telegramcanal` pode retornar 404 por enquanto

**Verificação:** acessar `http://localhost/painel`, adicionar canal-fonte via form, confirmar registro no MySQL.

---

### Phase 9: Bot Telegram no Laravel + Migração do n8n

**Goal:** Toda a lógica do bot Telegram migra do n8n para o Laravel. Cloudflare Tunnel aponta para Laravel. n8n deixa de ser necessário para o bot.

**Dependências:** Phase 8 (Laravel funcionando e acessível)

**O que entra:**
- Instalar `irazasyed/telegram-bot-sdk` (compatível com Laravel 11)
- `TelegramController@handle`: parsear Update, verificar allowlist, despachar comandos
- Implementar todos os 6 comandos no Laravel (replicar lógica de `rejeitar.py`, `processar.py`, MySQL nodes do n8n)
  - `/processar`: pode chamar `processar.py` via `shell_exec('docker exec clip-processor ...')` por enquanto
- `PipelineEventController@receive`: endpoint `POST /internal/pipeline-event`, formata mensagem e envia via SDK
- Laravel Scheduler: cron de resumo diário às 18h BRT (`php artisan schedule:run` via supervisor)
- nginx: ativar `location /telegramcanal`
- clip-processor: env var `NOTIFY_URL=http://laravel:8000/internal/pipeline-event` (substituir valor default de `N8N_NOTIFY_URL`)
- Cloudflare Tunnel: atualizar destino para `http://laravel:8000` (operação manual no CF dashboard)
- n8n: desativar workflows de bot (container permanece no compose)

**Verificação:** enviar `/status` no Telegram → resposta vem do Laravel (não do n8n). Upload publicado gera notificação via endpoint Laravel.

---

## Confidence Assessment

| Área | Nível | Razão |
|------|-------|-------|
| Integration points Python | HIGH | Código lido linha a linha; mudanças mapeadas a funções específicas |
| Schema DB | HIGH | Schema atual verificado; novas tabelas derivadas dos requisitos documentados |
| Docker Compose | HIGH | docker-compose.yml atual lido; mudanças são incrementais sobre estrutura já conhecida |
| Build order | HIGH | Dependências entre fases são claras e sem ciclos |
| Laravel/Filament interno | MEDIUM | Stack definida no PROJECT.md (Laravel 11 + Filament 3); implementação interna não verificada via Context7 — planner deve confirmar versões e pacotes |
| irazasyed/telegram-bot-sdk | MEDIUM | Pacote padrão para Laravel + Telegram; planner deve confirmar compatibilidade com Laravel 11 |

---

## Open Questions

1. **n8n após migração**
   - O que se sabe: n8n faz routing de comandos + cron + notificações; tudo migrará para Laravel na Phase 9
   - O que não está claro: se n8n permanece como trigger de pipeline ou pode ser removido completamente
   - Recomendação: manter n8n no compose mas desativar workflows do bot; APScheduler no clip-processor já cobre o ciclo de 6h sem n8n

2. **Armazenamento seguro de token.json por canal**
   - O que se sabe: cada `destination_channel` precisa de token OAuth separado; upload via Filament
   - O que não está claro: se o Filament FileUpload é suficientemente seguro para arquivos sensíveis
   - Recomendação: salvar tokens em `/app/tokens/` (volume Docker fora do webroot); Filament exibe apenas nome do arquivo, nunca conteúdo

3. **`/processar` no Laravel: PHP nativo vs exec Python**
   - O que se sabe: `processar.py` usa yt-dlp via `YoutubeDL(skip_download=True)` — dependência Python
   - O que não está claro: se Laravel deve reimplementar a lógica em PHP ou delegar ao container Python
   - Recomendação: Phase 9 usa `shell_exec('docker exec clip-processor python -m src.processar {url}')` para reutilizar código existente; refatorar para API HTTP interna em milestone futuro se necessário

4. **Quota Redis com múltiplos canais**
   - O que se sabe: `QuotaManager` atual usa chave `youtube_uploads:{date}` sem escopo de canal
   - Impacto: sem mudança, 2 canais compartilhariam quota → máx 3 uploads totais/dia em vez de 3 por canal
   - Recomendação: chave `youtube_uploads:{channel_id}:{date}` — independente por canal; 2 canais × 3 = 6 uploads totais dentro dos 10.000 unidades/dia da quota gratuita

---

## Sources

**Código lido diretamente (HIGH confidence):**
- `clip-processor/src/uploader.py` — token handling, upload resumível, estrutura YouTubeUploader
- `clip-processor/src/publisher.py` — fetch, quota guard, status transitions
- `clip-processor/src/video_processor.py` — FFmpeg pipeline, process_clip flow
- `clip-processor/src/metadata_generator.py` — SYSTEM_PROMPT, generate_metadata, context dict
- `clip-processor/src/telegram_notifier.py` — N8N_NOTIFY_URL, best-effort POST
- `clip-processor/src/pipeline_runner.py` — run_pipeline_once, uploader fixo atual
- `clip-processor/src/rss_poller.py` — poll_all_channels, _process_ai_pipeline
- `clip-processor/src/quota_manager.py` — chave Redis, limites, can_upload
- `clip-processor/src/main.py` — APScheduler, ciclo 6h
- `docker-compose.yml` — serviços atuais, volumes, redes, env vars

**Arquivos de planejamento (HIGH confidence):**
- `.planning/PROJECT.md` — decisões arquiteturais, requisitos v2.0
- `.planning/REQUIREMENTS.md` — requisitos funcionais v1 e v2
- `.planning/ROADMAP.md` — fases concluídas e em andamento
- `.planning/STATE.md` — decisões acumuladas de cada fase
