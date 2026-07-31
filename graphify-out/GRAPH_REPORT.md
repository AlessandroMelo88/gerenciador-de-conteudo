# Graph Report - canaldecortes  (2026-07-30)

## Corpus Check
- 338 files · ~309,600 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2053 nodes · 3633 edges · 171 communities (144 shown, 27 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 91 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `661b9854`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cn
- publish_pending_clips
- db.py
- DestinationChannels.tsx
- QuotaManager
- Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)
- rss_poller.py
- insert_selected_moments
- User.php
- Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)
- internal_api.py
- ClipProcessorClient
- niche-combobox.tsx
- processar.py
- devDependencies
- utils.ts
- publisher.py
- 05-01 Plan: Publishing schema, skeletons and RED tests
- Telegram\Bot\Commands\Command
- TestUploadClip
- uploader.py
- generate_metadata
- process_clip
- test_internal_api.py
- is_seen
- transcribe_video
- Illuminate\Http\Request
- components.json
- docker-compose.yml (raiz wordpress/)
- download_video
- SourceVideos.tsx
- Illuminate\Database\Eloquent\Factories\Factory
- Inertia\Response
- compilerOptions
- video_processor.py
- Phase 1: Infraestrutura Base
- Phase 7 Context: Schema Multi-Canal + Python Pipeline
- run_pipeline_once
- TelegramHttpClientHandler.php
- confirm-button.tsx
- notify
- Illuminate\Database\Eloquent\Model
- _download_pending_videos
- chart.tsx
- Settings.tsx
- ARCHITECTURE.md (as-built, commit dca6e44)
- process_clip
- dependencies
- _process_ai_pipeline
- YouTubeUploader
- scripts
- painel/README.md (setup fresh 10 passos)
- clip-processor/src/transcriber.py
- composer.json
- _select_pending_videos
- mysql/init/01-clips-schema.sql
- Documentation.tsx
- .planning/research/PITFALLS.md
- .planning/research/FEATURES.md
- sidebar.tsx
- internal_api.py sidecar (Flask, port 8090)
- validate-phase6-n8n.py
- Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan
- clip-processor/src/rss_poller.py
- append_credits
- conftest.py
- input-group.tsx
- Phase 8 Plan 08: Dashboard Widgets + Aprovar/Rejeitar Plan
- _process_pending_clips(conn)
- overlay_watermark
- require-dev
- 02-04-PLAN.md: Daemon main.py Plan
- .planning/research/ARCHITECTURE.md (v2.0 research, superseded)
- youtube_oauth.py
- pipeline_runner.py
- 02-01-PLAN: pytest scaffold RED state (Wave 0)
- Phase 8 Context (Painel Laravel/Filament)
- main.py
- TestYouTubeUploaderChannelSlug
- setup
- Phase 9-04 Plan: Telegram Bot Checkpoint
- Phase 7: Schema Multi-Canal + Python Pipeline
- 01-04-PLAN: OAuth YouTube e verificação do canal
- config
- require
- Illuminate\Http\RedirectResponse
- clip-processor/src/metadata_generator.py
- destination_channels table
- generated_clips.status state machine
- transcribe_video
- Phase 8 Research (Painel Laravel/Filament)
- Dashboard
- ClipProcessorClient.php
- psr-4
- v2.0 — Painel + Multi-Canal
- Pitfall: Content ID Claim Despite Watermark
- list-pending-clips.sh
- ExampleTest
- youtube/assets/BRANDING.md — Futebol em Cortes visual identity
- mark-failed.sh
- mark-published.sh
- test_transcription_job.py
- _process_ai_pipeline
- validate-infra.sh
- get_db_connection
- @dnd-kit/core
- @dnd-kit/sortable
- @dnd-kit/utilities
- ttl_worker.py
- rejeitar
- force-download.sh
- CreatePainelUser artisan command
- radix-ui
- react-dom
- recharts
- shadcn
- tailwind-merge
- Quick Task 1: Transcrição Local Summary
- vaul
- ziggy-js
- 03-RESEARCH.md: Phase 3 Research
- MCAN-04: 3 vídeos/dia por canal 19h-22h BRT
- Claude Haiku para seleção e metadados
- Resenha FC channel banner (2048x1152)
- Soccer-ball mascot with microphone (cartoon character)
- Resenha FC (brand/channel name)
- TelegramWebhookController.php
- test_rss_poller.py
- TestPollAllChannels
- SourceChannel
- package.json
- TestBlacklistGuard
- v1.0 — Pipeline Base
- ._load_credentials
- AppServiceProvider
- Phase 8 Plan 09: Checkpoint Final End-to-End Summary
- test_uploader.py
- post-create-project-cmd
- Phase 9 Plan 03: Migração Python + Artisan Schedule Plan
- keywords
- sonner
- zod

## God Nodes (most connected - your core abstractions)
1. `cn()` - 191 edges
2. `QuotaManager` - 39 edges
3. `YouTubeUploader` - 37 edges
4. `publish_pending_clips()` - 35 edges
5. `poll_all_channels()` - 25 edges
6. `get_db_connection()` - 23 edges
7. `process_clip()` - 23 edges
8. `GeneratedClip` - 23 edges
9. `run_pipeline_once()` - 22 edges
10. `ClipProcessorClient` - 22 edges

## Surprising Connections (you probably didn't know these)
- `publish_pending_clips()` --rationale_for--> `Publisher legacy fallback when destination_channels empty`  [EXTRACTED]
  clip-processor/src/publisher.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-06-SUMMARY.md
- `overlay_watermark()` --rationale_for--> `Graceful degradation pattern: return input unchanged when optional dependency missing`  [EXTRACTED]
  clip-processor/src/video_processor.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-05-SUMMARY.md
- `docker-compose.yml branding volume for clip-processor` --shares_data_with--> `overlay_watermark()`  [EXTRACTED]
  .planning/phases/07-schema-multi-canal-python-pipeline/07-07-PLAN.md → clip-processor/src/video_processor.py
- `.planning/research/ARCHITECTURE.md (v2.0 research, superseded)` --semantically_similar_to--> `ARCHITECTURE.md (as-built, commit dca6e44)`  [INFERRED] [semantically similar]
  .planning/research/ARCHITECTURE.md → ARCHITECTURE.md
- `generate_metadata()` --implements--> `Anthropic structured outputs via output_config json_schema`  [EXTRACTED]
  clip-processor/src/metadata_generator.py → .planning/phases/04-processamento-de-video/04-03-SUMMARY.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase 1 infrastructure setup flow: containers → schema → secrets → OAuth** — docker_compose_yml, clips_schema_sql, env_file, generate_token_py [EXTRACTED 1.00]
