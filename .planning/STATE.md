---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Plans 08-05 e 08-07 concluídos (PANEL-01/PANEL-04); Plans 08-04/06/08/09 pendentes ou em execução paralela
stopped_at: Completed 08-07-PLAN.md
last_updated: "2026-07-02T01:40:00.000Z"
last_activity: "2026-07-01 — Plan 08-07 executado: GREEN de resolve_channel (yt-dlp subprocess) e reject_clip (chamada direta a src.rejeitar.rejeitar) em internal_api.py; thread daemon Flask wired em main.py (iniciada antes do ciclo do pipeline); CLIP_PROCESSOR_INTERNAL_TOKEN propagado ao clip-processor via docker-compose.yml; 6/6 testes GREEN em test_internal_api.py; 401 validado end-to-end via container php"
progress:
  total_phases: 9
  completed_phases: 7
  total_plans: 45
  completed_plans: 41
  percent: 91
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-21)

**Core value:** Pipeline extrai e publica cortes virais de futebol automaticamente — do monitoramento à publicação — sem intervenção humana para cada vídeo.
**Current focus:** Milestone v2.0 — multi-canal, copyright (watermark/blacklist/créditos), painel Laravel/Filament, bot Telegram no Laravel

## Current Position

Phase: 8 of 9 (Painel Laravel/Filament) — IN PROGRESS (Wave 2/3 em execução paralela — Plans 04/05/06/07 concorrentes)
Plan: 07 of 9 — 08-07-PLAN.md (GREEN internal_api.py + wiring main.py + docker-compose)
Status: Plans 08-05 e 08-07 concluídos (PANEL-01/PANEL-04); Plans 08-04/06/08/09 pendentes ou em execução paralela
Last activity: 2026-07-01 — Plan 08-07 executado: resolve_channel/reject_clip GREEN em internal_api.py, thread daemon Flask em main.py (antes do ciclo do pipeline), CLIP_PROCESSOR_INTERNAL_TOKEN propagado ao docker-compose.yml, 6/6 testes GREEN, 401 validado end-to-end via container php, porta 8090 confirmada não publicada no host

Progress: [█████████░] 91% (41/45 planos — Phases 1-7 completas; Phase 8 em andamento 5/9 planos com SUMMARY; Phase 9 pendente)

## Performance Metrics

**Velocity:**
- Total plans completed: 29
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
| Phase 06-controle-manual-n8n-telegram P01 | 6min | 2 tasks | 16 files |
| Phase 06-controle-manual-n8n-telegram P03 | 5min | 1 tasks | 1 files |
| Phase 06-controle-manual-n8n-telegram P02 | 8min | 1 tasks | 2 files |
| Phase 06-controle-manual-n8n-telegram P04 | 7min | 1 tasks | 1 files |
| Phase 06-controle-manual-n8n-telegram P05 | 9min | 2 tasks | 2 files |
| Phase 06-controle-manual-n8n-telegram P06 | 35min | 2 tasks | 4 files |
| Phase 07-schema-multi-canal-python-pipeline P01 | 8min | 1 tasks | 1 files |
| Phase 07-schema-multi-canal-python-pipeline P02 | 18min | 2 tasks | 6 files |
| Phase 07-schema-multi-canal-python-pipeline P03 | 8min | 2 tasks | 2 files |
| Phase 07-schema-multi-canal-python-pipeline P04 | 12min | 1 tasks | 1 files |
| Phase 07-schema-multi-canal-python-pipeline P05 | 2min | 2 tasks | 2 files |
| Phase 07-schema-multi-canal-python-pipeline P06 | 29min | 2 tasks | 6 files |
| Phase 08 P02 | 35min | 3 tasks | 5 files |
| Phase 08 P01 | ~65min | 2 tasks | 96 files |
| Phase 08 P03 | ~40min | 3 tasks | 18 files |
| Phase 08-painel-laravel-filament P05 | ~30min | 2 tasks | 6 files |
| Phase 08 P07 | ~25min | 2 tasks | 3 files |

## Accumulated Context

### Roadmap Evolution

