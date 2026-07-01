# Requirements: Canal de Cortes — Futebol & Esportes

**Defined:** 2026-06-17
**Core Value:** O pipeline extrai e publica cortes virais automaticamente — do monitoramento à publicação em múltiplos canais — sem intervenção humana para cada vídeo.

## v1 Requirements (Complete — Milestone v1.0)

### Infraestrutura

- [x] **INFRA-01**: Sistema roda inteiramente em Docker no docker-compose existente
- [x] **INFRA-02**: Banco de dados `clips_automation` criado no MySQL existente com tabelas source_channels, source_videos e generated_clips
- [x] **INFRA-03**: Canal do YouTube criado, conta verificada, banner e bio preenchidos antes do primeiro upload
- [x] **INFRA-04**: Variáveis de ambiente e secrets configurados (.env com Claude API key, YouTube OAuth credentials)

### Aquisição de Conteúdo

- [x] **ACQU-01**: Sistema monitora canais de YouTube pré-configurados via RSS (sem consumir cota de API) a cada 6 horas
- [x] **ACQU-02**: Novos vídeos detectados são baixados automaticamente em 720p via yt-dlp
- [x] **ACQU-03**: Sistema não reprocessa vídeos já processados (deduplicação via Redis SET + MySQL UNIQUE em youtube_video_id)

### Processamento com IA

- [x] **AI-01**: Áudio do vídeo é transcrito via Groq Whisper API com idioma PT-BR, gerando texto com timestamps
- [x] **AI-02**: Claude Haiku API analisa a transcrição completa e retorna lista de momentos de alto impacto com score 1-10, start/end e motivo
- [x] **AI-03**: Apenas momentos com score ≥ 7 são enviados para corte (filtro de qualidade)

### Processamento de Vídeo

- [x] **VID-01**: FFmpeg corta o clip nos timestamps selecionados pela IA e faz resize para formato 9:16 (1080x1920) compatível com YouTube Shorts
- [x] **VID-02**: Legendas geradas pelo Whisper são queimadas no clip final com fonte legível e bordas
- [x] **VID-03**: Thumbnail automática é extraída do frame mais impactante do clip
- [x] **VID-04**: Claude Haiku gera título (máx 100 chars), descrição e tags otimizados para YouTube SEO

### Publicação

- [x] **PUB-01**: Clips prontos são publicados automaticamente no YouTube via Data API v3 com título, descrição, tags e thumbnail
- [x] **PUB-02**: Sistema respeita cota diária do YouTube usando contador Redis com reset à meia-noite
- [x] **PUB-03**: Uploads são agendados nos horários de maior audiência (19h-22h horário de Brasília)
- [x] **PUB-04**: Vídeos brutos são deletados automaticamente após processamento bem-sucedido

### Orquestração

- [x] **ORC-01**: n8n orquestra todo o pipeline end-to-end com tratamento de erros e retry
- [x] **ORC-02**: Status de cada job é registrado no MySQL

### Controle Manual

- [x] **CTRL-01**: Bot Telegram aceita comandos /status, /clipes, /aprovar, /rejeitar, /processar, /ajuda somente da allowlist
- [x] **CTRL-02**: publisher.py controlado por MANUAL_APPROVAL_REQUIRED; publica approved (manual) ou pending (auto)
- [x] **CTRL-03**: /aprovar muda pending→approved; /rejeitar muda pending→rejected e apaga MP4
- [x] **CTRL-04**: /processar insere vídeo arbitrário como pending (idempotente)
- [x] **CTRL-05**: Worker de TTL converte clips pending em rejected após 48h; aviso 24h antes
- [x] **CTRL-06**: Bot envia notificações proativas: upload publicado, falha crítica, resumo diário 18h BRT

---

## v2 Requirements (Active — Milestone v2.0)

### Multi-Canal

- [x] **MCAN-01**: Sistema suporta múltiplos canais YouTube de destino, cada um com token OAuth próprio e GCP Project separado
- [x] **MCAN-02**: Canais-fonte têm campo `niche` (futebol, podcast, etc.) que determina qual canal-destino recebe o clip
- [x] **MCAN-03**: Cota de uploads é independente por canal-destino (3/dia por canal; 2 canais = 6/dia total)
- [x] **MCAN-04**: Pipeline publica automaticamente 3 vídeos/dia por canal no horário 19h-22h BRT

### Copyright

- [x] **COPY-01**: Watermark/logo do canal é queimado no clip via FFmpeg após geração das legendas
- [x] **COPY-02**: Descrição gerada pelo Claude inclui créditos do canal original ("Créditos: @canal")
- [x] **COPY-03**: Canais blacklistados (Globo, SBT, Band, ESPN direto, Liga/Conmebol) são bloqueados no RSS poller antes do download