- **ACQU-01/02/03 requirements mapped to rss_poller/downloader/dedup modules** — planning_requirements_acqu_01, planning_requirements_acqu_02, planning_requirements_acqu_03, rss_poller_py, downloader_py, dedup_py [EXTRACTED 1.00]
- **Phase 2 TDD flow: tests RED → db.py GREEN → dedup/downloader/rss_poller GREEN** — test_db_py, db_py, dedup_py, downloader_py, rss_poller_py [EXTRACTED 1.00]
- **Phase 2 daemon assembly: main.py orchestrating rss_poller, db recovery, and scheduling** — clip_processor_src_main_py, clip_processor_src_rss_poller_py, clip_processor_src_db_py, apscheduler_blockingscheduler_pattern [EXTRACTED 1.00]
- **Phase 3 TDD cycle: skeletons, RED tests, then GREEN implementation of transcriber and selector wired into rss_poller** — clip_processor_tests_test_transcriber_py, clip_processor_tests_test_selector_py, clip_processor_src_transcriber_py, clip_processor_src_selector_py, process_ai_pipeline_function [EXTRACTED 1.00]
- **Phase 4 clip rendering: process_clip orchestrating cut, subtitles, thumbnail, and metadata** — process_clip_function, cut_clip_function, generate_srt_function, burn_subtitles_function, extract_thumbnail_function, generate_metadata_function [EXTRACTED 1.00]
- **MySQL 8.4 idempotent migration pattern via INFORMATION_SCHEMA** — mysql_init_03_schema_migration, mysql_init_04_publishing_migration, decision_migration_mysql84_information_schema [INFERRED 0.85]
- **Phase 4 clip processing pipeline: cut, subtitle, thumbnail, metadata** — clip_processor_src_video_processor_process_clip, clip_processor_src_metadata_generator_generate_metadata, clip_processor_src_rss_poller__process_pending_clips, generated_clips_status_pending_cut [EXTRACTED 1.00]
- **Phase 5 publishing pipeline: quota, upload, publisher, runner, n8n** — clip_processor_src_quota_manager, clip_processor_src_uploader, clip_processor_src_publisher, clip_processor_src_pipeline_runner_run_pipeline_once, n8n_workflows_canaldecortes_pipeline_json [EXTRACTED 1.00]
- **Wave 0 scaffolding delivers migration + 4 stubs + RED tests + n8n skeletons that unblock Waves 1-3** — planning_phases_06_controle_manual_n8n_telegram_06_01_plan, 05_controle_manual_migration_sql, clip_processor_src_processar_py, clip_processor_src_rejeitar_py, clip_processor_src_ttl_worker_py, clip_processor_src_telegram_notifier_py [EXTRACTED 0.95]
- **Phase 6 pipeline: pending clip → /aprovar → approved → publisher (guard) → publishing → published + notify** — ctrl_02_publisher_approved, clip_processor_src_publisher_py, telegram_n8n_workflows_06_router_json, clip_processor_src_telegram_notifier_py, status_guard_pattern [EXTRACTED 0.90]
- **3 proactive Telegram events (upload_published, pipeline_failure, clip_ttl_warning) routed through n8n webhook /notify** — clip_processor_src_publisher_py, clip_processor_src_pipeline_runner_py, clip_processor_src_ttl_worker_py, telegram_n8n_workflows_06_router_json [EXTRACTED 0.90]
- **Publisher multi-canal publication flow: per-channel quota, uploader, credits, watermark** — clip_processor_src_publisher_publish_pending_clips, clip_processor_src_quota_manager_quotamanager, clip_processor_src_uploader_youtubeuploader, clip_processor_src_metadata_generator_append_credits, clip_processor_src_video_processor_overlay_watermark [EXTRACTED 1.00]
- **Panel Laravel bootstrap: docker wiring, config, and clip-processor integration points** — painel_laravel_project, wordpress_docker_compose_yml, canaldecortes_nginx_conf, painel_config_services_clip_processor, painel_config_database_pipeline_connection [EXTRACTED 1.00]
- **OAuth expired flag lifecycle: producer (uploader), storage (migration), consumer (Laravel model)** — mysql_init_07_panel_oauth_flag_migration, oauth_expired_flag_column, painel_model_destinationchannel, clip_processor_src_uploader_youtubeuploader [EXTRACTED 1.00]
- **OAuth badge observability flow (uploader → flag → widget)** — clip_processor_src_uploader, google_auth_exceptions_refresherror, destination_channels_oauth_expired_flag, painel_app_filament_resources_destinationchannelresource [EXTRACTED 1.00]
- **HTTP sidecar bridge pattern (Laravel ↔ clip-processor)** — painel_app_services_clipprocessorclient, clip_processor_src_internal_api, clip_processor_src_main, http_sidecar_pattern3 [EXTRACTED 1.00]
- **Telegram bot migration from n8n to Laravel** — clip_processor_src_telegram_notifier, painel_app_http_controllers_telegramwebhookcontroller, painel_routes_console, clip_processor_src_ttl_worker [EXTRACTED 1.00]
- **Phase 9 Telegram-to-Laravel migration (research → plan → validation → n8n deprecation)** — planning_phases_09_bot_telegram_no_laravel_09_research_bot_telegram, planning_phases_09_bot_telegram_no_laravel_09_04_plan_telegram_checkpoint, planning_phases_09_bot_telegram_no_laravel_09_validation_phase9, planning_research_pitfalls_n8n_parallel_bot [INFERRED 0.85]
- **Multi-channel YouTube quota isolation design and its pitfalls** — planning_research_pitfalls_shared_quota_pool, planning_research_architecture_quota_manager_channel_scoping, architecture_asbuilt_quota_window_roundrobin, planning_research_features_multichannel_youtube_publishing [INFERRED 0.85]
- **Filament-era documentation now stale vs as-built Inertia/React reality** — readme_canaldecortes, painel_readme, planning_research_architecture_v2, architecture_asbuilt_filament_removed_commit, architecture_asbuilt_dead_filament_dashboard [INFERRED 0.85]
- **Roteamento multi-canal: selector -> generated_clips -> publisher** — planning_phases_07_schema_multi_canal_python_pipeline_07_research_selector, planning_phases_07_schema_multi_canal_python_pipeline_07_research_generated_clips_destination_channel_id, planning_phases_07_schema_multi_canal_python_pipeline_07_research_publisher, planning_phases_07_schema_multi_canal_python_pipeline_07_research_routing_target_niche [INFERRED 0.85]
- **Pipeline de processamento de vídeo: burn_subtitles + watermark** — planning_phases_07_schema_multi_canal_python_pipeline_07_research_video_processor, planning_phases_07_schema_multi_canal_python_pipeline_07_research_watermark_overlay, planning_phases_07_schema_multi_canal_python_pipeline_07_research_pitfall_intermediate_files, planning_phases_07_schema_multi_canal_python_pipeline_07_research_pitfall_overlay_input_order [EXTRACTED 0.90]
- **Publicação por canal: quota + uploader + publisher** — planning_phases_07_schema_multi_canal_python_pipeline_07_research_quota_manager, planning_phases_07_schema_multi_canal_python_pipeline_07_research_uploader, planning_phases_07_schema_multi_canal_python_pipeline_07_research_publisher, planning_phases_07_schema_multi_canal_python_pipeline_07_research_redis_quota_per_channel [EXTRACTED 0.90]

## Communities (171 total, 27 thin omitted)

### Community 0 - "cn"
Cohesion: 0.08
Nodes (35): Avatar(), AvatarBadge(), AvatarFallback(), AvatarGroup(), AvatarGroupCount(), AvatarImage(), Breadcrumb(), BreadcrumbEllipsis() (+27 more)

### Community 1 - "publish_pending_clips"
Cohesion: 0.05
Nodes (57): _fetch_destination_channels(), _fetch_pending_clips(), _fetch_pending_clips_for_channel(), _log(), _mark_clip_failed(), _mark_clip_published(), _maybe_finalize_source_video(), _publish_clips_for() (+49 more)

### Community 2 - "db.py"
Cohesion: 0.12
Nodes (19): insert_video(), _log(), db.py — Módulo de acesso ao MySQL para o daemon clip-processor. Exporta: -…, Redefine vídeos presos em status 'downloading' de volta para 'pending'.…, Devolve vídeos presos em 'selecting' para 'downloaded' (reprocessa a IA).…, Loga mensagem com timestamp para stdout., Atualiza o status de um vídeo na tabela source_videos. Args: conn: conexão…, Insere um novo vídeo na tabela source_videos com status 'pending'. Usa INSERT… (+11 more)

### Community 3 - "DestinationChannels.tsx"
Cohesion: 0.10
Nodes (26): STATUS_LABEL, FailuresTable(), PendingTable(), post(), QueuedTable(), useSelection(), ConfirmButton(), Niche (+18 more)

