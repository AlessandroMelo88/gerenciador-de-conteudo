# Research Summary: Canal de Cortes Automatizado

## Stack Recomendado

**Orquestração:** n8n self-hosted (Docker) — visual, gratuito, integra com qualquer API

**Pipeline de dados:**
- **Download:** yt-dlp — padrão da indústria, gratuito, suporta cookies
- **Transcrição:** faster-whisper (modelo `small`, PT-BR) — 4x mais rápido que Whisper padrão, 100% gratuito local
- **Seleção de momentos:** Claude Haiku API — menor custo da família Claude (~$0.001/vídeo), contexto de 200k tokens
- **Processamento de vídeo:** FFmpeg — corte, resize 9:16 para Shorts, burn de legendas
- **Publicação:** YouTube Data API v3 — 6 uploads gratuitos/dia (1.600 unidades por upload)

**Persistência:** MySQL (já existente) + Redis (já existente) — zero custo adicional

**Serviço Python custom** (`clip-processor`): FastAPI que conecta todos os componentes, expõe endpoints HTTP para o n8n chamar.

## Table Stakes (Não Tem Sem Isso)

1. Monitor de canais via YouTube RSS (sem cota)
2. Download automático com yt-dlp
3. Transcrição com faster-whisper (PT-BR)
4. Seleção de momentos por Claude Haiku
5. Corte com FFmpeg + legendas queimadas
6. Thumbnail automática (frame extraction)
7. Metadados (título/descrição/tags) gerados por IA
8. Upload automático via YouTube Data API
9. Deduplicação (Redis + MySQL UNIQUE)
10. Gestão de quota diária (máx 6 uploads/dia)

## Principais Riscos a Evitar

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Copyright strike | Fatal — canal removido | Priorizar canais que incentivam cortes; creditar o original |
| Spam detection pelo YouTube | Fatal — ban do canal | Começar com 1-2 posts/dia, não 6; qualidade > quantidade |
| Espaço em disco | Pipeline para | Deletar vídeo bruto após processamento; baixar em 720p |
| Whisper timeout em vídeos longos | Jobs travados | Extrair só o áudio antes de transcrever |
| Formato errado para Shorts | Zero tráfego | FFmpeg: 9:16, ≤60s, incluir #Shorts |
| Prompt Claude mal calibrado | Clips ruins = canal não cresce | Revisar primeiros 20 clips manualmente |

## Arquitetura em 6 Fases

```
Fase 1: Infraestrutura Base
  n8n + clip-processor + whisper no Docker; MySQL schema; YouTube channel criado e verificado

Fase 2: Aquisição de Vídeos
  Monitor RSS → download yt-dlp → deduplicação → fila Redis

Fase 3: Transcrição e Seleção de Momentos
  faster-whisper → Claude Haiku → lista de momentos com score

Fase 4: Processamento de Vídeo
  FFmpeg corte → resize 9:16 → burn subtitles → thumbnail

Fase 5: Publicação Automatizada
  YouTube OAuth → upload API → agendamento → quota management

Fase 6: Otimização
  Analytics feedback → ajuste de prompts → alertas de falha
```

## Custo Estimado Mensal (após v1)

| Item | Custo |
|------|-------|
| Claude Haiku API (30 vídeos/mês de 1h) | ~$0.03/mês |
| YouTube API | Gratuito (dentro da cota) |
| yt-dlp, FFmpeg, Whisper | Gratuito |
| n8n self-hosted | Gratuito |
| Infraestrutura Docker (Mac local) | Já existente |
| **Total** | **~$0/mês** |

## Decisão Crítica Antecipada

Usar YouTube RSS (e não `search.list` da YouTube API) para monitorar novos vídeos é fundamental — RSS não consome cota e atualiza a cada 15-30min. Isso preserva toda a cota diária (10.000 unidades) para uploads.
