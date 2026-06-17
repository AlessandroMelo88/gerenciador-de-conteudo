# Architecture Research: Automated YouTube Clips Channel

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        n8n Orchestrator                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Scheduler│  │ Monitor  │  │ Processor│  │  Publisher   │   │
│  │ (cron)   │→ │ Workflow │→ │ Workflow │→ │  Workflow    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────────────────┘
         │               │               │              │
         ▼               ▼               ▼              ▼
   [MySQL: jobs]   [yt-dlp svc]   [clip-processor]  [YT API]
                                        │
                                 ┌──────┴──────┐
                                 ▼             ▼
                           [Whisper]     [Claude API]
                                 └──────┬──────┘
                                        ▼
                                   [FFmpeg]
```

## Components

### 1. n8n (Orquestrador)
- **Responsabilidade:** Coordenar todo o pipeline via workflows visuais
- **Inputs:** Cron schedule, webhooks de status
- **Outputs:** Chamadas HTTP para cada serviço
- **Workflows principais:**
  - `monitor-channels`: verifica RSS/API do YouTube a cada 6h
  - `process-video`: download → transcrição → seleção → corte → legenda
  - `publish-clips`: upload + agendamento
  - `cleanup`: deleta vídeos brutos após processamento

### 2. clip-processor (Python Service)
- **Responsabilidade:** Lógica central de processamento — coordena whisper, claude, ffmpeg
- **Inputs:** video_id, video_path, channel_config
- **Outputs:** lista de clips prontos com metadados
- **Tecnologia:** Python 3.11, FastAPI (HTTP API para n8n chamar)
- **Endpoints:**
  - `POST /transcribe` → chama Whisper
  - `POST /select-moments` → chama Claude API
  - `POST /cut-clip` → chama FFmpeg
  - `POST /add-subtitles` → FFmpeg com SRT burn
  - `GET /job/{id}/status`

### 3. faster-whisper (Transcrição)
- **Responsabilidade:** Transcrever áudio em texto com timestamps
- **Input:** path do arquivo de áudio/vídeo
- **Output:** JSON `[{start, end, text}, ...]`
- **Modelo:** `small` (PT-BR) — bom equilíbrio velocidade/precisão sem GPU

### 4. Claude API (Seleção de Momentos)
- **Responsabilidade:** Analisar transcrição e retornar momentos de alto impacto
- **Input:** transcrição completa com timestamps
- **Output:** JSON `[{start, end, title, score, reason}, ...]`
- **Prompt strategy:** Pedir para identificar: polêmicas, revelações, humor, momentos únicos

### 5. FFmpeg (Processamento de Vídeo)
- **Responsabilidade:** Cortar clips, resize para Shorts (9:16), burn legendas
- **Inputs:** vídeo original, timestamps, arquivo SRT
- **Output:** clip.mp4 pronto para upload
- **Executado via:** subprocess Python dentro do clip-processor

### 6. YouTube Data API v3
- **Responsabilidade:** Upload de vídeos, configuração de metadados
- **Auth:** OAuth 2.0 (token refresh automático)
- **Quota:** 10.000 unidades/dia; upload = 1.600 unidades → máx 6 uploads/dia grátis

### 7. MySQL (já existente)
**Tabelas necessárias:**
```sql
-- Canais monitorados
CREATE TABLE source_channels (
  id INT PRIMARY KEY AUTO_INCREMENT,
  youtube_channel_id VARCHAR(50) UNIQUE,
  channel_name VARCHAR(255),
  channel_url VARCHAR(500),
  is_active BOOLEAN DEFAULT TRUE,
  last_checked_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vídeos descobertos
CREATE TABLE source_videos (
  id INT PRIMARY KEY AUTO_INCREMENT,
  channel_id INT REFERENCES source_channels(id),
  youtube_video_id VARCHAR(20) UNIQUE,
  title VARCHAR(500),
  duration_seconds INT,
  published_at TIMESTAMP,
  status ENUM('pending','downloading','downloaded','transcribing','transcribed','selecting','selected','failed') DEFAULT 'pending',
  local_path VARCHAR(500),
  transcript_path VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clips gerados
CREATE TABLE generated_clips (
  id INT PRIMARY KEY AUTO_INCREMENT,
  source_video_id INT REFERENCES source_videos(id),
  start_seconds FLOAT,
  end_seconds FLOAT,
  title VARCHAR(255),
  description TEXT,
  tags JSON,
  clip_path VARCHAR(500),
  thumbnail_path VARCHAR(500),
  virality_score FLOAT,
  status ENUM('pending','processing','ready','uploading','published','failed') DEFAULT 'pending',
  youtube_video_id VARCHAR(20),
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8. Redis (já existente)
- **Fila de jobs:** `clips:queue` — lista de video_ids para processar
- **Deduplicação:** SET com youtube_video_ids já processados
- **Rate limiting:** contador de uploads diários para não exceder quota

## Data Flow (Passo a Passo)

```
1. n8n cron (a cada 6h) → consulta YouTube RSS de cada canal em source_channels
2. Para cada novo vídeo descoberto:
   - INSERT em source_videos (status: pending)
   - PUSH video_id para Redis queue
3. n8n worker poll Redis queue → chama clip-processor POST /download
4. clip-processor: yt-dlp baixa vídeo → salva em /videos/{video_id}.mp4
   - UPDATE source_videos SET status='downloaded', local_path=...
5. clip-processor POST /transcribe → faster-whisper processa áudio
   - UPDATE source_videos SET status='transcribed', transcript_path=...
6. clip-processor POST /select-moments → Claude Haiku analisa transcrição
   - INSERT generated_clips (status: pending) para cada momento selecionado
7. Para cada clip pending:
   - clip-processor POST /cut-clip → FFmpeg corta segmento
   - clip-processor POST /add-subtitles → FFmpeg burn SRT
   - UPDATE generated_clips SET status='ready', clip_path=...
8. n8n publisher workflow (a cada hora, máx 6/dia):
   - SELECT clip WHERE status='ready' ORDER BY virality_score DESC LIMIT 1
   - clip-processor POST /upload → YouTube Data API v3
   - UPDATE generated_clips SET status='published', youtube_video_id=...
9. Cleanup: DELETE /videos/{video_id}.mp4 (manter apenas clips)
```

## Docker Service Layout (Adições ao docker-compose.yml)

```yaml
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: always
    ports:
      - "5678:5678"
    volumes:
      - ./docker/n8n_data:/home/node/.n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - DB_TYPE=mysqldb
      - DB_MYSQLDB_HOST=mysql
      - DB_MYSQLDB_DATABASE=clips_automation
      - DB_MYSQLDB_USER=root
      - DB_MYSQLDB_PASSWORD=rootpassword
    networks:
      - internal
      - outside
    depends_on:
      - mysql
      - redis

  clip-processor:
    build: ./services/clip-processor
    container_name: clip-processor
    restart: always
    ports:
      - "8080:8080"
    volumes:
      - ./docker/videos:/videos
      - ./docker/clips:/clips
      - ./docker/thumbnails:/thumbnails
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - MYSQL_HOST=mysql
      - MYSQL_DATABASE=clips_automation
      - REDIS_HOST=redis
      - WHISPER_URL=http://whisper:8000
      - YOUTUBE_CLIENT_SECRET_PATH=/secrets/youtube_client_secret.json
      - YOUTUBE_TOKEN_PATH=/secrets/youtube_token.json
    networks:
      - internal
    depends_on:
      - mysql
      - redis
      - whisper

  whisper:
    image: fedirz/faster-whisper-server:latest-cpu
    container_name: whisper
    restart: always
    ports:
      - "8001:8000"
    volumes:
      - ./docker/whisper_models:/root/.cache/huggingface
    environment:
      - WHISPER__MODEL=small
    networks:
      - internal
```

## Build Order (Sequência de Fases)

```
Fase 1: Infraestrutura Base
  → docker-compose atualizado com n8n + clip-processor + whisper
  → MySQL: criar banco clips_automation + migrations
  → Variáveis de ambiente e secrets configurados

Fase 2: Pipeline de Aquisição
  → n8n workflow: monitor canais via YouTube RSS
  → clip-processor: endpoint /download com yt-dlp
  → Deduplicação via Redis

Fase 3: Transcrição e Seleção de Momentos
  → clip-processor: endpoint /transcribe (faster-whisper)
  → clip-processor: endpoint /select-moments (Claude API)
  → Prompt engineering para nicho de futebol/esportes

Fase 4: Processamento de Vídeo
  → clip-processor: endpoint /cut-clip (FFmpeg)
  → clip-processor: endpoint /add-subtitles (burn SRT)
  → Thumbnail automática (frame extraction)

Fase 5: Publicação e Automação Completa
  → YouTube OAuth setup + token refresh
  → clip-processor: endpoint /upload (YouTube Data API)
  → n8n: workflow completo end-to-end + scheduler
  → Gerenciamento de quota diária

Fase 6: Otimização e Monitoramento
  → Dashboard de métricas (views, subs, crescimento)
  → Ajuste de prompts baseado em performance
  → Alertas de falha via n8n
```

## API Quota Management

| Operação | Custo (unidades) | Limite diário |
|----------|-----------------|---------------|
| video.insert (upload) | 1.600 | ~6 uploads/dia |
| videos.list | 1 | ~10.000 chamadas |
| search.list | 100 | ~100 buscas |
| channels.list | 1 | ~10.000 chamadas |

**Estratégia:**
- Usar YouTube RSS (sem cota) para monitorar novos vídeos em vez de search.list
- Limitar uploads a 6/dia com Redis counter (reset à meia-noite)
- Monitorar cota via Google Cloud Console
- Fila de publicação com prioridade por virality_score
