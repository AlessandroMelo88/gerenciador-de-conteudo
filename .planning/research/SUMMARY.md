# Research Summary: Canal de Cortes v2.0

**Researched:** 2026-06-21 | **Confidence:** HIGH

---

## Stack Additions

| Package | Version | Purpose |
|---------|---------|---------|
| `laravel/framework` | `^13.0` | Admin panel (Laravel 11 é EOL desde mar/2026 — usar 13) |
| `filament/filament` | `^5.0` | Admin UI — resources, widgets, forms (usar 5, não 3) |
| `livewire/livewire` | `^4.0` | Reactive layer (dependência do Filament v5) |
| `irazasyed/telegram-bot-sdk` | `^3.16` | Bot webhook em Laravel (v4 ainda WIP — usar 3.16) |

Sem novas bibliotecas Python. FFmpeg watermark usa `filter_complex overlay` já disponível.

---

## Feature Table Stakes

### Admin Panel (Filament)
- CRUD de canais-fonte (add/deactivate via formulário, sem SQL)
- CRUD de canais-destino com badge de OAuth (authorized/expired/missing)
- Dashboard de pipeline — status de source_videos e generated_clips com polling 5s
- Fila de clips: aprovar/rejeitar com modal de confirmação
- Auth básica via `php artisan make:filament-user`

### Multi-Canal YouTube
- Tabela `destination_channels` com `niche`, `token_file`, `uploads_per_day`
- Coluna `niche` em `source_channels` para roteamento
- Coluna `destination_channel_id` em `generated_clips`
- Quota Redis por canal: `youtube_uploads:{channel_id}:{date}`
- **GCP Project separado por canal-destino** (não opcional — quota é por projeto GCP)

### Telegram Bot (Laravel)
- Webhook `POST /telegramcanal` — substitui n8n + Cloudflare Tunnel
- Endpoint interno `POST /internal/pipeline-event` — substitui N8N_NOTIFY_URL
- Mesmos comandos do v1: /status, /clipes, /aprovar, /rejeitar, /processar, /ajuda
- Deduplicação de `update_id` via Redis desde o primeiro dia

### Copyright
- `burn_watermark()` em `video_processor.py` após `burn_subtitles`
- Blacklist verificada em `rss_poller.py` ANTES do download
- Créditos do canal original no prompt de `metadata_generator.py`
- Coluna `blacklisted` em `source_channels` gerenciável pelo painel

---

## Architecture Changes (mínimas no Python)

| Arquivo | Mudança | Linhas est. |
|---------|---------|-------------|
| `uploader.py` | `token_file` vira parâmetro obrigatório | ~1 |
| `publisher.py` | JOIN com `destination_channels`, quota por canal | ~10 |
| `quota_manager.py` | `channel_id` param, Redis key scoped | ~5 |
| `video_processor.py` | Adiciona `burn_watermark()` após subtítulos | ~15 |
| `metadata_generator.py` | Canal fonte no prompt, créditos na descrição | ~3 |
| `rss_poller.py` | Blacklist check + `assign_destination_channel()` | ~20 |
| `telegram_notifier.py` | Zero mudança de código — só env var `NOTIFY_URL` | 0 |

Schema — adições sem alterar colunas existentes:
```sql
CREATE TABLE destination_channels (id, name, niche, token_file, uploads_per_day, active)
CREATE TABLE channel_blacklist (id, channel_id, reason, created_at)
ALTER TABLE source_channels ADD COLUMN niche VARCHAR(100) DEFAULT 'futebol'
ALTER TABLE generated_clips ADD COLUMN destination_channel_id INT NULL
```

---

## Critical Warnings

1. **GCP Project separado por canal (CRÍTICO):** OAuth de dois canais no mesmo projeto GCP compartilha quota. 2 canais × 3 uploads × 1.600 unidades = 9.600/dia — qualquer chamada extra bloqueia tudo. Um projeto GCP por canal-destino, não negociável.

2. **OAuth app em Produção antes do primeiro upload público (CRÍTICO):** Apps em modo Testing expiram refresh token em 7 dias e publicam vídeos como privados silenciosamente. Aprovação Google leva 2–4 semanas — iniciar imediatamente ao configurar o primeiro canal.

3. **Nunca usar `--generate` do Filament em tabelas com ENUM (ALTO):** Gera input de texto livre no lugar do ENUM, permitindo corromper a state machine do pipeline. Criar resources com `Select::make()` e opções explícitas.

4. **Blacklist no RSS monitor, não no publisher (ALTO):** Verificação no publisher desperdiça Groq + Claude + FFmpeg antes de bloquear. Deve ser a primeira checagem em `rss_poller.py`.

5. **Deduplicar `update_id` do Telegram desde o dia 1 (ALTO):** Timeout ou HTTP 500 faz Telegram reenviar. `/aprovar 45` executado duas vezes corrompe estado. Armazenar `update_id` em Redis antes de processar qualquer comando.

---

## Build Order

| Phase | Nome | Entrega | Gate |
|-------|------|---------|------|
| 7 | Schema + Python Multi-Canal | Roteamento, quota por canal, watermark, blacklist, créditos | Pipeline publica no canal correto com watermark |
| 8 | Laravel/Filament Admin Panel | CRUD canais, dashboard, aprovar/rejeitar na web | Adicionar canal via formulário → row no MySQL |
| 9 | Telegram Bot no Laravel | Bot migrado do n8n, n8n desativado para bot | `/status` respondido pelo Laravel |
