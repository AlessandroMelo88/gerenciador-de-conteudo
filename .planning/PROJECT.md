# Canal de Cortes — Futebol & Esportes

## What This Is

Sistema 100% automatizado que monitora canais de YouTube com conteúdo de futebol e esportes (podcasts, lives, análises), extrai os melhores momentos usando IA, gera legendas automáticas, e publica os cortes como vídeos curtos no YouTube. O objetivo é construir um canal monetizável com o mínimo de intervenção manual possível, usando a infraestrutura Docker já existente.

## Core Value

O pipeline extrai e publica cortes virais de futebol automaticamente — do monitoramento à publicação — sem precisar de intervenção humana para cada vídeo.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Sistema monitora canais de YouTube pré-configurados e detecta novos vídeos
- [ ] Vídeos são baixados automaticamente via yt-dlp
- [ ] Áudio é transcrito localmente com Whisper (gratuito, sem custo de API)
- [ ] Claude API analisa a transcrição e identifica os melhores momentos (mais polêmicos, engraçados, informativos)
- [ ] FFmpeg corta os clipes nos timestamps selecionados pela IA
- [ ] Legendas são geradas e queimadas no vídeo automaticamente
- [ ] IA gera título, descrição e tags otimizados para YouTube
- [ ] Clipes são publicados automaticamente no canal via YouTube Data API
- [ ] n8n orquestra todo o workflow como pipeline automatizado
- [ ] Dashboard simples para monitorar status e resultados

### Out of Scope

- Publicação simultânea no TikTok e Instagram Reels — v2 após validar o sistema no YouTube
- Canal de política — v2 após primeiro canal monetizado
- Canal de assuntos gerais — v2 após primeiro canal monetizado
- Edição manual de qualquer vídeo — o sistema deve ser 100% autônomo
- Moderação de comentários — fora do escopo inicial

## Context

- **Infraestrutura existente:** Docker local (Mac) com nginx, PHP, MySQL, Redis já rodando
- **APIs disponíveis:** Claude API (acesso atual), OpenAI API (plano básico)
- **Preferência de custo:** Usar ferramentas gratuitas onde possível; pagar apenas onde a qualidade faz diferença real (Claude para seleção de momentos)
- **Nicho escolhido:** Futebol/esportes — nicho enorme no Brasil, alta demanda por cortes de comentaristas, análises e polêmica
- **Meta de monetização:** YouTube Partner Program exige 1.000 subscribers + 4.000 horas assistidas nos últimos 12 meses
- **Estratégia de escala:** Após validar o sistema com o canal de futebol, replicar para política e assuntos gerais

## Constraints

- **Custo:** Minimizar gastos com APIs — Whisper local (gratuito), Claude API apenas para análise de transcrição
- **Infraestrutura:** Tudo roda em Docker no Mac local; sem VPS por enquanto
- **Legal:** yt-dlp para download de conteúdo público; respeitar fair use e diretrizes do YouTube para cortes
- **YouTube API:** Cota gratuita limitada (10.000 unidades/dia) — uploads consomem 1.600 unidades cada; ~6 uploads/dia na cota gratuita
- **Tech Stack:** n8n como orquestrador de workflow, FFmpeg para processamento de vídeo, Whisper para transcrição

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Começar com futebol antes de outros nichos | Validar pipeline antes de escalar; futebol tem maior audiência no Brasil | — Pending |
| Whisper local em vez de API paga | Transcrição é o passo mais frequente e custoso; local elimina custo recorrente | — Pending |
| n8n como orquestrador | Self-hosted, visual, integra com qualquer API, já tem nodes para YouTube e HTTP | — Pending |
| Claude API para seleção de momentos | Qualidade de análise de texto superior a modelos gratuitos para identificar "pico" de engajamento | — Pending |
| Canal único por nicho | Algoritmo do YouTube favorece consistência; monetização mais rápida com foco | — Pending |

---
*Last updated: 2026-06-17 after initialization*