- Phase 6 added: Controle Manual N8N + Telegram
- Phases 7-9 added (v2.0): Schema Multi-Canal + Python Pipeline → Painel Laravel/Filament → Bot Telegram no Laravel

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
- [Phase 05-publicacao-e-automacao-total]: YouTubeUploader usa `/app/token.json`, upload resumivel e thumbnail customizada; testes mockam API real
- [Phase 05-publicacao-e-automacao-total]: Publisher retorna quantidade publicada e nao propaga falhas isoladas; quota incrementa somente em sucesso
- [Phase 05-publicacao-e-automacao-total]: n8n workflow usa Execute Command com retry 3x/15min; requer Docker socket no container n8n para `docker exec`
- [Phase 06-controle-manual-n8n-telegram]: ENUM Phase 6 final: ('pending_cut','pending','cutting','publishing','published','failed','approved','rejected') — append-only mantém metadata-only no MySQL 8.4 e backward-compat com dados legados
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-01 Wave 0 pattern: stubs Python com imports+constants module-level e NotImplementedError no corpo + test_*.py com imports no topo — espelha Phases 2/3/4 RED state
- [Phase 06-controle-manual-n8n-telegram]: n8n Switch v2 com renameOutput+outputKey por comando (status/clipes/aprovar/rejeitar/processar/ajuda) + fallbackOutput=ajuda — Plan 06-07 conecta sub-fluxos por nome legível
- [Phase 06-controle-manual-n8n-telegram]: 01-telegram-handler.json NÃO arquivado — fica em workflows/ como referência. Operador decide manualmente no n8n UI quando substituir pelo router Phase 6
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-03: rejeitar.py usa SELECT+UPDATE com guard 'status IN (pending,approved)' — race com publisher resolvida atomicamente, MP4 só removido se UPDATE afetou linha
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-03: exit codes documentados (0=ok, 1=clip não existe, 2=status inválido/argv inválido) — n8n executeCommand propaga para bot reportar erro diferenciado
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-03: alias db_connect = get_db_connection no namespace de rejeitar.py — satisfaz contrato Wave 0 dos testes (patch('src.rejeitar.db_connect')) sem alterar API pública de src.db
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-03: /aprovar NÃO terá módulo Python — será feito direto pelo n8n MySQL node com UPDATE parametrizado em Plan 06-07; rejeitar requer Python porque há side-effect (delete MP4)
- [Phase 06-controle-manual-n8n-telegram]: Phase 6 Plan 06-02: publisher.py SELECT muda 'pending'→'approved' + nova função _transition_approved_to_publishing com guard WHERE status='approved' e cursor.rowcount check (skip silencioso em race com /rejeitar)
- [Phase 06-controle-manual-n8n-telegram]: Phase 6 fixture pattern: make_conn_with_clips precisa de cursor.rowcount=1 para simular MySQL no caminho feliz do guard de status — Plans futuros que usem guards seguirão mesmo padrão
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-04: pseudo-channel manual:UCxxx com active=FALSE preserva FK quando vídeo manual vem de canal fora do pool RSS (RSS poller ignora linha; FK válida)
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-04: SELECT-then-INSERT (não INSERT...ON DUPLICATE KEY) — chamador precisa do status atual para mensagem Telegram ("já existia status=downloaded" vs "inserido status=pending")
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-04: yt-dlp metadata-only com skip_download=True não consome quota YouTube Data API — alavanca segura para n8n executeCommand chamado pelo bot
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-04: novo vídeo manual entra como status='pending' (não bypassa pipeline) — daemon APScheduler cuida do resto (download → transcribe → select → cut → publish)
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-04: exit codes CLI documentados (0=ok, 2=URL inválida, 3=metadata yt-dlp falhou) — Plan 06-07 roteia mensagem de erro amigável no router por código
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-05: APScheduler dentro do clip-processor (vs n8n cron) — worker é puro lado-Python, n8n cron precisaria de DNS+rede; consistente com pipeline_cycle Phase 5
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-05: ordem expire-then-warn — invertido geraria clip avisado e expirado no mesmo run (UX confusa para operador)
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-05: tradeoff aceito — falha de POST do warn marca Redis SET e perde 1 mensagem; rollback do SET introduziria atomicidade fictícia
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-05: ttl_worker usa requests.post direto (não delega a telegram_notifier) — isolamento, worker independe de Plan 06-06 para rodar
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-05: pattern idempotência durável de mensagens — Redis SET NX com TTL = janela do evento (24h); reaproveitar em futuros plans com side-effects out-of-band
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-06: telegram_notifier.notify implementado como best-effort (try/except RequestException + status_code check) — nunca propaga; default N8N_NOTIFY_URL=http://n8n:5678/webhook/notify (rede docker)
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-06: 3 chamadas notify('pipeline_failure', ...) em pipeline_runner.py (uma por estágio: poll/download/publish) em vez de 1 catch-all — Phase 5 estabeleceu 3 try/except separados; estágio nomeado por literal melhora observability
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-06: cloudflared como container separado (não sidecar do n8n) — restart independente, depends_on:[n8n] garante ordem sem acoplar lifecycle; n8n N8N_PORT=5678 literal (não env)
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-06: docker-compose.yml raiz (fora do repo canaldecortes/) modificado diretamente no FS — Task 2 sem commit git; validado via docker compose config (CONFIG VALID)
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-07: router n8n consolidado em `06-router.json` com Telegram Trigger, 6 comandos, Webhook interno `/webhook/notify` e allowlist via `TELEGRAM_CHAT_ID_ALLOWED`; cron diário separado em `06-cron-resumo-diario.json` às 18h America/Sao_Paulo
- [Phase 06-controle-manual-n8n-telegram]: Plan 06-07: checkpoints finais são manuais por dependerem de BotFather, Cloudflare Zero Trust, Telegram setWebhook, import/activate no n8n e confirmação no YouTube Studio
- [Roadmap v2.0]: Stack v2.0 confirmado — Laravel 13 (não 11, EOL) + Filament 5 (não 3) + Livewire 4 + irazasyed/telegram-bot-sdk 3.16
- [Roadmap v2.0]: GCP Project separado por canal-destino é obrigatório — compartilhar projeto GCP entre 2 canais consome cota única de 10.000 unidades/dia
- [Roadmap v2.0]: Filament: nunca usar --generate em tabelas com ENUM; criar resources com Select::make() e opções explícitas para evitar corrupção de state machine
- [Roadmap v2.0]: Blacklist verificada em rss_poller.py ANTES do download — verificar no publisher desperdiça Groq + Claude + FFmpeg
- [Roadmap v2.0]: Deduplicação de update_id Telegram via Redis desde o primeiro dia — /aprovar executado duas vezes corrompe estado
- [Roadmap v2.0]: Phase 7 deve preceder Phase 8 — Filament precisa da tabela destination_channels existir; Phase 8 precede Phase 9 — bot Laravel depende de Laravel running
- [Phase 07-schema-multi-canal-python-pipeline]: FK destination_channel_id em generated_clips é INT NULL — clips legados permanecem válidos sem canal destino definido
- [Phase 07-schema-multi-canal-python-pipeline]: blacklist UPDATE comentado na migration — evita blacklistar canais acidentalmente em dev; operador descomenta com channel_names reais
- [Phase 07-schema-multi-canal-python-pipeline]: INFORMATION_SCHEMA.STATISTICS usado para checar INDEX antes de ADD INDEX — complementa padrão de COLUMNS para ADD COLUMN
- [Phase 07-schema-multi-canal-python-pipeline]: Plan 07-02: Import de símbolos não existentes feito localmente dentro dos métodos de teste — evita ImportError no nível de módulo que quebraria coleta de testes existentes
- [Phase 07-schema-multi-canal-python-pipeline]: Plan 07-02: SAMPLE_CLIP enriquecido com destination_channel_id e channel_handle — campos extras em dicts Python são ignorados por testes existentes que não os verificam
- [Phase 07-schema-multi-canal-python-pipeline]: channel_slug takes precedence over token_file when provided — aligns with MCAN-01 where slug-based auth is the multi-canal path
- [Phase 07-schema-multi-canal-python-pipeline]: Redis key format youtube_uploads:{channel_id}:{date} isolates quota per destination channel without any shared counter
- [Phase 07-schema-multi-canal-python-pipeline]: Guard Python no loop (if channel.get('blacklisted'): continue) adicionado além do filtro SQL — mocks de teste injetam canais com blacklisted=True via fetchall.return_value, bypass o SQL; dual-layer garante correctness em produção e testes
- [Phase 07-schema-multi-canal-python-pipeline]: Plan 07-05: overlay_watermark usa -filter_complex overlay=W-w-20:20 com clip ANTES watermark nos -i args; graceful degradation retorna input_path se arquivo ausente
- [Phase 07-schema-multi-canal-python-pipeline]: Plan 07-05: append_credits guard duplo (not template or not handle) — basta um vazio para nao adicionar creditos malformados
- [Phase 07-schema-multi-canal-python-pipeline]: _lookup_destination_channel_id chamado uma vez antes do loop de moments em insert_selected_moments — consistência e eficiência de queries
- [Phase 07-schema-multi-canal-python-pipeline]: publish_pending_clips fallback legado quando _fetch_destination_channels retorna [] — pipeline funcional em ambientes sem migration Phase 7 aplicada
- [Phase 07-schema-multi-canal-python-pipeline]: make_conn_with_clips com fetchall.side_effect: primeiro [] aciona fallback legado, novos testes multi-canal sobrescrevem side_effect explicitamente
- [Phase 08]: [Phase 08-painel-laravel-filament]: oauth_expired_flag como coluna BOOLEAN em destination_channels (não Redis) — self-healing no proximo upload bem-sucedido
- [Phase 08]: [Phase 08-painel-laravel-filament]: internal_api.py importa src.rejeitar no topo do modulo para expor patch alvo aos testes (src.internal_api.rejeitar)
- [Phase 08-painel-laravel-filament P01]: Imagem wordpress-php reconstruída para PHP 8.3 (Dockerfile já declarava php:8.3-fpm mas imagem em uso ainda era 8.2.29) — pré-requisito não documentado para instalar Laravel 13
- [Phase 08-painel-laravel-filament P01]: config/database.php ganha conexão Redis nomeada 'pipeline' (DB 0) isolada da 'default' (DB 1) — nunca usar Redis::get() direto para ler chaves do pipeline Python
- [Phase 08-painel-laravel-filament P01]: Pest 4 não tem `php artisan pest:install` — usar `./vendor/bin/pest --init` para gerar tests/Pest.php
- [Phase 08-painel-laravel-filament P01]: wordpress/docker-compose.yml e wordpress/Dockerfile ficam fora do repo git canaldecortes/ — mudanças aplicadas direto no FS, validadas via docker compose config, sem commit (mesmo padrão da Phase 6 P06)
- [Phase 08-painel-laravel-filament P03]: DatabaseTransactions (não RefreshDatabase) em todos os testes Feature do painel — RefreshDatabase apagaria as tabelas do pipeline Python sem migration Laravel
- [Phase 08-painel-laravel-filament P03]: tests/Pest.php passa a estender Tests\TestCase também em Unit (não só Feature) — necessário para o helper config()/app() funcionar em testes Unit que não tocam o banco (ex: DestinationChannelOauthStatusTest)
- [Phase 08-painel-laravel-filament P03]: token_dir configurável via CLIP_PROCESSOR_TOKEN_DIR (default /var/www/html/painel/../youtube) — Plan 08-08 precisa adicionar bind mount ./canaldecortes/youtube:ro ao serviço php do docker-compose.yml (hoje só montado no clip-processor)
- [Phase 08-painel-laravel-filament P03]: Migrations Laravel nativas (users/cache/jobs) aplicadas em clips_automation via `php artisan migrate` — nunca haviam sido rodadas desde o bootstrap do Plan 08-01
- [Phase 08-painel-laravel-filament]: SourceChannelResource: navigationIcon deve ser string|BackedEnum|null (Filament 5.6.7), nao ?string; rotas REST POST/PATCH adicionadas em routes/web.php pois Filament Resource so expoe GET/HEAD (form submit via Livewire)
- [Phase 08-painel-laravel-filament]: Sidecar HTTP interno (Plan 08-07): thread daemon Flask iniciada ANTES do ciclo inicial do pipeline (não depois) para disponibilidade imediata ao painel
- [Phase 08-painel-laravel-filament]: wordpress/.env (nao canaldecortes/.env) e o arquivo real lido pelo Docker Compose para variaveis do docker-compose.yml raiz

### Pending Todos

None.

### Blockers/Concerns

- OAuth app YouTube em modo Testing expira refresh_token em 7 dias e publica vídeos como privados silenciosamente — ao configurar segundo canal, iniciar aprovação Production imediatamente (leva 2-4 semanas).
- Bind mount `./canaldecortes/youtube:ro` não existe ainda no serviço `php` do `wordpress/docker-compose.yml` (só existe no `clip-processor`) — necessário antes do Plan 08-08 (badge OAuth em produção) funcionar com o volume real.

## Session Continuity

Last session: 2026-07-02T01:37:22.295Z
Stopped at: Completed 08-07-PLAN.md
Resume file: None