### Community 4 - "QuotaManager"
Cohesion: 0.07
Nodes (32): datetime, QuotaManager, Controla uploads diarios do YouTube por data local de Sao_Paulo. Reserva de…, Janela + cota total, ignorando reserva por formato. Usado para decidir se o…, Retorna True se horario e quota (total + formato) permitirem upload., Incrementa contador diario (total e, se 'longo', o de formato) e garante TTL., dt_sp(), make_redis() (+24 more)

### Community 5 - "Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)"
Cohesion: 0.05
Nodes (66): mysql/init/05-controle-manual-migration.sql, mysql/init/06-multi-canal-migration.sql, mysql/manual-workflow/approve-backlog.sql — helper opcional para backlog de pending, BlockingScheduler daemon pattern (APScheduler), APScheduler dentro do clip-processor (vs n8n cron) para TTL worker, clip-processor/src/db.py, clip-processor/src/main.py, clip-processor/src/pipeline_runner.py (+58 more)

### Community 6 - "rss_poller.py"
Cohesion: 0.18
Nodes (13): _extract_video_id(), _is_blocked_title(), _log(), poll_all_channels(), _process_pending_clips(), rss_poller.py — Monitor de feeds RSS de canais YouTube e inserção de vídeos…, Processa clips com status pending_cut sem abortar o poll por falha isolada., Monitora feeds RSS de todos os canais ativos e insere vídeos novos. Args:… (+5 more)

### Community 7 - "insert_selected_moments"
Cohesion: 0.07
Nodes (32): _enforce_longform_duration(), insert_selected_moments(), _log(), _lookup_destination_channel_id(), _parse_moments(), selector.py — Seleção de momentos via IA com fallback automático. Prioridade em…, Garante duração mínima de MIN_LONGFORM_SECONDS para o modo 'longo'. O modelo…, Analisa transcrição e retorna momentos selecionados via IA. Fluxo de seleção de… (+24 more)

### Community 8 - "User.php"
Cohesion: 0.08
Nodes (14): Filament\Models\Contracts\FilamentUser interface, Illuminate\Console\Command, Illuminate\Database\Console\Seeds\WithoutModelEvents, Illuminate\Database\Seeder, Illuminate\Foundation\Auth\User, Illuminate\Foundation\Testing\TestCase, Illuminate\Notifications\Notifiable, CreatePainelUser (+6 more)

### Community 9 - "Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)"
Cohesion: 0.07
Nodes (34): canaldecortes/docker/nginx/canaldecortes.conf vhost, clip-processor não tem bind mount de src/ — exige rebuild+restart para refletir código, mysql/init/07-panel-oauth-flag-migration.sql (oauth_expired_flag idempotent migration), destination_channels.oauth_expired_flag column, config/database.php Redis 'pipeline' connection (DB 0), config/services.php clip_processor block (url/token), canaldecortes/painel/ — Laravel 13 + Filament 5.6.7 + Pest 4.7.4 project, App\Models\DestinationChannel Eloquent Model + getOauthStatusAttribute (+26 more)

### Community 10 - "internal_api.py"
Cohesion: 0.22
Nodes (16): internal_api.resolve_channel(url) — yt-dlp channel resolution, _check_auth(), delete_source_video_file(), internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.…, Roda yt-dlp em modo metadata-only e extrai id/name/handle. Padrão yt-dlp:…, Chama src.rejeitar.rejeitar(clip_id) diretamente. Preserva exit codes 0/1/2., Apaga o arquivo bruto (.mp4) de um source_video e zera local_path no banco. Não…, reject_clip() (+8 more)

### Community 11 - "ClipProcessorClient"
Cohesion: 0.15
Nodes (4): Illuminate\Http\JsonResponse, SourceVideoController, SourceVideo, ClipProcessorClient

### Community 12 - "niche-combobox.tsx"
Cohesion: 0.11
Nodes (24): NicheCombobox(), slugify(), Command(), CommandDialog(), CommandEmpty(), CommandGroup(), CommandInput(), CommandItem() (+16 more)

