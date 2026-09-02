# Canal de Cortes — Futebol & Esportes

## What This Is

Sistema 100% automatizado que monitora canais de YouTube com conteúdo de futebol, podcasts e variedades, extrai os melhores momentos usando IA, gera legendas automáticas, e publica os cortes como vídeos curtos em múltiplos canais YouTube. O operador gerencia tudo por um painel Laravel/Filament — adicionando canais-fonte, monitorando o pipeline e recebendo notificações no Telegram — sem precisar editar SQL ou código.

## Core Value

O pipeline extrai e publica cortes virais automaticamente — do monitoramento à publicação em múltiplos canais — sem intervenção humana para cada vídeo.

## Current Milestone: v2.0 — Painel + Multi-Canal

**Goal:** Tornar o sistema gerenciável por painel web e escalável para múltiplos canais YouTube de destino, com proteção de copyright integrada.

**Target features:**
- Painel Laravel/Filament para adicionar canais-fonte e canais-destino sem SQL
- Multi-canal de destino: cada nicho (futebol, podcasts/variedades) publica em canal próprio
- 3 uploads/dia por canal (escalável: 2 canais = 6/dia, 3 canais = 9/dia)
- Bot Telegram integrado ao Laravel para notificações e controle (sem Cloudflare, sem n8n para bot)
- Copyright: watermark/logo no clip, créditos na descrição, blacklist de emissoras grandes

## Requirements

### Validated (v1.0)

- ✓ Sistema monitora canais YouTube via RSS e detecta novos vídeos — Phase 2
- ✓ Vídeos são baixados automaticamente via yt-dlp — Phase 2
- ✓ Áudio é transcrito via Groq Whisper API — Phase 3
- ✓ Claude Haiku seleciona melhores momentos com score ≥ 7 — Phase 3
- ✓ FFmpeg corta clips em 9:16 com legendas queimadas e thumbnail — Phase 4
- ✓ Claude Haiku gera título, descrição e tags YouTube — Phase 4
- ✓ Clips são publicados automaticamente via YouTube Data API — Phase 5
- ✓ Quota máx/dia e janela horária 19h-22h BRT respeitadas — Phase 5
- ✓ MANUAL_APPROVAL_REQUIRED toggle auto/manual — Phase 6

### Active (v2.0)

- [ ] Painel web (Laravel/Filament) para adicionar/remover canais-fonte via URL ou channel_id
- [ ] Suporte a múltiplos canais YouTube de destino com OAuth por canal
- [ ] Roteamento: canal-fonte por nicho → canal-destino correspondente
- [ ] 3 uploads/dia por canal (quota independente por canal)
- [ ] Bot Telegram no Laravel: notificações de upload, falha, resumo diário
- [ ] Webhook Telegram em `alessandromelo.com.br/telegramcanal` via nginx → Laravel
- [ ] Watermark/logo queimado no clip via FFmpeg
- [ ] Créditos do canal original na descrição gerada pelo Claude
- [ ] Blacklist de canais para evitar emissoras grandes (Globo, SBT, Band, ESPN direto)
- [ ] Dashboard de pipeline: ver status de cada vídeo em tempo real no painel

### Out of Scope

- TikTok e Instagram Reels — após validar escala no YouTube
- Canal de política — risco de demonetização; validar futebol/podcasts primeiro
- Edição manual de qualquer vídeo — sistema 100% autônomo
- Moderação de comentários — fora do escopo

## Context

- **Infraestrutura existente:** Docker local (Mac) com nginx, PHP, MySQL, Redis já rodando; deploy planejado em servidor dedicado
- **v1.0 entregue:** Pipeline completo RSS→YouTube funcionando, bot Telegram com comandos básicos
- **Implantação futura:** Servidor com IP público; webhook Telegram via `alessandromelo.com.br/telegramcanal` (nginx proxy → Laravel)
- **Stack v2.0:** Laravel 11 + Filament 3 + MySQL existente (clips_automation) + bot Telegram via irazasyed/telegram-bot-sdk
- **Meta de escala:** 2 canais inicialmente (futebol + podcasts/variedades); crescer conforme canal cresce

## Constraints

- **YouTube API:** Cota gratuita 10.000 unidades/dia; 1.600 unidades por upload → máx 6 uploads totais/dia na cota gratuita; com 2 canais: 3/canal
- **Legal/Copyright:** Clips transformados (9:16, legendas, watermark) + créditos na descrição + duração ≤ 60s = Fair Use defensável; evitar emissoras com track record agressivo de DMCA
- **Infraestrutura:** Docker local → servidor; Laravel roda em container separado ou host
- **Custo:** Groq Whisper e Claude Haiku mantidos; sem adicionar APIs pagas desnecessárias

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Começar com futebol antes de outros nichos | Validar pipeline antes de escalar | ✓ Bom — v1.0 funcionando |
| Groq Whisper (API) em vez de Whisper local | Elimina 2.5GB de RAM, gratuito com boa qualidade | ✓ Bom |
| Claude Haiku para seleção e metadados | Custo ~$0.001/vídeo, qualidade superior | ✓ Bom |
| MANUAL_APPROVAL_REQUIRED env var | Alterna auto/manual sem alterar código | ✓ Bom |
| Bot Telegram no Laravel (v2) | Elimina dependência de Cloudflare Tunnel e n8n para bot | — Pending |
| Multi-canal com token OAuth por canal | Cada canal YouTube tem credenciais separadas | — Pending |

---
*Last updated: 2026-06-21 after milestone v2.0 start*