### Admin Panel

- [x] **PANEL-01**: Operador pode adicionar/remover/desativar canais-fonte via formulário web (URL do YouTube ou channel_id) sem SQL
- [x] **PANEL-02**: Operador pode adicionar canais-destino com niche e status OAuth (authorized/expired/missing) pelo painel
- [ ] **PANEL-03**: Dashboard mostra status em tempo real de source_videos e generated_clips com atualização automática
- [x] **PANEL-04**: Operador pode aprovar ou rejeitar clips da fila pelo painel web (alternativa ao Telegram)
- [ ] **PANEL-05**: Painel protegido por autenticação básica de usuário/senha

### Telegram Bot (Laravel)

- [ ] **BOT-01**: Bot Telegram migrado para Laravel; webhook em `alessandromelo.com.br/telegramcanal` via nginx → Laravel
- [ ] **BOT-02**: Todos os 6 comandos do v1 funcionam no novo bot Laravel com deduplicação de update_id via Redis
- [ ] **BOT-03**: Notificações do pipeline Python (upload publicado, falha crítica, resumo diário) enviadas via Laravel

---

## v3 Requirements (Deferred)

### Expansão de Plataformas

- **EXP-01**: Publicação simultânea no Instagram Reels
- **EXP-02**: Publicação simultânea no TikTok
- **EXP-03**: Canal de política (após validar futebol + podcasts)

### Otimização e Analytics

- **OPT-01**: Dashboard de métricas YouTube (views, subs, watch time por clip)
- **OPT-02**: A/B test de títulos/thumbnails
- **OPT-03**: Detecção de momentos por pico de volume de áudio

## Out of Scope

| Feature | Motivo |
|---------|--------|
| TikTok/Instagram no v2 | API do TikTok é restrita; validar escala YouTube primeiro |
| Edição manual de clips | Contradiz o objetivo de 100% automatizado |
| Geração de vídeo com IA (avatares/voz sintética) | Complexidade e custo altos; foge do modelo de canal de cortes |
| Canal de política no v2 | Risco de demonetização; validar futebol/podcasts primeiro |
| Site/blog para espectadores | O canal é o YouTube; não precisamos de site separado |
| Moderação de comentários | Não impacta crescimento |
| Content ID API | Não disponível para contas comuns; blacklist manual é a proteção correta |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 1 | Complete |
| INFRA-03 | Phase 1 | Complete |
| INFRA-04 | Phase 1 | Complete |
| ACQU-01 | Phase 2 | Complete |
| ACQU-02 | Phase 2 | Complete |
| ACQU-03 | Phase 2 | Complete |
| ORC-02 | Phase 2 | Complete |
| AI-01 | Phase 3 | Complete |
| AI-02 | Phase 3 | Complete |
| AI-03 | Phase 3 | Complete |
| VID-01 | Phase 4 | Complete |
| VID-02 | Phase 4 | Complete |
| VID-03 | Phase 4 | Complete |
| VID-04 | Phase 4 | Complete |
| PUB-01 | Phase 5 | Complete |
| PUB-02 | Phase 5 | Complete |
| PUB-03 | Phase 5 | Complete |
| PUB-04 | Phase 5 | Complete |
| ORC-01 | Phase 5 | Complete |
| CTRL-01 | Phase 6 | Complete |
| CTRL-02 | Phase 6 | Complete |
| CTRL-03 | Phase 6 | Complete |
| CTRL-04 | Phase 6 | Complete |
| CTRL-05 | Phase 6 | Complete |
| CTRL-06 | Phase 6 | Complete |
| MCAN-01 | Phase 7 | Complete |
| MCAN-02 | Phase 7 | Complete |
| MCAN-03 | Phase 7 | Complete |
| MCAN-04 | Phase 7 | Complete |
| COPY-01 | Phase 7 | Complete |
| COPY-02 | Phase 7 | Complete |
| COPY-03 | Phase 7 | Complete |
| PANEL-01 | Phase 8 | Complete |
| PANEL-02 | Phase 8 | Complete |
| PANEL-03 | Phase 8 | Pending |
| PANEL-04 | Phase 8 | Complete |
| PANEL-05 | Phase 8 | Pending |
| BOT-01 | Phase 9 | Pending |
| BOT-02 | Phase 9 | Pending |
| BOT-03 | Phase 9 | Pending |

**Coverage:**
- v1 requirements: 26 total — all Complete ✓
- v2 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-17*
*Last updated: 2026-06-21 — Milestone v2.0 requirements defined (MCAN, COPY, PANEL, BOT)*
