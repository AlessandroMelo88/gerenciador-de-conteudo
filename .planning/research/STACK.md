# Stack Research: Automated YouTube Clips Channel

## Recommended Stack

### Orchestration
| Tool | Version | Docker Image | Rationale |
|------|---------|--------------|-----------|
| n8n | 1.x (latest) | `n8nio/n8n:latest` | Self-hosted, visual workflow editor, native HTTP/webhook/YouTube nodes, free |
| Confidence | High | — | Industry standard para automação self-hosted |

### Video Download
| Tool | Version | Notes |
|------|---------|-------|
| yt-dlp | latest (pip) | Substituto do youtube-dl, mantido ativamente, suporta cookies, rate limiting, formatos múltiplos |
| Confidence | High | — |

Flags recomendados:
```
yt-dlp --format "bestvideo[height<=1080]+bestaudio/best[height<=1080]" \
       --output "%(id)s.%(ext)s" \
       --write-info-json \
       --no-playlist
```

### Transcrição (local, gratuito)
| Tool | Model | Docker Image | Notas |
|------|-------|--------------|-------|
| Whisper (OpenAI) | `base` ou `small` (português) | `onerahmet/openai-whisper-asr-webservice:latest` | Gratuito, local, suporte nativo a PT-BR |
| Alternativa | faster-whisper | `fedirz/faster-whisper-server:latest-cpu` | 4x mais rápido que whisper padrão no CPU |

Recomendação: `faster-whisper` com modelo `small` para português — melhor custo/benefício sem GPU.

### Seleção de Momentos (IA)
| Tool | Uso |
|------|-----|
| Claude API (claude-haiku-4-5) | Mais barato da família Claude, suficiente para analisar transcrições e identificar momentos de alto impacto |
| Alternativa gratuita | Ollama + llama3 local — qualidade menor mas zero custo |

Recomendação: Claude Haiku para seleção (menor custo da família), com prompt bem estruturado. Custo estimado: ~$0.001 por vídeo de 1h.

### Processamento de Vídeo
| Tool | Docker Image | Uso |
|------|--------------|-----|
| FFmpeg | `linuxserver/ffmpeg` ou via Alpine | Corte, resize para Shorts (9:16), burn subtitles (ASS/SRT), thumbnail |
| Python + MoviePy | via python:3.11-slim | Wrapper para lógica complexa de corte |

Comando padrão para Shorts:
```bash
ffmpeg -ss {start} -to {end} -i input.mp4 \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,subtitles=sub.srt" \
  -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k \
  output_short.mp4
```

### Geração de Legendas
| Tool | Formato | Notas |
|------|---------|-------|
| Whisper output | SRT/VTT | Já gera timestamped com a transcrição |
| ass-converter | ASS | Para estilo de legenda estilizada (fonte maior, bordas) |

### Publicação
| Tool | Notas |
|------|-------|
| YouTube Data API v3 | Gratuito até 10.000 unidades/dia; upload = 1.600 unidades; ~6 uploads/dia na cota free |
| google-api-python-client | Biblioteca oficial Python |

Quota diária estratégia: publicar no máximo 6 vídeos/dia, espaçados para não violar rate limits.

### Banco de Dados
| Tool | Uso |
|------|-----|
| MySQL (já existente) | Armazenar canais monitorados, vídeos processados, clipes gerados, status de publicação |
| Redis (já existente) | Fila de jobs, cache de metadados, deduplicação |

### Armazenamento de Arquivos
| Tool | Notas |
|------|-------|
| Volume Docker local | Videos brutos (temporário, deletar após processamento) |
| Volume Docker persistente | Clipes finais (manter para reprocessar se necessário) |

## Docker Services (novos a adicionar)
```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    ports: ["5678:5678"]
    volumes: ["./docker/n8n_data:/home/node/.n8n"]
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=senha_forte

  whisper:
    image: fedirz/faster-whisper-server:latest-cpu
    ports: ["8000:8000"]
    volumes: ["./docker/whisper_models:/root/.cache/huggingface"]
    environment:
      - WHISPER__MODEL=small

  clip-processor:
    build: ./services/clip-processor  # Python + FFmpeg custom
    volumes:
      - ./docker/videos:/videos
      - ./docker/clips:/clips
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - MYSQL_HOST=mysql
      - REDIS_HOST=redis
```

## What NOT to Use

| Tool | Motivo |
|------|--------|
| youtube-dl | Abandonado, use yt-dlp |
| AssemblyAI / Deepgram | Pagos — Whisper local é equivalente e gratuito |
| OpenAI Whisper API | $0.006/min — com vídeos de 1h isso vira caro rápido |
| Make (Integromat) | Plano pago e limitado; n8n self-hosted é superior |
| Zapier | Mesma razão que Make |
| Remotion | Overkill para cortes simples; FFmpeg resolve |

## Integration Map
```
[n8n Scheduler]
     ↓ (cron: a cada 6h)
[YouTube RSS / API] → detecta novos vídeos
     ↓
[yt-dlp service] → baixa vídeo para /videos/
     ↓
[MySQL] → registra job de transcrição
     ↓
[faster-whisper] → transcreve → retorna JSON com timestamps
     ↓
[Claude Haiku API] → analisa transcrição → retorna lista de momentos com start/end/score
     ↓
[FFmpeg service] → corta clips + burn subtitles → salva em /clips/
     ↓
[YouTube Data API] → faz upload com título/descrição/tags gerados por IA
     ↓
[MySQL] → registra status published + video_id
     ↓
[limpeza] → deleta vídeo bruto, mantém clip
```

## Confidence Levels
| Componente | Confiança | Motivo |
|-----------|-----------|--------|
| n8n como orquestrador | Alta | Amplamente usado para automações deste tipo |
| yt-dlp | Alta | Padrão da indústria, bem mantido |
| faster-whisper | Alta | Benchmark mostra 4x speedup vs whisper padrão |
| Claude Haiku para seleção | Alta | Custo baixo, qualidade adequada para análise de texto |
| YouTube Data API v3 | Alta | API oficial, estável |
| FFmpeg para corte + legendas | Alta | Padrão absoluto para processamento de vídeo |
