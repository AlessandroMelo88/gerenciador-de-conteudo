# Requirements: Canal de Cortes — Futebol & Esportes

**Defined:** 2026-06-17
**Core Value:** O pipeline extrai e publica cortes virais de futebol automaticamente — do monitoramento à publicação — sem precisar de intervenção humana para cada vídeo.

## v1 Requirements

### Infraestrutura

- [x] **INFRA-01**: Sistema roda inteiramente em Docker no docker-compose existente (novos serviços: n8n, clip-processor, whisper)
- [x] **INFRA-02**: Banco de dados `clips_automation` criado no MySQL existente com tabelas source_channels, source_videos e generated_clips
- [x] **INFRA-03**: Canal do YouTube criado, conta verificada, banner e bio preenchidos antes do primeiro upload
- [x] **INFRA-04**: Variáveis de ambiente e secrets configurados (.env com Claude API key, YouTube OAuth credentials)

### Aquisição de Conteúdo

- [x] **ACQU-01**: Sistema monitora canais de YouTube pré-configurados via RSS (sem consumir cota de API) a cada 6 horas
- [x] **ACQU-02**: Novos vídeos detectados são baixados automaticamente em 720p via yt-dlp
- [x] **ACQU-03**: Sistema não reprocessa vídeos já processados (deduplicação via Redis SET + MySQL UNIQUE em youtube_video_id)

### Processamento com IA

- [x] **AI-01**: Áudio do vídeo é transcrito localmente pelo faster-whisper com modelo `small` e idioma PT-BR, gerando texto com timestamps
- [x] **AI-02**: Claude Haiku API analisa a transcrição completa e retorna lista de momentos de alto impacto com score 1-10, start/end e motivo
- [x] **AI-03**: Apenas momentos com score ≥ 7 são enviados para corte (filtro de qualidade)

### Processamento de Vídeo

- [x] **VID-01**: FFmpeg corta o clip nos timestamps selecionados pela IA e faz resize para formato 9:16 (1080x1920) compatível com YouTube Shorts
- [x] **VID-02**: Legendas geradas pelo Whisper são queimadas no clip final (burn subtitles) com fonte legível e bordas
- [x] **VID-03**: Thumbnail automática é extraída do frame mais impactante do clip
- [x] **VID-04**: Claude Haiku gera título (máx 100 chars), descrição e tags otimizados para YouTube SEO do nicho de futebol

### Publicação

- [x] **PUB-01**: Clips prontos são publicados automaticamente no YouTube via Data API v3 com título, descrição, tags e thumbnail
- [x] **PUB-02**: Sistema respeita cota diária do YouTube (máx 6 uploads/dia) usando contador Redis com reset à meia-noite
- [x] **PUB-03**: Uploads são agendados nos horários de maior audiência (19h-22h horário de Brasília)
- [x] **PUB-04**: Vídeos brutos são deletados automaticamente após processamento bem-sucedido; apenas clips finais são mantidos

### Orquestração

- [x] **ORC-01**: n8n orquestra todo o pipeline end-to-end como workflow automatizado com tratamento de erros e retry
- [x] **ORC-02**: Status de cada job é registrado no MySQL (pending/downloading/transcribing/selecting/cutting/publishing/published/failed)

## v2 Requirements

### Expansão de Plataformas

- **EXP-01**: Publicação simultânea no Instagram Reels
- **EXP-02**: Publicação simultânea no TikTok
- **EXP-03**: Segundo canal (política) replicando o mesmo pipeline

### Otimização e Analytics

- **OPT-01**: Dashboard web de métricas (views, subs, watch time por clip)
- **OPT-02**: A/B test de títulos/thumbnails
- **OPT-03**: Detecção de momentos por pico de volume de áudio (além da análise de texto)
- **OPT-04**: Notificações de falha via Telegram/email

### Gerenciamento

- **MGT-01**: Interface para adicionar/remover canais-fonte sem editar código
- **MGT-02**: Blacklist de conteúdo (evitar clips com palavras específicas)

## Out of Scope

| Feature | Motivo |
|---------|--------|
| TikTok/Instagram no v1 | API do TikTok é restrita; aumenta escopo desnecessariamente |
| Edição manual de clips | Contradiz o objetivo de 100% automatizado |
| Geração de vídeo com IA (avatares/voz sintética) | Complexidade e custo altos; foge do modelo de canal de cortes |
| Canal de política no v1 | Risco de demonetização; validar sistema com futebol primeiro |
| Site/blog para espectadores | O canal é o YouTube; não precisamos de site separado |
| Moderação de comentários | Não impacta crescimento no v1 |
| Multi-conta YouTube simultânea | Complexidade de OAuth múltiplo; uma conta por vez |

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

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-17*
*Last updated: 2026-06-18 — Phase 5 publication/orchestration complete*
