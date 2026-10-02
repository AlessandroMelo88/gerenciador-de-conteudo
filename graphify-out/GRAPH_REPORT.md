# Graph Report - canaldecortes  (2026-10-02)

## Corpus Check
- 578 files · ~889,894 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4989 nodes · 9061 edges · 339 communities (299 shown, 40 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 185 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `290152bd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_media_channel_flow.py
- publish_pending_clips
- db.py
- clip-queue-tabs.tsx
- make_redis
- Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)
- rss_poller.py
- watchdog.py
- _cookie
- Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)
- internal_api.py
- test_retention_collector.py
- TranscricaoLocal.tsx
- processar.py
- devDependencies
- utils.ts
- publisher.py
- 05-01 Plan: Publishing schema, skeletons and RED tests
- Illuminate\Database\Eloquent\Factories\HasFactory
- TestUploadClip
- uploader.py
- metadata_generator.py
- cut_clip
- test_internal_api.py
- is_seen
- transcribe_video
- DestinationChannel
- components.json
- docker-compose.yml (raiz wordpress/)
- download_video
- Illuminate\Http\RedirectResponse
- Plano — Prompts de IA editáveis pelo painel
- Offer
- compilerOptions
- video_processor.py
- Phase 1: Infraestrutura Base
- Phase 7 Context: Schema Multi-Canal + Python Pipeline
- run_pipeline_once
- TelegramHttpClientHandler.php
- Plano mestre — estado, decisões e próximos passos
- Offers.tsx
- TestArquivoDaAula
- TestDownloadPendingVideos
- chart.tsx
- SourceVideos.tsx
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
- Illuminate\Http\Request
- .planning/research/PITFALLS.md
- .planning/research/FEATURES.md
- cn
- internal_api.py sidecar (Flask, port 8090)
- validate-phase6-n8n.py
- test_transcription_worker.py
- clip-processor/src/rss_poller.py
- overlay_watermark
- conftest.py
- Backlog de bugs
- publisher.py
- active-window-table.tsx
- test_video_processor.py
- require-dev
- 02-04-PLAN.md: Daemon main.py Plan
- .planning/research/ARCHITECTURE.md (v2.0 research, superseded)
- Sistema — IA de seleção de cortes
- pipeline_runner.py
- 02-01-PLAN: pytest scaffold RED state (Wave 0)
- insert_selected_moments
- main.py
- _seg
- FakeDb
- Phase 9-04 Plan: Telegram Bot Checkpoint
- Phase 7: Schema Multi-Canal + Python Pipeline
- 01-RESEARCH.md
- config
- require
- local_download_worker.py
- cli.py
- destination_channels table
- _client
- clip-processor/src/downloader.py
- Illuminate\Console\Command
- TestDiscardFailedDownload
- User
- psr-4
- v2.0 — Painel + Multi-Canal
- Pitfall: Content ID Claim Despite Watermark
- list-pending-clips.sh
- ExampleTest
- youtube/assets/BRANDING.md — Futebol em Cortes visual identity
- mark-failed.sh
- mark-published.sh
- transcription_job.py
- _clip
- validate-infra.sh
- Sistema de Alertas, Monitoramento e Watchdog
- _maybe_finalize_source_video
- Fases
- rules
- notify
- rejeitar
- force-download.sh
- CreatePainelUser artisan command
- BuscaTranscricoes.tsx
- transcript_indexer.py
- Sistema — `painel/`
- Runbook de operação
- captura.js
- Quick Task 1: Transcrição Local Summary
- Publicação no YouTube
- test_local_download_worker.py
- has_burned_subtitles
- adr/README.md
- test_prompt_profiles.py
- validate_short_media
- 03-RESEARCH.md: Phase 3 Research
- MCAN-04: 3 vídeos/dia por canal 19h-22h BRT
- Claude Haiku para seleção e metadados
- Path
- Banco de dados — `clips_automation`
- Mapa dos módulos
- Descoberta e download
- Offer
- Docs/README.md
- metrics_collector.py
- test_watchdog.py
- transcription_worker.py
- v1.0 — Pipeline Base
- Docs/sistema — como o sistema funciona
- Plano — vídeo longo automático, escolhido por canal
- Inertia\Response
- Gitflow do Canal de Cortes
- Passo a passo
- fair_pick
- compile_prompt_profiles.py
- Guia de Deploy Rápido (Produção)
- test_video_render.py
- TranscriptionJob
- Pipeline e scheduler
- _fetch_pending_clips_for_channel
- Sidecar HTTP e controles de fila
- Corte e pós-produção de vídeo
- MediaAsset
- test_cli.py
- FakeSession
- Illuminate\Database\Eloquent\Model
- extensao_api.py
- Estados e transições do pipeline
- Transcrições — base de conhecimento (17/09/2026)
- cleanup_stale_downloads
- resume_claude_session.sh
- make_offer
- package.json
- test_db.py
- TestAIPipelineIntegration
- 📋 Regras de Negócio e Gatilhos Operacionais — Canal de Cortes
- Foco de revisão
- TranscriptSearch
- render_short_clip
- clip-processor/src/main.py
- manifest.json
- 3. Como Saber se o Cron Funcionou
- copywriter.py
- TestLoginDosCursos
- resume_claude_daemon.sh
- Sistema de afiliados
- deploy.sh
- @dnd-kit/core
- @dnd-kit/sortable
- FakeRemote
- check_cron_status.sh
- manual.py
- TestProgresso
- OfferCopywriter
- Migração para a VM A1 + PostgreSQL — como ficou
- Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel
- 2026_09_18_000000_transcricao_status_pausado.php
- selector.py
- Phase 8 Plan 08: Dashboard Widgets + Aprovar/Rejeitar Plan
- dt_sp
- affiliate-worker
- RuntimeError
- FakeCursor
- recover_stuck_selecting
- mysql/init/06-multi-canal-migration.sql
- migrar_mysql_para_postgres.py
- Foco de revisão
- clip-processor/src/publisher.py
- download_hls_audio
- _niche_windows
- Parte 2 — Técnica
- popup.js
- download_media
- test_recovery_states.py
- save_media_entry
- Settings.tsx
- check_download_window_health
- Extensão "Transcrever esta aula"
- _seg
- test_publisher.py
- test_sigterm_shutdown.py
- _process_pending_clips(conn)
- TestTituloEditorial
- test_long_format_mode.py
- Radar de Performance: pacote de entrega
- datetime
- QuotaManager
- TestDownloadHls
- Estado do projeto — leia primeiro
- Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan
- MetricsReport
- Phase 8 Context (Painel Laravel/Filament)
- Retomada — Transcrições, extensão e estudos (18/09/2026)
- _TwoFormatCursor
- Referência técnica
- test_quota_manager.py
- TestQuotaManagerMultiCanal
- Desenvolvimento — lint, testes e CI
- FakeCursor
- Referência técnica
- TestFinalizacaoComDoisFormatos
- Parte 1 — Para quem usa o painel
- Plano PostgreSQL — fase A (local) e fase B (produção)
- test_uploader.py
- Docs — mapa da documentação
- react
- 0001-busca-vetorial-nas-transcricoes.md
- changelog.py
- Contribuindo
- SPEC-001 — Retenção do YouTube Analytics por clip
- Release Notes
- extra
- setup
- TestPromptsDoSeletor
- cmdk
- @dnd-kit/modifiers
- @inertiajs/react
- lucide-react
- Illuminate\Database\Seeder
- dev-pgvector.sh
- restore-postgres.sh
- clip-processor
- Estratégia de Conteúdo, Benchmark e YouTube Analytics
- SPEC-002 — Revisão de palavrão na aprovação, com julgamento tipado (JEV)
- indexar_ligado
- update_status
- Phase 8 Research (Painel Laravel/Filament)
- TestRecordUpload
- channel_cap
- BlockingScheduler
- TestPausarEApagar
- Progresso — o que foi feito e o que falta
- _max_window_slots
- generated_clips.status state machine
- Deploy automático diário — opções e decisão
- CHANGELOG.d — fragmentos de release notes
- Estado atual em uma tela
- check_disk_space
- check-doc-links.py
- TestEnderecosDeMidia
- shadcn
- TelegramWebhookController::handle
- janela_16
- test
- recharts
- sonner
- tw-animate-css
- zod

## God Nodes (most connected - your core abstractions)
1. `cn()` - 203 edges
2. `QuotaManager` - 64 edges
3. `react` - 64 edges
4. `YouTubeUploader` - 41 edges
5. `publish_pending_clips()` - 40 edges
6. `get_db_connection()` - 39 edges
7. `process_clip()` - 38 edges
8. `DestinationChannel` - 33 edges
9. `User` - 33 edges
10. `dt_sp()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `generate_metadata()` --implements--> `Fallback determinístico de metadata (não bloqueia pipeline)`  [EXTRACTED]
  clip-processor/src/metadata_generator.py → .planning/phases/04-processamento-de-video/04-03-SUMMARY.md
- `publish_pending_clips()` --rationale_for--> `Publisher legacy fallback when destination_channels empty`  [EXTRACTED]
  clip-processor/src/publisher.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-06-SUMMARY.md
- `overlay_watermark()` --rationale_for--> `Graceful degradation pattern: return input unchanged when optional dependency missing`  [EXTRACTED]
  clip-processor/src/video_processor.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-05-SUMMARY.md
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

## Communities (339 total, 40 thin omitted)

### Community 0 - "test_media_channel_flow.py"
Cohesion: 0.05
Nodes (75): _as_int(), _asset_specificity(), _channel_directory(), choose_media_asset(), _log(), media_format_enabled(), Path, Resolve assets de pós-produção (intro, encerramento, música) por canal e… (+67 more)

### Community 1 - "publish_pending_clips"
Cohesion: 0.11
Nodes (25): publish_pending_clips(), Publica clips prontos e retorna quantidade publicada. Fluxo multi-canal (Phase…, dt_sp(), make_conn_with_clips(), make_mock_uploader(), Upload bem-sucedido: pending → publishing → published., Upload com erro: status vai para 'failed', quota não é incrementada., Quando quota/janela bloqueada, clip deve continuar como pending. (+17 more)

### Community 2 - "db.py"
Cohesion: 0.10
Nodes (25): count_longos_aguardando(), get_db_driver(), insert_video(), _log(), PostgresConnectionWrapper, PostgresCursorWrapper, db.py — Módulo de acesso ao banco de dados (MySQL e PostgreSQL) para o daemon…, Wrapper para conexão do psycopg2 expondo cursor com dicionário e atributo… (+17 more)

### Community 3 - "clip-queue-tabs.tsx"
Cohesion: 0.06
Nodes (41): ClipPreviewModal(), ClipPreviewModalProps, ClipQueueTabs(), FailuresTable(), PendingTable(), post(), useSelection(), OverviewCards() (+33 more)

### Community 4 - "make_redis"
Cohesion: 0.11
Nodes (14): make_redis(), Helper: mock Redis com contador configurável., Deve permitir upload dentro da janela da noite (19h às 22h)., Deve permitir upload dentro da janela do almoço/meio-dia (12h às 14h)., Deve negar upload entre as janelas (ex: 15h) quando não há bypass., Deve permitir upload fora das janelas quando bypass_window=True., Deve negar upload às 22h ou depois., Deve negar upload à meia-noite. (+6 more)

### Community 5 - "Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)"
Cohesion: 0.10
Nodes (30): mysql/init/05-controle-manual-migration.sql, mysql/manual-workflow/approve-backlog.sql — helper opcional para backlog de pending, CTRL-01: Telegram allowlist (chat_id 5760918317, silêncio para outros), CTRL-02: publisher.py seleciona clips 'approved' (não mais 'pending'), CTRL-03: /rejeitar <id> marca rejected + apaga MP4 mantém raw, CTRL-04: /processar <url> ingestão manual de vídeo YouTube, CTRL-05: TTL worker expira pending>48h, avisa 24h antes, mysql/manual-workflow/approve-backlog.sql (+22 more)

### Community 6 - "rss_poller.py"
Cohesion: 0.06
Nodes (33): _count_clips_of_format(), _detect_format(), _extract_video_id(), _is_blocked_title(), _log(), _plan_selection_runs(), poll_all_channels(), _process_ai_pipeline() (+25 more)

### Community 7 - "watchdog.py"
Cohesion: 0.22
Nodes (10): _avisar_janela_aguardando_aprovacao(), check_approval_queue_activity(), _horas_atras(), _log(), datetime, watchdog.py — Monitor inteligente de integridade do pipeline e detector de…, Aviso informativo (no máximo 1 por dia) de que a janela está cheia esperando o…, Avisa se a fila de aprovação estiver zerada há mais de 6h em horário comercial… (+2 more)

### Community 8 - "_cookie"
Cohesion: 0.07
Nodes (12): _cookie(), parametrize, Testes da API local que a extensão do Chrome chama no worker do Mac. Rodar:…, Qualquer site aberto no Chrome consegue chamar 127.0.0.1; só extensão manda…, A extensão manda só o site da aba; se vier cookie de outro domínio, descarta., TestDominioRegistravel, TestFormatoNetscape, TestJuntarCookies (+4 more)

### Community 9 - "Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)"
Cohesion: 0.07
Nodes (34): canaldecortes/docker/nginx/canaldecortes.conf vhost, clip-processor não tem bind mount de src/ — exige rebuild+restart para refletir código, mysql/init/07-panel-oauth-flag-migration.sql (oauth_expired_flag idempotent migration), destination_channels.oauth_expired_flag column, config/database.php Redis 'pipeline' connection (DB 0), config/services.php clip_processor block (url/token), canaldecortes/painel/ — Laravel 13 + Filament 5.6.7 + Pest 4.7.4 project, App\Models\DestinationChannel Eloquent Model + getOauthStatusAttribute (+26 more)

### Community 10 - "internal_api.py"
Cohesion: 0.20
Nodes (23): internal_api.resolve_channel(url) — yt-dlp channel resolution, _check_auth(), internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.…, Liveness sem auth e sem tocar em banco/Redis: só diz que o sidecar responde., Dispara um ciclo imediato de publicação de clipes aprovados., Roda yt-dlp em modo metadata-only e extrai id/name/handle. Padrão yt-dlp:…, Chama src.rejeitar.rejeitar(clip_id) diretamente. Preserva exit codes 0/1/2., reject_clip() (+15 more)

### Community 11 - "test_retention_collector.py"
Cohesion: 0.07
Nodes (58): main(), retention_backfill.py — carga retroativa da retenção (SPEC-001 R15). Rodado À…, _as_date(), _channel_has_budget(), _chunks(), _collect_channel(), collector_enabled(), _count_call() (+50 more)

### Community 12 - "TranscricaoLocal.tsx"
Cohesion: 0.06
Nodes (59): ChannelTemplateModal(), COLOR_PRESETS, Props, TemplateConfig, Niche, NicheCombobox(), slugify(), Button() (+51 more)

### Community 13 - "processar.py"
Cohesion: 0.10
Nodes (21): fetch_metadata(), main(), _normalize_upload_date(), parse_video_id(), processar.py — Ingestão manual de vídeo YouTube via comando /processar do…, Entrypoint CLI. Exit codes: - 0: OK (inserido ou já existia) - 2: URL inválida…, Extrai videoId de 11 caracteres de uma URL YouTube. None se URL inválida.…, Converte 'YYYYMMDD' (formato yt-dlp) para 'YYYY-MM-DD HH:MM:SS' (TIMESTAMP… (+13 more)

### Community 14 - "devDependencies"
Cohesion: 0.08
Nodes (25): concurrently, laravel-vite-plugin, oxlint, devDependencies, concurrently, laravel-vite-plugin, oxlint, tailwindcss (+17 more)

### Community 15 - "utils.ts"
Cohesion: 0.14
Nodes (18): Brand, BrandMark(), FALLBACK, ICONS, useBrand(), LoginForm(), InputGroup(), InputGroupAddon() (+10 more)

### Community 16 - "publisher.py"
Cohesion: 0.08
Nodes (30): Blacklist guard (source_channels.blacklisted), COPY-01: watermark queimado via FFmpeg, COPY-02: descrição inclui créditos do canal original, COPY-03: canais blacklistados bloqueados no RSS poller, credit_template / channel_handle credits, generated_clips.destination_channel_id FK, MCAN-01: múltiplos canais YouTube com OAuth próprio, MCAN-02: campo niche determina canal-destino (+22 more)

### Community 17 - "05-01 Plan: Publishing schema, skeletons and RED tests"
Cohesion: 0.09
Nodes (29): quota_manager.py — Limite diario e janela de horario para uploads YouTube.…, YouTubeUploader.upload_clip(clip), MAX_UPLOADS_PER_DAY clamped to <= 6, default 2, Migration Phase 3 usa INFORMATION_SCHEMA em vez de ADD COLUMN IF NOT EXISTS, Persistir arquivos renderizados no volume montado /app/videos, Raw source só removido quando todos clips do source video estão terminais, YOUTUBE_TOKEN_FILE (default /app/token.json), mysql/init/03-schema-migration.sql (+21 more)

### Community 18 - "Illuminate\Database\Eloquent\Factories\HasFactory"
Cohesion: 0.07
Nodes (17): Illuminate\Database\Eloquent\Factories\Factory, Illuminate\Database\Eloquent\Factories\HasFactory, AjudaCommand, AprovarCommand, ClipesCommand, ProcessarCommand, RejeitarCommand, StatusCommand (+9 more)

### Community 19 - "TestUploadClip"
Cohesion: 0.11
Nodes (12): make_youtube_mock(), token_file inexistente deve levantar FileNotFoundError., Se thumbnail_path existir, thumbnails().set() deve ser chamado., Cria um mock do serviço YouTube que simula upload bem-sucedido., Falha no upload da thumbnail customizada deve logar aviso e manter o vídeo…, Tags em formato string separado por vírgula devem virar lista., YOUTUBE_PRIVACY_STATUS do env deve ser usado no upload., Upload bem-sucedido deve retornar o youtube_video_id. (+4 more)

### Community 20 - "uploader.py"
Cohesion: 0.10
Nodes (17): Credentials, HttpError, MediaFileUpload, Exception, uploader.py — Upload de clips para YouTube Data API v3. Exporta: -…, RefreshError, RED test para captura de RefreshError e persistência de oauth_expired_flag…, RefreshError em creds.refresh() deve setar oauth_expired_flag=TRUE em… (+9 more)

### Community 21 - "metadata_generator.py"
Cohesion: 0.07
Nodes (36): Anthropic structured outputs via output_config json_schema, _build_prompt(), _contains_forbidden_title_label(), generate_metadata(), _generate_via_anthropic(), _generate_via_groq(), _is_original_source_title(), _log() (+28 more)

### Community 22 - "cut_clip"
Cohesion: 0.13
Nodes (11): _apply_youtube_thumbnail_graphics(), cut_clip(), extract_thumbnail(), _log(), Corta um trecho do vídeo fonte. fmt='curto' (padrão): converte pra vertical…, Extrai um frame do clip como thumbnail JPG e aplica tipografia de alto CTR…, Aplica tipografia profissional e efeito de nuvem de sombra de alto CTR estilo…, TestVideoProcessor (+3 more)

### Community 23 - "test_internal_api.py"
Cohesion: 0.08
Nodes (15): purge_old_videos(), Limpa vídeos fonte com published_at anterior a `before_date` (formato 'YYYY-MM-…, client(), fixture, RED tests for internal_api sidecar (implementação GREEN no Plan 08-07)., POST /internal/process-url com format='longo' repassa fmt='longo' pro…, POST /internal/process-url sem campo 'url' retorna 400., purge_old_videos apaga linhas sem clips e libera arquivo de linhas com clips… (+7 more)

### Community 24 - "is_seen"
Cohesion: 0.13
Nodes (15): is_seen(), _log(), mark_failed_redis(), dedup.py — Deduplicação de vídeos via Redis com fallback para MySQL. Exporta: -…, Loga mensagem com timestamp para stdout., Verifica se o vídeo já foi processado anteriormente. Consulta o Redis primeiro.…, Remove a chave do vídeo do Redis quando o download falha. Isso permite que o…, Testes ACQU-03: deduplicação via Redis com fallback para MySQL. Módulo alvo:… (+7 more)

### Community 25 - "transcribe_video"
Cohesion: 0.10
Nodes (19): _log(), _prepare_audio(), transcriber.py — Transcrição de vídeos via Groq Whisper API. Exporta: -…, Salva JSON de transcrição em disco e atualiza transcript_path no banco. Args:…, Extrai áudio MP3 de um arquivo de vídeo via ffmpeg. Args: video_path: caminho…, Divide áudio grande em partes de TRANSCRIPTION_CHUNK_SECONDS (mono, 16 kbit/s).…, Transcreve um vídeo via Groq Whisper API. Args: video_id: youtube_video_id do…, save_transcript() (+11 more)

### Community 26 - "DestinationChannel"
Cohesion: 0.13
Nodes (3): Illuminate\Database\Eloquent\Relations\HasMany, DestinationChannelController, DestinationChannel

### Community 27 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 28 - "docker-compose.yml (raiz wordpress/)"
Cohesion: 0.18
Nodes (13): ANTHROPIC_API_KEY intencionalmente vazia até Phase 3, clip-processor/Dockerfile, CLIP_PROCESSOR_INTERNAL_TOKEN env var, clip-processor service (build local), docker-compose.yml (raiz wordpress/), .env (secrets reais), n8n service (docker.n8n.io/n8nio/n8n:2.27.0), Pitfall: faster-whisper baixando modelo em cada restart (+5 more)

### Community 29 - "download_video"
Cohesion: 0.12
Nodes (17): _cleanup_partial(), download_video(), _log(), downloader.py — Download de vídeos YouTube via yt-dlp com disk guard e retry.…, Baixa um vídeo do YouTube em formato 720p mp4. Returns: True se download bem-…, Loga mensagem com timestamp para stdout., Deleta artefatos de trabalho do yt-dlp gerados por download incompleto. O glob…, is_paused() (+9 more)

### Community 30 - "Illuminate\Http\RedirectResponse"
Cohesion: 0.09
Nodes (7): Illuminate\Http\RedirectResponse, DashboardController, SourceVideoController, GeneratedClip, SourceVideo, ClipProcessorClient, Carbon

### Community 31 - "Plano — Prompts de IA editáveis pelo painel"
Cohesion: 0.05
Nodes (37): 10. Riscos e mitigação, 11. Fora de escopo neste plano, 1. Situação atual (verificada em 13/08/2026), 2. Versões confirmadas (regra `docs-first`), 3. Por onde o prompt deve trafegar — decisão, 4.1 `ai_prompts` — o *slot*, 4.2 `ai_prompt_versions` — histórico imutável, 4.3 `generated_clips.ai_prompt_version_id` (+29 more)

### Community 32 - "Offer"
Cohesion: 0.14
Nodes (3): PublishOffersToTelegram, OfferController, Offer

### Community 33 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 34 - "video_processor.py"
Cohesion: 0.10
Nodes (21): _build_clip_context(), _fetch_clip(), process_clip(), video_processor.py — Corte, legendas, thumbnail e processamento de clips.…, Corte + legenda + watermark do Short em uma única recodificação (padrão).…, Busca a imagem de background 1920x1080 do canal ou nicho., Processa um registro de generated_clips com status pending_cut. Pipeline: cut →…, Gera configuração padrão inteligente de template 9:16 baseada no nicho do canal. (+13 more)

### Community 35 - "Phase 1: Infraestrutura Base"
Cohesion: 0.26
Nodes (10): ACQU-01: Monitoramento RSS de canais, ACQU-02: Download automático 720p via yt-dlp, ACQU-03: Deduplicação Redis + MySQL UNIQUE, INFRA-01: Sistema roda em Docker, INFRA-02: Banco clips_automation com 3 tabelas, INFRA-03: Canal YouTube verificado, INFRA-04: Variáveis de ambiente e secrets, ORC-02: Status de cada job registrado no MySQL (+2 more)

### Community 36 - "Phase 7 Context: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.15
Nodes (17): rss_poller blacklist guard + target_niche SELECT extension, COPY-01 requirement: watermark burned into every clip, COPY-02 requirement: original channel credits in description, COPY-03 requirement: blacklisted channels never downloaded, Dual-layer blacklist guard pattern (SQL filter + Python loop guard), Graceful degradation pattern: return input unchanged when optional dependency missing, MCAN-01 requirement: OAuth token per destination channel, MCAN-02 requirement: destination_channel_id routing by niche (+9 more)

### Community 37 - "run_pipeline_once"
Cohesion: 0.10
Nodes (18): Executa RSS/download/AI/video e depois publicacao. Falhas isoladas sao logadas,…, run_pipeline_once(), Conexão injetada não deve ser fechada pelo runner (responsabilidade do caller)., Erro em publish_pending_clips não deve propagar — scheduler continua., Erro em poll_all_channels não deve impedir tentativa de publicação., Sem injeção, deve criar e fechar a própria conexão., Erro em _download_pending_videos não deve propagar., Deve chamar poll → download → publish em ordem. (+10 more)

### Community 38 - "TelegramHttpClientHandler.php"
Cohesion: 0.15
Nodes (8): GuzzleHttp\Promise\PromiseInterface, Illuminate\Support\ServiceProvider, AppServiceProvider, static, TelegramHttpClientHandler, Psr\Http\Message\ResponseInterface, Telegram\Bot\HttpClients\HttpClientInterface, Laravel Http adapter for SDK (enables Http::fake())

### Community 39 - "Plano mestre — estado, decisões e próximos passos"
Cohesion: 0.06
Nodes (35): 0. Situação apurada em 14/09/2026, 10. Pendente do usuário, 1. Advertência de direitos autorais — o assunto que bloqueia todo o resto, 2. Gate de licença — a correção estrutural, 3. Banco de dados — MySQL para PostgreSQL, 4. Infraestrutura — migrar para A1 Flex 12 GB, 5. Marca — Umbrella Solutions, 6. Afiliados (+27 more)

### Community 40 - "Offers.tsx"
Cohesion: 0.08
Nodes (28): CtaHint(), GenerateCopyButton(), OfferCopy, Source, Popover(), PopoverContent(), PopoverDescription(), PopoverHeader() (+20 more)

### Community 42 - "TestDownloadPendingVideos"
Cohesion: 0.18
Nodes (8): Cursor fake cujo fetchone e fetchall caem num default depois da lista informada., Download bem-sucedido deve atualizar status para downloaded com local_path., Download falho deve marcar failed já limpando local_path (libera a vaga)., Sem vídeos pending, não deve chamar download_video., Janela já cheia nos dois nichos não deve chamar download_video., Ordem fixa: repõe futebol primeiro, depois política., Importar main.py não deve iniciar o scheduler (coalesce = True verificado via…, TestDownloadPendingVideos

### Community 43 - "chart.tsx"
Cohesion: 0.16
Nodes (15): react, ChartConfig, ChartContainer(), ChartContext, ChartContextProps, ChartLegendContent(), ChartTooltipContent(), getPayloadConfigFromPayload() (+7 more)

### Community 44 - "SourceVideos.tsx"
Cohesion: 0.09
Nodes (27): Select(), SelectContent(), SelectGroup(), SelectItem(), SelectLabel(), SelectScrollDownButton(), SelectScrollUpButton(), SelectSeparator() (+19 more)

### Community 45 - "ARCHITECTURE.md (as-built, commit dca6e44)"
Cohesion: 0.18
Nodes (13): ARCHITECTURE.md (as-built, commit dca6e44), AI fallback chain (Claude → Groq → deterministic), niches table (only Laravel-migration-managed pipeline table), Quota, window and round-robin logic, source_videos.status state machine, CLAUDE.md — Canal de Cortes work instructions, Rules for destructive operations, metadata_generator.py Groq fallback fix (27/07/2026) (+5 more)

### Community 46 - "process_clip"
Cohesion: 0.11
Nodes (24): burn_subtitles(), clip-processor/src/metadata_generator.py, clip-processor/src/video_processor.py, clip-processor/tests/test_clip_pipeline.py, clip-processor/tests/test_metadata_generator.py, clip-processor/tests/test_video_processor.py, cut_clip(), extract_thumbnail() (+16 more)

### Community 47 - "dependencies"
Cohesion: 0.10
Nodes (21): class-variance-authority, clsx, @dnd-kit/utilities, @fontsource-variable/geist, dependencies, class-variance-authority, clsx, @dnd-kit/utilities (+13 more)

### Community 48 - "_process_ai_pipeline"
Cohesion: 0.17
Nodes (15): output_config json_schema em vez de prefill para Claude Haiku 4.5, generate_metadata(), insert_selected_moments(), Algoritmo de remoção de overlap por score, 03-CONTEXT.md: Phase 3 Context, _process_ai_pipeline(), _remove_overlaps(), AI-01: transcrição via Groq Whisper (+7 more)

### Community 49 - "YouTubeUploader"
Cohesion: 0.19
Nodes (7): _default_service_for(), Marca destination_channels.oauth_expired_flag=TRUE para o slug atual. Best-…, Self-healing: reseta oauth_expired_flag=FALSE após upload bem-sucedido., Cliente fino para videos.insert + thumbnails.set., YouTubeUploader, Multi-canal extension via optional constructor param + None-guard retrocompat, Publisher legacy fallback when destination_channels empty

### Community 50 - "scripts"
Cohesion: 0.13
Nodes (15): scripts, dev, post-autoload-dump, post-create-project-cmd, post-update-cmd, pre-package-uninstall, Composer\\Config::disableProcessTimeout, Illuminate\\Foundation\\ComposerScripts::postAutoloadDump (+7 more)

### Community 51 - "painel/README.md (setup fresh 10 passos)"
Cohesion: 0.25
Nodes (8): Filament removal commit dca6e44, painel/ — Laravel 13 + Inertia 3 + React 19 (Filament removed), clip-processor/requirements.txt, painel/README.md (setup fresh 10 passos), YouTube OAuth authorization CLI flow (youtube_oauth.py), Filament 5.x version choice (not 3), PROJECT_BRIEF.md — Canal de Cortes as-built brief, README.md (root, outdated Filament references)

### Community 52 - "clip-processor/src/transcriber.py"
Cohesion: 0.15
Nodes (14): clip-processor/src/selector.py, clip-processor/src/transcriber.py, clip-processor/tests/test_selector.py, clip-processor/tests/test_transcriber.py, Groq Whisper whisper-large-v3-turbo + verbose_json + timestamp_granularities segment + pt, mysql/init/03-schema-migration.sql, 03-01-PLAN.md: Wave 0 skeletons + RED tests, 03-01-SUMMARY.md: Wave 0 Summary (+6 more)

### Community 53 - "composer.json"
Cohesion: 0.14
Nodes (13): autoload-dev, psr-4, description, keywords, license, minimum-stability, name, prefer-stable (+5 more)

### Community 54 - "_select_pending_videos"
Cohesion: 0.15
Nodes (16): _active_source_channels(), Seleciona vídeos pendentes pra repor a janela de download ativo por nicho. Para…, Quantos canais de origem ativos o nicho tem — base do teto por canal., _select_pending_videos(), Bug 17 — decisão registrada: a ocupação da janela CONTA clip em 'pending'. Clip…, _sqls_de_ocupacao(), test_ocupacao_conta_clip_pending_e_estados_ativos(), Testes para _select_pending_videos — janela por nicho e justiça por canal. (+8 more)

### Community 55 - "mysql/init/01-clips-schema.sql"
Cohesion: 0.24
Nodes (12): mysql/init/01-clips-schema.sql, db.py: quem chama é responsável por fechar a conexão, clip-processor/src/db.py, generated_clips table, INSERT IGNORE para idempotência de vídeos/canais, 01-02-PLAN: Schema SQL clips_automation e validate-infra.sh, 02-02-PLAN: docker-compose + requirements + seed + db.py, 02-02-SUMMARY: db.py GREEN, seed 5 canais (+4 more)

### Community 56 - "Illuminate\Http\Request"
Cohesion: 0.06
Nodes (18): Closure, Illuminate\Foundation\Configuration\Middleware, Illuminate\Http\JsonResponse, Illuminate\Http\Request, Illuminate\Http\Response, Inertia\Middleware, OfferApiController, AuthController (+10 more)

### Community 57 - ".planning/research/PITFALLS.md"
Cohesion: 0.20
Nodes (9): n8n 06-router.json deactivation, QuotaManager per-channel Redis key design, Pitfall: Blacklist Check Happens Too Late in the Pipeline, Pitfall: Filament Delete Button Deletes MySQL Row Without Deleting Files, Pitfall: Laravel Writes Conflict with Python Pipeline Mid-Transaction, Pitfall: n8n Still Running Telegram Bot in Parallel After Migration, Pitfall: OAuth App in Testing Mode Breaks Weekly, Pitfall: Quota Cega — shared GCP project quota (+1 more)

### Community 58 - ".planning/research/FEATURES.md"
Cohesion: 0.20
Nodes (9): irazasyed/telegram-bot-sdk ^3.16, burn_watermark() function design, Admin Panel (Laravel/Filament) feature spec, Copyright Protection feature spec, Multi-Channel YouTube Publishing feature spec, OAuth testing-mode token expiry warning (7 days), Telegram Bot in Laravel feature spec, Laravel 13 version choice (not 11) (+1 more)

### Community 59 - "cn"
Cohesion: 0.04
Nodes (87): affiliateItems, AppSidebar(), clipItems, NavItem, resolveWorkspace(), SidebarItem, WORKSPACES, NavUser() (+79 more)

### Community 60 - "internal_api.py sidecar (Flask, port 8090)"
Cohesion: 0.20
Nodes (11): APScheduler jobs (ingest_cycle, publish_cycle, clip_pending_ttl), Boundary rule: painel reads directly, writes via sidecar, clip-processor service (as-built), internal_api.py sidecar (Flask, port 8090), CLIP_PROCESSOR_INTERNAL_TOKEN shared setup, Telegram Command classes (Status/Clipes/Aprovar/Rejeitar/Processar/Ajuda), Pitfall: Python→Laravel via wrong Host header (404), POST /internal/pipeline-event (Laravel endpoint) (+3 more)

### Community 61 - "validate-phase6-n8n.py"
Cohesion: 0.53
Nodes (10): assert_contains(), assert_has_node(), load_json(), main(), nodes_by_name(), Path, validate_cron(), validate_docs() (+2 more)

### Community 62 - "test_transcription_worker.py"
Cohesion: 0.08
Nodes (13): fixture, Testes da transcrição multiplataforma feita pelo worker do Mac. Rodar: python3…, Os testes nunca chamam o indexador real (modelo/rede): ligado só nos testes que…, Sem isso o Cloudflare do Groq devolve 403 'error code: 1010'., Nenhum teste lê ou grava o ~/.config/canaldecortes/media-urls.json de verdade., _sem_indexador_real(), _sem_media_urls_real(), TestArgumentosHls (+5 more)

### Community 63 - "clip-processor/src/rss_poller.py"
Cohesion: 0.27
Nodes (11): _cleanup_partial() chamado fora do loop de retry, clip-processor/src/dedup.py, clip-processor/src/dedup.py, Dedup pattern: Redis NX → fallback MySQL → False, download_video(video_id, output_path), clip-processor/src/downloader.py, is_seen(video_id, redis_client, db_conn), 02-03-PLAN: dedup.py, downloader.py, rss_poller.py (+3 more)

### Community 64 - "overlay_watermark"
Cohesion: 0.07
Nodes (26): append_credits(), Adiciona linha de créditos ao final da descrição. Nunca sobrescreve conteúdo…, overlay_watermark(), Aplica watermark PNG no canto superior direito do clip via FFmpeg. Usa…, generate_token(), main(), Helper CLI para gerar token OAuth YouTube por canal-destino. Uso: python -m…, Gera token OAuth para o canal-destino e salva em… (+18 more)

### Community 65 - "conftest.py"
Cohesion: 0.24
Nodes (10): mock_db_conn(), mock_redis(), fixture, Fixtures compartilhadas para todos os testes do clip-processor. Fornece:…, MagicMock simulando redis.Redis. - .set() retorna True por padrão (NX success —…, MagicMock simulando conexão pymysql com suporte a context manager em cursor().…, Feed RSS Atom do YouTube com 2 entradas válidas. VideoIds: 'abc123def456' e…, ID de vídeo YouTube válido (11 caracteres). (+2 more)

### Community 66 - "Backlog de bugs"
Cohesion: 0.09
Nodes (22): 10. ABERTO — 287 clips com `clip_path` apontando para arquivo inexistente, 11. FEITO — Container não honrava SIGTERM, todo `docker stop` virava SIGKILL, 12. FEITO — Worker local de download ignorava a janela, 13. FEITO — Rejeitar no painel não apagava os arquivos do clip, 14. FEITO — Usuários de teste com senha padrão no banco de produção, 15. FEITO — Groq recusava toda seleção com 429, 16. ABERTO — Senha de root do MySQL publicada em repositório público, 17. FEITO (por decisão) — Vaga da janela presa por clip aguardando aprovação (+14 more)

### Community 67 - "publisher.py"
Cohesion: 0.15
Nodes (18): clip_format_sql(), Expressão SQL do formato do clip: `generated_clips.format` (fonte da verdade)…, Handle a usar no crédito: prioriza @handle real; cai para o nome do canal fonte…, resolve_credit_handle(), _fetch_pending_clips(), _has_longo_waiting(), _mark_clip_failed(), _mark_clip_published() (+10 more)

### Community 68 - "active-window-table.tsx"
Cohesion: 0.12
Nodes (22): ActiveWindowTable(), postAction(), SortableRow(), STATUS_LABEL, useSelection(), VideoActions(), VideoCells(), VideoTable() (+14 more)

### Community 69 - "test_video_processor.py"
Cohesion: 0.11
Nodes (14): burn_subtitles(), _format_srt_time(), generate_srt(), Gera arquivo SRT relativo ao início do clip a partir dos segmentos Whisper., Queima legendas SRT no clip usando FFmpeg., _encadeamento_legado(), fixture, test_video_processor.py — Testes Phase 4 VID-01, VID-02, VID-03. Estado inicial… (+6 more)

### Community 70 - "require-dev"
Cohesion: 0.18
Nodes (11): require-dev, fakerphp/faker, larastan/larastan, laravel/pail, laravel/pao, laravel/pint, mockery/mockery, nunomaduro/collision (+3 more)

### Community 71 - "02-04-PLAN.md: Daemon main.py Plan"
Cohesion: 0.20
Nodes (10): 02-04-PLAN.md: Daemon main.py Plan, 02-04-SUMMARY.md: Daemon main.py Summary, 02-CONTEXT.md: Phase 2 Context, 02-RESEARCH.md: Phase 2 Research, 02-VALIDATION.md: Phase 2 Validation Strategy, pytest test infra (Phase 2 Wave 0), ACQU-01: monitorar canais via RSS a cada 6h, ACQU-02: baixar vídeos novos em 720p via yt-dlp (+2 more)

### Community 72 - ".planning/research/ARCHITECTURE.md (v2.0 research, superseded)"
Cohesion: 0.29
Nodes (8): Dead code: painel/app/Filament/Pages/Dashboard.php orphan, env() outside config() pitfall in DashboardController, Section 10: Known divergences and technical debt, channel_blacklist table (research design), destination_channels table (research design), Phase 7: Schema Multi-Canal + Watermark + Copyright (research plan), Phase 8: Laravel/Filament Painel Base (research plan), .planning/research/ARCHITECTURE.md (v2.0 research, superseded)

### Community 73 - "Sistema — IA de seleção de cortes"
Cohesion: 0.06
Nodes (31): 1. Confirmar qual provider respondeu, 1. Qual IA, e por quê, 2. Confirmar as keys dentro do container, 2. Os prompts, na íntegra, 3. Palavras-chave e frases-chave, por formato, 3. Ver o filtro de 30s agindo, 4. Conferir a duração dos clips no banco, 4. Regras de duração (+23 more)

### Community 74 - "pipeline_runner.py"
Cohesion: 0.11
Nodes (22): _clips_need_raw(), _discard_failed_download(), _download_pending_videos(), _log(), pipeline_runner.py — Uma execucao completa do pipeline. Usado pelo daemon e…, Diz se algum clip desse vídeo ainda precisa do arquivo bruto em disco.…, Marca o download como 'failed' e libera a vaga que ele ocupava na janela. Antes…, Verifica vídeos na janela ativa cujo arquivo não existe mais em disco e limpa. (+14 more)

### Community 75 - "02-01-PLAN: pytest scaffold RED state (Wave 0)"
Cohesion: 0.33
Nodes (9): clip-processor/tests/conftest.py, 02-01-PLAN: pytest scaffold RED state (Wave 0), 02-01-SUMMARY: 17 testes RED criados, clip-processor/pytest.ini, TDD RED-GREEN-REFACTOR pattern (imports no topo causam ModuleNotFoundError), tests/test_db.py, tests/test_dedup.py, tests/test_downloader.py (+1 more)

### Community 76 - "insert_selected_moments"
Cohesion: 0.07
Nodes (19): insert_selected_moments(), _lookup_destination_channel_id(), Remove momentos sobrepostos, mantendo o de maior score. Retorna no máximo…, Resolve destination_channel_id via JOIN source_videos → source_channels →…, Filtra momentos com score >= 7 e insere em generated_clips. clip_format: None…, _remove_overlaps(), test_selector.py — Testes unitários para selector.py (AI-02, AI-03). Estado…, AI-03: Momento com score=7 é inserido em generated_clips com status pending_cut. (+11 more)

### Community 77 - "main.py"
Cohesion: 0.08
Nodes (32): get_db_connection(), Abre conexão com o banco de dados (MySQL ou PostgreSQL) usando variáveis de…, _hard_exit(), install_signal_handlers(), log(), pipeline_enabled(), Executa o ciclo de integridade e auto-cura do Watchdog., Registra os handlers e a thread vigia (vale já durante o ciclo inicial). (+24 more)

### Community 78 - "_seg"
Cohesion: 0.06
Nodes (15): fake_embed(), FakeDb, FakeRemote, _fala(), parametrize, Testes do indexador de transcrições (chunker, SRT, SQL, backfill). Sem rede nem…, n segmentos consecutivos de `tamanho` caracteres, `passo` segundos cada., Banco de mentira do backfill: ids e a fonte de cada job. (+7 more)

### Community 79 - "FakeDb"
Cohesion: 0.11
Nodes (17): column_exists(), generated_clips_has_format(), get_long_format_mode(), _log(), normalize_mode(), format_mode.py — modo de formato longo por canal destino…, Valor desconhecido, NULL ou vazio → 'auto'., True se a coluna existe no schema atual. Só cacheia o positivo (a migration… (+9 more)

### Community 80 - "Phase 9-04 Plan: Telegram Bot Checkpoint"
Cohesion: 0.33
Nodes (9): PipelineEventTest.php, setWebhook registration to https://alessandromelo.com.br/telegramcanal, Phase 9-04 Plan: Telegram Bot Checkpoint, TelegramCommandsTest.php, TelegramWebhookTest.php, Artisan Schedule daily summary 18h BRT, Phase 9 Research: Bot Telegram no Laravel, Phase 9 Validation Strategy (+1 more)

### Community 81 - "Phase 7: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.25
Nodes (7): Bot Telegram no Laravel (v2), Groq Whisper (API) em vez de Whisper local, Multi-canal com token OAuth por canal, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 8: Painel Laravel/Filament, Phase 9: Bot Telegram no Laravel, recover_stuck_downloads só recupera 'downloading' → 'pending'

### Community 82 - "01-RESEARCH.md"
Cohesion: 0.14
Nodes (14): CLIPS_DB_PASSWORD como placeholder no SQL, youtube/generate_token.py, N8N_ENCRYPTION_KEY via ${VAR} nunca hardcoded, n8n usa SQLite default (não MySQL), OAuth app type 'installed' (Desktop App), não 'web', OAuth app publicado em Production, Pitfall: N8N_ENCRYPTION_KEY não definida antes do primeiro boot, Pitfall: n8n MySQL Deprecation Confusion (+6 more)

### Community 83 - "config"
Cohesion: 0.22
Nodes (9): pestphp/pest-plugin, php-http/discovery, config, allow-plugins, optimize-autoloader, platform, preferred-install, sort-packages (+1 more)

### Community 84 - "require"
Cohesion: 0.29
Nodes (7): require, inertiajs/inertia-laravel, irazasyed/telegram-bot-sdk, laravel/framework, laravel/tinker, php, tightenco/ziggy

### Community 85 - "local_download_worker.py"
Cohesion: 0.09
Nodes (44): acquire_pid_lock(), active_source_channels(), _corte_frescor(), count_window_occupancy(), download_video_locally(), fetch_pending_videos(), get_video_duration(), _guardar_aula_kwargs() (+36 more)

### Community 86 - "cli.py"
Cohesion: 0.09
Nodes (21): build_parser(), cmd_copy(), cmd_import(), cmd_run(), cmd_search(), info(), _label(), main() (+13 more)

### Community 87 - "destination_channels table"
Cohesion: 0.33
Nodes (6): destination_channels table, Migration idempotente via INFORMATION_SCHEMA + prepared statement, 06-multi-canal-migration.sql, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 7 — Validation Strategy, pytest test framework (clip-processor)

### Community 88 - "_client"
Cohesion: 0.06
Nodes (28): BaseModel, create_app(), EmbedRequest, Sidecar de embeddings (FastAPI) — só a rede interna do compose, sem porta…, add_prefix(), embed(), Embedder, EmbedderError (+20 more)

### Community 89 - "clip-processor/src/downloader.py"
Cohesion: 0.40
Nodes (5): clip-processor/src/downloader.py, Guard de espaço em disco antes do download (<2GB), Retry de download: 3x com 60s entre tentativas, Extração de áudio ffmpeg para arquivos >24MB, _prepare_audio()

### Community 90 - "Illuminate\Console\Command"
Cohesion: 0.13
Nodes (6): Illuminate\Console\Command, BackupDatabaseCommand, CreatePainelUser, IndexarTranscricoes, ResetPainelPassword, RestoreDatabaseCommand

### Community 91 - "TestDiscardFailedDownload"
Cohesion: 0.25
Nodes (6): Download falho não pode deixar arquivo em disco nem local_path preenchido. A…, Arquivo parcial em disco é apagado ANTES do UPDATE, e local_path vira NULL., Sem arquivo em disco (falha antes de escrever nada), segue e limpa a coluna., Se o arquivo sobrevive à remoção, não limpa local_path — banco não divergir do…, Clip em pending_cut/cutting ainda lê o raw — não apaga nem zera local_path., TestDiscardFailedDownload

### Community 92 - "User"
Cohesion: 0.04
Nodes (21): Filament\Models\Contracts\FilamentUser interface, Illuminate\Foundation\Auth\User, Illuminate\Foundation\Testing\DatabaseTransactions, Illuminate\Foundation\Testing\TestCase, Illuminate\Notifications\Notifiable, ResetPainelPassword artisan command, User, static (+13 more)

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

### Community 103 - "_clip"
Cohesion: 0.12
Nodes (11): _clip(), _conn(), _inserts(), _limpa_estado(), fixture, Coleta de métricas: lotes de 50, falha de API, clip sem video_id e frequência., YouTube falso: videos().list(...).execute() devolve statistics dos ids pedidos., _service() (+3 more)

### Community 109 - "Sistema de Alertas, Monitoramento e Watchdog"
Cohesion: 0.10
Nodes (21): 1. Visão Geral, 2. Camada 1: Better Stack (Uptime, Heartbeat e Incidentes), 3. Camada 2: Sentry (Erros de Código e Runtime), 4.1. Auto-Cura de Clipes Fantasmas (`check_ghost_clips`), 4.2. Monitor de Deadlock da Janela de Download (`check_download_window_health`), 4.3. Monitor de Fila Ociosa (`check_approval_queue_activity`), 4.4. Validador Prévio de OAuth (`check_youtube_tokens`), 4.5. Monitor de Armazenamento SSD (`check_disk_space`) (+13 more)

### Community 110 - "_maybe_finalize_source_video"
Cohesion: 0.19
Nodes (13): finalize_settled_source_videos(), _log(), _maybe_finalize_source_video(), Encerra o vídeo fonte quando todos os clips dele chegaram a estado terminal.…, Encerra vídeos em 'selecting' cujos clips estão todos em estado terminal.…, make_conn(), Bug 17 — vídeo em 'selecting' com todos os clips em estado terminal…, pending_cut/cutting contam como não-terminal: raw fica, vaga fica. (+5 more)

### Community 111 - "Fases"
Cohesion: 0.11
Nodes (19): 1. Não fazer upgrade para Pay As You Go (a camada que realmente importa), 2. Provisionar só recursos com o selo "Always Free-eligible", 3. Orçamento com alerta em US$ 1, 4. Conferência após provisionar, Como o custo zero é garantido, Decisão tomada, Depois da migração, Fase 0 — Conta e blindagem de cobrança  ⬜ NÃO INICIADA (+11 more)

### Community 112 - "rules"
Cohesion: 0.05
Nodes (42): categories, correctness, perf, suspicious, env, browser, es2024, ignorePatterns (+34 more)

### Community 113 - "notify"
Cohesion: 0.13
Nodes (17): notify(), telegram_notifier.py — Cliente HTTP que publica eventos do pipeline para o…, POST para LARAVEL_NOTIFY_URL com {event, payload}. Retorna True em 2xx, False…, Testes para telegram_notifier.py — cliente HTTP que dispara eventos para o…, notify() captura RequestException e retorna False sem propagar., notify() retorna False quando o endpoint retorna 4xx., notify() faz POST para LARAVEL_NOTIFY_URL — RED até Plan 09-03. Importa…, notify() inclui header Host para nginx routing — RED até Plan 09-03. (+9 more)

### Community 114 - "rejeitar"
Cohesion: 0.15
Nodes (17): internal_api.reject_clip(clip_id) — calls src.rejeitar.rejeitar directly, _clip_artifacts(), rejeitar.py — Rejeição manual de clip via comando /rejeitar do Telegram…, Arquivos em disco de um clip. Só clip_path e thumbnail_path ficam no banco;…, Marca o clip como rejected, remove os artefatos do clip, preserva raw video.…, rejeitar(), Testes para rejeitar.py — comando /rejeitar do Telegram. Estado RED até Plan…, rejeitar(123): executa UPDATE generated_clips SET status='rejected' WHERE… (+9 more)

### Community 117 - "BuscaTranscricoes.tsx"
Cohesion: 0.13
Nodes (21): BuscaTranscricoes(), MODOS, decodificar(), ENTIDADES, formatarTempo(), LinkDoTrecho(), partesDoSnippet(), ResultadoBusca() (+13 more)

### Community 118 - "transcript_indexer.py"
Cohesion: 0.10
Nodes (33): backfill(), build_chunks(), build_index_sql(), Chunk, chunk_segments(), chunk_text_only(), _dollar_quote(), _embed_all() (+25 more)

### Community 119 - "Sistema — `painel/`"
Cohesion: 0.12
Nodes (17): A regra da fronteira, Armadilhas conhecidas, Autenticação, Banco, Canais e Estúdio de Templates, Comandos Artisan do Painel, Como ler o Dashboard, Dashboard — `DashboardController` (+9 more)

### Community 120 - "Runbook de operação"
Cohesion: 0.12
Nodes (17): Backup antes de DELETE em massa, Comandos do painel, Convenções, Diagnosticar falhas de upload, Espaço em disco, Estado preso sem recuperação automática, Está tudo de pé?, Nada sobe para o YouTube (+9 more)

### Community 121 - "captura.js"
Cohesion: 0.18
Nodes (13): cabecalho(), capturaDe(), ehPlaylist(), escolher(), exigeCaptura(), hostDe(), hostPermitido(), prioridade() (+5 more)

### Community 122 - "Quick Task 1: Transcrição Local Summary"
Cohesion: 0.15
Nodes (12): Accomplishments, Auto-fixed Issues, Decisions Made, Deviations from Plan, Files Created/Modified, Issues Encountered, Next Phase Readiness, Performance (+4 more)

### Community 123 - "Publicação no YouTube"
Cohesion: 0.11
Nodes (19): Coleta de métricas (views) e tela "Métricas", Cota diária e janela horária, Fallback legado, Finalização do vídeo fonte, Guard de corrida com a rejeição, Janela horária, Limites, OAuth por canal-destino (+11 more)

### Community 124 - "test_local_download_worker.py"
Cohesion: 0.09
Nodes (21): FakeRemote, fixture, Testes da janela de download do local_download_worker. Rodar: python3 -m pytest…, 10 vagas livres, 2 canais de origem ativos: teto de 5 por canal, intercalando., Responde às queries do worker: contagem da janela e lista de pendentes., test_abaixo_do_teto_baixa_normalmente(), test_busca_so_o_deficit_de_cada_nicho(), test_canal_destino_novo_soma_dez() (+13 more)

### Community 125 - "has_burned_subtitles"
Cohesion: 0.11
Nodes (19): detection_enabled(), has_burned_subtitles(), _log(), subtitle_detector.py — Detecta legenda já queimada no vídeo-fonte. Exporta: -…, Extrai o rodapé do quadro em `moment` e devolve o texto lido pelo OCR., Palavras da transcrição faladas em torno de `moment`., Normaliza o texto e devolve as palavras longas o bastante para comparar., Detecção é opt-in (BURNED_SUBTITLE_DETECTION=true): exige tesseract na imagem e… (+11 more)

### Community 135 - "adr/README.md"
Cohesion: 0.06
Nodes (29): ADR-0002 — Compose isolado por projeto (proposta não adotada), Alternativas consideradas, Consequências, Contexto, Decisão, ADR-0003 — A fila mora no banco; Redis guarda só dedup, cota e idempotência, Consequências, Contexto (+21 more)

### Community 143 - "test_prompt_profiles.py"
Cohesion: 0.13
Nodes (26): apply_profile_layer(), _first_value(), load_profile_for_source_video(), _normalise_aliases(), profile_from_row(), profile_matches_niche(), profile_prompt(), Helpers para transportar perfis de prompt do PostgreSQL até os providers de IA.… (+18 more)

### Community 144 - "validate_short_media"
Cohesion: 0.14
Nodes (14): Any, MediaContractError, probe_media(), Contrato técnico da mídia publicada como YouTube Short. Reconciliação com a…, Teto de duração do Short (env ``SHORTS_MAX_DURATION_SECONDS``, padrão 180)., Arquivo de mídia não atende ao contrato de publicação., Lê duração e dimensões do arquivo usando o ffprobe disponível no worker., Valida o arquivo final de um Short: vertical 9:16 e duração dentro dos limites. (+6 more)

### Community 150 - "Path"
Cohesion: 0.21
Nodes (13): groq_transcribe(), guardar_aula(), guardar_aula_ligado(), load_groq_key(), _probe_duration(), Path, Variável do ambiente ou do .env do projeto (que nunca vai ao git)., TRANSCRICAO_GUARDAR_AULA=1 guarda a aula; qualquer outra coisa apaga. (+5 more)

### Community 151 - "Banco de dados — `clips_automation`"
Cohesion: 0.12
Nodes (17): 1. Backup Automatizado (`db:backup`), 2. Restauração e Smoke Test (`db:restore`), Acesso, Banco de dados — `clips_automation`, `destination_channels`, Divergência banco × disco (bug aberto), Evolução das Migrations do Laravel, `generated_clips` (+9 more)

### Community 152 - "Mapa dos módulos"
Cohesion: 0.09
Nodes (22): Aquisição — [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md), Base, Configuração, Duração do Short: reconciliação com a regra da master, Editar código: hoje basta reiniciar, Inteligência — [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md), [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md), Interface com o painel — [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md), Mapa dos módulos (+14 more)

### Community 153 - "Descoberta e download"
Cohesion: 0.12
Nodes (17): Artefatos em disco, `_cleanup_partial` — por download (no `except`), `cleanup_stale_downloads` — varredura de órfãos, Dedup, Descoberta e download, Descoberta via RSS, Detecção de formato, `_discard_failed_download` (13/08/2026) (+9 more)

### Community 154 - "Offer"
Cohesion: 0.07
Nodes (26): _blank_to_none(), chunked(), is_http_url(), Offer, Modelo Offer e validação local espelhando o contrato de POST /api/offers. A…, Normaliza tipos vindos de CSV (tudo string). Valor inválido é mantido para a…, Chave de deduplicação local (mesma lógica de upsert do servidor quando há…, Retorna lista de erros (vazia = válido para push). (+18 more)

### Community 156 - "metrics_collector.py"
Cohesion: 0.21
Nodes (19): _as_utc(), _channel_has_budget(), _chunks(), _collect_channel(), collector_enabled(), _count_call(), _fetch_candidates(), _insert_metrics() (+11 more)

### Community 157 - "test_watchdog.py"
Cohesion: 0.17
Nodes (11): check_ghost_clips(), check_youtube_tokens(), Verifica se todos os canais destino ativos possuem arquivo de credencial OAuth…, Executa o ciclo completo de monitoramento do Watchdog., Identifica e cura clipes que perderam seus arquivos no disco: 1. Clipes em…, run_watchdog_cycle(), test_watchdog.py — Testes unitários para o módulo watchdog.py (monitoramento e…, TestCheckGhostClips (+3 more)

### Community 158 - "transcription_worker.py"
Cohesion: 0.14
Nodes (18): Cancelado, dollar_quote(), _done_sql(), _failed_sql(), format_srt_time(), merge_chunks(), process_one_job(), _progress_sql() (+10 more)

### Community 159 - "v1.0 — Pipeline Base"
Cohesion: 0.53
Nodes (6): v1.0 — Pipeline Base, MANUAL_APPROVAL_REQUIRED toggle, Phase 3: IA — Transcrição e Seleção, Phase 4: Processamento de Vídeo, Phase 5: Publicação e Automação Total, Phase 6: Controle Manual N8N + Telegram

### Community 160 - "Docs/sistema — como o sistema funciona"
Cohesion: 0.29
Nodes (7): As três armadilhas que pegam todo mundo, Como atualizar estes documentos, Docs/sistema — como o sistema funciona, Documentos desta pasta, O que o sistema é, em um parágrafo, Painel, dados, observabilidade e negócio, Pipeline (o robô)

### Community 161 - "Plano — vídeo longo automático, escolhido por canal"
Cohesion: 0.12
Nodes (16): Coleta de métrica (nova), Como é hoje (`master`), Cuidado com o strike, Decisões do dono (01/10/2026), Decisões em aberto (do dono), Decisões fechadas (01/10/2026), Disco: o que realmente limita (medido em 01/10/2026), Estado da implementação (01/10/2026) (+8 more)

### Community 162 - "Inertia\Response"
Cohesion: 0.10
Nodes (10): Inertia\Response, AssistantController, DocumentationController, MetricsController, NicheController, ProcessVideoController, SourceChannelController, UsefulLinksController (+2 more)

### Community 163 - "Gitflow do Canal de Cortes"
Cohesion: 0.25
Nodes (7): Branches de trabalho, Branches permanentes, Ciclo de uma tarefa, Estado das branches (17/09/2026), Gitflow do Canal de Cortes, Mensagem de commit, Regras que não se negociam

### Community 164 - "Passo a passo"
Cohesion: 0.17
Nodes (11): 1. Conferir a branch, 2. Testes da branch, 3. Documentação e grafo, ainda na branch, 4. Merge na master, 5. Push para o GitHub, 6. Deploy, 7. Conferir a versão no ar, 8. Relatório (+3 more)

### Community 165 - "fair_pick"
Cohesion: 0.24
Nodes (8): fair_pick(), fair_queue.py — Justiça por canal de origem na fila de download. A janela de…, Escolhe até `deficit` vídeos intercalando canais de origem. Devolve os próprios…, _c(), _ids(), Testes da escolha justa de vídeos por canal de origem na fila de download., Canal com menos vagas ocupadas continua na frente, mesmo com prioridade menor., TestFairPick

### Community 166 - "compile_prompt_profiles.py"
Cohesion: 0.18
Nodes (20): _prompts_dir(), Compilador de camadas YAML (scripts/compile_prompt_profiles.py)., test_canal_sem_alvo_longo_e_rejeitado(), test_compila_canal_valido_com_as_tres_camadas(), test_sem_canais_nao_gera_nada(), test_yaml_invalido_da_erro_claro(), apply_to_db(), compile_all() (+12 more)

### Community 168 - "Guia de Deploy Rápido (Produção)"
Cohesion: 0.13
Nodes (14): 1. Deploy Padrão (~20 a 25 segundos), 2. Deploy Ultrarrápido Backend (~8 a 12 segundos), 3. Deploy com Rebuild do Docker (Apenas quando estritamente necessário), A Solução Definitiva, ⚡ Como Fazer Deploy, Guia de Deploy Rápido (Produção), 🌐 Informações do Servidor de Produção, 🔧 Modo manutenção durante o deploy (18/09/2026) (+6 more)

### Community 169 - "test_video_render.py"
Cohesion: 0.19
Nodes (13): audio_encoder_options(), dynamic_audio_filter(), loudnorm_enabled(), Opções de encode dos vídeos publicados (modos de render). O YouTube reprocessa…, Filtro de áudio: loudnorm (-14 LUFS) + fade in/out curtos contra estalo de…, video_encoder_options(), video_render_mode(), _env_limpo() (+5 more)

### Community 171 - "TranscriptionJob"
Cohesion: 0.20
Nodes (4): TranscriptionController, TranscriptionJob, transcricaoPronta(), Symfony\Component\HttpFoundation\StreamedResponse

### Community 172 - "Pipeline e scheduler"
Cohesion: 0.18
Nodes (11): Armadilha recorrente: editar código não muda nada sem rebuild, Conexões, Entrypoint, Jobs agendados, O que cada ciclo executa, Onde mexer, Pipeline e scheduler, `run_ingest_cycle` (20 min) (+3 more)

### Community 173 - "_fetch_pending_clips_for_channel"
Cohesion: 0.15
Nodes (11): _fetch_destination_channels(), _fetch_pending_clips_for_channel(), Retorna canais-destino ativos de destination_channels., Retorna clips prontos para publicar filtrados por canal-destino. Faz fairness…, Reordena clips (já em ordem created_at ASC) intercalando por source_channel_id,…, _round_robin_by_source_channel(), Testes RED para roteamento multi-canal no publisher (MCAN-02, MCAN-04)., MCAN-02: _fetch_pending_clips_for_channel filtra por destination_channel_id.… (+3 more)

### Community 174 - "Sidecar HTTP e controles de fila"
Cohesion: 0.20
Nodes (10): A regra, As duas rotas que apagam, Caminho inverso: eventos para o Telegram, Controles de fila, `delete_source_video_file` — só disco, `purge_old_videos` — apaga linha, Rede e autenticação, Rejeição de clip (+2 more)

### Community 175 - "Corte e pós-produção de vídeo"
Cohesion: 0.18
Nodes (11): Abortar um corte em andamento, Artefatos em disco, Buraco que sobra, Corte e pós-produção de vídeo, Corte por formato, Legendas, Marca d'água, Metadata do clip (+3 more)

### Community 176 - "MediaAsset"
Cohesion: 0.13
Nodes (11): POST /internal/resolve-channel (sidecar endpoint), Filament Resource GET/HEAD-only routing pattern, Illuminate\Support\Facades\Storage, App\Filament\Resources\SourceChannelResource, CreateSourceChannel Page, MediaAssetController, MediaAsset, routes/web.php POST/PATCH source-channels REST routes (+3 more)

### Community 177 - "test_cli.py"
Cohesion: 0.12
Nodes (22): ApiClient, ApiError, BatchResult, _parse_422(), Exception, Cliente HTTP de POST /api/offers. - Lotes de até 100 itens. - Retry com backoff…, Envia em lotes. 401/503 persistente interrompem (ApiError); 422/outros seguem…, Erro que interrompe o push inteiro (401, 503 persistente, configuração). (+14 more)

### Community 178 - "FakeSession"
Cohesion: 0.21
Nodes (21): FakeResponse, FakeSession, Session que devolve respostas em sequência (ou exceções) e grava as chamadas., client(), items(), test_200_e_header_bearer(), test_401_sem_retry(), test_422_sem_retry_mapeia_erros_e_segue_proximo_lote() (+13 more)

### Community 179 - "Illuminate\Database\Eloquent\Model"
Cohesion: 0.18
Nodes (6): Illuminate\Database\Eloquent\Model, Illuminate\Database\Eloquent\Relations\BelongsTo, OfferPerformanceController, OfferRedirectController, OfferClick, TranscriptChunk

### Community 180 - "extensao_api.py"
Cohesion: 0.16
Nodes (18): HTTPServer, cookie_to_netscape(), handle_transcrever(), _host_permitido(), make_server(), media_hosts(), merge_cookies(), _origem_permitida() (+10 more)

### Community 181 - "Estados e transições do pipeline"
Cohesion: 0.29
Nodes (7): A terceira query (`local_path IS NULL` → `failed`), `cutting` e `publishing` em `source_videos`: valores mortos, Estados e transições do pipeline, `generated_clips.status`, O que fazer quando a recuperação não resolve, Recuperação automática: o que tem e o que não tem, `source_videos.status`

### Community 182 - "Transcrições — base de conhecimento (17/09/2026)"
Cohesion: 0.11
Nodes (18): Aulas em player HLS (Hotmart) — só o áudio, via extensão (30/09/2026), Baixar a aula — opcional, desligado, Binário e modelo, Chunking, Conversão para áudio acima de 24 MB, Detalhes que importam, Formato do transcript salvo, O arquivo baixado é apagado depois da transcrição (18/09/2026) (+10 more)

### Community 183 - "cleanup_stale_downloads"
Cohesion: 0.21
Nodes (9): cleanup_stale_downloads(), Remove artefatos de download parados há mais de `max_age_hours`. Rede de…, _age(), Testes ACQU-02: download 720p, disk guard, partial cleanup. Módulo alvo:…, Envelhece o mtime do arquivo em `hours` horas., Nomes reais tirados do disco de produção após crashes (Jul/Ago 2026)., Artefato recente é download vivo — não pode ser apagado no meio., clips/ e thumbnails/ têm outro ciclo de vida — cleanup não entra. (+1 more)

### Community 184 - "resume_claude_session.sh"
Cohesion: 0.32
Nodes (7): HOME, log(), PATH, resume_claude_session.sh script, SHELL, update_status(), USER

### Community 185 - "make_offer"
Cohesion: 0.16
Nodes (20): apply_copy(), generate_copy(), _log(), Gera copy e devolve (campos, provedor_usado). provider: auto = Anthropic → Groq…, Preenche só os campos de copy vazios. Retorna provedor usado ou None se nada a…, make_offer(), FakeAnthropic, FakeGroq (+12 more)

### Community 186 - "package.json"
Cohesion: 0.20
Nodes (9): private, $schema, scripts, build, dev, lint, lint:fix, typecheck (+1 more)

### Community 187 - "test_db.py"
Cohesion: 0.20
Nodes (9): longo_teto_atingido(), max_longos_pendentes_por_canal(), Teto de longos aguardando aprovação por canal-destino (env…, True se o canal já tem longos aguardando >= teto configurado. Ponto de chamada…, parametrize, Testes ORC-02: operações de banco de dados do pipeline. Módulo alvo: src.db…, recover_stuck_downloads() executa UPDATE SET status='pending' WHERE…, TestRecoverStuckDownloads (+1 more)

### Community 188 - "TestAIPipelineIntegration"
Cohesion: 0.16
Nodes (8): AI-04: Testes de integração do pipeline de IA no rss_poller., Configura mock_db_conn para retornar canais e vídeos downloaded em fetchall().…, AI-04: poll_all_channels chama _process_ai_pipeline para cada vídeo com status…, AI-04: Falha no pipeline de IA de um vídeo não aborta os demais., AI-04: _process_ai_pipeline chama transcribe_video e select_moments em…, AI-04: Falha na transcrição (None) marca vídeo como failed e não chama…, AI-04: Pipeline atualiza status: transcribing → (save) → selecting., TestAIPipelineIntegration

### Community 189 - "📋 Regras de Negócio e Gatilhos Operacionais — Canal de Cortes"
Cohesion: 0.40
Nodes (5): 1. 🎯 Metas Diárias de Publicação (Cota do Canal), 2. 📥 Janela de Download e Captação, 3. 🤖 Seleção e Ranqueamento por IA, 4. 🧹 Gatilhos de Auto-Expurgo e Limpeza de Disco (Watchdog & TTL), 📋 Regras de Negócio e Gatilhos Operacionais — Canal de Cortes

### Community 190 - "Foco de revisão"
Cohesion: 0.14
Nodes (14): Depois do plano, com o dono, Foco de revisão, Plano — retenção do YouTube Analytics por clip (SPEC-001, etapa 1 de 3), Restrições globais, Tarefa 10: documentação e fechamento, Tarefa 1: tabela `clip_daily_metrics`, Tarefa 2: escopo `yt-analytics.readonly` no OAuth, Tarefa 3: ler a resposta da Analytics API por `columnHeaders` (+6 more)

### Community 191 - "TranscriptSearch"
Cohesion: 0.16
Nodes (3): EmbedderException, EmbedderClient, TranscriptSearch

### Community 192 - "render_short_clip"
Cohesion: 0.27
Nodes (5): Renderiza um Short 1080x1920 em UMA recodificação de vídeo. Enquadramento…, Filtro `subtitles=` com o estilo do canal (cor vinda do template_config)., render_short_clip(), _subtitle_filter(), TestRenderShortClip

### Community 193 - "clip-processor/src/main.py"
Cohesion: 0.32
Nodes (8): BlockingScheduler daemon pattern (APScheduler), clip-processor/src/db.py, clip-processor/src/main.py, clip-processor/src/rss_poller.py, 03-04-PLAN.md: AI pipeline integration plan, 03-04-SUMMARY.md: AI pipeline integration Summary, poll_all_channels(db_conn, redis_client), recover_stuck_downloads()

### Community 194 - "manifest.json"
Cohesion: 0.10
Nodes (20): action, default_popup, default_title, background, service_worker, description, host_permissions, storage (+12 more)

### Community 195 - "3. Como Saber se o Cron Funcionou"
Cohesion: 0.17
Nodes (11): 1. Contexto e Diagnóstico, 2.1. Script de Execução e Retentativas (`scripts/resume_claude_session.sh`), 2.2. Camadas de Agendamento Configuradas, 2. O que Foi Feito, 3. Como Saber se o Cron Funcionou, Dados da Sessão Interrompida, Opção A: Executar o verificador automático (Recomendado), Opção B: Verificação manual por arquivos de log (+3 more)

### Community 196 - "copywriter.py"
Cohesion: 0.22
Nodes (18): _anthropic_text(), build_user_prompt(), CopyError, format_price(), generate_via_anthropic(), generate_via_groq(), generate_via_template(), normalize_copy() (+10 more)

### Community 203 - "Sistema de afiliados"
Cohesion: 0.10
Nodes (20): API, Autenticação, Banco, Componentes, Configuração, Configuração (18/09/2026), Deploy, Divulgação no Telegram (+12 more)

### Community 204 - "deploy.sh"
Cohesion: 0.73
Nodes (5): artisan_remoto(), entrar_manutencao(), remoto(), sair_manutencao(), deploy.sh script

### Community 207 - "FakeRemote"
Cohesion: 0.17
Nodes (6): FakeRemote, Banco de mentira: responde ao claim e guarda o que o worker grava.…, Ponta a ponta com o módulo de verdade: sem sentence-transformers/modelo, o job…, TestIndexacaoDaBusca, TestJobComMidiaDaExtensao, TestProcessaUmJob

### Community 214 - "manual.py"
Cohesion: 0.22
Nodes (14): load_csv(), load_file(), load_json(), _normalize_row(), OfferImportError, _price_to_cents(), Exception, Path (+6 more)

### Community 217 - "Migração para a VM A1 + PostgreSQL — como ficou"
Cohesion: 0.17
Nodes (12): Backup, Busca vetorial: Postgres com pgvector (29/09/2026), Como foi feita (para repetir ou auditar), Em resumo, Encontrado na migração, Migração para a VM A1 + PostgreSQL — como ficou, O que falta, Pendência: imagem do Postgres com pgvector (busca nas transcrições) (+4 more)

### Community 218 - "Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel"
Cohesion: 0.24
Nodes (10): APScheduler dentro do clip-processor (vs n8n cron) para TTL worker, clip-processor/src/processar.py, clip-processor/src/ttl_worker.py, Cloudflare Tunnel via container cloudflared — exposição segura sem porta aberta/ngrok, docker-compose.yml (raiz wordpress/, cloudflared + n8n envs), Phase 6 Context — Controle Manual N8N + Telegram, Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel, Pseudo-channel manual:UCxxx com active=FALSE para vídeos de canais fora do pool RSS (+2 more)

### Community 219 - "2026_09_18_000000_transcricao_status_pausado.php"
Cohesion: 0.83
Nodes (3): down(), trocar(), up()

### Community 220 - "selector.py"
Cohesion: 0.08
Nodes (30): _clamp_moment_bounds(), _clean_reason(), _drop_moments_over_unseen_text(), _enforce_longform_duration(), _filter_shortform_duration(), _filter_strict_longform(), _log(), _normalize_scores() (+22 more)

### Community 221 - "Phase 8 Plan 08: Dashboard Widgets + Aprovar/Rejeitar Plan"
Cohesion: 0.20
Nodes (12): Phase 8 Deferred Items, Filament $isLazy=false widget pattern, generated_clips.status ENUM (approved/rejected), mysql/init/05-controle-manual-migration.sql, App\Filament\Widgets\PendingApprovalWidget, App\Filament\Widgets\QuotaTodayWidget, App\Filament\Widgets\RecentFailuresWidget, App\Filament\Widgets\RecentUploadsWidget (+4 more)

### Community 222 - "dt_sp"
Cohesion: 0.16
Nodes (8): _drain(), dt_sp(), FakeRedis, Redis em memória: get/incr/expire/set suficientes para o QuotaManager., Helper: datetime no fuso São Paulo., 12-14h + 19-22h = 5h; ciclo de 20 min => 1 upload por ciclo = até 15 vagas., TestCotaPorFormato, TestEspacamento

### Community 223 - "affiliate-worker"
Cohesion: 0.20
Nodes (9): affiliate-worker, Arquivos locais (`data/`), Exemplo rápido, Fluxo, Formato do CSV, Instalação, Mercado Livre, Regras que o worker garante (+1 more)

### Community 224 - "RuntimeError"
Cohesion: 0.23
Nodes (15): delete_source_video_file(), Apaga o arquivo bruto (.mp4), clips gerados (videos/clips/), thumbnails e…, can_delete_raw(), _cleanup_partial(), _kill_ffmpeg_for_clip(), _kill_ytdlp_for(), _log(), pause_video() (+7 more)

### Community 226 - "recover_stuck_selecting"
Cohesion: 0.18
Nodes (7): Devolve vídeos presos em 'selecting' para 'downloaded' (reprocessa a IA).…, recover_stuck_selecting(), A query de 'sem arquivo' não pode capturar quem ainda tem o raw., Vídeos com clips já gerados não podem voltar para downloaded (evita duplicação)., selecting' com local_path NULL precisa de saída própria. As duas queries…, TestPostgresSupport, TestRecoverStuckSelecting

### Community 227 - "mysql/init/06-multi-canal-migration.sql"
Cohesion: 0.28
Nodes (9): mysql/init/06-multi-canal-migration.sql, destination_channels table (slug, name, niche, youtube_channel_id, credit_template, active), generated_clips.destination_channel_id FK to destination_channels, INFORMATION_SCHEMA + prepared statements idempotent migration pattern, MCAN-01..04, COPY-01..03: requirements multi-canal (channel_slug, destination_channel_id, quota por canal, blacklist, watermark, credits), Phase 7 Plan 01: Schema Multi-Canal Migration, Phase 7 Plan 01 Summary, Phase 7 Plan 02: Extender testes multi-canal (RED state) (+1 more)

### Community 228 - "migrar_mysql_para_postgres.py"
Cohesion: 0.60
Nodes (4): convert(), main(), pg_columns(), Copia os dados do MySQL de produção para o PostgreSQL da VM A1. O schema do…

### Community 230 - "Foco de revisão"
Cohesion: 0.15
Nodes (12): Depois do plano, com o dono, Foco de revisão, Plano — integração JEV e revisão de palavrão (SPEC-002), Restrições globais, Tarefa 1: tabelas e colunas, Tarefa 2: liga/desliga no painel, Tarefa 3: cliente do JEV, Tarefa 4: candidatas e lista de palavras (o fallback) (+4 more)

### Community 231 - "clip-processor/src/publisher.py"
Cohesion: 0.31
Nodes (9): clip-processor/src/pipeline_runner.py, clip-processor/src/publisher.py, clip-processor/src/rejeitar.py, clip-processor/src/telegram_notifier.py, CTRL-06: notificações proativas via Cloudflare Tunnel + n8n webhook, Phase 6 Plan 06: telegram_notifier + Cloudflare Tunnel, Phase 6 Plan 06 Summary, Status guard em UPDATE (WHERE id=%s AND status='X' + rowcount check) — defesa contra race condition (+1 more)

### Community 232 - "download_hls_audio"
Cohesion: 0.17
Nodes (13): download_hls_audio(), _erro_hls(), ffmpeg_hls_args(), hls_headers(), _hls_info(), _origin_of(), Referer e Origin que o player mandou ao pedir o m3u8 (a CDN confere)., yt-dlp sobre o m3u8 capturado: só o áudio (mp3), com os cabeçalhos do player.… (+5 more)

### Community 233 - "_niche_windows"
Cohesion: 0.40
Nodes (4): _niche_windows(), Teto da janela por nicho: DOWNLOAD_WINDOW_PER_CHANNEL × canais destino ativos.…, Teto = DOWNLOAD_WINDOW_PER_CHANNEL por canal destino ativo do nicho., TestNicheWindows

### Community 234 - "Parte 2 — Técnica"
Cohesion: 0.12
Nodes (16): Arquitetura, Backfill (carga das transcrições antigas), Banco, Busca: RRF, Calibração do piso de similaridade (30/09/2026), Como verificar que está funcionando, Embedder (sidecar), Endpoint e página de detalhe (contrato fixo) (+8 more)

### Community 235 - "popup.js"
Cohesion: 0.24
Nodes (3): enviar(), SEGUNDO_NIVEL, siteDaAula()

### Community 236 - "download_media"
Cohesion: 0.17
Nodes (12): _arquivo_baixado(), download_media(), explain_error(), parse_progress(), Linha de comando do yt-dlp: só o áudio, ou a aula em vídeo (até 720p, mp4)…, [progresso] 42.3%' -> 42.3. Qualquer outra linha do yt-dlp -> None., Erro de login vira instrução do que fazer; qualquer outro passa intacto., O `aula.<ext>` final: ignora info.json, pedaço .part e as faixas separadas… (+4 more)

### Community 237 - "test_recovery_states.py"
Cohesion: 0.10
Nodes (11): _executed(), parametrize, Recovery de estados presos (transcribing/publishing/cutting), PIPELINE_ENABLED…, Sem trigger no banco, a idade dos recoveries depende disto., TestPipelineEnabled, TestRecoverCuttingOnBoot, TestRecoverStuckCutting, TestRecoverStuckPublishing (+3 more)

### Community 238 - "save_media_entry"
Cohesion: 0.25
Nodes (11): _drop_expired(), forget_media_entry(), lookup_media_entry(), normalize_source_url(), Chave do arquivo de endereços: esquema e host em minúsculas, sem fragmento., Temporário + rename, com 0600: nunca um arquivo pela metade nem legível por…, Guarda o endereço do m3u8 da aula e, de passagem, limpa as entradas com mais de…, Entrada do link da aula, se existir e não tiver vencido (24 h). (+3 more)

### Community 239 - "Settings.tsx"
Cohesion: 0.09
Nodes (26): Badge(), badgeVariants, Card(), CardAction(), CardContent(), CardDescription(), CardFooter(), CardHeader() (+18 more)

### Community 240 - "check_download_window_health"
Cohesion: 0.39
Nodes (3): check_download_window_health(), Verifica se a janela de 7 vagas está 100% cheia e estagnada há mais de…, TestCheckDownloadWindowHealth

### Community 241 - "Extensão "Transcrever esta aula""
Cohesion: 0.25
Nodes (7): Atualizar / recarregar a extensão, Aulas do Hotmart (player HLS) — v1.1.0, Como funciona e o que sai do seu Mac, Extensão "Transcrever esta aula", Instalar (uma vez), Se o embed do Hotmart usar outro domínio, Usar

### Community 242 - "_seg"
Cohesion: 0.20
Nodes (4): _seg(), TestPedacos, TestSrt, TestTexto

### Community 243 - "test_publisher.py"
Cohesion: 0.19
Nodes (11): _fetch_source_channel_last_upload(), _pick_next_by_rotation(), datetime (aware ou naive=UTC) ou epoch -> epoch; None -> -inf (nunca publicou)., Último upload (epoch) por canal-fonte neste canal-destino, para o revezamento., Revezamento entre canais-fonte: escolhe o clip do canal-fonte que publicou há…, _to_epoch(), _clip(), make_mock_quota() (+3 more)

### Community 244 - "test_sigterm_shutdown.py"
Cohesion: 0.29
Nodes (6): _espera_linha(), skipif, Bug 11 — o container tem de honrar SIGTERM (`docker stop` sem virar exit 137).…, _sobe_daemon(), TestHandlerSoSinaliza, TestSigtermShutdown

### Community 245 - "_process_pending_clips(conn)"
Cohesion: 0.50
Nodes (4): Checkpoint humano: verificação end-to-end Phase 4, _process_pending_clips(conn), generated_clips.status = pending_cut, 04-04 Plan: Poller Integration

### Community 247 - "TestTituloEditorial"
Cohesion: 0.18
Nodes (4): parametrize, update_clip_metadata e o fallback final nunca podem travar o pipeline., Se as duas IAs falham, o título bruto do vídeo é o último recurso (regra do…, TestTituloEditorial

### Community 248 - "test_long_format_mode.py"
Cohesion: 0.14
Nodes (17): Índices das linhas mantidas: `windows` blocos espalhados pelo vídeo, cada um…, Analisa transcrição e retorna momentos selecionados via IA. Args: transcript:…, _sample_transcript_windows(), select_moments(), _client(), _limpa_cache_de_colunas(), _moment(), fixture (+9 more)

### Community 249 - "Radar de Performance: pacote de entrega"
Cohesion: 0.13
Nodes (14): Arquivos SOBRESCRITOS (revise com git diff antes de qualquer coisa), Como aplicar, Como desfazer tudo, Decisões que você precisa saber que foram tomadas por mim, O que abrir primeiro no painel, O que este pacote faz, Ordem de execução, Passo 1, a parte manual sua (Fase 0) (+6 more)

### Community 250 - "datetime"
Cohesion: 0.32
Nodes (4): datetime, Incrementa contador diario (total e, se 'longo', o de formato) e garante TTL., Janela + cota total, ignorando reserva por formato. Usado para decidir se o…, Retorna True se horario e quota (total + formato/reserva) permitirem upload.

### Community 253 - "QuotaManager"
Cohesion: 0.22
Nodes (6): QuotaManager, None = sem teto de curto (comportamento anterior)., Controla uploads diarios do YouTube por data local de Sao_Paulo.…, Com MAX=5 / LONGO=2 e 3 uploads, curto bloqueia se ainda há longo na fila., Sem longo na fila, curto pode usar o restante da cota total., TestLongoReservation

### Community 260 - "Estado do projeto — leia primeiro"
Cohesion: 0.20
Nodes (10): 0. Para onde vamos, 1. Onde está cada coisa, 2. Produção, 3. Linha do tempo, 4. Decisões que custaram caro para descobrir, 5. Armadilhas operacionais, 6. Em aberto, 7. Como começar uma rodada nova (+2 more)

### Community 261 - "Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan"
Cohesion: 0.25
Nodes (8): BOT-01 requirement (webhook + allowlist + dedup), BOT-02 requirement (6 Telegram commands), BOT-03 requirement (pipeline-event notifications), PipelineEventTest.php (4 RED tests), TelegramCommandsTest.php (7 RED tests), TelegramWebhookTest.php (3 RED tests), Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan, irazasyed/telegram-bot-sdk ^3.16

### Community 262 - "MetricsReport"
Cohesion: 0.29
Nodes (5): Illuminate\Support\Carbon, MetricsReport, metric(), metricsProps(), publishedClip()

### Community 263 - "Phase 8 Context (Painel Laravel/Filament)"
Cohesion: 0.17
Nodes (15): nginx bind mount painel fix (404 puro), routes/web.php raiz '/' redirect fix, PANEL-01 requirement (CRUD canal-fonte sem SQL), PANEL-02 requirement (CRUD canal-destino + badge OAuth), PANEL-03 requirement (dashboard tempo real), PANEL-04 requirement (aprovar/rejeitar clip), PANEL-05 requirement (autenticação single-user), Phase 8 human checkpoint (7-step verification) (+7 more)

### Community 264 - "Retomada — Transcrições, extensão e estudos (18/09/2026)"
Cohesion: 0.20
Nodes (10): 1. ~~Destino local/produção~~ → só produção, com botão "Baixar aula" (feito em 18/09/2026), 2. Contexto para estudo: título, curso, seção, do que a aula trata, 3. Hotmart, Aprendizados que custaram caro (não repetir), Feito em 17/09/2026 (outras frentes, já em produção), O que funciona hoje, provado com uso real, Onde as coisas estão agora, Pendências do operador (fora das tarefas acima) (+2 more)

### Community 265 - "_TwoFormatCursor"
Cohesion: 0.20
Nodes (3): Estado real de clips: o COUNT e o SELECT de clips respondem pelo que está na…, _TwoFormatCursor, TwoFormatDb

### Community 266 - "Referência técnica"
Cohesion: 0.25
Nodes (8): Banco, Clip-processor, Ficou de fora de propósito, Mídia por canal (intro, encerramento, música), Painel, Para quem opera o painel, Referência técnica, Testes

### Community 267 - "test_quota_manager.py"
Cohesion: 0.50
Nodes (4): clean_env(), fixture, Testes para QuotaManager — controle de quota e janela de publicação., reset_bypass()

### Community 268 - "TestQuotaManagerMultiCanal"
Cohesion: 0.20
Nodes (6): Testes RED para suporte a channel_id no QuotaManager (MCAN-03, MCAN-04)., MCAN-03: _key() deve incluir channel_id quando fornecido. QuotaManager(r,…, Retrocompat: _key() sem channel_id retorna 'youtube_uploads:2026-06-18'., MCAN-04: Dois QuotaManager com channel_id diferentes usam keys Redis distintas.…, MCAN-04: Quota atingida no canal A não bloqueia canal B., TestQuotaManagerMultiCanal

### Community 269 - "Desenvolvimento — lint, testes e CI"
Cohesion: 0.20
Nodes (10): Changelog, CI, Como rodar, Desenvolvimento — lint, testes e CI, Fluxo de mudança, O que cada gate faz hoje, Referências, Restaurar um backup do PostgreSQL (+2 more)

### Community 271 - "Referência técnica"
Cohesion: 0.29
Nodes (7): Banco, Clip-processor, Frescor e prioridade por canal-fonte, Painel, Para quem opera o painel, Referência técnica, Testes

### Community 273 - "Parte 1 — Para quem usa o painel"
Cohesion: 0.29
Nodes (7): Como ler o resultado, Como o fluxo funciona, em uma figura, O que mudou na tela de Transcrições, O que significam os termos (sem jargão), Parte 1 — Para quem usa o painel, Perguntas frequentes, Três jeitos de buscar

### Community 274 - "Plano PostgreSQL — fase A (local) e fase B (produção)"
Cohesion: 0.22
Nodes (9): Como retomar depois de reiniciar a sessão, Decisões, Divergência encontrada na A2 (importante para a fase B), Estado em 15/09/2026, Falhas de teste pré-existentes encontradas (não são da migração), Fase A — local, Fase B — produção (fazer junto da VM A1 de 12 GB), Plano PostgreSQL — fase A (local) e fase B (produção) (+1 more)

### Community 275 - "test_uploader.py"
Cohesion: 0.17
Nodes (8): make_uploader(), Testes para YouTubeUploader — upload de clips e thumbnails. Todas as chamadas…, Testes RED para suporte a channel_slug no YouTubeUploader (MCAN-01)., MCAN-01: channel_slug='futebol-em-cortes' → token_file='/app/youtube/token-…, Retrocompat: sem channel_slug, usa DEFAULT_TOKEN_FILE., Retrocompat: token_file explícito tem precedência sobre channel_slug., Cria YouTubeUploader com credenciais e YouTube mockados., TestYouTubeUploaderChannelSlug

### Community 276 - "Docs — mapa da documentação"
Cohesion: 0.22
Nodes (9): Arquivo — `historico/` (obsoleto ou superado), Como funciona — `sistema/` (vigente), Como manter, Como operar — `operacao/`, Decisões — `adr/`, Docs — mapa da documentação, Estudos e mapas — `estudos/`, `mapas/`, Pastas, por tipo de documento (+1 more)

### Community 277 - "react"
Cohesion: 0.12
Nodes (13): SiteHeader(), ThemeToggle(), Accordion(), AccordionContent(), AccordionItem(), AccordionTrigger(), Toaster(), AppShellProps (+5 more)

### Community 278 - "0001-busca-vetorial-nas-transcricoes.md"
Cohesion: 0.20
Nodes (8): ADR-0001 — Busca híbrida (texto + vetor) nas transcrições, com embeddings locais e degradação para texto, Consequências, Contexto, Decisão, ADR-0007 — PostgreSQL 17 como banco único do painel e do clip-processor, Consequências, Contexto, Decisão

### Community 279 - "changelog.py"
Cohesion: 0.73
Nodes (5): cmd_preview(), cmd_release(), load_fragments(), main(), render()

### Community 280 - "Contribuindo"
Cohesion: 0.40
Nodes (5): Antes de alterar, Branches e commits, Changelog e documentação, Contribuindo, Verificação

### Community 281 - "SPEC-001 — Retenção do YouTube Analytics por clip"
Cohesion: 0.20
Nodes (10): 1. Objetivo, 2. Fora de escopo, 3. Regras de negócio, 4. Contrato, 5. Critérios de pronto, 6. Riscos e perguntas em aberto, Chamada à Analytics API, SPEC-001 — Retenção do YouTube Analytics por clip (+2 more)

### Community 283 - "extra"
Cohesion: 0.67
Nodes (3): extra, laravel, dont-discover

### Community 284 - "setup"
Cohesion: 0.25
Nodes (8): post-root-package-install, setup, composer install, npm install --ignore-scripts, npm run build, @php artisan key:generate, @php artisan migrate --force, @php -r \"file_exists('.env') || copy('.env.example', '.env');\

### Community 295 - "Illuminate\Database\Seeder"
Cohesion: 0.29
Nodes (5): Illuminate\Database\Console\Seeds\WithoutModelEvents, Illuminate\Database\Seeder, BaselineSeeder, DatabaseSeeder, SourceChannelsSeeder

### Community 301 - "Estratégia de Conteúdo, Benchmark e YouTube Analytics"
Cohesion: 0.29
Nodes (6): 1. Como Diagnosticar e Alimentar a IA com Métricas do YouTube Studio, 2. Benchmark de Concorrentes & Canais de Referência, 3. Modelo dos Cortes Virais de Política (MBL / Missão), 4. Monetização e RPM Médio no YouTube Brasil, Estratégia de Conteúdo, Benchmark e YouTube Analytics, Ferramenta de Diagnóstico no Painel (`/painel/assistente`)

### Community 302 - "SPEC-002 — Revisão de palavrão na aprovação, com julgamento tipado (JEV)"
Cohesion: 0.11
Nodes (17): Como poderia funcionar (rascunho, a validar), O problema, O que o dono quer (nas palavras dele), Ordem sugerida quando for implementar, Perguntas em aberto, Plano — revisão de palavrão antes de publicar, 1. Objetivo, 2. Fora de escopo (+9 more)

### Community 303 - "indexar_ligado"
Cohesion: 0.33
Nodes (6): indexar_ligado(), indexar_padrao(), _indexar_sem_derrubar(), TRANSCRICAO_INDEXAR: indexa a transcrição para a busca (default ligado). Só…, Indexador real (scripts/transcript_indexer.py), carregado só na hora de usar., A transcrição já está `done` no banco: indexar é bônus. Qualquer falha vira…

### Community 304 - "update_status"
Cohesion: 0.28
Nodes (6): Atualiza o status de um vídeo na tabela source_videos. `local_path=None`…, update_status(), update_status() executa SQL UPDATE com status correto., update_status() com local_path inclui local_path no SQL., clear_local_path=True deve gravar local_path=NULL (libera vaga da janela)., TestUpdateStatus

### Community 308 - "Phase 8 Research (Painel Laravel/Filament)"
Cohesion: 0.33
Nodes (6): docker exec / Docker socket bridge anti-pattern, Pattern 3: ponte HTTP interna clip-processor↔painel, Phase 8 Plan 07: internal_api.py GREEN Plan, Phase 8 Plan 07: internal_api.py GREEN Summary, Phase 8 Research (Painel Laravel/Filament), Sidecar HTTP interno em thread daemon (antes do ciclo do pipeline)

### Community 309 - "TestRecordUpload"
Cohesion: 0.22
Nodes (5): record_upload deve chamar INCR no Redis., Primeiro upload do dia deve definir TTL até meia-noite., Segundo upload não deve redefinir o TTL., TTL deve ser o número de segundos até meia-noite em SP., TestRecordUpload

### Community 310 - "channel_cap"
Cohesion: 0.43
Nodes (3): channel_cap(), Quantas vagas da janela um único canal de origem pode ocupar. Divide a janela…, TestChannelCap

### Community 316 - "Progresso — o que foi feito e o que falta"
Cohesion: 0.33
Nodes (6): 1. FEITO (em produção), 2. EM ANDAMENTO, 3. PLANEJADO / IDEIA (escrito, não implementado), 4. PENDÊNCIA DO DONO (só você faz), 5. OBSOLETO (guardado, não vale mais), Progresso — o que foi feito e o que falta

### Community 317 - "_max_window_slots"
Cohesion: 0.40
Nodes (4): _max_window_slots(), Teto total da janela: DOWNLOAD_WINDOW_PER_CHANNEL × canais destino ativos., Teto = DOWNLOAD_WINDOW_PER_CHANNEL por canal destino ativo., TestMaxWindowSlots

### Community 322 - "generated_clips.status state machine"
Cohesion: 0.40
Nodes (5): generated_clips.status state machine, list-pending-clips.sh, mark-published.sh, manual-workflow/README.md — manual clip publishing guide, Pitfall: Filament Auto-Generated Resources Break on ENUM Columns

### Community 323 - "Deploy automático diário — opções e decisão"
Cohesion: 0.40
Nodes (5): A trava obrigatória, em qualquer uma das três, As três opções, Deploy automático diário — opções e decisão, O que se quer, Pendências antes de implementar

### Community 324 - "CHANGELOG.d — fragmentos de release notes"
Cohesion: 0.40
Nodes (4): CHANGELOG.d — fragmentos de release notes, Comandos, Conteúdo, Nome do arquivo

### Community 325 - "Estado atual em uma tela"
Cohesion: 0.50
Nodes (4): Corrigido em 12–13/08/2026, Estado atual em uma tela, Estado do sistema em agosto/2026 (arquivado), Os dois que mais doem hoje

### Community 326 - "check_disk_space"
Cohesion: 0.50
Nodes (3): check_disk_space(), Verifica espaço livre em disco no volume de vídeos., TestCheckDiskSpace

### Community 330 - "TelegramWebhookController::handle"
Cohesion: 0.50
Nodes (4): Pitfall: CSRF blocking Telegram webhook (419), Redis SET NX dedup pattern (tg:dedup:{update_id}), TelegramWebhookController::handle, Pitfall: Webhook Receives Duplicate Updates on Server Errors

### Community 331 - "janela_16"
Cohesion: 0.67
Nodes (3): janela_16(), fixture, Mantém os cenários abaixo com teto 16, isolados da consulta a…

### Community 332 - "test"
Cohesion: 0.67
Nodes (3): test, @php artisan config:clear --ansi @no_additional_args, @php artisan test

## Ambiguous Edges - Review These
- `clip-processor/src/ttl_worker.py` → `clip-processor/src/telegram_notifier.py`  [AMBIGUOUS]
  .planning/phases/06-controle-manual-n8n-telegram/06-05-SUMMARY.md · relation: conceptually_related_to

## Knowledge Gaps
- **925 isolated node(s):** `clip-processor`, `test`, `assert`, `C`, `fs` (+920 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `clip-processor/src/ttl_worker.py` and `clip-processor/src/telegram_notifier.py`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `run_pipeline_once()` connect `run_pipeline_once` to `publish_pending_clips`, `publisher.py`, `rss_poller.py`, `pipeline_runner.py`, `main.py`, `notify`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `n8n/workflows/canaldecortes-pipeline.json` connect `run_pipeline_once` to `05-01 Plan: Publishing schema, skeletons and RED tests`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `05-06 Plan: n8n workflow and production checkpoint` connect `run_pipeline_once` to `Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `QuotaManager` (e.g. with `FakeRedis` and `TestCanUpload`) actually correct?**
  _`QuotaManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `clip-processor`, `test`, `assert` to the rest of the system?**
  _925 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_media_channel_flow.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05339506172839506 - nodes in this community are weakly interconnected._