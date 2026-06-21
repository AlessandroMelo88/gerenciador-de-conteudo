# Milestones: Canal de Cortes

## v1.0 — Pipeline Base (Concluído: 2026-06-21)

**Goal:** Pipeline 100% automático do RSS ao YouTube, com controle manual opcional via Telegram.

**Phases:** 1–6 (29 planos, todos concluídos)

| Phase | Nome | Resultado |
|-------|------|-----------|
| 1 | Infraestrutura Base | Docker, MySQL schema, canal YouTube, secrets |
| 2 | Aquisição de Vídeos | RSS monitor, yt-dlp download, deduplicação |
| 3 | IA — Transcrição e Seleção | Groq Whisper + Claude Haiku, filtro score ≥ 7 |
| 4 | Processamento de Vídeo | FFmpeg 9:16, legendas queimadas, thumbnail, metadados |
| 5 | Publicação e Automação Total | Upload YouTube API, quota 6/dia, janela 19h-22h BRT |
| 6 | Controle Manual N8N + Telegram | Bot Telegram, /aprovar, /rejeitar, MANUAL_APPROVAL_REQUIRED |

**Capacidades entregues:**
- Pipeline RSS → download → transcrição → seleção IA → corte → upload 100% automático
- `MANUAL_APPROVAL_REQUIRED=true/false` para alternar entre automático e aprovação manual
- Bot Telegram com 6 comandos (/status, /clipes, /aprovar, /rejeitar, /processar, /ajuda)
- TTL worker: clips rejeitados automaticamente após 48h sem aprovação
- Notificações proativas: upload publicado, falha crítica, resumo diário 18h BRT
- Quota máx 2/dia (configurável até 6), janela 19h-22h America/Sao_Paulo

**Last phase:** 6
**Next milestone starts at:** Phase 7
