# Phase 7: Schema Multi-Canal + Python Pipeline - Context

**Gathered:** 2026-06-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Estender o pipeline Python (`clip-processor`) para publicar clips no canal YouTube de destino correto por nicho, com quota Redis independente por canal, watermark queimado no FFmpeg antes do upload, créditos do canal original na descrição gerada pelo Claude, e bloqueio de canais blacklistados no RSS poller antes do download.

Esta fase mexe apenas em: schema MySQL (migrations), `clip-processor/src/` e `mysql/init/`. Painel Laravel fica na Fase 8.

</domain>

<decisions>
## Implementation Decisions

### Tabela destination_channels no MySQL

Criar tabela `destination_channels` (não ENV vars) — Filament da Fase 8 precisa de CRUD natural; ENV vars exigem restart a cada mudança e dão UX horrível no painel.

Schema decidido:
```sql
CREATE TABLE destination_channels (
  id                 INT AUTO_INCREMENT PRIMARY KEY,
  slug               VARCHAR(50) UNIQUE NOT NULL,          -- ex: 'futebol-em-cortes'
  name               VARCHAR(120) NOT NULL,                 -- nome exibido no painel
  niche              VARCHAR(50) NOT NULL,                  -- ex: 'futebol' — usado no roteamento
  youtube_channel_id VARCHAR(50) UNIQUE NOT NULL,          -- UCxxx do canal destino
  credit_template    TEXT,                                  -- ex: 'Créditos: @{channel_handle}'
  active             BOOLEAN DEFAULT TRUE,
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

Path do token e do watermark **não ficam na tabela** — derivados do `slug` por convenção (ver abaixo).

Roteamento: `source_channels` ganha coluna `target_niche VARCHAR(50)`. Pipeline busca `destination_channels WHERE niche = source_channel.target_niche`.

Seed inicial: 2 canais (futebol + podcast/variedades).

### OAuth por canal (token por arquivo, path derivado do slug)

- Arquivo `youtube/token-{slug}.json` por convenção de path — path **não fica no banco**
- `YouTubeUploader` recebe `channel_slug` e lê `f'/app/youtube/token-{channel_slug}.json'`
- `DEFAULT_TOKEN_FILE = '/app/token.json'` permanece como fallback para retrocompatibilidade (Phase 5 não quebra)
- Nova ferramenta: `python -m src.youtube_oauth --channel <slug>` — gera `token-{slug}.json` para cada canal destino (fluxo OAuth igual ao setup da Phase 1)
- Cada token é independente; refresh tokens não conflitam entre canais
- Edge case: token expirado/revogado → `telegram_notifier.notify('oauth_expired', {'channel_slug': slug})` (estende o CTRL-06 já existente)

### Watermark: PNG com alpha por canal, canto superior direito

- Path por convenção: `/app/branding/watermark-{slug}.png` — volume novo `./branding:/app/branding:ro`
- Tamanho recomendado: 100-180px de largura (testar contra Shorts 1080×1920)
- Posição: **canto superior direito** → filtro FFmpeg: `overlay=W-w-20:20` (margem 20px)
- Transparência: PNG com canal alpha resolve (sem flags extras no FFmpeg)
- Mudança em `video_processor.py`: adicionar passo de overlay após o corte/format existente, antes do `burn_subtitles`
- Edge case: arquivo de watermark ausente no disco → log warning + continua sem watermark (não quebra o pipeline)
- Rationale canto superior: canto inferior direito coberto pelos botões Subscribe/Like/Share/Comment em 95% dos devices móveis

### Blacklist de canais: coluna no banco + guard no RSS poller

- Adicionar coluna `blacklisted BOOLEAN DEFAULT FALSE` em `source_channels` + `INDEX idx_blacklisted`
- Guard no `rss_poller.py`: verificar `blacklisted = TRUE` antes de baixar o vídeo; registrar log antes de bloquear
- `rss_poller.py` descobre canais novos via feeds → ENV var não funciona para o desconhecido; coluna permite toggle via Filament na Fase 8
- Seed inicial: Globo Esporte, SBT, Band, ESPN Brasil com `blacklisted = TRUE` (IDs reais a preencher antes do docker compose up)
- Edge case retroativo: canal que vira blacklisted depois de ter `source_videos` na fila → **não mexer retroativamente**; vídeos já enfileirados continuam. Para purgar: SQL helper manual em `mysql/manual-workflow/`

### Quota por canal no Redis

- Estender `QuotaManager` para receber `channel_id` (ou `channel_slug`)
- Redis key muda de `youtube_uploads:{date}` para `youtube_uploads:{channel_id}:{date}`
- `publisher.py` instancia `QuotaManager(redis, channel_id=channel.youtube_channel_id)` por canal
- Limite padrão: 3 uploads/dia por canal (via `MAX_UPLOADS_PER_DAY`, mesma lógica existente)

### Créditos na descrição (COPY-02)

- `destination_channels.credit_template` armazena o template (ex: `"Créditos: @{channel_handle}"`)
- O campo `channel_handle` ou `channel_name` de `source_channels` preenche o template
- Créditos são adicionados **programaticamente** após o Claude gerar a descrição (não via prompt) — separação clara entre conteúdo gerado e metadados de compliance
- `source_channels` ganha coluna `channel_handle VARCHAR(100)` para armazenar o `@handle` do canal fonte

### Claude's Discretion

- Ordem exata dos filtros FFmpeg (watermark antes ou depois do burn_subtitles — testar qual dá melhor resultado visual)
- Mensagem de log exata quando canal blacklistado é bloqueado
- Estrutura interna do `youtube_oauth` helper (wizard interativo vs flags diretas)
- Estratégia de retry quando token OAuth expira durante upload (1 tentativa de refresh antes de notificar)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `clip-processor/src/uploader.py` — `YouTubeUploader.__init__` já aceita `token_file` como parâmetro; extensão para `channel_slug` é natural
- `clip-processor/src/quota_manager.py` — `_key(now)` retorna `youtube_uploads:{date}`; adicionar `channel_id` no construtor e na key
- `clip-processor/src/publisher.py` — `_fetch_pending_clips()` e `publish_pending_clips()` precisam receber `destination_channel` para roteamento e quota por canal
- `clip-processor/src/video_processor.py` — `burn_subtitles()` chama FFmpeg via `subprocess.run`; watermark entra como step adicional no mesmo padrão
- `clip-processor/src/rss_poller.py` — busca `source_channels` do MySQL; adicionar filtro `blacklisted = FALSE` e coluna `target_niche` no SELECT
- `clip-processor/src/telegram_notifier.py` — `notify()` já existe e é best-effort; reusar para `oauth_expired` e outros eventos de multi-canal
- `clip-processor/src/metadata_generator.py` — ponto de extensão para receber `credit_template` e appender créditos após geração do Claude

### Established Patterns

- **Migrations SQL:** idempotente via `INFORMATION_SCHEMA` + prepared statements (padrão dos arquivos 03, 04, 05 em `mysql/init/`)
- **ENV vars para limites:** `MAX_UPLOADS_PER_DAY` já resolve por variável de ambiente; `MANUAL_APPROVAL_REQUIRED` como toggle — seguir mesmo padrão
- **Injeção de dependência nos testes:** `YouTubeUploader(service=mock)`, `QuotaManager(redis_client=mock)` — seguir mesmo padrão nos novos módulos
- **Logger `_log()` por módulo:** padrão `[TIMESTAMP] [PREFIX] mensagem` em todos os módulos; manter

### Integration Points

- **MySQL `source_channels`:** adicionar colunas `target_niche` e `channel_handle`; adicionar coluna `blacklisted`
- **MySQL nova tabela `destination_channels`:** criada na migration da Fase 7; CRUD pelo Filament na Fase 8
- **Redis:** chave `youtube_uploads:{channel_id}:{date}` substituindo `youtube_uploads:{date}`
- **Docker volumes:** novo bind mount `./branding:/app/branding:ro` em `docker-compose.yml`
- **`clip-processor/src/publisher.py`:** recebe `destination_channel` object para roteamento, quota e credenciais
- **`clip-processor/src/video_processor.py`:** recebe `watermark_path` (derivado do slug do canal destino)

</code_context>

<specifics>
## Specific Ideas

- Roteamento é por `niche`: `source_channels.target_niche` → `destination_channels.niche` — join simples, sem lógica condicional no código Python
- Path do token segue slug: `token-futebol-em-cortes.json` — determinístico, sem campo no banco, sem risco de path errado no Filament
- Watermark no canto SUPERIOR DIREITO — não inferior como seria instintivo — porque os botões do YouTube Shorts cobrem o canto inferior direito em mobile
- Créditos adicionados programaticamente (não no prompt do Claude) — garante compliance independente do que o Claude retornar
- Blacklist retroativa não é automática — protege contra edge cases onde o operador blacklista um canal popular que já tem 20 vídeos na fila

</specifics>

<deferred>
## Deferred Ideas

- Dashboard de status de OAuth (token expirado/ativo) pelo painel — Fase 8 (PANEL-02 já inclui "status OAuth")
- Toggle de `blacklisted` pelo painel sem SQL — Fase 8
- Múltiplos nichos por canal-fonte (canal que publica futebol E podcast) — deferred; validar 1:1 primeiro
- Rate limiting por canal-fonte (não só por canal-destino) — deferred; não está nos requisitos v2.0

</deferred>

---

*Phase: 07-schema-multi-canal-python-pipeline*
*Context gathered: 2026-06-22*
