---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Phase 5 PLANEJADA — 6 planos prontos para publicacao, quota, YouTube upload, runner e n8n
stopped_at: Planned 05-publicacao-e-automacao-total
last_updated: "2026-06-18T19:45:00.000Z"
last_activity: 2026-06-18 — Phase 5 planejada com migration, QuotaManager, YouTubeUploader, Publisher, runner e workflow n8n
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 22
  completed_plans: 16
  percent: 73
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-17)

**Core value:** Pipeline extrai e publica cortes virais de futebol automaticamente — do monitoramento à publicação — sem intervenção humana para cada vídeo.
**Current focus:** Phase 5 — Publicação e Automação Total (planejada; próxima ação é executar 05-01)

## Current Position

Phase: 5 of 5 (Publicação e Automação Total) — PLANNED
Plan: 0 of 6 in current phase — READY
Status: Phase 5 PLANEJADA — 6 planos prontos para publicacao, quota, YouTube upload, runner e n8n
Last activity: 2026-06-18 — Phase 5 planejada com migration, QuotaManager, YouTubeUploader, Publisher, runner e workflow n8n

Progress: [███████░░░] 73% (Phases 1-4 completas — 16/22 planos)

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01-infraestrutura-base P01 | 2 | 3 tasks | 8 files |
| Phase 01-infraestrutura-base P02 | 1 | 2 tasks | 2 files |
| Phase 01-infraestrutura-base P03 | ~30min | 3 tasks | 2 files |
| Phase 01-infraestrutura-base P04 | ~2h | 3 tasks | 3 files |
| Phase 02-aquisicao-de-videos P01 | 3min | 3 tasks | 8 files |
| Phase 02-aquisicao-de-videos P02 | 15min | 3 tasks | 4 files |
| Phase 02-aquisicao-de-videos P03 | 10min | 3 tasks | 3 files |
| Phase 02-aquisicao-de-videos P04 | ~10min | 2 tasks | 1 file |
| Phase 03-ia-transcricao P01 | 2min | 2 tasks | 5 files |
| Phase 03-ia-transcri-o-e-sele-o P02 | 6min | 1 tasks | 1 files |
| Phase 03-ia-transcricao P03 | 5min | 1 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Project init: YouTube RSS para monitoramento (não `search.list`) — preserva toda a cota diária para uploads
- Project init: faster-whisper modelo `small` PT-BR para transcrição gratuita local
- Project init: Claude Haiku (não Sonnet) para seleção de momentos — custo ~$0.001/vídeo
- Project init: Máximo 1-2 uploads/dia inicialmente (não 6) para evitar spam detection pelo YouTube
- [Phase 01-infraestrutura-base]: n8n usa SQLite default — DB_TYPE=mysqldb removido no n8n 2.0 causaria falha silenciosa
- [Phase 01-infraestrutura-base]: Imagem n8n pinada em 2.27.0 (não :latest) para estabilidade de produção
- [Phase 01-infraestrutura-base]: token.json placeholder {} criado (gitignored) para volume mount antes do OAuth ser configurado no Plan 03
- [Phase 01-infraestrutura-base]: CLIPS_DB_PASSWORD como placeholder no SQL — substituição via envsubst no Plan 03
- [Phase 01-infraestrutura-base]: ENUM source_videos com 9 estados do pipeline: pending → downloading → downloaded → transcribing → selecting → cutting → publishing → published → failed
- [Phase 01-infraestrutura-base]: validate-infra.sh usa check() isolado para exibir todos PASS/FAIL mesmo quando algum falha
- [Phase 01-infraestrutura-base]: Whisper local removido — substituído por Groq Whisper API (gratuito, online) para economizar ~2.5GB de disco no Mac. Container whisper removido do docker-compose.yml. GROQ_API_KEY adicionado ao .env e clip-processor.
- [Phase 01-infraestrutura-base P03]: N8N_ENCRYPTION_KEY e CLIPS_DB_PASSWORD gerados via openssl rand automaticamente — nunca hardcoded. ANTHROPIC_API_KEY intencionalmente vazia até Phase 3.
- [Phase 01-infraestrutura-base P03]: token.json placeholder {} criado para volume mount — evita erro de boot do clip-processor antes do OAuth real (Plan 04).
- [Phase 01-infraestrutura-base P04]: OAuth app type deve ser "installed" (Desktop App), não "web" — web type causa erro no InstalledAppFlow do Python.
- [Phase 01-infraestrutura-base P04]: OAuth app publicado em Production para evitar expiração do refresh_token em 7 dias (limite do modo Testing).
- [Phase 01-infraestrutura-base P04]: Canal "Futebol em Cortes" verificado via SMS — desbloqueia uploads longos e thumbnails customizadas.
- [Phase 02-aquisicao-de-videos P01]: Imports de src.* no topo dos arquivos de teste (não dentro das funções) — coleta falha com ModuleNotFoundError = RED state correto e mais simples
- [Phase 02-aquisicao-de-videos P01]: requirements.txt atualizado com redis, feedparser, apscheduler antecipando necessidades dos Planos 02-04
- [Phase 02-aquisicao-de-videos]: db.py: quem chama é responsável por fechar a conexão — padrão de uso do daemon
- [Phase 02-aquisicao-de-videos]: INSERT IGNORE em insert_video para idempotência — RSS pode re-publicar o mesmo item entre polls
- [Phase 02-aquisicao-de-videos]: Seed SQL com 5 canais PT-BR reais: SporTV, ge.globo, ESPN Brasil, Canal do Nicola, TNT Sports Brasil
- [Phase 02-aquisicao-de-videos]: _cleanup_partial() chamado fora do loop de retry: cleanup uma única vez após todas as tentativas, não por iteração
- [Phase 02-aquisicao-de-videos]: rss_poller.py usa requests.get + feedparser.parse(response.text) para permitir mock de HTTP nos testes
- [Phase 02-aquisicao-de-videos]: poll_all_channels aceita db_conn/redis_client opcionais: None cria conexão de produção, injetados nos testes
- [Phase 02-aquisicao-de-videos P04]: Guard if __name__ == '__main__' mantido em main.py para que imports nos testes não disparem o scheduler BlockingScheduler
- [Phase 02-aquisicao-de-videos P04]: recover_stuck_downloads chamado ANTES de poll_all_channels na boot — evita re-processar jobs já em andamento após restart
- [Phase 02-aquisicao-de-videos P04]: coalesce=True + max_instances=1 no BlockingScheduler — evita execuções paralelas do poll caso iteração demore mais que 6 horas
- [Phase 03-ia-transcricao P01]: VIDEOS_DIR = '/app/videos' definido como constante patchável em transcriber.py — sem hardcode nos métodos
- [Phase 03-ia-transcricao P01]: transcribe_video/select_moments usam injeção de dependência (groq_client=None, anthropic_client=None) — consistente com downloader.py
- [Phase 03-ia-transcricao P01]: ENUM generated_clips.status: pending_cut como primeiro valor e novo default — todo clip Phase 3 começa em pending_cut
- [Phase 03-ia-transcricao P01]: insert_selected_moments: score >= 7 insere; score < 7 descarta sem INSERT — threshold definido na interface
- [Phase 03-ia-transcricao]: try/except amplo em transcribe_video captura qualquer falha Groq e retorna None — chamador responsável por marcar vídeo como failed
- [Phase 03-ia-transcricao]: _prepare_audio() retorna tuple (path, bool) para sinalizar ao chamador se deve deletar arquivo temporário de áudio
- [Phase 03-ia-transcricao]: _remove_overlaps aplicado em insert_selected_moments além de select_moments — contrato de deduplicação robusto independente da origem dos momentos
- [Phase 03-ia-transcricao]: output_config com json_schema para Claude Haiku — prefill retorna HTTP 400 em modelos claude-haiku-4-5
- [Phase 03-ia-transcri-o-e-sele-o]: groq_client e anthropic_client NÃO injetados em poll_all_channels — módulos criam clientes em produção; injeção apenas nos testes via _process_ai_pipeline
- [Phase 03-ia-transcri-o-e-sele-o]: source_video_id lookup via SELECT id FROM source_videos WHERE youtube_video_id = %s dentro de _process_ai_pipeline — FK INT necessária para generated_clips
- [Phase 03-ia-transcri-o-e-sele-o]: Phase 4 (cutting) responsável pela transição de status após pending_cut — _process_ai_pipeline não define status final do clip
- [Phase 04-processamento-de-video]: Nenhuma migration necessária — generated_clips já possui clip_path, thumbnail_path, title, description e tags
- [Phase 04-processamento-de-video]: Status flow definido como pending_cut → cutting → pending; Phase 5 publicará clips pending
- [Phase 04-processamento-de-video]: FFmpeg unit tests devem mockar subprocess.run; verificação visual real fica no checkpoint do Plan 04-04
- [Phase 04-processamento-de-video]: Clips e thumbnails ficam em /app/videos/clips e /app/videos/thumbnails para persistir no volume Docker existente
- [Phase 04-processamento-de-video]: MySQL 8.4 não aceitou ADD COLUMN IF NOT EXISTS; migrations idempotentes usam INFORMATION_SCHEMA + prepared statements
- [Phase 05-publicacao-e-automacao-total planning]: Upload real deve usar `youtube/token.json` montado como `/app/token.json`; testes mockam YouTube Data API
- [Phase 05-publicacao-e-automacao-total planning]: Quota diaria usa Redis por data local America/Sao_Paulo e nunca pode exceder 6 uploads/dia; default inicial recomendado e 2
- [Phase 05-publicacao-e-automacao-total planning]: Raw source video so deve ser removido quando todos os clips do mesmo source estiverem terminais e ao menos um foi publicado
- [Phase 05-publicacao-e-automacao-total planning]: Primeiro checkpoint de upload deve usar `YOUTUBE_PRIVACY_STATUS=private`

### Pending Todos

None yet.

### Blockers/Concerns

None — Phase 5 planejada. Pronto para executar 05-01 (migration, skeletons e testes RED).

## Session Continuity

Last session: 2026-06-18T17:39:18.305Z
Stopped at: Completed 04-processamento-de-video Plan 04
Resume file: None
