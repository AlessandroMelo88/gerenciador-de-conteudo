# Graph Report - canaldecortes  (2026-09-15)

## Corpus Check
- 399 files · ~766,512 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2837 nodes · 4818 edges · 217 communities (193 shown, 24 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 87 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7c4d40d5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ClipProcessorClient
- make_conn_with_clips
- db.py
- clip-queue-tabs.tsx
- QuotaManager
- Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)
- rss_poller.py
- test_watchdog.py
- User.php
- Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)
- internal_api.py
- selector.py
- SourceVideos.tsx
- processar.py
- devDependencies
- cn
- publisher.py
- 05-01 Plan: Publishing schema, skeletons and RED tests
- Telegram\Bot\Commands\Command
- TestUploadClip
- uploader.py
- generate_metadata
- cut_clip
- test_internal_api.py
- is_seen
- transcribe_video
- DestinationChannel
- components.json
- docker-compose.yml (raiz wordpress/)
- download_video
- Illuminate\Http\RedirectResponse
- Illuminate\Database\Eloquent\Factories\Factory
- Illuminate\Http\Request
- compilerOptions
- video_processor.py
- Phase 1: Infraestrutura Base
- Phase 7 Context: Schema Multi-Canal + Python Pipeline
- run_pipeline_once
- TelegramHttpClientHandler.php
- Plano — Prompts de IA editáveis pelo painel
- active-window-table.tsx
- TestPublisherMultiCanal
- _download_pending_videos
- chart.tsx
- Assistant.tsx
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
- niche-combobox.tsx
- clip-processor/src/rss_poller.py
- overlay_watermark
- conftest.py
- Plano mestre — estado, decisões e próximos passos
- publisher.py
- get_db_connection
- test_video_processor.py
- require-dev
- 02-04-PLAN.md: Daemon main.py Plan
- .planning/research/ARCHITECTURE.md (v2.0 research, superseded)
- Sistema — IA de seleção de cortes
- run_ingest_cycle
- 02-01-PLAN: pytest scaffold RED state (Wave 0)
- Phase 8 Context (Painel Laravel/Filament)
- main.py
- TestYouTubeUploaderChannelSlug
- setup
- Phase 9-04 Plan: Telegram Bot Checkpoint
- Phase 7: Schema Multi-Canal + Python Pipeline
- 01-RESEARCH.md
- config
- require
- local_download_worker.py
- clip-processor/src/metadata_generator.py
- destination_channels table
- Illuminate\Database\Eloquent\Model
- clip-processor/src/downloader.py
- Illuminate\Console\Command
- _discard_failed_download
- field.tsx
- psr-4
- v2.0 — Painel + Multi-Canal
- Pitfall: Content ID Claim Despite Watermark
- list-pending-clips.sh
- ExampleTest
- youtube/assets/BRANDING.md — Futebol em Cortes visual identity
- mark-failed.sh
- mark-published.sh
- transcription_job.py
- _process_ai_pipeline
- validate-infra.sh
- Sistema de Alertas, Monitoramento e Watchdog
- clip-processor/src/main.py
- Fases
- @dnd-kit/utilities
- ttl_worker.py
- rejeitar
- force-download.sh
- CreatePainelUser artisan command
- radix-ui
- react-dom
- Sistema — `painel/`
- Runbook de operação
- tailwind-merge
- Quick Task 1: Transcrição Local Summary
- Publicação no YouTube
- test_local_download_worker.py
- 03-RESEARCH.md: Phase 3 Research
- MCAN-04: 3 vídeos/dia por canal 19h-22h BRT
- Claude Haiku para seleção e metadados
- Radar de Performance: pacote de entrega
- Banco de dados — `clips_automation`
- Mapa dos módulos
- Descoberta e download
- Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan
- TestProcessClipWithWatermark
- Backlog de bugs
- select_moments
- v1.0 — Pipeline Base
- Docs — Sistema Canal de Cortes
- 3. Como Saber se o Cron Funcionou
- clip-processor/src/db.py
- notify
- Passo a passo
- shadcn
- Guia de Deploy Rápido (Produção)
- zod
- sonner
- Pipeline e scheduler
- _niche_windows
- Sidecar HTTP e controles de fila
- Corte e pós-produção de vídeo
- 04-04 Summary: Poller Integration Summary
- HandleInertiaRequests.php
- TelegramWebhookController.php
- pipeline_runner.py
- test_uploader_expired.py
- Estados e transições do pipeline
- Pipeline principal — Groq Whisper
- test_rss_poller.py
- resume_claude_session.sh
- TestPollAllChannels
- package.json
- TestBlacklistGuard
- Estratégia de Conteúdo, Benchmark e YouTube Analytics
- 📋 Regras de Negócio e Gatilhos Operacionais — Canal de Cortes
- Plano PostgreSQL — fase A (local) e fase B (produção)
- generated_clips.status state machine
- n8n/workflows/canaldecortes-pipeline.json
- test_pipeline_runner.py
- _fetch_destination_channels
- Diretório de Documentação (`Docs/`)
- test_uploader.py
- keywords
- resume_claude_daemon.sh
- post-create-project-cmd
- deploy.sh script
- @dnd-kit/core
- @dnd-kit/sortable
- ziggy-js
- check_cron_status.sh
- generate_sample_thumbnails.py
- @tanstack/react-table
- tw-animate-css