### Community 13 - "processar.py"
Cohesion: 0.10
Nodes (21): fetch_metadata(), main(), _normalize_upload_date(), parse_video_id(), processar.py — Ingestão manual de vídeo YouTube via comando /processar do…, Entrypoint CLI. Exit codes: - 0: OK (inserido ou já existia) - 2: URL inválida…, Extrai videoId de 11 caracteres de uma URL YouTube. None se URL inválida.…, Converte 'YYYYMMDD' (formato yt-dlp) para 'YYYY-MM-DD HH:MM:SS' (TIMESTAMP… (+13 more)

### Community 14 - "devDependencies"
Cohesion: 0.09
Nodes (23): concurrently, laravel-vite-plugin, devDependencies, concurrently, laravel-vite-plugin, tailwindcss, @tailwindcss/typography, @tailwindcss/vite (+15 more)

### Community 15 - "utils.ts"
Cohesion: 0.14
Nodes (14): LoginForm(), Field(), FieldContent(), FieldDescription(), FieldError(), FieldGroup(), FieldLegend(), FieldSeparator() (+6 more)

### Community 16 - "publisher.py"
Cohesion: 0.08
Nodes (30): Blacklist guard (source_channels.blacklisted), COPY-01: watermark queimado via FFmpeg, COPY-02: descrição inclui créditos do canal original, COPY-03: canais blacklistados bloqueados no RSS poller, credit_template / channel_handle credits, generated_clips.destination_channel_id FK, MCAN-01: múltiplos canais YouTube com OAuth próprio, MCAN-02: campo niche determina canal-destino (+22 more)

### Community 17 - "05-01 Plan: Publishing schema, skeletons and RED tests"
Cohesion: 0.07
Nodes (34): quota_manager.py — Limite diario e janela de horario para uploads YouTube.…, YouTubeUploader.upload_clip(clip), MAX_UPLOADS_PER_DAY clamped to <= 6, default 2, Migration Phase 3 usa INFORMATION_SCHEMA em vez de ADD COLUMN IF NOT EXISTS, Persistir arquivos renderizados no volume montado /app/videos, Raw source só removido quando todos clips do source video estão terminais, Workflow usa Execute Command com retry 3x e espera 15 minutos, YOUTUBE_TOKEN_FILE (default /app/token.json) (+26 more)

### Community 18 - "Telegram\Bot\Commands\Command"
Cohesion: 0.17
Nodes (8): AjudaCommand, AprovarCommand, ClipesCommand, ProcessarCommand, RejeitarCommand, Phase 9 Plan 02: TelegramWebhookController + Commands Plan, Phase 9 Plan 02: TelegramWebhookController + Commands Summary, Telegram\Bot\Commands\Command

### Community 19 - "TestUploadClip"
Cohesion: 0.11
Nodes (12): make_youtube_mock(), token_file inexistente deve levantar FileNotFoundError., Se thumbnail_path existir, thumbnails().set() deve ser chamado., Cria um mock do serviço YouTube que simula upload bem-sucedido., Falha no upload da thumbnail deve ser propagada ao caller., Tags em formato string separado por vírgula devem virar lista., YOUTUBE_PRIVACY_STATUS do env deve ser usado no upload., Upload bem-sucedido deve retornar o youtube_video_id. (+4 more)

### Community 20 - "uploader.py"
Cohesion: 0.15
Nodes (12): MediaFileUpload, uploader.py — Upload de clips para YouTube Data API v3. Exporta: -…, RefreshError, RED test para captura de RefreshError e persistência de oauth_expired_flag…, RefreshError em creds.refresh() deve setar oauth_expired_flag=TRUE em…, test_load_credentials_catches_refresh_error_and_flags_channel(), destination_channels.oauth_expired_flag column, google.auth.exceptions.RefreshError (+4 more)

### Community 21 - "generate_metadata"
Cohesion: 0.11
Nodes (21): Anthropic structured outputs via output_config json_schema, _build_prompt(), generate_metadata(), _generate_via_anthropic(), _generate_via_groq(), _log(), _normalize_metadata(), metadata_generator.py — Geração de título, descrição e tags para YouTube.… (+13 more)

### Community 22 - "process_clip"
Cohesion: 0.12
Nodes (15): _build_clip_context(), cut_clip(), extract_thumbnail(), _fetch_clip(), process_clip(), Extrai um frame do clip como thumbnail JPG., Processa um registro de generated_clips com status pending_cut. Pipeline: cut →…, Corta um trecho do vídeo fonte. fmt='curto' (padrão): converte pra vertical… (+7 more)

### Community 23 - "test_internal_api.py"
Cohesion: 0.08
Nodes (15): purge_old_videos(), Limpa vídeos fonte com published_at anterior a `before_date` (formato 'YYYY-MM-…, client(), fixture, RED tests for internal_api sidecar (implementação GREEN no Plan 08-07)., POST /internal/process-url com format='longo' repassa fmt='longo' pro…, POST /internal/process-url sem campo 'url' retorna 400., purge_old_videos apaga linhas sem clips e libera arquivo de linhas com clips… (+7 more)

### Community 24 - "is_seen"
Cohesion: 0.13
Nodes (15): is_seen(), _log(), mark_failed_redis(), dedup.py — Deduplicação de vídeos via Redis com fallback para MySQL. Exporta: -…, Loga mensagem com timestamp para stdout., Verifica se o vídeo já foi processado anteriormente. Consulta o Redis primeiro.…, Remove a chave do vídeo do Redis quando o download falha. Isso permite que o…, Testes ACQU-03: deduplicação via Redis com fallback para MySQL. Módulo alvo:… (+7 more)

### Community 25 - "transcribe_video"
Cohesion: 0.13
Nodes (15): _log(), _prepare_audio(), transcriber.py — Transcrição de vídeos via Groq Whisper API. Exporta: -…, Salva JSON de transcrição em disco e atualiza transcript_path no banco. Args:…, Extrai áudio MP3 de um arquivo de vídeo via ffmpeg. Args: video_path: caminho…, Transcreve um vídeo via Groq Whisper API. Args: video_id: youtube_video_id do…, save_transcript(), transcribe_video() (+7 more)

### Community 26 - "Illuminate\Http\Request"
Cohesion: 0.17
Nodes (7): Illuminate\Http\Request, Inertia\Middleware, DestinationChannelController, NicheController, HandleInertiaRequests, DestinationChannel, Niche

### Community 27 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 28 - "docker-compose.yml (raiz wordpress/)"
Cohesion: 0.12
Nodes (20): ANTHROPIC_API_KEY intencionalmente vazia até Phase 3, clip-processor/Dockerfile, CLIP_PROCESSOR_INTERNAL_TOKEN env var, clip-processor service (build local), CLIPS_DB_PASSWORD como placeholder no SQL, docker-compose.yml (raiz wordpress/), .env (secrets reais), N8N_ENCRYPTION_KEY via ${VAR} nunca hardcoded (+12 more)

### Community 29 - "download_video"
Cohesion: 0.14
Nodes (14): _cleanup_partial(), download_video(), _log(), downloader.py — Download de vídeos YouTube via yt-dlp com disk guard e retry.…, Loga mensagem com timestamp para stdout., Deleta arquivos .part gerados por download incompleto. Usa glob para encontrar…, Baixa um vídeo do YouTube em formato 720p mp4. Args: video_id: ID do vídeo…, Testes ACQU-02: download 720p, disk guard, partial cleanup. Módulo alvo:… (+6 more)

### Community 30 - "SourceVideos.tsx"
Cohesion: 0.13
Nodes (17): Checkbox(), Select(), SelectContent(), SelectGroup(), SelectItem(), SelectLabel(), SelectScrollDownButton(), SelectScrollUpButton() (+9 more)

### Community 31 - "Illuminate\Database\Eloquent\Factories\Factory"
Cohesion: 0.15
Nodes (7): Illuminate\Database\Eloquent\Factories\Factory, DestinationChannelFactory, GeneratedClipFactory, SourceChannelFactory, SourceVideoFactory, static, UserFactory

### Community 32 - "Inertia\Response"
Cohesion: 0.15
Nodes (6): Inertia\Response, AuthController, Controller, DocumentationController, ProcessVideoController, SettingsController

### Community 33 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 34 - "video_processor.py"
Cohesion: 0.13
Nodes (16): burn_subtitles(), _format_srt_time(), generate_srt(), video_processor.py — Corte, legendas, thumbnail e processamento de clips.…, Queima legendas SRT no clip usando FFmpeg. Alignment=2 (rodapé-centro), estilo…, Gera arquivo SRT relativo ao início do clip a partir dos segmentos Whisper., _update_clip_status(), TestSubtitles (+8 more)

### Community 35 - "Phase 1: Infraestrutura Base"
Cohesion: 0.26
Nodes (10): ACQU-01: Monitoramento RSS de canais, ACQU-02: Download automático 720p via yt-dlp, ACQU-03: Deduplicação Redis + MySQL UNIQUE, INFRA-01: Sistema roda em Docker, INFRA-02: Banco clips_automation com 3 tabelas, INFRA-03: Canal YouTube verificado, INFRA-04: Variáveis de ambiente e secrets, ORC-02: Status de cada job registrado no MySQL (+2 more)

### Community 36 - "Phase 7 Context: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.14
Nodes (18): rss_poller blacklist guard + target_niche SELECT extension, COPY-01 requirement: watermark burned into every clip, COPY-02 requirement: original channel credits in description, COPY-03 requirement: blacklisted channels never downloaded, Dual-layer blacklist guard pattern (SQL filter + Python loop guard), Graceful degradation pattern: return input unchanged when optional dependency missing, MCAN-01 requirement: OAuth token per destination channel, MCAN-02 requirement: destination_channel_id routing by niche (+10 more)

### Community 37 - "run_pipeline_once"
Cohesion: 0.10
Nodes (16): Executa RSS/download/AI/video e depois publicacao. Falhas isoladas sao logadas,…, run_pipeline_once(), HttpError, Sem injeção, deve criar e fechar a própria conexão., Erro em _download_pending_videos não deve propagar., Deve chamar poll → download → publish em ordem., Erro em _download_pending_videos não deve propagar., Conexões injetadas devem ser passadas para os sub-módulos. (+8 more)

### Community 38 - "TelegramHttpClientHandler.php"
Cohesion: 0.23
Nodes (6): GuzzleHttp\Promise\PromiseInterface, static, TelegramHttpClientHandler, Psr\Http\Message\ResponseInterface, Telegram\Bot\HttpClients\HttpClientInterface, Laravel Http adapter for SDK (enables Http::fake())

### Community 39 - "confirm-button.tsx"
Cohesion: 0.20
Nodes (14): ConfirmButtonProps, AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent(), AlertDialogDescription(), AlertDialogFooter(), AlertDialogHeader() (+6 more)

### Community 40 - "notify"
Cohesion: 0.17
Nodes (14): notify(), telegram_notifier.py — Cliente HTTP que publica eventos do pipeline para o…, POST para LARAVEL_NOTIFY_URL com {event, payload}. Retorna True em 2xx, False…, Testes para telegram_notifier.py — cliente HTTP que dispara eventos para o…, notify() captura RequestException e retorna False sem propagar., notify() retorna False quando o endpoint retorna 4xx., notify() faz POST para LARAVEL_NOTIFY_URL — RED até Plan 09-03. Importa…, notify() inclui header Host para nginx routing — RED até Plan 09-03. (+6 more)

### Community 41 - "Illuminate\Database\Eloquent\Model"
Cohesion: 0.18
Nodes (5): Illuminate\Database\Eloquent\Factories\HasFactory, Illuminate\Database\Eloquent\Model, TranscriptionController, TranscriptionJob, Symfony\Component\HttpFoundation\StreamedResponse

### Community 42 - "_download_pending_videos"
Cohesion: 0.20
Nodes (9): _download_pending_videos(), Baixa vídeos com status 'pending', um por vez, atualizando status no DB., Download bem-sucedido deve atualizar status para downloaded com local_path., Download falho deve atualizar status para failed., Sem vídeos pending, não deve chamar download_video., Janela já cheia nos dois formatos não deve chamar download_video., Ordem fixa: repõe longos primeiro, depois curtos., Importar main.py não deve iniciar o scheduler (coalesce = True verificado via… (+1 more)

### Community 43 - "chart.tsx"
Cohesion: 0.12
Nodes (19): react, ChartConfig, ChartContainer(), ChartContext, ChartContextProps, ChartLegendContent(), ChartTooltipContent(), getPayloadConfigFromPayload() (+11 more)

### Community 44 - "Settings.tsx"
Cohesion: 0.07
Nodes (33): ActiveWindowTable(), ClipQueueTabs(), OverviewCards(), SiteHeader(), Card(), CardAction(), CardContent(), CardDescription() (+25 more)

### Community 45 - "ARCHITECTURE.md (as-built, commit dca6e44)"
Cohesion: 0.18
Nodes (13): ARCHITECTURE.md (as-built, commit dca6e44), AI fallback chain (Claude → Groq → deterministic), niches table (only Laravel-migration-managed pipeline table), Quota, window and round-robin logic, source_videos.status state machine, CLAUDE.md — Canal de Cortes work instructions, Rules for destructive operations, metadata_generator.py Groq fallback fix (27/07/2026) (+5 more)

### Community 46 - "process_clip"
Cohesion: 0.14
Nodes (18): burn_subtitles(), clip-processor/src/video_processor.py, clip-processor/tests/test_clip_pipeline.py, clip-processor/tests/test_video_processor.py, cut_clip(), extract_thumbnail(), generate_srt(), Pitfall: container restart com vídeo em status downloading (+10 more)

### Community 47 - "dependencies"
Cohesion: 0.11
Nodes (19): class-variance-authority, clsx, cmdk, @dnd-kit/modifiers, @fontsource-variable/geist, @inertiajs/react, lucide-react, dependencies (+11 more)

### Community 48 - "_process_ai_pipeline"
Cohesion: 0.22
Nodes (11): output_config json_schema em vez de prefill para Claude Haiku 4.5, generate_metadata(), insert_selected_moments(), Algoritmo de remoção de overlap por score, _process_ai_pipeline(), _remove_overlaps(), AI-03: filtro de qualidade score >= 7, máx 3 clips, VID-04: metadata SEO via Claude Haiku (+3 more)

### Community 49 - "YouTubeUploader"
Cohesion: 0.26
Nodes (5): Self-healing: reseta oauth_expired_flag=FALSE após upload bem-sucedido., Cliente fino para videos.insert + thumbnails.set., YouTubeUploader, Multi-canal extension via optional constructor param + None-guard retrocompat, Publisher legacy fallback when destination_channels empty

### Community 50 - "scripts"
Cohesion: 0.14
Nodes (14): scripts, dev, post-autoload-dump, post-update-cmd, pre-package-uninstall, test, Composer\\Config::disableProcessTimeout, Illuminate\\Foundation\\ComposerScripts::postAutoloadDump (+6 more)

### Community 51 - "painel/README.md (setup fresh 10 passos)"
Cohesion: 0.20
Nodes (10): Boundary rule: painel reads directly, writes via sidecar, Filament removal commit dca6e44, painel/ — Laravel 13 + Inertia 3 + React 19 (Filament removed), clip-processor/requirements.txt, painel/README.md (setup fresh 10 passos), YouTube OAuth authorization CLI flow (youtube_oauth.py), Filament 5.x version choice (not 3), PROJECT_BRIEF.md — Canal de Cortes as-built brief (+2 more)

### Community 52 - "clip-processor/src/transcriber.py"
Cohesion: 0.15
Nodes (14): clip-processor/src/selector.py, clip-processor/src/transcriber.py, clip-processor/tests/test_selector.py, clip-processor/tests/test_transcriber.py, Groq Whisper whisper-large-v3-turbo + verbose_json + timestamp_granularities segment + pt, mysql/init/03-schema-migration.sql, 03-01-PLAN.md: Wave 0 skeletons + RED tests, 03-01-SUMMARY.md: Wave 0 Summary (+6 more)

### Community 53 - "composer.json"
Cohesion: 0.14
Nodes (13): autoload-dev, psr-4, description, extra, laravel, dont-discover, license, minimum-stability (+5 more)

### Community 54 - "_select_pending_videos"
Cohesion: 0.24
Nodes (8): Seleciona vídeos pendentes pra repor a janela de download ativo. Para cada…, _select_pending_videos(), Testes para _select_pending_videos — janela de download ativo (DOWNLOAD-01)., Janela vazia (occupied=0) deve buscar até o teto de cada formato., Formato já na janela cheia não gera nenhuma query SELECT (só o COUNT)., Déficit parcial (occupied=1 de janela 4) deve pedir LIMIT 3, não o teto inteiro., SELECT deve restringir a published_at de hoje ou ontem (FRESHNESS_DAYS=1)., TestSelectPendingVideos

### Community 55 - "mysql/init/01-clips-schema.sql"
Cohesion: 0.24
Nodes (12): mysql/init/01-clips-schema.sql, db.py: quem chama é responsável por fechar a conexão, clip-processor/src/db.py, generated_clips table, INSERT IGNORE para idempotência de vídeos/canais, 01-02-PLAN: Schema SQL clips_automation e validate-infra.sh, 02-02-PLAN: docker-compose + requirements + seed + db.py, 02-02-SUMMARY: db.py GREEN, seed 5 canais (+4 more)

### Community 56 - "Documentation.tsx"
Cohesion: 0.33
Nodes (6): Accordion(), AccordionContent(), AccordionItem(), AccordionTrigger(), CHAIN, PageProps

### Community 57 - ".planning/research/PITFALLS.md"
Cohesion: 0.20
Nodes (9): n8n 06-router.json deactivation, QuotaManager per-channel Redis key design, Pitfall: Blacklist Check Happens Too Late in the Pipeline, Pitfall: Filament Delete Button Deletes MySQL Row Without Deleting Files, Pitfall: Laravel Writes Conflict with Python Pipeline Mid-Transaction, Pitfall: n8n Still Running Telegram Bot in Parallel After Migration, Pitfall: OAuth App in Testing Mode Breaks Weekly, Pitfall: Quota Cega — shared GCP project quota (+1 more)

### Community 58 - ".planning/research/FEATURES.md"
Cohesion: 0.20
Nodes (9): irazasyed/telegram-bot-sdk ^3.16, burn_watermark() function design, Admin Panel (Laravel/Filament) feature spec, Copyright Protection feature spec, Multi-Channel YouTube Publishing feature spec, OAuth testing-mode token expiry warning (7 days), Telegram Bot in Laravel feature spec, Laravel 13 version choice (not 11) (+1 more)

### Community 59 - "sidebar.tsx"
Cohesion: 0.06
Nodes (40): AppSidebar(), NavItem, navItems, NavUser(), Sheet(), SheetContent(), SheetDescription(), SheetFooter() (+32 more)

### Community 60 - "internal_api.py sidecar (Flask, port 8090)"
Cohesion: 0.17
Nodes (13): APScheduler jobs (ingest_cycle, publish_cycle, clip_pending_ttl), clip-processor service (as-built), internal_api.py sidecar (Flask, port 8090), CLIP_PROCESSOR_INTERNAL_TOKEN shared setup, Telegram Command classes (Status/Clipes/Aprovar/Rejeitar/Processar/Ajuda), Pitfall: CSRF blocking Telegram webhook (419), Pitfall: Python→Laravel via wrong Host header (404), POST /internal/pipeline-event (Laravel endpoint) (+5 more)

### Community 61 - "validate-phase6-n8n.py"
Cohesion: 0.53
Nodes (10): AssertionError, assert_contains(), assert_has_node(), load_json(), main(), nodes_by_name(), validate_cron(), validate_docs() (+2 more)

### Community 62 - "Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan"
Cohesion: 0.20
Nodes (9): BOT-01 requirement (webhook + allowlist + dedup), BOT-02 requirement (6 Telegram commands), BOT-03 requirement (pipeline-event notifications), Illuminate\Foundation\Configuration\Middleware, PipelineEventTest.php (4 RED tests), TelegramCommandsTest.php (7 RED tests), TelegramWebhookTest.php (3 RED tests), Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan (+1 more)

### Community 63 - "clip-processor/src/rss_poller.py"
Cohesion: 0.27
Nodes (11): _cleanup_partial() chamado fora do loop de retry, clip-processor/src/dedup.py, clip-processor/src/dedup.py, Dedup pattern: Redis NX → fallback MySQL → False, download_video(video_id, output_path), clip-processor/src/downloader.py, is_seen(video_id, redis_client, db_conn), 02-03-PLAN: dedup.py, downloader.py, rss_poller.py (+3 more)

### Community 64 - "append_credits"
Cohesion: 0.22
Nodes (8): append_credits(), Adiciona linha de créditos ao final da descrição. Nunca sobrescreve conteúdo…, COPY-02: template vazio → retorna descrição sem modificação., COPY-02: handle vazio → retorna descrição sem modificação., Testes RED para append_credits (COPY-02)., COPY-02: template com {channel_handle} é substituído pelo handle real., TestAppendCredits, Phase 07 Plan 05: overlay_watermark e append_credits (COPY-01/02)

### Community 65 - "conftest.py"
Cohesion: 0.24
Nodes (10): mock_db_conn(), mock_redis(), fixture, Fixtures compartilhadas para todos os testes do clip-processor. Fornece:…, MagicMock simulando redis.Redis. - .set() retorna True por padrão (NX success —…, MagicMock simulando conexão pymysql com suporte a context manager em cursor().…, Feed RSS Atom do YouTube com 2 entradas válidas. VideoIds: 'abc123def456' e…, ID de vídeo YouTube válido (11 caracteres). (+2 more)

### Community 66 - "input-group.tsx"
Cohesion: 0.24
Nodes (9): InputGroup(), InputGroupAddon(), inputGroupAddonVariants, InputGroupButton(), inputGroupButtonVariants, InputGroupInput(), InputGroupText(), InputGroupTextarea() (+1 more)

### Community 67 - "Phase 8 Plan 08: Dashboard Widgets + Aprovar/Rejeitar Plan"
Cohesion: 0.16
Nodes (14): Phase 8 Deferred Items, Filament $isLazy=false widget pattern, generated_clips.status ENUM (approved/rejected), mysql/init/05-controle-manual-migration.sql, App\Filament\Widgets\PendingApprovalWidget, App\Filament\Widgets\QuotaTodayWidget, App\Filament\Widgets\RecentFailuresWidget, App\Filament\Widgets\RecentUploadsWidget (+6 more)

### Community 68 - "_process_pending_clips(conn)"
Cohesion: 0.40
Nodes (5): Checkpoint humano: verificação end-to-end Phase 4, _process_pending_clips(conn), generated_clips.status = pending_cut, 04-03 Summary: metadata_generator.py implementation, 04-04 Plan: Poller Integration

### Community 69 - "overlay_watermark"
Cohesion: 0.22
Nodes (8): _log(), overlay_watermark(), Aplica watermark PNG no canto superior direito do clip via FFmpeg. Usa…, Testes RED para overlay_watermark (COPY-01)., COPY-01: wm_path existente → ffmpeg com -filter_complex e overlay=W-w-20:20., COPY-01: wm_path ausente → retorna input_path sem chamar subprocess., TestOverlayWatermark, FFmpeg dual-input pattern: -filter_complex overlay (clip first, watermark second)

### Community 70 - "require-dev"
Cohesion: 0.20
Nodes (10): require-dev, fakerphp/faker, laravel/pail, laravel/pao, laravel/pint, mockery/mockery, nunomaduro/collision, pestphp/pest (+2 more)

### Community 71 - "02-04-PLAN.md: Daemon main.py Plan"
Cohesion: 0.20
Nodes (10): 02-04-PLAN.md: Daemon main.py Plan, 02-04-SUMMARY.md: Daemon main.py Summary, 02-CONTEXT.md: Phase 2 Context, 02-RESEARCH.md: Phase 2 Research, 02-VALIDATION.md: Phase 2 Validation Strategy, pytest test infra (Phase 2 Wave 0), ACQU-01: monitorar canais via RSS a cada 6h, ACQU-02: baixar vídeos novos em 720p via yt-dlp (+2 more)

### Community 72 - ".planning/research/ARCHITECTURE.md (v2.0 research, superseded)"
Cohesion: 0.29
Nodes (8): Dead code: painel/app/Filament/Pages/Dashboard.php orphan, env() outside config() pitfall in DashboardController, Section 10: Known divergences and technical debt, channel_blacklist table (research design), destination_channels table (research design), Phase 7: Schema Multi-Canal + Watermark + Copyright (research plan), Phase 8: Laravel/Filament Painel Base (research plan), .planning/research/ARCHITECTURE.md (v2.0 research, superseded)

### Community 73 - "youtube_oauth.py"
Cohesion: 0.28
Nodes (8): generate_token(), main(), Helper CLI para gerar token OAuth YouTube por canal-destino. Uso: python -m…, Gera token OAuth para o canal-destino e salva em…, docker-compose.yml branding volume for clip-processor, Path, Phase 07 Plan 07: YouTube OAuth CLI + Branding Volume, Phase 07 Plan 07 Summary: YouTube OAuth CLI + Branding Volume (paused)

### Community 74 - "pipeline_runner.py"
Cohesion: 0.16
Nodes (12): _log(), pipeline_runner.py — Uma execucao completa do pipeline. Usado pelo daemon e…, Roda só a publicação de clips aprovados, sem RSS/download/AI. Existe pra drenar…, Roda RSS/download/AI (poll_all_channels + _download_pending_videos), sem…, run_ingest_cycle(), run_publish_only(), Testes para pipeline_runner.py — ciclo completo do pipeline., Deve chamar poll → download em ordem, sem publish. (+4 more)

### Community 75 - "02-01-PLAN: pytest scaffold RED state (Wave 0)"
Cohesion: 0.33
Nodes (9): clip-processor/tests/conftest.py, 02-01-PLAN: pytest scaffold RED state (Wave 0), 02-01-SUMMARY: 17 testes RED criados, clip-processor/pytest.ini, TDD RED-GREEN-REFACTOR pattern (imports no topo causam ModuleNotFoundError), tests/test_db.py, tests/test_dedup.py, tests/test_downloader.py (+1 more)

### Community 76 - "Phase 8 Context (Painel Laravel/Filament)"
Cohesion: 0.36
Nodes (8): PANEL-01 requirement (CRUD canal-fonte sem SQL), PANEL-03 requirement (dashboard tempo real), PANEL-04 requirement (aprovar/rejeitar clip), PANEL-05 requirement (autenticação single-user), Phase 8 human checkpoint (7-step verification), Phase 8 Plan 04: Autenticação Summary, Phase 8 Context (Painel Laravel/Filament), Phase 8 Validation Strategy

### Community 77 - "main.py"
Cohesion: 0.14
Nodes (7): BlockingScheduler, _FallbackJob, log(), shutdown(), Phase 8 Plan 07: internal_api.py GREEN Plan, Phase 8 Plan 07: internal_api.py GREEN Summary, Sidecar HTTP interno em thread daemon (antes do ciclo do pipeline)

### Community 78 - "TestYouTubeUploaderChannelSlug"
Cohesion: 0.25
Nodes (5): Testes RED para suporte a channel_slug no YouTubeUploader (MCAN-01)., MCAN-01: channel_slug='futebol-em-cortes' → token_file='/app/youtube/token-…, Retrocompat: sem channel_slug, usa DEFAULT_TOKEN_FILE., Retrocompat: token_file explícito tem precedência sobre channel_slug., TestYouTubeUploaderChannelSlug

### Community 79 - "setup"
Cohesion: 0.25
Nodes (8): post-root-package-install, setup, composer install, npm install --ignore-scripts, npm run build, @php artisan key:generate, @php artisan migrate --force, @php -r \"file_exists('.env') || copy('.env.example', '.env');\

### Community 80 - "Phase 9-04 Plan: Telegram Bot Checkpoint"
Cohesion: 0.33
Nodes (9): PipelineEventTest.php, setWebhook registration to https://alessandromelo.com.br/telegramcanal, Phase 9-04 Plan: Telegram Bot Checkpoint, TelegramCommandsTest.php, TelegramWebhookTest.php, Artisan Schedule daily summary 18h BRT, Phase 9 Research: Bot Telegram no Laravel, Phase 9 Validation Strategy (+1 more)

### Community 81 - "Phase 7: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.25
Nodes (7): Bot Telegram no Laravel (v2), Groq Whisper (API) em vez de Whisper local, Multi-canal com token OAuth por canal, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 8: Painel Laravel/Filament, Phase 9: Bot Telegram no Laravel, recover_stuck_downloads só recupera 'downloading' → 'pending'

### Community 82 - "01-04-PLAN: OAuth YouTube e verificação do canal"
Cohesion: 0.29
Nodes (7): youtube/generate_token.py, OAuth app type 'installed' (Desktop App), não 'web', OAuth app publicado em Production, Pitfall: YouTube OAuth em modo Testing expira em 7 dias, 01-04-PLAN: OAuth YouTube e verificação do canal, 01-04-SUMMARY: OAuth e canal configurados, Canal YouTube "Futebol em Cortes"

### Community 83 - "config"
Cohesion: 0.29
Nodes (7): pestphp/pest-plugin, php-http/discovery, config, allow-plugins, optimize-autoloader, preferred-install, sort-packages

### Community 84 - "require"
Cohesion: 0.29
Nodes (7): require, inertiajs/inertia-laravel, irazasyed/telegram-bot-sdk, laravel/framework, laravel/tinker, php, tightenco/ziggy

### Community 85 - "Illuminate\Http\RedirectResponse"
Cohesion: 0.18
Nodes (4): Illuminate\Http\RedirectResponse, DashboardController, GeneratedClip, StatusCommand

### Community 86 - "clip-processor/src/metadata_generator.py"
Cohesion: 0.33
Nodes (6): clip-processor/src/metadata_generator.py, clip-processor/tests/test_metadata_generator.py, 04-01-PLAN.md: Phase 4 Wave 0 skeletons + RED tests, 04-01-SUMMARY.md: Phase 4 Wave 0 Summary, 04-03-PLAN.md: metadata_generator.py GREEN plan, update_clip_metadata()

### Community 87 - "destination_channels table"
Cohesion: 0.33
Nodes (6): destination_channels table, Migration idempotente via INFORMATION_SCHEMA + prepared statement, 06-multi-canal-migration.sql, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 7 — Validation Strategy, pytest test framework (clip-processor)

### Community 88 - "generated_clips.status state machine"
Cohesion: 0.40
Nodes (5): generated_clips.status state machine, list-pending-clips.sh, mark-published.sh, manual-workflow/README.md — manual clip publishing guide, Pitfall: Filament Auto-Generated Resources Break on ENUM Columns

### Community 89 - "transcribe_video"
Cohesion: 0.22
Nodes (9): clip-processor/src/downloader.py, Guard de espaço em disco antes do download (<2GB), Retry de download: 3x com 60s entre tentativas, Extração de áudio ffmpeg para arquivos >24MB, 03-CONTEXT.md: Phase 3 Context, _prepare_audio(), AI-01: transcrição via Groq Whisper, AI-02: seleção de momentos via Claude Haiku (+1 more)

### Community 90 - "Phase 8 Research (Painel Laravel/Filament)"
Cohesion: 0.67
Nodes (3): docker exec / Docker socket bridge anti-pattern, Pattern 3: ponte HTTP interna clip-processor↔painel, Phase 8 Research (Painel Laravel/Filament)

### Community 91 - "Dashboard"
Cohesion: 0.50
Nodes (3): Filament\Pages\Dashboard, Illuminate\Contracts\Support\Htmlable, Dashboard

### Community 92 - "ClipProcessorClient.php"
Cohesion: 0.25
Nodes (7): POST /internal/resolve-channel (sidecar endpoint), Filament Resource GET/HEAD-only routing pattern, App\Filament\Resources\SourceChannelResource, CreateSourceChannel Page, routes/web.php POST/PATCH source-channels REST routes, Phase 8 Plan 05: SourceChannelResource Plan, Phase 8 Plan 05: SourceChannelResource Summary

### Community 93 - "psr-4"
Cohesion: 0.40
Nodes (5): autoload, psr-4, App\\, Database\\Factories\\, Database\\Seeders\\

### Community 94 - "v2.0 — Painel + Multi-Canal"
Cohesion: 0.40
Nodes (4): v2.0 — Painel + Multi-Canal, BOT-01: Bot Telegram migrado para Laravel, MCAN-01: Múltiplos canais destino com OAuth próprio, PANEL-01: Adicionar/remover canais-fonte via formulário web

### Community 95 - "Pitfall: Content ID Claim Despite Watermark"
Cohesion: 0.40
Nodes (5): Pitfall: Content ID Claim Despite Watermark, strategy/MONETIZATION.md — monetization strategy, Betting affiliate programs (Betano, Bet365, Pixbet, Blaze), DMCA/copyright takedown risk, YouTube Partner Program requirements (Opção A: Shorts)

### Community 96 - "list-pending-clips.sh"
Cohesion: 0.83
Nodes (3): mysql_exec(), mysql_exec_pretty(), list-pending-clips.sh script

### Community 99 - "youtube/assets/BRANDING.md — Futebol em Cortes visual identity"
Cohesion: 0.50
Nodes (3): youtube/assets/BRANDING.md — Futebol em Cortes visual identity, Banner generation prompt (2560x1440px), Logo generation prompt (scissors + play button, red/black/white)

### Community 102 - "test_transcription_job.py"
Cohesion: 0.13
Nodes (10): create_transcription_job(), Insere um novo job em transcription_jobs com status='pending' e retorna o id…, Monta um UPDATE dinâmico só com os campos passados (não sobrescreve os demais)., update_job(), client(), fixture, test_transcription_job.py — Testes unitários para transcription_job.py…, TestCreateTranscriptionJob (+2 more)

### Community 103 - "_process_ai_pipeline"
Cohesion: 0.16
Nodes (10): _process_ai_pipeline(), Executa transcrição + seleção para um vídeo com status downloaded. Args: conn:…, AI-04: Testes de integração do pipeline de IA no rss_poller., Configura mock_db_conn para retornar canais e vídeos downloaded em fetchall().…, AI-04: poll_all_channels chama _process_ai_pipeline para cada vídeo com status…, AI-04: Falha no pipeline de IA de um vídeo não aborta os demais., AI-04: _process_ai_pipeline chama transcribe_video e select_moments em…, AI-04: Falha na transcrição (None) marca vídeo como failed e não chama… (+2 more)

### Community 109 - "get_db_connection"
Cohesion: 0.19
Nodes (12): get_db_connection(), Abre conexão com o MySQL usando variáveis de ambiente. Variáveis de ambiente…, _download_audio(), process_transcription_job(), transcription_job.py — Worker de "Transcrição Local" (QUICK-1). Feature isolada…, Executa o ciclo completo de uma transcrição local (roda em thread de…, Cria o job no banco e dispara a thread de background que processa a…, Baixa o áudio da URL via yt-dlp em formato wav para TRANSCRIPTS_DIR. Raises:… (+4 more)

### Community 113 - "ttl_worker.py"
Cohesion: 0.19
Nodes (9): Worker de TTL para clipes pending (CTRL-05). - Expira: clipes com…, Executa 1 iteração do TTL: expira clipes >TTL_HOURS, avisa clipes WARN_HOURS-…, run_ttl_once(), Testes para ttl_worker.py — expiração automática de clips pending. Estado RED…, run_ttl_once: clips pending > TTL_HOURS são marcados rejected via UPDATE., run_ttl_once: clips entre WARN_HOURS e TTL_HOURS disparam notify() para Laravel., Redis SET NX False (já avisou): NÃO dispara notify() extra., TestExpire (+1 more)

### Community 114 - "rejeitar"
Cohesion: 0.21
Nodes (11): internal_api.reject_clip(clip_id) — calls src.rejeitar.rejeitar directly, rejeitar.py — Rejeição manual de clip via comando /rejeitar do Telegram…, Marca o clip como rejected, remove o MP4 do disco, preserva raw video.…, rejeitar(), Testes para rejeitar.py — comando /rejeitar do Telegram. Estado RED até Plan…, rejeitar(123): executa UPDATE generated_clips SET status='rejected' WHERE…, rejeitar apaga clip_path mas NÃO toca source_videos.local_path (raw)., rejeitar(999) com fetchone=None retorna 1 e não executa UPDATE. (+3 more)

### Community 122 - "Quick Task 1: Transcrição Local Summary"
Cohesion: 0.15
Nodes (12): Accomplishments, Auto-fixed Issues, Decisions Made, Deviations from Plan, Files Created/Modified, Issues Encountered, Next Phase Readiness, Performance (+4 more)

### Community 153 - "TelegramWebhookController.php"
Cohesion: 0.22
Nodes (4): Illuminate\Http\Response, JsonResponse, TelegramWebhookController, tg:dedup:{update_id} Redis SET NX EX 300 dedup pattern

### Community 154 - "test_rss_poller.py"
Cohesion: 0.36
Nodes (4): _detect_format(), Decide 'curto' ou 'longo' com base na duração real do vídeo fonte. Vídeos com…, Testes ACQU-01: detecção de vídeos novos via RSS. Testes AI-04: integração do…, TestDetectFormat

### Community 155 - "TestPollAllChannels"
Cohesion: 0.29
Nodes (4): Dado feed RSS com 2 entradas nunca vistas, poll_all_channels() insere 2…, Dado vídeo já no Redis (is_seen retorna True), poll não chama insert_video para…, Feed sem entradas não levanta exceção., TestPollAllChannels

### Community 157 - "package.json"
Cohesion: 0.29
Nodes (6): private, $schema, scripts, build, dev, type

### Community 158 - "TestBlacklistGuard"
Cohesion: 0.33
Nodes (4): Testes RED para blacklist guard no rss_poller (COPY-03)., COPY-03: canal com blacklisted=True não chama insert_video. O guard deve checar…, COPY-03: canal com blacklisted=False (ou None) chama insert_video normalmente., TestBlacklistGuard

### Community 159 - "v1.0 — Pipeline Base"
Cohesion: 0.53
Nodes (6): v1.0 — Pipeline Base, MANUAL_APPROVAL_REQUIRED toggle, Phase 3: IA — Transcrição e Seleção, Phase 4: Processamento de Vídeo, Phase 5: Publicação e Automação Total, Phase 6: Controle Manual N8N + Telegram

### Community 162 - "Phase 8 Plan 09: Checkpoint Final End-to-End Summary"
Cohesion: 0.40
Nodes (5): nginx bind mount painel fix (404 puro), routes/web.php raiz '/' redirect fix, Phase 8 Plan 09: Checkpoint Final End-to-End Plan, Phase 8 Plan 09: Checkpoint Final End-to-End Summary, ./canaldecortes/youtube:/var/www/html/youtube:ro bind mount (php service)

### Community 163 - "test_uploader.py"
Cohesion: 0.50
Nodes (3): make_uploader(), Testes para YouTubeUploader — upload de clips e thumbnails. Todas as chamadas…, Cria YouTubeUploader com credenciais e YouTube mockados.

### Community 164 - "post-create-project-cmd"
Cohesion: 0.50
Nodes (4): post-create-project-cmd, @php artisan key:generate --ansi, @php artisan migrate --graceful --ansi, @php -r \"file_exists('database/database.sqlite') || touch('database/database.sqlite');\

### Community 165 - "Phase 9 Plan 03: Migração Python + Artisan Schedule Plan"
Cohesion: 0.67
Nodes (3): docker/php/crontab (schedule:run entry), Phase 9 Plan 03: Migração Python + Artisan Schedule Plan, Phase 9 Plan 03: Migração Python + Artisan Schedule Summary

### Community 166 - "keywords"
Cohesion: 0.67
Nodes (3): keywords, framework, laravel

## Ambiguous Edges - Review These
- `clip-processor/src/ttl_worker.py` → `clip-processor/src/telegram_notifier.py`  [AMBIGUOUS]
  .planning/phases/06-controle-manual-n8n-telegram/06-05-SUMMARY.md · relation: conceptually_related_to

## Knowledge Gaps
- **281 isolated node(s):** `force-download.sh script`, `$schema`, `style`, `rsc`, `tsx` (+276 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `clip-processor/src/ttl_worker.py` and `clip-processor/src/telegram_notifier.py`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `run_pipeline_once()` connect `run_pipeline_once` to `publish_pending_clips`, `rss_poller.py`, `notify`, `pipeline_runner.py`, `_download_pending_videos`, `get_db_connection`, `main.py`, `05-01 Plan: Publishing schema, skeletons and RED tests`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `n8n/workflows/canaldecortes-pipeline.json` connect `05-01 Plan: Publishing schema, skeletons and RED tests` to `run_pipeline_once`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `05-06 Plan: n8n workflow and production checkpoint` connect `05-01 Plan: Publishing schema, skeletons and RED tests` to `Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `QuotaManager` (e.g. with `TestCanUpload` and `TestQuotaManagerMultiCanal`) actually correct?**
  _`QuotaManager` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `YouTubeUploader` (e.g. with `TestUploadClip` and `TestYouTubeUploaderChannelSlug`) actually correct?**
  _`YouTubeUploader` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `force-download.sh script`, `$schema`, `style` to the rest of the system?**
  _281 weakly-connected nodes found - possible documentation gaps or missing edges._