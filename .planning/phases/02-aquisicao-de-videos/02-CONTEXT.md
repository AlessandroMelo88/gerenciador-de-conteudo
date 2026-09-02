# Phase 2: Aquisição de Vídeos - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning

<domain>
## Phase Boundary

O clip-processor monitora canais de YouTube via RSS, detecta vídeos novos, baixa automaticamente em 720p via yt-dlp e registra o status de cada job no MySQL. Processamento de áudio/IA e publicação são fases separadas.

Vídeos brutos são armazenados temporariamente — deletados após processamento e upload bem-sucedido. Espaço em disco é recurso crítico a ser gerenciado ativamente.

</domain>

<decisions>
## Implementation Decisions

### Orquestrador do polling RSS
- clip-processor roda como daemon Python com APScheduler interno
- Poll de RSS a cada 6 horas (conforme ACQU-01) — sem depender do n8n para disparar
- n8n não participa da fase de aquisição; fica disponível para fases futuras de orquestração complexa

### Estrutura de diretórios
- Vídeos brutos: `./videos/{youtube_video_id}.mp4` (volume montado no Docker)
- Clips gerados (fases seguintes): `./videos/clips/{youtube_video_id}_clip_{n}.mp4`
- Pasta `videos/` na raiz do projeto, montada como volume Docker no clip-processor
- Deletar arquivos automaticamente após upload bem-sucedido para o YouTube

### Gerenciamento de espaço em disco
- Verificar espaço livre antes de cada download
- Se espaço disponível < 2GB: não iniciar o download, logar aviso, manter vídeo como `pending`
- Não há limpeza periódica forçada — a deleção pós-upload já mantém o disco limpo

### Deduplicação (Redis + MySQL)
- Redis como cache de dedup com TTL de 30 dias por chave (`video:{youtube_video_id}`)
- Fallback para MySQL-only (`source_videos` UNIQUE em `youtube_video_id`) se Redis estiver indisponível
- Redis é otimização de performance, não barreira única — MySQL é a fonte de verdade

### Falha no download
- Retry automático 3 vezes com 60s de espera entre tentativas
- Após 3 falhas: status `failed` no banco, não tenta mais automaticamente
- Vídeos privados, removidos ou geo-restritos: marca como `failed` na primeira tentativa (yt-dlp retorna erro distinguível)
- Arquivos parciais deletados em caso de falha para não acumular lixo em disco

### Paralelismo
- 1 download por vez — fila sequencial
- Evita pico de disco e rede; suficiente para o volume inicial de poucos canais

### Cadastro de canais
- Script SQL de seed (`mysql/init/02-seed-channels.sql`) com os canais iniciais
- Executado manualmente uma vez: `docker exec -i mysql mysql ... < 02-seed-channels.sql`
- Versionado no git — histórico de canais monitorados fica rastreável

### Observabilidade
- Logs via stdout simples: `docker logs clip-processor -f`
- Formato: `[2026-06-18 10:00:00] [ACQU] Novo vídeo detectado: {video_id} — {title}`
- Sem arquivo de log em disco para não consumir espaço adicional

### Claude's Discretion
- Implementação interna do APScheduler (BlockingScheduler vs BackgroundScheduler)
- Formato exato de parse do RSS (feedparser ou xmltodict)
- Tratamento de edge cases do yt-dlp (formatos ausentes, retries de rede internos do yt-dlp)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `clip-processor/src/main.py`: Stub Python existente com loop infinito — será substituído pela implementação real do daemon
- `clip-processor/requirements.txt`: yt-dlp, pymysql, google-api-python-client já instalados; precisará adicionar `apscheduler`, `feedparser`, `redis`
- `clip-processor/Dockerfile`: Python 3.12 + ffmpeg — sem mudanças necessárias no Dockerfile para esta fase

### Established Patterns
- MySQL schema `source_videos` já tem ENUM com 9 estados de pipeline — usar exatamente esses estados, não criar novos
- `source_channels.rss_url` já está no schema — o feed RSS de cada canal já tem campo dedicado
- `mysql/init/01-clips-schema.sql`: padrão de SQL idempotente com `IF NOT EXISTS` — seed de canais deve seguir o mesmo padrão

### Integration Points
- `clips_user`@MySQL com acesso total a `clips_automation` — usar estas credenciais (via `CLIPS_DB_PASSWORD` do .env)
- Docker Compose: clip-processor já tem serviço definido; adicionar volume mount `./videos:/app/videos`
- `.env` já tem `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, credenciais MySQL — adicionar `REDIS_HOST=redis`, `REDIS_PORT=6379`
- Redis: verificar se já existe no docker-compose do wordpress; se não, adicionar serviço

</code_context>

<specifics>
## Specific Ideas

- "Não posso ficar armazenando vídeo na máquina — após upload, deletar imediatamente"
- "Usar Redis só se necessário, com TTL para não ter gargalo de memória"
- "Pouco espaço no Mac — precisa ser inteligente no gerenciamento"

</specifics>

<deferred>
## Deferred Ideas

- **Painel de gestão de canais** — Interface web para adicionar/remover canais sem editar SQL. Alinhado com MGT-01 (v2 requirements)
- **Analytics de CPM e performance** — Agente ou script que monitora quanto cada vídeo está pagando. Alinhado com OPT-01 (v2 requirements)

</deferred>

---

*Phase: 02-aquisicao-de-videos*
*Context gathered: 2026-06-18*