## God Nodes (most connected - your core abstractions)
1. `cn()` - 197 edges
2. `QuotaManager` - 44 edges
3. `YouTubeUploader` - 37 edges
4. `publish_pending_clips()` - 36 edges
5. `get_db_connection()` - 34 edges
6. `GeneratedClip` - 32 edges
7. `ClipProcessorClient` - 30 edges
8. `DestinationChannel` - 28 edges
9. `SourceVideo` - 27 edges
10. `poll_all_channels()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `generate_metadata()` --implements--> `Fallback determinístico de metadata (não bloqueia pipeline)`  [EXTRACTED]
  clip-processor/src/metadata_generator.py → .planning/phases/04-processamento-de-video/04-03-SUMMARY.md
- `publish_pending_clips()` --rationale_for--> `Publisher legacy fallback when destination_channels empty`  [EXTRACTED]
  clip-processor/src/publisher.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-06-SUMMARY.md
- `overlay_watermark()` --rationale_for--> `Graceful degradation pattern: return input unchanged when optional dependency missing`  [EXTRACTED]
  clip-processor/src/video_processor.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-05-SUMMARY.md
- `docker-compose.yml branding volume for clip-processor` --shares_data_with--> `overlay_watermark()`  [EXTRACTED]
  .planning/phases/07-schema-multi-canal-python-pipeline/07-07-PLAN.md → clip-processor/src/video_processor.py
- `.planning/research/ARCHITECTURE.md (v2.0 research, superseded)` --semantically_similar_to--> `ARCHITECTURE.md (as-built, commit dca6e44)`  [INFERRED] [semantically similar]
  .planning/research/ARCHITECTURE.md → ARCHITECTURE.md

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

## Communities (217 total, 24 thin omitted)

### Community 0 - "ClipProcessorClient"
Cohesion: 0.12
Nodes (4): TranscriptionController, TranscriptionJob, ClipProcessorClient, Symfony\Component\HttpFoundation\StreamedResponse

### Community 1 - "make_conn_with_clips"
Cohesion: 0.10
Nodes (24): dt_sp(), make_conn_with_clips(), make_mock_quota(), make_mock_uploader(), Testes para publisher.py — publicação de clips pendentes., Upload bem-sucedido: pending → publishing → published., Upload com erro: status vai para 'failed', quota não é incrementada., Quando quota/janela bloqueada, clip deve continuar como pending. (+16 more)

### Community 2 - "db.py"
Cohesion: 0.06
Nodes (31): get_db_driver(), insert_video(), _log(), PostgresConnectionWrapper, PostgresCursorWrapper, db.py — Módulo de acesso ao banco de dados (MySQL e PostgreSQL) para o daemon…, Wrapper para conexão do psycopg2 expondo cursor com dicionário e atributo…, Atualiza o status de um vídeo na tabela source_videos. `local_path=None`… (+23 more)

### Community 3 - "clip-queue-tabs.tsx"
Cohesion: 0.10
Nodes (18): ClipPreviewModal(), ClipPreviewModalProps, ClipQueueTabs(), FailuresTable(), PendingTable(), post(), useSelection(), OverviewCards() (+10 more)

### Community 4 - "QuotaManager"
Cohesion: 0.06
Nodes (39): datetime, QuotaManager, Controla uploads diarios do YouTube por data local de Sao_Paulo.…, Janela + cota total, ignorando reserva por formato. Usado para decidir se o…, Retorna True se horario e quota (total + formato/reserva) permitirem upload., Incrementa contador diario (total e, se 'longo', o de formato) e garante TTL., dt_sp(), make_redis() (+31 more)

### Community 5 - "Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)"
Cohesion: 0.06
Nodes (58): mysql/init/05-controle-manual-migration.sql, mysql/init/06-multi-canal-migration.sql, mysql/manual-workflow/approve-backlog.sql — helper opcional para backlog de pending, APScheduler dentro do clip-processor (vs n8n cron) para TTL worker, clip-processor/src/pipeline_runner.py, clip-processor/src/processar.py, clip-processor/src/publisher.py, clip-processor/src/rejeitar.py (+50 more)

### Community 6 - "rss_poller.py"
Cohesion: 0.18
Nodes (13): _extract_video_id(), _is_blocked_title(), _log(), poll_all_channels(), _process_pending_clips(), rss_poller.py — Monitor de feeds RSS de canais YouTube e inserção de vídeos…, Processa clips com status pending_cut sem abortar o poll por falha isolada., Monitora feeds RSS de todos os canais ativos e insere vídeos novos. Args:… (+5 more)

### Community 7 - "test_watchdog.py"
Cohesion: 0.07
Nodes (32): check_approval_queue_activity(), check_disk_space(), check_download_window_health(), check_ghost_clips(), check_youtube_tokens(), _horas_atras(), _log(), _max_window_slots() (+24 more)

### Community 8 - "User.php"
Cohesion: 0.09
Nodes (12): Filament\Models\Contracts\FilamentUser interface, Illuminate\Database\Console\Seeds\WithoutModelEvents, Illuminate\Database\Seeder, Illuminate\Foundation\Auth\User, Illuminate\Foundation\Testing\TestCase, Illuminate\Notifications\Notifiable, ResetPainelPassword artisan command, User (+4 more)

### Community 9 - "Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)"
Cohesion: 0.06
Nodes (41): canaldecortes/docker/nginx/canaldecortes.conf vhost, generate_token(), main(), Helper CLI para gerar token OAuth YouTube por canal-destino. Uso: python -m…, Gera token OAuth para o canal-destino e salva em…, docker-compose.yml branding volume for clip-processor, clip-processor não tem bind mount de src/ — exige rebuild+restart para refletir código, mysql/init/07-panel-oauth-flag-migration.sql (oauth_expired_flag idempotent migration) (+33 more)

### Community 10 - "internal_api.py"
Cohesion: 0.18
Nodes (22): internal_api.resolve_channel(url) — yt-dlp channel resolution, _check_auth(), purge_old_videos(), internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.…, Limpa vídeos fonte com published_at anterior a `before_date` (formato 'YYYY-MM-…, Roda yt-dlp em modo metadata-only e extrai id/name/handle. Padrão yt-dlp:…, Dispara um ciclo imediato de publicação de clipes aprovados., Chama src.rejeitar.rejeitar(clip_id) diretamente. Preserva exit codes 0/1/2. (+14 more)

### Community 11 - "selector.py"
Cohesion: 0.05
Nodes (43): _enforce_longform_duration(), _filter_shortform_duration(), insert_selected_moments(), _log(), _lookup_destination_channel_id(), _normalize_scores(), _parse_moments(), selector.py — Seleção de momentos via IA com fallback automático. Prioridade em… (+35 more)

### Community 12 - "SourceVideos.tsx"
Cohesion: 0.09
Nodes (32): ChannelTemplateModal(), COLOR_PRESETS, Props, TemplateConfig, ConfirmButton(), Niche, Dialog(), DialogContent() (+24 more)

### Community 13 - "processar.py"
Cohesion: 0.10
Nodes (21): fetch_metadata(), main(), _normalize_upload_date(), parse_video_id(), processar.py — Ingestão manual de vídeo YouTube via comando /processar do…, Entrypoint CLI. Exit codes: - 0: OK (inserido ou já existia) - 2: URL inválida…, Extrai videoId de 11 caracteres de uma URL YouTube. None se URL inválida.…, Converte 'YYYYMMDD' (formato yt-dlp) para 'YYYY-MM-DD HH:MM:SS' (TIMESTAMP… (+13 more)

### Community 14 - "devDependencies"
Cohesion: 0.09
Nodes (23): concurrently, laravel-vite-plugin, devDependencies, concurrently, laravel-vite-plugin, tailwindcss, @tailwindcss/typography, @tailwindcss/vite (+15 more)

### Community 15 - "cn"
Cohesion: 0.06
Nodes (51): Avatar(), AvatarBadge(), AvatarFallback(), AvatarGroup(), AvatarGroupCount(), AvatarImage(), Breadcrumb(), BreadcrumbEllipsis() (+43 more)

### Community 16 - "publisher.py"
Cohesion: 0.08
Nodes (30): Blacklist guard (source_channels.blacklisted), COPY-01: watermark queimado via FFmpeg, COPY-02: descrição inclui créditos do canal original, COPY-03: canais blacklistados bloqueados no RSS poller, credit_template / channel_handle credits, generated_clips.destination_channel_id FK, MCAN-01: múltiplos canais YouTube com OAuth próprio, MCAN-02: campo niche determina canal-destino (+22 more)

### Community 17 - "05-01 Plan: Publishing schema, skeletons and RED tests"
Cohesion: 0.12
Nodes (22): quota_manager.py — Limite diario e janela de horario para uploads YouTube.…, YouTubeUploader.upload_clip(clip), MAX_UPLOADS_PER_DAY clamped to <= 6, default 2, YOUTUBE_TOKEN_FILE (default /app/token.json), mysql/init/04-publishing-migration.sql, Pattern: clock injection para testes deterministas, 05-01 Plan: Publishing schema, skeletons and RED tests, 05-01 Summary: publishing migration + TDD suite (+14 more)

### Community 18 - "Telegram\Bot\Commands\Command"
Cohesion: 0.09
Nodes (17): POST /internal/resolve-channel (sidecar endpoint), Filament Resource GET/HEAD-only routing pattern, generated_clips.status ENUM (approved/rejected), App\Filament\Resources\SourceChannelResource, CreateSourceChannel Page, App\Filament\Widgets\PendingApprovalWidget, AjudaCommand, AprovarCommand (+9 more)

### Community 19 - "TestUploadClip"
Cohesion: 0.11
Nodes (12): make_youtube_mock(), token_file inexistente deve levantar FileNotFoundError., Se thumbnail_path existir, thumbnails().set() deve ser chamado., Cria um mock do serviço YouTube que simula upload bem-sucedido., Falha no upload da thumbnail customizada deve logar aviso e manter o vídeo…, Tags em formato string separado por vírgula devem virar lista., YOUTUBE_PRIVACY_STATUS do env deve ser usado no upload., Upload bem-sucedido deve retornar o youtube_video_id. (+4 more)

### Community 20 - "uploader.py"
Cohesion: 0.14
Nodes (12): Credentials, MediaFileUpload, uploader.py — Upload de clips para YouTube Data API v3. Exporta: -…, Default privacyStatus=private, configuravel por YOUTUBE_PRIVACY_STATUS, destination_channels.oauth_expired_flag column, google.auth.exceptions.RefreshError, Fallback determinístico de metadata (não bloqueia pipeline), App\Filament\Resources\DestinationChannelResource (+4 more)

### Community 21 - "generate_metadata"
Cohesion: 0.11
Nodes (23): Anthropic structured outputs via output_config json_schema, Checkpoint humano: verificação end-to-end Phase 4, _build_prompt(), generate_metadata(), _generate_via_anthropic(), _generate_via_groq(), _log(), _normalize_metadata() (+15 more)

### Community 22 - "cut_clip"
Cohesion: 0.17
Nodes (8): _apply_youtube_thumbnail_graphics(), cut_clip(), extract_thumbnail(), _log(), Extrai um frame do clip como thumbnail JPG e aplica tipografia de alto CTR…, Aplica tipografia profissional e efeito de nuvem de sombra de alto CTR estilo…, Corta um trecho do vídeo fonte. fmt='curto' (padrão): converte pra vertical…, TestVideoProcessor

### Community 23 - "test_internal_api.py"
Cohesion: 0.08
Nodes (13): client(), fixture, RED tests for internal_api sidecar (implementação GREEN no Plan 08-07)., POST /internal/process-url com format='longo' repassa fmt='longo' pro…, POST /internal/process-url sem campo 'url' retorna 400., purge_old_videos apaga linhas sem clips e libera arquivo de linhas com clips…, POST /internal/process-url sem token retorna 401., POST /internal/process-url chama processar_main(url) e retorna {'exit_code': N}. (+5 more)

### Community 24 - "is_seen"
Cohesion: 0.13
Nodes (15): is_seen(), _log(), mark_failed_redis(), dedup.py — Deduplicação de vídeos via Redis com fallback para MySQL. Exporta: -…, Loga mensagem com timestamp para stdout., Verifica se o vídeo já foi processado anteriormente. Consulta o Redis primeiro.…, Remove a chave do vídeo do Redis quando o download falha. Isso permite que o…, Testes ACQU-03: deduplicação via Redis com fallback para MySQL. Módulo alvo:… (+7 more)

### Community 25 - "transcribe_video"
Cohesion: 0.13
Nodes (15): _log(), _prepare_audio(), transcriber.py — Transcrição de vídeos via Groq Whisper API. Exporta: -…, Salva JSON de transcrição em disco e atualiza transcript_path no banco. Args:…, Extrai áudio MP3 de um arquivo de vídeo via ffmpeg. Args: video_path: caminho…, Transcreve um vídeo via Groq Whisper API. Args: video_id: youtube_video_id do…, save_transcript(), transcribe_video() (+7 more)

### Community 26 - "DestinationChannel"
Cohesion: 0.13
Nodes (5): DestinationChannelController, NicheController, DestinationChannel, Niche, BaselineSeeder

### Community 27 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 28 - "docker-compose.yml (raiz wordpress/)"
Cohesion: 0.18
Nodes (13): ANTHROPIC_API_KEY intencionalmente vazia até Phase 3, clip-processor/Dockerfile, CLIP_PROCESSOR_INTERNAL_TOKEN env var, clip-processor service (build local), docker-compose.yml (raiz wordpress/), .env (secrets reais), n8n service (docker.n8n.io/n8nio/n8n:2.27.0), Pitfall: faster-whisper baixando modelo em cada restart (+5 more)

### Community 29 - "download_video"
Cohesion: 0.08
Nodes (26): _cleanup_partial(), cleanup_stale_downloads(), download_video(), _log(), downloader.py — Download de vídeos YouTube via yt-dlp com disk guard e retry.…, Baixa um vídeo do YouTube em formato 720p mp4. Returns: True se download bem-…, Loga mensagem com timestamp para stdout., Deleta artefatos de trabalho do yt-dlp gerados por download incompleto. O glob… (+18 more)

### Community 30 - "Illuminate\Http\RedirectResponse"
Cohesion: 0.12
Nodes (5): Illuminate\Http\RedirectResponse, DashboardController, SourceVideoController, GeneratedClip, SourceVideo

### Community 31 - "Illuminate\Database\Eloquent\Factories\Factory"
Cohesion: 0.15
Nodes (7): Illuminate\Database\Eloquent\Factories\Factory, DestinationChannelFactory, GeneratedClipFactory, SourceChannelFactory, SourceVideoFactory, static, UserFactory

### Community 32 - "Illuminate\Http\Request"
Cohesion: 0.11
Nodes (12): Illuminate\Http\JsonResponse, Illuminate\Http\Request, Inertia\Response, AssistantController, AuthController, Controller, DocumentationController, ProcessVideoController (+4 more)

### Community 33 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 34 - "video_processor.py"
Cohesion: 0.12
Nodes (19): _build_clip_context(), _fetch_clip(), process_clip(), video_processor.py — Corte, legendas, thumbnail e processamento de clips.…, Busca a imagem de background 1920x1080 do canal ou nicho., Processa um registro de generated_clips com status pending_cut. Pipeline: cut →…, Gera configuração padrão inteligente de template 9:16 baseada no nicho do canal., resolve_background_path() (+11 more)

### Community 35 - "Phase 1: Infraestrutura Base"
Cohesion: 0.26
Nodes (10): ACQU-01: Monitoramento RSS de canais, ACQU-02: Download automático 720p via yt-dlp, ACQU-03: Deduplicação Redis + MySQL UNIQUE, INFRA-01: Sistema roda em Docker, INFRA-02: Banco clips_automation com 3 tabelas, INFRA-03: Canal YouTube verificado, INFRA-04: Variáveis de ambiente e secrets, ORC-02: Status de cada job registrado no MySQL (+2 more)

### Community 36 - "Phase 7 Context: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.15
Nodes (17): rss_poller blacklist guard + target_niche SELECT extension, COPY-01 requirement: watermark burned into every clip, COPY-02 requirement: original channel credits in description, COPY-03 requirement: blacklisted channels never downloaded, Dual-layer blacklist guard pattern (SQL filter + Python loop guard), Graceful degradation pattern: return input unchanged when optional dependency missing, MCAN-01 requirement: OAuth token per destination channel, MCAN-02 requirement: destination_channel_id routing by niche (+9 more)

### Community 37 - "run_pipeline_once"
Cohesion: 0.13
Nodes (13): Executa RSS/download/AI/video e depois publicacao. Falhas isoladas sao logadas,…, run_pipeline_once(), Conexão injetada não deve ser fechada pelo runner (responsabilidade do caller)., Erro em publish_pending_clips não deve propagar — scheduler continua., Erro em poll_all_channels não deve impedir tentativa de publicação., Sem injeção, deve criar e fechar a própria conexão., Erro em _download_pending_videos não deve propagar., Deve chamar poll → download → publish em ordem. (+5 more)

### Community 38 - "TelegramHttpClientHandler.php"
Cohesion: 0.14
Nodes (9): GuzzleHttp\Promise\PromiseInterface, Illuminate\Support\ServiceProvider, AppServiceProvider, static, TelegramHttpClientHandler, Phase 9 Plan 02: TelegramWebhookController + Commands Summary, Psr\Http\Message\ResponseInterface, Telegram\Bot\HttpClients\HttpClientInterface (+1 more)

### Community 39 - "Plano — Prompts de IA editáveis pelo painel"
Cohesion: 0.05
Nodes (36): 10. Riscos e mitigação, 11. Fora de escopo neste plano, 1. Situação atual (verificada em 13/08/2026), 2. Versões confirmadas (regra `docs-first`), 3. Por onde o prompt deve trafegar — decisão, 4.1 `ai_prompts` — o *slot*, 4.2 `ai_prompt_versions` — histórico imutável, 4.3 `generated_clips.ai_prompt_version_id` (+28 more)

### Community 40 - "active-window-table.tsx"
Cohesion: 0.08
Nodes (31): ActiveWindowTable(), postAction(), SortableRow(), STATUS_LABEL, useSelection(), VideoActions(), VideoCells(), VideoTable() (+23 more)

### Community 41 - "TestPublisherMultiCanal"
Cohesion: 0.15
Nodes (10): _fetch_pending_clips_for_channel(), Retorna clips prontos para publicar filtrados por canal-destino. Faz fairness…, Reordena clips (já em ordem created_at ASC) intercalando por source_channel_id,…, _round_robin_by_source_channel(), Testes RED para roteamento multi-canal no publisher (MCAN-02, MCAN-04)., MCAN-02: _fetch_pending_clips_for_channel filtra por destination_channel_id.…, MCAN-02: clips de canal 2 não aparecem na busca do canal 1., MCAN-04: quota atingida no canal 1 não bloqueia publicação no canal 2. Cada… (+2 more)

### Community 42 - "_download_pending_videos"
Cohesion: 0.18
Nodes (10): _download_pending_videos(), Baixa vídeos com status 'pending', um por vez, atualizando status no DB., Cursor fake cujo fetchone e fetchall caem num default depois da lista informada., Download bem-sucedido deve atualizar status para downloaded com local_path., Download falho deve marcar failed já limpando local_path (libera a vaga)., Sem vídeos pending, não deve chamar download_video., Janela já cheia nos dois nichos não deve chamar download_video., Ordem fixa: repõe futebol primeiro, depois política. (+2 more)

### Community 43 - "chart.tsx"
Cohesion: 0.23
Nodes (10): ChartConfig, ChartContext, ChartContextProps, ChartLegendContent(), ChartTooltipContent(), getPayloadConfigFromPayload(), INITIAL_DIMENSION, THEMES (+2 more)

### Community 44 - "Assistant.tsx"
Cohesion: 0.10
Nodes (27): Badge(), badgeVariants, Card(), CardAction(), CardContent(), CardDescription(), CardFooter(), CardHeader() (+19 more)

### Community 45 - "ARCHITECTURE.md (as-built, commit dca6e44)"
Cohesion: 0.15
Nodes (15): ARCHITECTURE.md (as-built, commit dca6e44), AI fallback chain (Claude → Groq → deterministic), niches table (only Laravel-migration-managed pipeline table), Quota, window and round-robin logic, source_videos.status state machine, CLAUDE.md — Canal de Cortes work instructions, Rules for destructive operations, metadata_generator.py Groq fallback fix (27/07/2026) (+7 more)

### Community 46 - "process_clip"
Cohesion: 0.18
Nodes (15): burn_subtitles(), clip-processor/src/video_processor.py, clip-processor/tests/test_clip_pipeline.py, clip-processor/tests/test_video_processor.py, cut_clip(), extract_thumbnail(), generate_srt(), 04-02-PLAN.md: video_processor.py GREEN plan (+7 more)

### Community 47 - "dependencies"
Cohesion: 0.11
Nodes (19): class-variance-authority, clsx, cmdk, @dnd-kit/modifiers, @fontsource-variable/geist, @inertiajs/react, lucide-react, dependencies (+11 more)

### Community 48 - "_process_ai_pipeline"
Cohesion: 0.22
Nodes (10): insert_selected_moments(), 03-CONTEXT.md: Phase 3 Context, _prepare_audio(), _process_ai_pipeline(), AI-01: transcrição via Groq Whisper, AI-02: seleção de momentos via Claude Haiku, AI-03: filtro de qualidade score >= 7, máx 3 clips, Lookup de source_video_id INT via SELECT antes de INSERT em generated_clips (+2 more)

### Community 49 - "YouTubeUploader"
Cohesion: 0.21
Nodes (6): Marca destination_channels.oauth_expired_flag=TRUE para o slug atual. Best-…, Self-healing: reseta oauth_expired_flag=FALSE após upload bem-sucedido., Cliente fino para videos.insert + thumbnails.set., YouTubeUploader, Multi-canal extension via optional constructor param + None-guard retrocompat, Publisher legacy fallback when destination_channels empty

### Community 50 - "scripts"
Cohesion: 0.14
Nodes (14): scripts, dev, post-autoload-dump, post-update-cmd, pre-package-uninstall, test, Composer\\Config::disableProcessTimeout, Illuminate\\Foundation\\ComposerScripts::postAutoloadDump (+6 more)

### Community 51 - "painel/README.md (setup fresh 10 passos)"
Cohesion: 0.15
Nodes (13): Filament removal commit dca6e44, painel/ — Laravel 13 + Inertia 3 + React 19 (Filament removed), clip-processor/requirements.txt, nginx bind mount painel fix (404 puro), painel/README.md (setup fresh 10 passos), routes/web.php raiz '/' redirect fix, YouTube OAuth authorization CLI flow (youtube_oauth.py), Phase 8 Plan 09: Checkpoint Final End-to-End Plan (+5 more)

### Community 52 - "clip-processor/src/transcriber.py"
Cohesion: 0.15
Nodes (14): clip-processor/src/selector.py, clip-processor/src/transcriber.py, clip-processor/tests/test_selector.py, clip-processor/tests/test_transcriber.py, Groq Whisper whisper-large-v3-turbo + verbose_json + timestamp_granularities segment + pt, mysql/init/03-schema-migration.sql, 03-01-PLAN.md: Wave 0 skeletons + RED tests, 03-01-SUMMARY.md: Wave 0 Summary (+6 more)

### Community 53 - "composer.json"
Cohesion: 0.14
Nodes (13): autoload-dev, psr-4, description, extra, laravel, dont-discover, license, minimum-stability (+5 more)

### Community 54 - "_select_pending_videos"
Cohesion: 0.24
Nodes (8): Seleciona vídeos pendentes pra repor a janela de download ativo por nicho. Para…, _select_pending_videos(), Testes para _select_pending_videos — janela de download ativo por nicho., Janela vazia (occupied=0) deve buscar até o teto de cada nicho., Nicho já na janela cheia não gera nenhuma query SELECT (só o COUNT)., Déficit parcial (occupied=9 de janela 10) deve pedir LIMIT 1, não o teto…, SELECT deve restringir a published_at de até FRESHNESS_DAYS dias atrás., TestSelectPendingVideos

### Community 55 - "mysql/init/01-clips-schema.sql"
Cohesion: 0.53
Nodes (6): mysql/init/01-clips-schema.sql, generated_clips table, 01-02-PLAN: Schema SQL clips_automation e validate-infra.sh, source_channels table, source_videos table (ENUM 9 estados), scripts/validate-infra.sh

### Community 56 - "Documentation.tsx"
Cohesion: 0.33
Nodes (6): Accordion(), AccordionContent(), AccordionItem(), AccordionTrigger(), CHAIN, PageProps

### Community 57 - ".planning/research/PITFALLS.md"
Cohesion: 0.17
Nodes (11): n8n 06-router.json deactivation, Pitfall: CSRF blocking Telegram webhook (419), Redis SET NX dedup pattern (tg:dedup:{update_id}), TelegramWebhookController::handle, Pitfall: Blacklist Check Happens Too Late in the Pipeline, Pitfall: Filament Delete Button Deletes MySQL Row Without Deleting Files, Pitfall: Laravel Writes Conflict with Python Pipeline Mid-Transaction, Pitfall: n8n Still Running Telegram Bot in Parallel After Migration (+3 more)

### Community 58 - ".planning/research/FEATURES.md"
Cohesion: 0.20
Nodes (9): irazasyed/telegram-bot-sdk ^3.16, burn_watermark() function design, Admin Panel (Laravel/Filament) feature spec, Copyright Protection feature spec, Multi-Channel YouTube Publishing feature spec, OAuth testing-mode token expiry warning (7 days), Telegram Bot in Laravel feature spec, Laravel 13 version choice (not 11) (+1 more)

### Community 59 - "sidebar.tsx"
Cohesion: 0.05
Nodes (54): react, AppSidebar(), NavItem, navItems, NavUser(), SiteHeader(), ThemeToggle(), ChartContainer() (+46 more)

### Community 60 - "internal_api.py sidecar (Flask, port 8090)"
Cohesion: 0.20
Nodes (11): APScheduler jobs (ingest_cycle, publish_cycle, clip_pending_ttl), Boundary rule: painel reads directly, writes via sidecar, clip-processor service (as-built), internal_api.py sidecar (Flask, port 8090), CLIP_PROCESSOR_INTERNAL_TOKEN shared setup, Telegram Command classes (Status/Clipes/Aprovar/Rejeitar/Processar/Ajuda), Pitfall: Python→Laravel via wrong Host header (404), POST /internal/pipeline-event (Laravel endpoint) (+3 more)

### Community 61 - "validate-phase6-n8n.py"
Cohesion: 0.45
Nodes (11): AssertionError, assert_contains(), assert_has_node(), load_json(), main(), nodes_by_name(), Path, validate_cron() (+3 more)

### Community 62 - "niche-combobox.tsx"
Cohesion: 0.13
Nodes (18): NicheCombobox(), slugify(), Command(), CommandDialog(), CommandEmpty(), CommandGroup(), CommandInput(), CommandItem() (+10 more)

### Community 63 - "clip-processor/src/rss_poller.py"
Cohesion: 0.27
Nodes (11): _cleanup_partial() chamado fora do loop de retry, clip-processor/src/dedup.py, clip-processor/src/dedup.py, Dedup pattern: Redis NX → fallback MySQL → False, download_video(video_id, output_path), clip-processor/src/downloader.py, is_seen(video_id, redis_client, db_conn), 02-03-PLAN: dedup.py, downloader.py, rss_poller.py (+3 more)

### Community 64 - "overlay_watermark"
Cohesion: 0.12
Nodes (16): append_credits(), Adiciona linha de créditos ao final da descrição. Nunca sobrescreve conteúdo…, overlay_watermark(), Aplica watermark PNG no canto superior direito do clip via FFmpeg. Usa…, COPY-02: template vazio → retorna descrição sem modificação., COPY-02: handle vazio → retorna descrição sem modificação., Testes RED para append_credits (COPY-02)., COPY-02: template com {channel_handle} é substituído pelo handle real. (+8 more)

### Community 65 - "conftest.py"
Cohesion: 0.24
Nodes (10): mock_db_conn(), mock_redis(), fixture, Fixtures compartilhadas para todos os testes do clip-processor. Fornece:…, MagicMock simulando redis.Redis. - .set() retorna True por padrão (NX success —…, MagicMock simulando conexão pymysql com suporte a context manager em cursor().…, Feed RSS Atom do YouTube com 2 entradas válidas. VideoIds: 'abc123def456' e…, ID de vídeo YouTube válido (11 caracteres). (+2 more)

### Community 66 - "Plano mestre — estado, decisões e próximos passos"
Cohesion: 0.06
Nodes (34): 0. Situação apurada em 14/09/2026, 10. Pendente do usuário, 1. Advertência de direitos autorais — o assunto que bloqueia todo o resto, 2. Gate de licença — a correção estrutural, 3. Banco de dados — MySQL para PostgreSQL, 4. Infraestrutura — migrar para A1 Flex 12 GB, 5. Marca — Umbrella Solutions, 6. Afiliados (+26 more)

### Community 67 - "publisher.py"
Cohesion: 0.16
Nodes (22): Handle a usar no crédito: prioriza @handle real; cai para o nome do canal fonte…, resolve_credit_handle(), _fetch_pending_clips(), _has_longo_waiting(), _log(), _mark_clip_failed(), _mark_clip_published(), _maybe_finalize_source_video() (+14 more)

### Community 68 - "get_db_connection"
Cohesion: 0.22
Nodes (16): get_db_connection(), Abre conexão com o banco de dados (MySQL ou PostgreSQL) usando variáveis de…, delete_source_video_file(), Apaga o arquivo bruto (.mp4), clips gerados (videos/clips/), thumbnails e…, can_delete_raw(), _cleanup_partial(), _kill_ffmpeg_for_clip(), _kill_ytdlp_for() (+8 more)

### Community 69 - "test_video_processor.py"
Cohesion: 0.24
Nodes (7): burn_subtitles(), _format_srt_time(), generate_srt(), Gera arquivo SRT relativo ao início do clip a partir dos segmentos Whisper., Queima legendas SRT no clip usando FFmpeg., test_video_processor.py — Testes Phase 4 VID-01, VID-02, VID-03. Estado inicial…, TestSubtitles

### Community 70 - "require-dev"
Cohesion: 0.20
Nodes (10): require-dev, fakerphp/faker, laravel/pail, laravel/pao, laravel/pint, mockery/mockery, nunomaduro/collision, pestphp/pest (+2 more)

### Community 71 - "02-04-PLAN.md: Daemon main.py Plan"
Cohesion: 0.18
Nodes (11): 02-04-PLAN.md: Daemon main.py Plan, 02-04-SUMMARY.md: Daemon main.py Summary, 02-CONTEXT.md: Phase 2 Context, 02-RESEARCH.md: Phase 2 Research, 02-VALIDATION.md: Phase 2 Validation Strategy, pytest test infra (Phase 2 Wave 0), ACQU-01: monitorar canais via RSS a cada 6h, ACQU-02: baixar vídeos novos em 720p via yt-dlp (+3 more)

### Community 72 - ".planning/research/ARCHITECTURE.md (v2.0 research, superseded)"
Cohesion: 0.28
Nodes (9): Dead code: painel/app/Filament/Pages/Dashboard.php orphan, env() outside config() pitfall in DashboardController, Section 10: Known divergences and technical debt, channel_blacklist table (research design), destination_channels table (research design), Phase 7: Schema Multi-Canal + Watermark + Copyright (research plan), Phase 8: Laravel/Filament Painel Base (research plan), Phase 9: Bot Telegram no Laravel + Migração do n8n (research plan) (+1 more)

### Community 73 - "Sistema — IA de seleção de cortes"
Cohesion: 0.07
Nodes (30): 1. Confirmar qual provider respondeu, 1. Qual IA, e por quê, 2. Confirmar as keys dentro do container, 2. Os prompts, na íntegra, 3. Palavras-chave e frases-chave, por formato, 3. Ver o filtro de 30s agindo, 4. Conferir a duração dos clips no banco, 4. Regras de duração (+22 more)

### Community 74 - "run_ingest_cycle"
Cohesion: 0.21
Nodes (8): Roda RSS/download/AI (poll_all_channels + _download_pending_videos), sem…, run_ingest_cycle(), Deve chamar poll → download em ordem, sem publish., Erro em _download_pending_videos não deve propagar., Erro em poll_all_channels não deve impedir tentativa de download., Sem injeção, deve criar e fechar a própria conexão., Conexão injetada não deve ser fechada pelo runner., TestRunIngestCycle

### Community 75 - "02-01-PLAN: pytest scaffold RED state (Wave 0)"
Cohesion: 0.33
Nodes (9): clip-processor/tests/conftest.py, 02-01-PLAN: pytest scaffold RED state (Wave 0), 02-01-SUMMARY: 17 testes RED criados, clip-processor/pytest.ini, TDD RED-GREEN-REFACTOR pattern (imports no topo causam ModuleNotFoundError), tests/test_db.py, tests/test_dedup.py, tests/test_downloader.py (+1 more)

### Community 76 - "Phase 8 Context (Painel Laravel/Filament)"
Cohesion: 0.33
Nodes (9): PANEL-01 requirement (CRUD canal-fonte sem SQL), PANEL-02 requirement (CRUD canal-destino + badge OAuth), PANEL-03 requirement (dashboard tempo real), PANEL-04 requirement (aprovar/rejeitar clip), PANEL-05 requirement (autenticação single-user), Phase 8 human checkpoint (7-step verification), Phase 8 Plan 04: Autenticação Summary, Phase 8 Context (Painel Laravel/Filament) (+1 more)

### Community 77 - "main.py"
Cohesion: 0.10
Nodes (14): BlockingScheduler, _FallbackJob, log(), Roda os recoveries de estado preso. Agendado, não só no boot. Enquanto isso…, Executa o ciclo de integridade e auto-cura do Watchdog., run_recovery_once(), run_watchdog_once(), shutdown() (+6 more)

### Community 78 - "TestYouTubeUploaderChannelSlug"
Cohesion: 0.25
Nodes (5): Testes RED para suporte a channel_slug no YouTubeUploader (MCAN-01)., MCAN-01: channel_slug='futebol-em-cortes' → token_file='/app/youtube/token-…, Retrocompat: sem channel_slug, usa DEFAULT_TOKEN_FILE., Retrocompat: token_file explícito tem precedência sobre channel_slug., TestYouTubeUploaderChannelSlug

### Community 79 - "setup"
Cohesion: 0.25
Nodes (8): post-root-package-install, setup, composer install, npm install --ignore-scripts, npm run build, @php artisan key:generate, @php artisan migrate --force, @php -r \"file_exists('.env') || copy('.env.example', '.env');\

### Community 80 - "Phase 9-04 Plan: Telegram Bot Checkpoint"
Cohesion: 0.39
Nodes (8): PipelineEventTest.php, setWebhook registration to https://alessandromelo.com.br/telegramcanal, Phase 9-04 Plan: Telegram Bot Checkpoint, TelegramCommandsTest.php, TelegramWebhookTest.php, Artisan Schedule daily summary 18h BRT, Phase 9 Research: Bot Telegram no Laravel, Phase 9 Validation Strategy

### Community 81 - "Phase 7: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.25
Nodes (7): Bot Telegram no Laravel (v2), Groq Whisper (API) em vez de Whisper local, Multi-canal com token OAuth por canal, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 8: Painel Laravel/Filament, Phase 9: Bot Telegram no Laravel, recover_stuck_downloads só recupera 'downloading' → 'pending'

### Community 82 - "01-RESEARCH.md"
Cohesion: 0.14
Nodes (14): CLIPS_DB_PASSWORD como placeholder no SQL, youtube/generate_token.py, N8N_ENCRYPTION_KEY via ${VAR} nunca hardcoded, n8n usa SQLite default (não MySQL), OAuth app type 'installed' (Desktop App), não 'web', OAuth app publicado em Production, Pitfall: N8N_ENCRYPTION_KEY não definida antes do primeiro boot, Pitfall: n8n MySQL Deprecation Confusion (+6 more)

### Community 83 - "config"
Cohesion: 0.29
Nodes (7): pestphp/pest-plugin, php-http/discovery, config, allow-plugins, optimize-autoloader, preferred-install, sort-packages

### Community 84 - "require"
Cohesion: 0.29
Nodes (7): require, inertiajs/inertia-laravel, irazasyed/telegram-bot-sdk, laravel/framework, laravel/tinker, php, tightenco/ziggy

### Community 85 - "local_download_worker.py"
Cohesion: 0.13
Nodes (29): acquire_pid_lock(), _corte_frescor(), count_window_occupancy(), download_video_locally(), fetch_pending_videos(), get_video_duration(), _log(), main() (+21 more)

### Community 86 - "clip-processor/src/metadata_generator.py"
Cohesion: 0.33
Nodes (6): clip-processor/src/metadata_generator.py, clip-processor/tests/test_metadata_generator.py, 04-01-PLAN.md: Phase 4 Wave 0 skeletons + RED tests, 04-01-SUMMARY.md: Phase 4 Wave 0 Summary, 04-03-PLAN.md: metadata_generator.py GREEN plan, update_clip_metadata()

### Community 87 - "destination_channels table"
Cohesion: 0.33
Nodes (6): destination_channels table, Migration idempotente via INFORMATION_SCHEMA + prepared statement, 06-multi-canal-migration.sql, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 7 — Validation Strategy, pytest test framework (clip-processor)

### Community 88 - "Illuminate\Database\Eloquent\Model"
Cohesion: 0.23
Nodes (3): Illuminate\Database\Eloquent\Factories\HasFactory, Illuminate\Database\Eloquent\Model, SystemSetting

### Community 89 - "clip-processor/src/downloader.py"
Cohesion: 0.50
Nodes (4): clip-processor/src/downloader.py, Guard de espaço em disco antes do download (<2GB), Retry de download: 3x com 60s entre tentativas, Extração de áudio ffmpeg para arquivos >24MB

### Community 90 - "Illuminate\Console\Command"
Cohesion: 0.15
Nodes (5): Illuminate\Console\Command, BackupDatabaseCommand, CreatePainelUser, ResetPainelPassword, RestoreDatabaseCommand

### Community 91 - "_discard_failed_download"
Cohesion: 0.24
Nodes (8): _discard_failed_download(), Marca o download como 'failed' e libera a vaga que ele ocupava na janela. Antes…, Download falho não pode deixar arquivo em disco nem local_path preenchido. A…, Arquivo parcial em disco é apagado ANTES do UPDATE, e local_path vira NULL., Sem arquivo em disco (falha antes de escrever nada), segue e limpa a coluna., Se o arquivo sobrevive à remoção, não limpa local_path — banco não divergir do…, Clip em pending_cut/cutting ainda lê o raw — não apaga nem zera local_path., TestDiscardFailedDownload

### Community 92 - "field.tsx"
Cohesion: 0.14
Nodes (13): LoginForm(), Field(), FieldContent(), FieldDescription(), FieldError(), FieldGroup(), FieldLegend(), FieldSeparator() (+5 more)

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
Cohesion: 0.67
Nodes (3): youtube/assets/BRANDING.md — Futebol em Cortes visual identity, Banner generation prompt (2560x1440px), Logo generation prompt (scissors + play button, red/black/white)

### Community 102 - "transcription_job.py"
Cohesion: 0.08
Nodes (29): _audio_duration_seconds(), create_transcription_job(), _download_audio(), _merge_srt_chunks(), process_transcription_job(), transcription_job.py — Worker de "Transcrição Local" (QUICK-1). Feature isolada…, Divide o wav em `num_chunks` pedaços de duração igual via ffmpeg (recorte por…, Roda whisper-cpp local sobre um wav, gerando `<out_prefix>.srt`. Raises:… (+21 more)

### Community 103 - "_process_ai_pipeline"
Cohesion: 0.16
Nodes (10): _process_ai_pipeline(), Executa transcrição + seleção para um vídeo com status downloaded. Args: conn:…, AI-04: Testes de integração do pipeline de IA no rss_poller., Configura mock_db_conn para retornar canais e vídeos downloaded em fetchall().…, AI-04: poll_all_channels chama _process_ai_pipeline para cada vídeo com status…, AI-04: Falha no pipeline de IA de um vídeo não aborta os demais., AI-04: _process_ai_pipeline chama transcribe_video e select_moments em…, AI-04: Falha na transcrição (None) marca vídeo como failed e não chama… (+2 more)

### Community 109 - "Sistema de Alertas, Monitoramento e Watchdog"
Cohesion: 0.10
Nodes (21): 1. Visão Geral, 2. Camada 1: Better Stack (Uptime, Heartbeat e Incidentes), 3. Camada 2: Sentry (Erros de Código e Runtime), 4.1. Auto-Cura de Clipes Fantasmas (`check_ghost_clips`), 4.2. Monitor de Deadlock da Janela de Download (`check_download_window_health`), 4.3. Monitor de Fila Ociosa (`check_approval_queue_activity`), 4.4. Validador Prévio de OAuth (`check_youtube_tokens`), 4.5. Monitor de Armazenamento SSD (`check_disk_space`) (+13 more)

### Community 110 - "clip-processor/src/main.py"
Cohesion: 0.22
Nodes (11): BlockingScheduler daemon pattern (APScheduler), clip-processor/src/db.py, clip-processor/src/main.py, clip-processor/src/rss_poller.py, Pitfall: container restart com vídeo em status downloading, 03-04-PLAN.md: AI pipeline integration plan, 03-04-SUMMARY.md: AI pipeline integration Summary, poll_all_channels(db_conn, redis_client) (+3 more)

### Community 111 - "Fases"
Cohesion: 0.11
Nodes (19): 1. Não fazer upgrade para Pay As You Go (a camada que realmente importa), 2. Provisionar só recursos com o selo "Always Free-eligible", 3. Orçamento com alerta em US$ 1, 4. Conferência após provisionar, Como o custo zero é garantido, Decisão tomada, Depois da migração, Fase 0 — Conta e blindagem de cobrança  ⬜ NÃO INICIADA (+11 more)

### Community 113 - "ttl_worker.py"
Cohesion: 0.15
Nodes (12): Worker de TTL para clipes pending (CTRL-05). - Expira: clipes com…, Executa 1 iteração do TTL: expira clipes >TTL_HOURS, avisa clipes WARN_HOURS-…, run_ttl_once(), Testes para ttl_worker.py — expiração automática de clips pending. Estado RED…, run_ttl_once: clips pending > TTL_HOURS são marcados rejected via UPDATE., run_ttl_once: clips entre WARN_HOURS e TTL_HOURS disparam notify() para Laravel., Redis SET NX False (já avisou): NÃO dispara notify() extra., TestExpire (+4 more)

### Community 114 - "rejeitar"
Cohesion: 0.15
Nodes (17): internal_api.reject_clip(clip_id) — calls src.rejeitar.rejeitar directly, _clip_artifacts(), rejeitar.py — Rejeição manual de clip via comando /rejeitar do Telegram…, Arquivos em disco de um clip. Só clip_path e thumbnail_path ficam no banco;…, Marca o clip como rejected, remove os artefatos do clip, preserva raw video.…, rejeitar(), Testes para rejeitar.py — comando /rejeitar do Telegram. Estado RED até Plan…, rejeitar(123): executa UPDATE generated_clips SET status='rejected' WHERE… (+9 more)

### Community 119 - "Sistema — `painel/`"
Cohesion: 0.12
Nodes (17): A regra da fronteira, Armadilhas conhecidas, Autenticação, Banco, Canais e Estúdio de Templates, Comandos Artisan do Painel, Como ler o Dashboard, Dashboard — `DashboardController` (+9 more)

### Community 120 - "Runbook de operação"
Cohesion: 0.12
Nodes (16): Backup antes de DELETE em massa, Comandos do painel, Convenções, Diagnosticar falhas de upload, Espaço em disco, Estado preso sem recuperação automática, Está tudo de pé?, Nada sobe para o YouTube (+8 more)

### Community 122 - "Quick Task 1: Transcrição Local Summary"
Cohesion: 0.15
Nodes (12): Accomplishments, Auto-fixed Issues, Decisions Made, Deviations from Plan, Files Created/Modified, Issues Encountered, Next Phase Readiness, Performance (+4 more)

### Community 123 - "Publicação no YouTube"
Cohesion: 0.12
Nodes (16): Cota diária e janela horária, Fallback legado, Finalização do vídeo fonte, Guard de corrida com a rejeição, Janela horária, Limites, OAuth por canal-destino, Ordem da fila: round-robin por canal fonte (+8 more)

### Community 124 - "test_local_download_worker.py"
Cohesion: 0.17
Nodes (11): FakeRemote, fixture, Testes da janela de download do local_download_worker. Rodar: python3 -m pytest…, Responde às queries do worker: contagem da janela e lista de pendentes., test_busca_so_o_deficit_de_cada_nicho(), test_canal_destino_novo_soma_dez(), test_falha_na_contagem_nao_baixa_nada(), test_janela_cheia_nao_busca_nada() (+3 more)

### Community 150 - "Radar de Performance: pacote de entrega"
Cohesion: 0.13
Nodes (14): Arquivos SOBRESCRITOS (revise com git diff antes de qualquer coisa), Como aplicar, Como desfazer tudo, Decisões que você precisa saber que foram tomadas por mim, O que abrir primeiro no painel, O que este pacote faz, Ordem de execução, Passo 1, a parte manual sua (Fase 0) (+6 more)

### Community 151 - "Banco de dados — `clips_automation`"
Cohesion: 0.13
Nodes (15): 1. Backup Automatizado (`db:backup`), 2. Restauração e Smoke Test (`db:restore`), Acesso, Banco de dados — `clips_automation`, `destination_channels`, Divergência banco × disco (bug aberto), Evolução das Migrations do Laravel, `generated_clips` (+7 more)

### Community 152 - "Mapa dos módulos"
Cohesion: 0.13
Nodes (15): Aquisição — [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md), Base, Configuração, Editar código exige rebuild, Inteligência — [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md), [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md), Interface com o painel — [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md), Mapa dos módulos, O que o Redis guarda (e o que não guarda) (+7 more)

### Community 153 - "Descoberta e download"
Cohesion: 0.13
Nodes (15): Artefatos em disco, `_cleanup_partial` — por download (no `except`), `cleanup_stale_downloads` — varredura de órfãos, Dedup, Descoberta e download, Descoberta via RSS, Detecção de formato, `_discard_failed_download` (13/08/2026) (+7 more)

### Community 154 - "Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan"
Cohesion: 0.12
Nodes (18): Phase 8 Deferred Items, BOT-01 requirement (webhook + allowlist + dedup), BOT-02 requirement (6 Telegram commands), BOT-03 requirement (pipeline-event notifications), Filament $isLazy=false widget pattern, mysql/init/05-controle-manual-migration.sql, App\Filament\Widgets\QuotaTodayWidget, App\Filament\Widgets\RecentFailuresWidget (+10 more)

### Community 156 - "TestProcessClipWithWatermark"
Cohesion: 0.25
Nodes (5): Testes de integração: process_clip aplica overlay_watermark com slug do canal-…, MCAN-02: process_clip chama overlay_watermark com watermark_path derivado do…, MCAN-02: destination_channel_slug NULL → os.rename é usado, overlay_watermark…, Verifica que cut_clip com background_path usa overlay 320:72 e loop de imagem., TestProcessClipWithWatermark

### Community 157 - "Backlog de bugs"
Cohesion: 0.13
Nodes (15): 10. ABERTO — 287 clips com `clip_path` apontando para arquivo inexistente, 11. ABERTO — Container não honra SIGTERM, todo `docker stop` vira SIGKILL, 12. FEITO — Worker local de download ignorava a janela, 13. FEITO — Rejeitar no painel não apagava os arquivos do clip, 14. FEITO — Usuários de teste com senha padrão no banco de produção, 1. FEITO — Órfãos de download nunca eram apagados, 2. FEITO — `_raw.mp4` nunca era apagado, 3. SUSPEITA — Thumbnail não aplicada nos vídeos longos no YouTube (+7 more)

### Community 158 - "select_moments"
Cohesion: 0.40
Nodes (6): output_config json_schema em vez de prefill para Claude Haiku 4.5, generate_metadata(), Algoritmo de remoção de overlap por score, _remove_overlaps(), VID-04: metadata SEO via Claude Haiku, select_moments()

### Community 159 - "v1.0 — Pipeline Base"
Cohesion: 0.53
Nodes (6): v1.0 — Pipeline Base, MANUAL_APPROVAL_REQUIRED toggle, Phase 3: IA — Transcrição e Seleção, Phase 4: Processamento de Vídeo, Phase 5: Publicação e Automação Total, Phase 6: Controle Manual N8N + Telegram

### Community 160 - "Docs — Sistema Canal de Cortes"
Cohesion: 0.17
Nodes (12): As três armadilhas que pegam todo mundo, Como atualizar estes documentos, Como o sistema funciona, por subsistema, Corrigido em 12–13/08/2026, Docs — Sistema Canal de Cortes, Estado atual em uma tela, Infra, O que o sistema é, em um parágrafo (+4 more)

### Community 161 - "3. Como Saber se o Cron Funcionou"
Cohesion: 0.17
Nodes (11): 1. Contexto e Diagnóstico, 2.1. Script de Execução e Retentativas (`scripts/resume_claude_session.sh`), 2.2. Camadas de Agendamento Configuradas, 2. O que Foi Feito, 3. Como Saber se o Cron Funcionou, Dados da Sessão Interrompida, Opção A: Executar o verificador automático (Recomendado), Opção B: Verificação manual por arquivos de log (+3 more)

### Community 162 - "clip-processor/src/db.py"
Cohesion: 0.50
Nodes (5): db.py: quem chama é responsável por fechar a conexão, clip-processor/src/db.py, INSERT IGNORE para idempotência de vídeos/canais, 02-02-PLAN: docker-compose + requirements + seed + db.py, 02-02-SUMMARY: db.py GREEN, seed 5 canais

### Community 163 - "notify"
Cohesion: 0.17
Nodes (14): notify(), telegram_notifier.py — Cliente HTTP que publica eventos do pipeline para o…, POST para LARAVEL_NOTIFY_URL com {event, payload}. Retorna True em 2xx, False…, Testes para telegram_notifier.py — cliente HTTP que dispara eventos para o…, notify() captura RequestException e retorna False sem propagar., notify() retorna False quando o endpoint retorna 4xx., notify() faz POST para LARAVEL_NOTIFY_URL — RED até Plan 09-03. Importa…, notify() inclui header Host para nginx routing — RED até Plan 09-03. (+6 more)

### Community 164 - "Passo a passo"
Cohesion: 0.17
Nodes (11): 1. Conferir a branch, 2. Testes da branch, 3. Documentação e grafo, ainda na branch, 4. Merge na master, 5. Push para o GitHub, 6. Deploy, 7. Conferir a versão no ar, 8. Relatório (+3 more)

### Community 168 - "Guia de Deploy Rápido (Produção)"
Cohesion: 0.17
Nodes (11): 1. Deploy Padrão (~20 a 25 segundos), 2. Deploy Ultrarrápido Backend (~8 a 12 segundos), 3. Deploy com Rebuild do Docker (Apenas quando estritamente necessário), A Solução Definitiva, ⚡ Como Fazer Deploy, Guia de Deploy Rápido (Produção), 🌐 Informações do Servidor de Produção, O Problema Antigo (+3 more)

### Community 172 - "Pipeline e scheduler"
Cohesion: 0.18
Nodes (11): Armadilha recorrente: editar código não muda nada sem rebuild, Conexões, Entrypoint, Jobs agendados, O que cada ciclo executa, Onde mexer, Pipeline e scheduler, `run_ingest_cycle` (20 min) (+3 more)

### Community 173 - "_niche_windows"
Cohesion: 0.40
Nodes (4): _niche_windows(), Teto da janela por nicho: DOWNLOAD_WINDOW_PER_CHANNEL × canais destino ativos.…, Teto = DOWNLOAD_WINDOW_PER_CHANNEL por canal destino ativo do nicho., TestNicheWindows

### Community 174 - "Sidecar HTTP e controles de fila"
Cohesion: 0.20
Nodes (10): A regra, As duas rotas que apagam, Caminho inverso: eventos para o Telegram, Controles de fila, `delete_source_video_file` — só disco, `purge_old_videos` — apaga linha, Rede e autenticação, Rejeição de clip (+2 more)

### Community 175 - "Corte e pós-produção de vídeo"
Cohesion: 0.20
Nodes (10): Abortar um corte em andamento, Artefatos em disco, Buraco que sobra, Corte e pós-produção de vídeo, Corte por formato, Legendas, Marca d'água, Metadata do clip (+2 more)

### Community 176 - "04-04 Summary: Poller Integration Summary"
Cohesion: 0.40
Nodes (5): Migration Phase 3 usa INFORMATION_SCHEMA em vez de ADD COLUMN IF NOT EXISTS, Persistir arquivos renderizados no volume montado /app/videos, Raw source só removido quando todos clips do source video estão terminais, mysql/init/03-schema-migration.sql, 04-04 Summary: Poller Integration Summary

### Community 177 - "HandleInertiaRequests.php"
Cohesion: 0.33
Nodes (3): Illuminate\Foundation\Configuration\Middleware, Inertia\Middleware, HandleInertiaRequests

### Community 178 - "TelegramWebhookController.php"
Cohesion: 0.22
Nodes (4): Illuminate\Http\Response, JsonResponse, TelegramWebhookController, tg:dedup:{update_id} Redis SET NX EX 300 dedup pattern

### Community 179 - "pipeline_runner.py"
Cohesion: 0.24
Nodes (10): _clips_need_raw(), _log(), pipeline_runner.py — Uma execucao completa do pipeline. Usado pelo daemon e…, Diz se algum clip desse vídeo ainda precisa do arquivo bruto em disco.…, Verifica vídeos na janela ativa cujo arquivo não existe mais em disco e limpa., Roda só a publicação de clips aprovados, sem RSS/download/AI. Existe pra drenar…, reconcile_active_window(), run_publish_only() (+2 more)

### Community 180 - "test_uploader_expired.py"
Cohesion: 0.22
Nodes (6): HttpError, Exception, RefreshError, RED test para captura de RefreshError e persistência de oauth_expired_flag…, RefreshError em creds.refresh() deve setar oauth_expired_flag=TRUE em…, test_load_credentials_catches_refresh_error_and_flags_channel()

### Community 181 - "Estados e transições do pipeline"
Cohesion: 0.22
Nodes (9): A terceira query (`local_path IS NULL` → `failed`), `cutting` e `publishing` em `source_videos`: valores mortos, Estados e transições do pipeline, Estados × ocupação da janela de download, Estados terminais e o que sobra em disco, `generated_clips.status`, O que fazer com o que não tem recuperação, Recuperação automática: o que tem e o que não tem (+1 more)

### Community 182 - "Pipeline principal — Groq Whisper"
Cohesion: 0.22
Nodes (9): Binário e modelo, Chunking, Conversão para áudio acima de 24 MB, Formato do transcript salvo, Pipeline principal — Groq Whisper, Progresso, Sem fallback, Transcrição (+1 more)

### Community 183 - "test_rss_poller.py"
Cohesion: 0.36
Nodes (4): _detect_format(), Decide 'curto' ou 'longo' com base na duração real do vídeo fonte. Vídeos com…, Testes ACQU-01: detecção de vídeos novos via RSS. Testes AI-04: integração do…, TestDetectFormat

### Community 184 - "resume_claude_session.sh"
Cohesion: 0.32
Nodes (7): HOME, log(), PATH, resume_claude_session.sh script, SHELL, update_status(), USER

### Community 185 - "TestPollAllChannels"
Cohesion: 0.29
Nodes (4): Dado feed RSS com 2 entradas nunca vistas, poll_all_channels() insere 2…, Dado vídeo já no Redis (is_seen retorna True), poll não chama insert_video para…, Feed sem entradas não levanta exceção., TestPollAllChannels

### Community 186 - "package.json"
Cohesion: 0.29
Nodes (6): private, $schema, scripts, build, dev, type

### Community 187 - "TestBlacklistGuard"
Cohesion: 0.33
Nodes (4): Testes RED para blacklist guard no rss_poller (COPY-03)., COPY-03: canal com blacklisted=True não chama insert_video. O guard deve checar…, COPY-03: canal com blacklisted=False (ou None) chama insert_video normalmente., TestBlacklistGuard

### Community 188 - "Estratégia de Conteúdo, Benchmark e YouTube Analytics"
Cohesion: 0.33
Nodes (6): 1. Como Diagnosticar e Alimentar a IA com Métricas do YouTube Studio, 2. Benchmark de Concorrentes & Canais de Referência, 3. Modelo dos Cortes Virais de Política (MBL / Missão), 4. Monetização e RPM Médio no YouTube Brasil, Estratégia de Conteúdo, Benchmark e YouTube Analytics, Ferramenta de Diagnóstico no Painel (`/painel/assistente`)

### Community 189 - "📋 Regras de Negócio e Gatilhos Operacionais — Canal de Cortes"
Cohesion: 0.33
Nodes (5): 1. 🎯 Metas Diárias de Publicação (Cota do Canal), 2. 📥 Janela de Download e Captação, 3. 🤖 Seleção e Ranqueamento por IA, 4. 🧹 Gatilhos de Auto-Expurgo e Limpeza de Disco (Watchdog & TTL), 📋 Regras de Negócio e Gatilhos Operacionais — Canal de Cortes

### Community 190 - "Plano PostgreSQL — fase A (local) e fase B (produção)"
Cohesion: 0.22
Nodes (9): Como retomar depois de reiniciar a sessão, Decisões, Divergência encontrada na A2 (importante para a fase B), Estado em 15/09/2026, Falhas de teste pré-existentes encontradas (não são da migração), Fase A — local, Fase B — produção (fazer junto da VM A1 de 12 GB), Plano PostgreSQL — fase A (local) e fase B (produção) (+1 more)

### Community 191 - "generated_clips.status state machine"
Cohesion: 0.40
Nodes (5): generated_clips.status state machine, list-pending-clips.sh, mark-published.sh, manual-workflow/README.md — manual clip publishing guide, Pitfall: Filament Auto-Generated Resources Break on ENUM Columns

### Community 192 - "n8n/workflows/canaldecortes-pipeline.json"
Cohesion: 0.40
Nodes (5): Workflow usa Execute Command com retry 3x e espera 15 minutos, n8n/workflows/canaldecortes-pipeline.json, n8n/workflows/README.md, 05-06 Plan: n8n workflow and production checkpoint, 05-06 Summary: n8n workflow importable, retry documented

### Community 193 - "test_pipeline_runner.py"
Cohesion: 0.40
Nodes (4): _janela_fixa(), fixture, Testes para pipeline_runner.py — ciclo completo do pipeline., Isola os testes da consulta a destination_channels: 1 canal por nicho.

### Community 194 - "_fetch_destination_channels"
Cohesion: 0.50
Nodes (3): _fetch_destination_channels(), Retorna canais-destino ativos de destination_channels., MCAN-01: _fetch_destination_channels retorna apenas canais ativos.

### Community 195 - "Diretório de Documentação (`Docs/`)"
Cohesion: 0.50
Nodes (4): 1. Documentação do Sistema (`Docs/sistema/`), 2. Estudos e Pesquisas (`Docs/estudos/`), Diretório de Documentação (`Docs/`), Estrutura de Pastas

### Community 196 - "test_uploader.py"
Cohesion: 0.50
Nodes (3): make_uploader(), Testes para YouTubeUploader — upload de clips e thumbnails. Todas as chamadas…, Cria YouTubeUploader com credenciais e YouTube mockados.

### Community 197 - "keywords"
Cohesion: 0.67
Nodes (3): keywords, framework, laravel

### Community 203 - "post-create-project-cmd"
Cohesion: 0.50
Nodes (4): post-create-project-cmd, @php artisan key:generate --ansi, @php artisan migrate --graceful --ansi, @php -r \"file_exists('database/database.sqlite') || touch('database/database.sqlite');\

### Community 214 - "generate_sample_thumbnails.py"
Cohesion: 0.67
Nodes (3): extract_frame(), main(), scripts/generate_sample_thumbnails.py — Gera amostras de thumbnails…

## Ambiguous Edges - Review These
- `clip-processor/src/ttl_worker.py` → `clip-processor/src/telegram_notifier.py`  [AMBIGUOUS]
  .planning/phases/06-controle-manual-n8n-telegram/06-05-SUMMARY.md · relation: conceptually_related_to

## Knowledge Gaps
- **589 isolated node(s):** `deploy.sh script`, `force-download.sh script`, `$schema`, `style`, `rsc` (+584 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `clip-processor/src/ttl_worker.py` and `clip-processor/src/telegram_notifier.py`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `run_pipeline_once()` connect `run_pipeline_once` to `n8n/workflows/canaldecortes-pipeline.json`, `test_pipeline_runner.py`, `publisher.py`, `get_db_connection`, `notify`, `rss_poller.py`, `_download_pending_videos`, `main.py`, `pipeline_runner.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `n8n/workflows/canaldecortes-pipeline.json` connect `n8n/workflows/canaldecortes-pipeline.json` to `05-01 Plan: Publishing schema, skeletons and RED tests`, `run_pipeline_once`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `05-06 Plan: n8n workflow and production checkpoint` connect `n8n/workflows/canaldecortes-pipeline.json` to `Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `QuotaManager` (e.g. with `TestCanUpload` and `TestLongoReservation`) actually correct?**
  _`QuotaManager` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `YouTubeUploader` (e.g. with `TestUploadClip` and `TestYouTubeUploaderChannelSlug`) actually correct?**
  _`YouTubeUploader` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `force-download.sh script`, `$schema` to the rest of the system?**
  _589 weakly-connected nodes found - possible documentation gaps or missing edges._