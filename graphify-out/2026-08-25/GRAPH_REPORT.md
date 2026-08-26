# Graph Report - canaldecortes  (2026-08-13)

## Corpus Check
- 345 files · ~320,878 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2215 nodes · 3888 edges · 186 communities (158 shown, 28 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 85 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2af06574`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SourceVideos.tsx
- publish_pending_clips
- db.py
- SourceChannels.tsx
- QuotaManager
- Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel
- rss_poller.py
- insert_selected_moments
- User.php
- Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)
- internal_api.py
- selector.py
- DestinationChannels.tsx
- processar.py
- devDependencies
- field.tsx
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
- DestinationChannel
- components.json
- docker-compose.yml (raiz wordpress/)
- download_video
- Illuminate\Http\RedirectResponse
- SourceChannel
- Illuminate\Http\Request
- compilerOptions
- video_processor.py
- Phase 1: Infraestrutura Base
- Phase 7 Context: Schema Multi-Canal + Python Pipeline
- run_pipeline_once
- TelegramHttpClientHandler.php
- confirm-button.tsx
- notify
- TranscriptionController.php
- _download_pending_videos
- chart.tsx
- utils.ts
- ARCHITECTURE.md (as-built, commit dca6e44)
- process_clip
- dependencies
- select_moments
- YouTubeUploader
- scripts
- painel/README.md (setup fresh 10 passos)
- clip-processor/src/selector.py
- composer.json
- _select_pending_videos
- mysql/init/01-clips-schema.sql
- app-shell.tsx
- .planning/research/PITFALLS.md
- .planning/research/FEATURES.md
- cn
- internal_api.py sidecar (Flask, port 8090)
- validate-phase6-n8n.py
- Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan
- clip-processor/src/rss_poller.py
- append_credits
- conftest.py
- input-group.tsx
- publisher.py
- queue_controls.py
- overlay_watermark
- require-dev
- 02-04-PLAN.md: Daemon main.py Plan
- .planning/research/ARCHITECTURE.md (v2.0 research, superseded)
- youtube_oauth.py
- run_ingest_cycle
- 02-01-PLAN: pytest scaffold RED state (Wave 0)
- Phase 8 Context (Painel Laravel/Filament)
- get_db_connection
- TestYouTubeUploaderChannelSlug
- setup
- Phase 9-04 Plan: Telegram Bot Checkpoint
- Phase 7: Schema Multi-Canal + Python Pipeline
- 01-RESEARCH.md
- config
- require
- GeneratedClip
- clip-processor/src/metadata_generator.py
- destination_channels table
- test_publisher.py
- clip-processor/src/downloader.py
- Phase 8 Research (Painel Laravel/Filament)
- _discard_failed_download
- Phase 8 Plan 05: SourceChannelResource Plan
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
- transcription_job.py
- clip-processor/src/main.py
- Plano de migração — Oracle Cloud (Always Free)
- @dnd-kit/utilities
- run_ttl_once
- rejeitar
- force-download.sh
- CreatePainelUser artisan command
- radix-ui
- react-dom
- Phase 6 Plan 07: workflows n8n completos + setup operacional + smoke E2E
- clip-processor/src/transcriber.py
- tailwind-merge
- Quick Task 1: Transcrição Local Summary
- toggle-group.tsx
- mysql/init/06-multi-canal-migration.sql
- 03-RESEARCH.md: Phase 3 Research
- MCAN-04: 3 vídeos/dia por canal 19h-22h BRT
- Claude Haiku para seleção e metadados
- Resenha FC channel banner (2048x1152)
- Soccer-ball mascot with microphone (cartoon character)
- Resenha FC (brand/channel name)
- 05-03 Plan: YouTube uploader
- Phase 6 Plan 05: TTL Worker (expire 48h + warn 24h)
- README.md
- TestProcessClipWithWatermark
- Backlog de bugs
- Sistema — `painel/`
- v1.0 — Pipeline Base
- clip-processor/src/db.py
- Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)
- autoload-dev
- @tanstack/react-table
- post-create-project-cmd
- tw-animate-css
- clip-processor/src/publisher.py
- zod
- sonner
- Fases
- Mapa dos módulos
- Rotas
- ._load_credentials
- 04-04 Summary: Poller Integration Summary
- Sistema — `clip-processor`
- test_uploader.py
- Phase 6 Plan 04: Implementar processar.py
- @dnd-kit/modifiers
- @fontsource-variable/geist
- @inertiajs/react
- lucide-react
- recharts
- vaul

## God Nodes (most connected - your core abstractions)
1. `cn()` - 199 edges
2. `QuotaManager` - 42 edges
3. `YouTubeUploader` - 37 edges
4. `publish_pending_clips()` - 36 edges
5. `ClipProcessorClient` - 32 edges
6. `get_db_connection()` - 30 edges
7. `poll_all_channels()` - 25 edges
8. `process_clip()` - 23 edges
9. `GeneratedClip` - 23 edges
10. `run_pipeline_once()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `publish_pending_clips()` --rationale_for--> `Publisher legacy fallback when destination_channels empty`  [EXTRACTED]
  clip-processor/src/publisher.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-06-SUMMARY.md
- `docker-compose.yml branding volume for clip-processor` --shares_data_with--> `overlay_watermark()`  [EXTRACTED]
  .planning/phases/07-schema-multi-canal-python-pipeline/07-07-PLAN.md → clip-processor/src/video_processor.py
- `.planning/research/ARCHITECTURE.md (v2.0 research, superseded)` --semantically_similar_to--> `ARCHITECTURE.md (as-built, commit dca6e44)`  [INFERRED] [semantically similar]
  .planning/research/ARCHITECTURE.md → ARCHITECTURE.md
- `clip-processor / painel service boundary (rigid)` --semantically_similar_to--> `Boundary rule: painel reads directly, writes via sidecar`  [INFERRED] [semantically similar]
  PROJECT_BRIEF.md → ARCHITECTURE.md
- `PROJECT_BRIEF.md — Canal de Cortes as-built brief` --semantically_similar_to--> `README.md (root, outdated Filament references)`  [INFERRED] [semantically similar]
  PROJECT_BRIEF.md → README.md

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

## Communities (186 total, 28 thin omitted)

### Community 0 - "SourceVideos.tsx"
Cohesion: 0.12
Nodes (18): Checkbox(), Select(), SelectContent(), SelectGroup(), SelectItem(), SelectLabel(), SelectScrollDownButton(), SelectScrollUpButton() (+10 more)

### Community 1 - "publish_pending_clips"
Cohesion: 0.11
Nodes (25): publish_pending_clips(), datetime, Publica clips prontos e retorna quantidade publicada. Fluxo multi-canal (Phase…, dt_sp(), make_conn_with_clips(), make_mock_uploader(), Upload bem-sucedido: pending → publishing → published., Upload com erro: status vai para 'failed', quota não é incrementada. (+17 more)

### Community 2 - "db.py"
Cohesion: 0.11
Nodes (20): insert_video(), _log(), db.py — Módulo de acesso ao MySQL para o daemon clip-processor. Exporta: -…, Insere um novo vídeo na tabela source_videos com status 'pending'. Usa INSERT…, Redefine vídeos presos em status 'downloading' de volta para 'pending'.…, Devolve vídeos presos em 'selecting' para 'downloaded' (reprocessa a IA).…, Loga mensagem com timestamp para stdout., Atualiza o status de um vídeo na tabela source_videos. `local_path=None`… (+12 more)

### Community 3 - "SourceChannels.tsx"
Cohesion: 0.09
Nodes (30): ActiveWindowTable(), postAction(), SortableRow(), STATUS_LABEL, useSelection(), VideoActions(), VideoCells(), VideoTable() (+22 more)

### Community 4 - "QuotaManager"
Cohesion: 0.07
Nodes (35): datetime, QuotaManager, Controla uploads diarios do YouTube por data local de Sao_Paulo.…, Janela + cota total, ignorando reserva por formato. Usado para decidir se o…, Retorna True se horario e quota (total + formato/reserva) permitirem upload., Incrementa contador diario (total e, se 'longo', o de formato) e garante TTL., dt_sp(), make_redis() (+27 more)

### Community 5 - "Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel"
Cohesion: 0.22
Nodes (11): APScheduler dentro do clip-processor (vs n8n cron) para TTL worker, clip-processor/src/processar.py, clip-processor/src/ttl_worker.py, Cloudflare Tunnel via container cloudflared — exposição segura sem porta aberta/ngrok, docker-compose.yml (raiz wordpress/, cloudflared + n8n envs), Phase 6 Context — Controle Manual N8N + Telegram, Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel, Pseudo-channel manual:UCxxx com active=FALSE para vídeos de canais fora do pool RSS (+3 more)

### Community 6 - "rss_poller.py"
Cohesion: 0.08
Nodes (25): _detect_format(), _extract_video_id(), _is_blocked_title(), _log(), poll_all_channels(), _process_pending_clips(), rss_poller.py — Monitor de feeds RSS de canais YouTube e inserção de vídeos…, Processa clips com status pending_cut sem abortar o poll por falha isolada. (+17 more)

### Community 7 - "insert_selected_moments"
Cohesion: 0.10
Nodes (17): insert_selected_moments(), _lookup_destination_channel_id(), Remove momentos sobrepostos, mantendo o de maior score. Retorna no máximo…, Resolve destination_channel_id via JOIN source_videos → source_channels →…, Filtra momentos com score >= 7 e insere em generated_clips. Returns: Número de…, _remove_overlaps(), test_selector.py — Testes unitários para selector.py (AI-02, AI-03). Estado…, AI-03: Momento com score=6 não é inserido — count retorna 0. (+9 more)

### Community 8 - "User.php"
Cohesion: 0.07
Nodes (16): Filament\Models\Contracts\FilamentUser interface, Illuminate\Console\Command, Illuminate\Database\Console\Seeds\WithoutModelEvents, Illuminate\Database\Seeder, Illuminate\Foundation\Auth\User, Illuminate\Foundation\Testing\TestCase, Illuminate\Notifications\Notifiable, CreatePainelUser (+8 more)

### Community 9 - "Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)"
Cohesion: 0.07
Nodes (34): canaldecortes/docker/nginx/canaldecortes.conf vhost, clip-processor não tem bind mount de src/ — exige rebuild+restart para refletir código, mysql/init/07-panel-oauth-flag-migration.sql (oauth_expired_flag idempotent migration), destination_channels.oauth_expired_flag column, config/database.php Redis 'pipeline' connection (DB 0), config/services.php clip_processor block (url/token), canaldecortes/painel/ — Laravel 13 + Filament 5.6.7 + Pest 4.7.4 project, App\Models\DestinationChannel Eloquent Model + getOauthStatusAttribute (+26 more)

### Community 10 - "internal_api.py"
Cohesion: 0.26
Nodes (16): internal_api.resolve_channel(url) — yt-dlp channel resolution, _check_auth(), internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.…, Roda yt-dlp em modo metadata-only e extrai id/name/handle. Padrão yt-dlp:…, resolve_channel(), _route_delete_source_video(), _route_pause_video(), _route_prioritize_video() (+8 more)

### Community 11 - "selector.py"
Cohesion: 0.12
Nodes (20): _enforce_longform_duration(), _filter_shortform_duration(), _log(), _normalize_scores(), _parse_moments(), selector.py — Seleção de momentos via IA com fallback automático. Prioridade em…, Garante duração mínima de MIN_LONGFORM_SECONDS para o modo 'longo'. O modelo…, Descarta momentos do formato 'curto' com duração inferior a… (+12 more)

### Community 12 - "DestinationChannels.tsx"
Cohesion: 0.09
Nodes (29): Niche, NicheCombobox(), slugify(), Command(), CommandDialog(), CommandEmpty(), CommandGroup(), CommandInput() (+21 more)

### Community 13 - "processar.py"
Cohesion: 0.10
Nodes (21): fetch_metadata(), main(), _normalize_upload_date(), parse_video_id(), processar.py — Ingestão manual de vídeo YouTube via comando /processar do…, Entrypoint CLI. Exit codes: - 0: OK (inserido ou já existia) - 2: URL inválida…, Extrai videoId de 11 caracteres de uma URL YouTube. None se URL inválida.…, Converte 'YYYYMMDD' (formato yt-dlp) para 'YYYY-MM-DD HH:MM:SS' (TIMESTAMP… (+13 more)

### Community 14 - "devDependencies"
Cohesion: 0.07
Nodes (29): concurrently, laravel-vite-plugin, devDependencies, concurrently, laravel-vite-plugin, tailwindcss, @tailwindcss/typography, @tailwindcss/vite (+21 more)

### Community 15 - "field.tsx"
Cohesion: 0.10
Nodes (20): LoginForm(), Field(), FieldContent(), FieldDescription(), FieldError(), FieldGroup(), FieldLabel(), FieldLegend() (+12 more)

### Community 16 - "publisher.py"
Cohesion: 0.08
Nodes (30): Blacklist guard (source_channels.blacklisted), COPY-01: watermark queimado via FFmpeg, COPY-02: descrição inclui créditos do canal original, COPY-03: canais blacklistados bloqueados no RSS poller, credit_template / channel_handle credits, generated_clips.destination_channel_id FK, MCAN-01: múltiplos canais YouTube com OAuth próprio, MCAN-02: campo niche determina canal-destino (+22 more)

### Community 17 - "05-01 Plan: Publishing schema, skeletons and RED tests"
Cohesion: 0.15
Nodes (18): quota_manager.py — Limite diario e janela de horario para uploads YouTube.…, MAX_UPLOADS_PER_DAY clamped to <= 6, default 2, mysql/init/04-publishing-migration.sql, Pattern: clock injection para testes deterministas, 05-01 Plan: Publishing schema, skeletons and RED tests, 05-01 Summary: publishing migration + TDD suite, 05-02 Plan: Quota and schedule guard, 05-02 Summary: QuotaManager implemented (+10 more)

### Community 18 - "Telegram\Bot\Commands\Command"
Cohesion: 0.09
Nodes (15): POST /internal/resolve-channel (sidecar endpoint), generated_clips.status ENUM (approved/rejected), Illuminate\Http\Response, JsonResponse, CreateSourceChannel Page, App\Filament\Widgets\PendingApprovalWidget, TelegramWebhookController, AjudaCommand (+7 more)

### Community 19 - "TestUploadClip"
Cohesion: 0.11
Nodes (12): make_youtube_mock(), token_file inexistente deve levantar FileNotFoundError., Se thumbnail_path existir, thumbnails().set() deve ser chamado., Cria um mock do serviço YouTube que simula upload bem-sucedido., Falha no upload da thumbnail deve ser propagada ao caller., Tags em formato string separado por vírgula devem virar lista., YOUTUBE_PRIVACY_STATUS do env deve ser usado no upload., Upload bem-sucedido deve retornar o youtube_video_id. (+4 more)

### Community 20 - "uploader.py"
Cohesion: 0.12
Nodes (14): HttpError, MediaFileUpload, Exception, uploader.py — Upload de clips para YouTube Data API v3. Exporta: -…, RefreshError, RED test para captura de RefreshError e persistência de oauth_expired_flag…, RefreshError em creds.refresh() deve setar oauth_expired_flag=TRUE em…, test_load_credentials_catches_refresh_error_and_flags_channel() (+6 more)

### Community 21 - "generate_metadata"
Cohesion: 0.10
Nodes (24): Anthropic structured outputs via output_config json_schema, Checkpoint humano: verificação end-to-end Phase 4, _build_prompt(), generate_metadata(), _generate_via_anthropic(), _generate_via_groq(), _log(), _normalize_metadata() (+16 more)

### Community 22 - "process_clip"
Cohesion: 0.12
Nodes (17): burn_subtitles(), cut_clip(), extract_thumbnail(), _fetch_clip(), _format_srt_time(), generate_srt(), process_clip(), Queima legendas SRT no clip usando FFmpeg. Alignment=2 (rodapé-centro), estilo… (+9 more)

### Community 23 - "test_internal_api.py"
Cohesion: 0.08
Nodes (15): purge_old_videos(), Limpa vídeos fonte com published_at anterior a `before_date` (formato 'YYYY-MM-…, client(), fixture, RED tests for internal_api sidecar (implementação GREEN no Plan 08-07)., POST /internal/process-url com format='longo' repassa fmt='longo' pro…, POST /internal/process-url sem campo 'url' retorna 400., purge_old_videos apaga linhas sem clips e libera arquivo de linhas com clips… (+7 more)

### Community 24 - "is_seen"
Cohesion: 0.13
Nodes (15): is_seen(), _log(), mark_failed_redis(), dedup.py — Deduplicação de vídeos via Redis com fallback para MySQL. Exporta: -…, Loga mensagem com timestamp para stdout., Verifica se o vídeo já foi processado anteriormente. Consulta o Redis primeiro.…, Remove a chave do vídeo do Redis quando o download falha. Isso permite que o…, Testes ACQU-03: deduplicação via Redis com fallback para MySQL. Módulo alvo:… (+7 more)

### Community 25 - "transcribe_video"
Cohesion: 0.13
Nodes (15): _log(), _prepare_audio(), transcriber.py — Transcrição de vídeos via Groq Whisper API. Exporta: -…, Salva JSON de transcrição em disco e atualiza transcript_path no banco. Args:…, Extrai áudio MP3 de um arquivo de vídeo via ffmpeg. Args: video_path: caminho…, Transcreve um vídeo via Groq Whisper API. Args: video_id: youtube_video_id do…, save_transcript(), transcribe_video() (+7 more)

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
Cohesion: 0.09
Nodes (6): Illuminate\Http\JsonResponse, Illuminate\Http\RedirectResponse, DashboardController, SourceVideoController, SourceVideo, ClipProcessorClient

### Community 31 - "SourceChannel"
Cohesion: 0.16
Nodes (7): Illuminate\Database\Eloquent\Factories\Factory, SourceChannelController, SourceChannel, DestinationChannelFactory, GeneratedClipFactory, SourceChannelFactory, SourceVideoFactory

### Community 32 - "Illuminate\Http\Request"
Cohesion: 0.11
Nodes (11): Illuminate\Http\Request, Inertia\Middleware, Inertia\Response, AuthController, Controller, DocumentationController, NicheController, ProcessVideoController (+3 more)

### Community 33 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 34 - "video_processor.py"
Cohesion: 0.22
Nodes (10): _build_clip_context(), video_processor.py — Corte, legendas, thumbnail e processamento de clips.…, Pattern: FFmpeg Shorts Transform (crop/pad 1080x1920), Pattern: Patchable Directories (module constants for output folders), Pattern: Subtitle Burn-In (SRT from transcript segments), Phase 4 Research: Video Processing, VID-01: FFmpeg corta clip e resize 9:16 1080x1920, VID-02: Legendas Whisper queimadas no clip (+2 more)

### Community 35 - "Phase 1: Infraestrutura Base"
Cohesion: 0.26
Nodes (10): ACQU-01: Monitoramento RSS de canais, ACQU-02: Download automático 720p via yt-dlp, ACQU-03: Deduplicação Redis + MySQL UNIQUE, INFRA-01: Sistema roda em Docker, INFRA-02: Banco clips_automation com 3 tabelas, INFRA-03: Canal YouTube verificado, INFRA-04: Variáveis de ambiente e secrets, ORC-02: Status de cada job registrado no MySQL (+2 more)

### Community 36 - "Phase 7 Context: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.19
Nodes (14): rss_poller blacklist guard + target_niche SELECT extension, COPY-01 requirement: watermark burned into every clip, COPY-03 requirement: blacklisted channels never downloaded, MCAN-01 requirement: OAuth token per destination channel, MCAN-02 requirement: destination_channel_id routing by niche, MCAN-03 requirement: independent Redis quota per channel, MCAN-04 requirement: quota isolation verified between channels, Phase 07 Plan 02 Summary: RED Tests Multi-Canal e Copyright (+6 more)

### Community 37 - "run_pipeline_once"
Cohesion: 0.10
Nodes (18): Executa RSS/download/AI/video e depois publicacao. Falhas isoladas sao logadas,…, run_pipeline_once(), Sem injeção, deve criar e fechar a própria conexão., Erro em _download_pending_videos não deve propagar., Deve chamar poll → download → publish em ordem., Conexões injetadas devem ser passadas para os sub-módulos., Conexão injetada não deve ser fechada pelo runner (responsabilidade do caller)., Erro em publish_pending_clips não deve propagar — scheduler continua. (+10 more)

### Community 38 - "TelegramHttpClientHandler.php"
Cohesion: 0.14
Nodes (9): GuzzleHttp\Promise\PromiseInterface, Illuminate\Support\ServiceProvider, AppServiceProvider, static, TelegramHttpClientHandler, Phase 9 Plan 02: TelegramWebhookController + Commands Summary, Psr\Http\Message\ResponseInterface, Telegram\Bot\HttpClients\HttpClientInterface (+1 more)

### Community 39 - "confirm-button.tsx"
Cohesion: 0.20
Nodes (14): ConfirmButtonProps, AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent(), AlertDialogDescription(), AlertDialogFooter(), AlertDialogHeader() (+6 more)

### Community 40 - "notify"
Cohesion: 0.13
Nodes (18): notify(), telegram_notifier.py — Cliente HTTP que publica eventos do pipeline para o…, POST para LARAVEL_NOTIFY_URL com {event, payload}. Retorna True em 2xx, False…, Worker de TTL para clipes pending (CTRL-05). - Expira: clipes com…, Testes para telegram_notifier.py — cliente HTTP que dispara eventos para o…, notify() captura RequestException e retorna False sem propagar., notify() retorna False quando o endpoint retorna 4xx., notify() faz POST para LARAVEL_NOTIFY_URL — RED até Plan 09-03. Importa… (+10 more)

### Community 41 - "TranscriptionController.php"
Cohesion: 0.36
Nodes (3): TranscriptionController, TranscriptionJob, Symfony\Component\HttpFoundation\StreamedResponse

### Community 42 - "_download_pending_videos"
Cohesion: 0.18
Nodes (10): _download_pending_videos(), Baixa vídeos com status 'pending', um por vez, atualizando status no DB., Cursor fake cujo fetchone cai num default depois da lista informada. Os testes…, Download bem-sucedido deve atualizar status para downloaded com local_path., Download falho deve marcar failed já limpando local_path (libera a vaga)., Sem vídeos pending, não deve chamar download_video., Janela já cheia nos dois formatos não deve chamar download_video., Ordem fixa: repõe longos primeiro, depois curtos. (+2 more)

### Community 43 - "chart.tsx"
Cohesion: 0.17
Nodes (14): react, ChartConfig, ChartContainer(), ChartContext, ChartContextProps, ChartLegendContent(), ChartTooltipContent(), getPayloadConfigFromPayload() (+6 more)

### Community 44 - "utils.ts"
Cohesion: 0.12
Nodes (22): ClipQueueTabs(), OverviewCards(), quotaTone(), Badge(), badgeVariants, Card(), CardAction(), CardContent() (+14 more)

### Community 45 - "ARCHITECTURE.md (as-built, commit dca6e44)"
Cohesion: 0.15
Nodes (15): ARCHITECTURE.md (as-built, commit dca6e44), AI fallback chain (Claude → Groq → deterministic), niches table (only Laravel-migration-managed pipeline table), Quota, window and round-robin logic, source_videos.status state machine, CLAUDE.md — Canal de Cortes work instructions, Rules for destructive operations, metadata_generator.py Groq fallback fix (27/07/2026) (+7 more)

### Community 46 - "process_clip"
Cohesion: 0.18
Nodes (15): burn_subtitles(), clip-processor/src/video_processor.py, clip-processor/tests/test_clip_pipeline.py, clip-processor/tests/test_video_processor.py, cut_clip(), extract_thumbnail(), generate_srt(), 04-02-PLAN.md: video_processor.py GREEN plan (+7 more)

### Community 47 - "dependencies"
Cohesion: 0.13
Nodes (15): class-variance-authority, clsx, cmdk, @dnd-kit/core, @dnd-kit/sortable, dependencies, class-variance-authority, clsx (+7 more)

### Community 48 - "select_moments"
Cohesion: 0.24
Nodes (10): output_config json_schema em vez de prefill para Claude Haiku 4.5, generate_metadata(), insert_selected_moments(), Algoritmo de remoção de overlap por score, 03-CONTEXT.md: Phase 3 Context, _remove_overlaps(), AI-02: seleção de momentos via Claude Haiku, AI-03: filtro de qualidade score >= 7, máx 3 clips (+2 more)

### Community 49 - "YouTubeUploader"
Cohesion: 0.26
Nodes (5): Self-healing: reseta oauth_expired_flag=FALSE após upload bem-sucedido., Cliente fino para videos.insert + thumbnails.set., YouTubeUploader, Multi-canal extension via optional constructor param + None-guard retrocompat, Publisher legacy fallback when destination_channels empty

### Community 50 - "scripts"
Cohesion: 0.14
Nodes (14): scripts, dev, post-autoload-dump, post-update-cmd, pre-package-uninstall, test, Composer\\Config::disableProcessTimeout, Illuminate\\Foundation\\ComposerScripts::postAutoloadDump (+6 more)

### Community 51 - "painel/README.md (setup fresh 10 passos)"
Cohesion: 0.18
Nodes (11): Filament removal commit dca6e44, painel/ — Laravel 13 + Inertia 3 + React 19 (Filament removed), nginx bind mount painel fix (404 puro), painel/README.md (setup fresh 10 passos), routes/web.php raiz '/' redirect fix, YouTube OAuth authorization CLI flow (youtube_oauth.py), Phase 8 Plan 09: Checkpoint Final End-to-End Plan, Phase 8 Plan 09: Checkpoint Final End-to-End Summary (+3 more)

### Community 52 - "clip-processor/src/selector.py"
Cohesion: 0.22
Nodes (9): clip-processor/src/selector.py, clip-processor/tests/test_selector.py, clip-processor/tests/test_transcriber.py, mysql/init/03-schema-migration.sql, 03-01-PLAN.md: Wave 0 skeletons + RED tests, 03-01-SUMMARY.md: Wave 0 Summary, 03-03-PLAN.md: selector.py GREEN plan, 03-03-SUMMARY.md: selector.py Summary (+1 more)

### Community 53 - "composer.json"
Cohesion: 0.14
Nodes (13): description, extra, laravel, keywords, dont-discover, license, minimum-stability, name (+5 more)

### Community 54 - "_select_pending_videos"
Cohesion: 0.24
Nodes (8): Seleciona vídeos pendentes pra repor a janela de download ativo. Para cada…, _select_pending_videos(), Testes para _select_pending_videos — janela de download ativo (DOWNLOAD-01)., Janela vazia (occupied=0) deve buscar até o teto de cada formato., Formato já na janela cheia não gera nenhuma query SELECT (só o COUNT)., Déficit parcial (occupied=1 de janela 4) deve pedir LIMIT 3, não o teto inteiro., SELECT deve restringir a published_at de hoje ou ontem (FRESHNESS_DAYS=1)., TestSelectPendingVideos

### Community 55 - "mysql/init/01-clips-schema.sql"
Cohesion: 0.53
Nodes (6): mysql/init/01-clips-schema.sql, generated_clips table, 01-02-PLAN: Schema SQL clips_automation e validate-infra.sh, source_channels table, source_videos table (ENUM 9 estados), scripts/validate-infra.sh

### Community 56 - "app-shell.tsx"
Cohesion: 0.14
Nodes (13): AppSidebar(), SiteHeader(), Accordion(), AccordionContent(), AccordionItem(), AccordionTrigger(), Separator(), Toaster() (+5 more)

### Community 57 - ".planning/research/PITFALLS.md"
Cohesion: 0.15
Nodes (12): generated_clips.status state machine, list-pending-clips.sh, mark-published.sh, manual-workflow/README.md — manual clip publishing guide, n8n 06-router.json deactivation, Pitfall: Blacklist Check Happens Too Late in the Pipeline, Pitfall: Filament Delete Button Deletes MySQL Row Without Deleting Files, Pitfall: Filament Auto-Generated Resources Break on ENUM Columns (+4 more)

### Community 58 - ".planning/research/FEATURES.md"
Cohesion: 0.20
Nodes (9): irazasyed/telegram-bot-sdk ^3.16, burn_watermark() function design, Admin Panel (Laravel/Filament) feature spec, Copyright Protection feature spec, Multi-Channel YouTube Publishing feature spec, OAuth testing-mode token expiry warning (7 days), Telegram Bot in Laravel feature spec, Laravel 13 version choice (not 11) (+1 more)

### Community 59 - "cn"
Cohesion: 0.04
Nodes (75): NavItem, navItems, NavUser(), Avatar(), AvatarBadge(), AvatarFallback(), AvatarGroup(), AvatarGroupCount() (+67 more)

### Community 60 - "internal_api.py sidecar (Flask, port 8090)"
Cohesion: 0.15
Nodes (14): APScheduler jobs (ingest_cycle, publish_cycle, clip_pending_ttl), Boundary rule: painel reads directly, writes via sidecar, clip-processor service (as-built), internal_api.py sidecar (Flask, port 8090), CLIP_PROCESSOR_INTERNAL_TOKEN shared setup, Telegram Command classes (Status/Clipes/Aprovar/Rejeitar/Processar/Ajuda), Pitfall: CSRF blocking Telegram webhook (419), Pitfall: Python→Laravel via wrong Host header (404) (+6 more)

### Community 61 - "validate-phase6-n8n.py"
Cohesion: 0.53
Nodes (10): AssertionError, assert_contains(), assert_has_node(), load_json(), main(), nodes_by_name(), validate_cron(), validate_docs() (+2 more)

### Community 62 - "Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan"
Cohesion: 0.11
Nodes (19): Phase 8 Deferred Items, BOT-01 requirement (webhook + allowlist + dedup), BOT-02 requirement (6 Telegram commands), BOT-03 requirement (pipeline-event notifications), Filament $isLazy=false widget pattern, Illuminate\Foundation\Configuration\Middleware, mysql/init/05-controle-manual-migration.sql, App\Filament\Widgets\QuotaTodayWidget (+11 more)

### Community 63 - "clip-processor/src/rss_poller.py"
Cohesion: 0.27
Nodes (11): _cleanup_partial() chamado fora do loop de retry, clip-processor/src/dedup.py, clip-processor/src/dedup.py, Dedup pattern: Redis NX → fallback MySQL → False, download_video(video_id, output_path), clip-processor/src/downloader.py, is_seen(video_id, redis_client, db_conn), 02-03-PLAN: dedup.py, downloader.py, rss_poller.py (+3 more)

### Community 64 - "append_credits"
Cohesion: 0.24
Nodes (7): append_credits(), Adiciona linha de créditos ao final da descrição. Nunca sobrescreve conteúdo…, COPY-02: template vazio → retorna descrição sem modificação., COPY-02: handle vazio → retorna descrição sem modificação., Testes RED para append_credits (COPY-02)., COPY-02: template com {channel_handle} é substituído pelo handle real., TestAppendCredits

### Community 65 - "conftest.py"
Cohesion: 0.24
Nodes (10): mock_db_conn(), mock_redis(), fixture, Fixtures compartilhadas para todos os testes do clip-processor. Fornece:…, MagicMock simulando redis.Redis. - .set() retorna True por padrão (NX success —…, MagicMock simulando conexão pymysql com suporte a context manager em cursor().…, Feed RSS Atom do YouTube com 2 entradas válidas. VideoIds: 'abc123def456' e…, ID de vídeo YouTube válido (11 caracteres). (+2 more)

### Community 66 - "input-group.tsx"
Cohesion: 0.24
Nodes (9): InputGroup(), InputGroupAddon(), inputGroupAddonVariants, InputGroupButton(), inputGroupButtonVariants, InputGroupInput(), InputGroupText(), InputGroupTextarea() (+1 more)

### Community 67 - "publisher.py"
Cohesion: 0.17
Nodes (18): Handle a usar no crédito: prioriza @handle real; cai para o nome do canal fonte…, resolve_credit_handle(), _fetch_pending_clips(), _has_longo_waiting(), _log(), _mark_clip_failed(), _mark_clip_published(), _maybe_finalize_source_video() (+10 more)

### Community 68 - "queue_controls.py"
Cohesion: 0.24
Nodes (14): delete_source_video_file(), Apaga o arquivo bruto (.mp4), clips gerados (videos/clips/), thumbnails e…, can_delete_raw(), _cleanup_partial(), _kill_ffmpeg_for_clip(), _kill_ytdlp_for(), _log(), pause_video() (+6 more)

### Community 69 - "overlay_watermark"
Cohesion: 0.15
Nodes (13): _log(), overlay_watermark(), Aplica watermark PNG no canto superior direito do clip via FFmpeg. Usa…, Testes RED para overlay_watermark (COPY-01)., COPY-01: wm_path existente → ffmpeg com -filter_complex e overlay=W-w-20:20., COPY-01: wm_path ausente → retorna input_path sem chamar subprocess., TestOverlayWatermark, COPY-02 requirement: original channel credits in description (+5 more)

### Community 70 - "require-dev"
Cohesion: 0.20
Nodes (10): require-dev, fakerphp/faker, laravel/pail, laravel/pao, laravel/pint, mockery/mockery, nunomaduro/collision, pestphp/pest (+2 more)

### Community 71 - "02-04-PLAN.md: Daemon main.py Plan"
Cohesion: 0.18
Nodes (11): 02-04-PLAN.md: Daemon main.py Plan, 02-04-SUMMARY.md: Daemon main.py Summary, 02-CONTEXT.md: Phase 2 Context, 02-RESEARCH.md: Phase 2 Research, 02-VALIDATION.md: Phase 2 Validation Strategy, pytest test infra (Phase 2 Wave 0), ACQU-01: monitorar canais via RSS a cada 6h, ACQU-02: baixar vídeos novos em 720p via yt-dlp (+3 more)

### Community 72 - ".planning/research/ARCHITECTURE.md (v2.0 research, superseded)"
Cohesion: 0.28
Nodes (9): Dead code: painel/app/Filament/Pages/Dashboard.php orphan, env() outside config() pitfall in DashboardController, Section 10: Known divergences and technical debt, channel_blacklist table (research design), destination_channels table (research design), Phase 7: Schema Multi-Canal + Watermark + Copyright (research plan), Phase 8: Laravel/Filament Painel Base (research plan), Phase 9: Bot Telegram no Laravel + Migração do n8n (research plan) (+1 more)

### Community 73 - "youtube_oauth.py"
Cohesion: 0.28
Nodes (8): generate_token(), main(), Helper CLI para gerar token OAuth YouTube por canal-destino. Uso: python -m…, Gera token OAuth para o canal-destino e salva em…, docker-compose.yml branding volume for clip-processor, Path, Phase 07 Plan 07: YouTube OAuth CLI + Branding Volume, Phase 07 Plan 07 Summary: YouTube OAuth CLI + Branding Volume (paused)

### Community 74 - "run_ingest_cycle"
Cohesion: 0.18
Nodes (9): Roda RSS/download/AI (poll_all_channels + _download_pending_videos), sem…, run_ingest_cycle(), Testes para pipeline_runner.py — ciclo completo do pipeline., Deve chamar poll → download em ordem, sem publish., Erro em _download_pending_videos não deve propagar., Erro em poll_all_channels não deve impedir tentativa de download., Sem injeção, deve criar e fechar a própria conexão., Conexão injetada não deve ser fechada pelo runner. (+1 more)

### Community 75 - "02-01-PLAN: pytest scaffold RED state (Wave 0)"
Cohesion: 0.33
Nodes (9): clip-processor/tests/conftest.py, 02-01-PLAN: pytest scaffold RED state (Wave 0), 02-01-SUMMARY: 17 testes RED criados, clip-processor/pytest.ini, TDD RED-GREEN-REFACTOR pattern (imports no topo causam ModuleNotFoundError), tests/test_db.py, tests/test_dedup.py, tests/test_downloader.py (+1 more)

### Community 76 - "Phase 8 Context (Painel Laravel/Filament)"
Cohesion: 0.29
Nodes (10): PANEL-01 requirement (CRUD canal-fonte sem SQL), PANEL-02 requirement (CRUD canal-destino + badge OAuth), PANEL-03 requirement (dashboard tempo real), PANEL-04 requirement (aprovar/rejeitar clip), PANEL-05 requirement (autenticação single-user), Phase 8 human checkpoint (7-step verification), Phase 8 Plan 04: Autenticação Summary, Phase 8 Plan 06: uploader RefreshError + DestinationChannelResource Summary (+2 more)

### Community 77 - "get_db_connection"
Cohesion: 0.13
Nodes (10): get_db_connection(), Abre conexão com o MySQL usando variáveis de ambiente. Variáveis de ambiente…, BlockingScheduler, _FallbackJob, log(), shutdown(), _log(), pipeline_runner.py — Uma execucao completa do pipeline. Usado pelo daemon e… (+2 more)

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

### Community 85 - "GeneratedClip"
Cohesion: 0.22
Nodes (4): Illuminate\Database\Eloquent\Factories\HasFactory, Illuminate\Database\Eloquent\Model, GeneratedClip, StatusCommand

### Community 86 - "clip-processor/src/metadata_generator.py"
Cohesion: 0.33
Nodes (6): clip-processor/src/metadata_generator.py, clip-processor/tests/test_metadata_generator.py, 04-01-PLAN.md: Phase 4 Wave 0 skeletons + RED tests, 04-01-SUMMARY.md: Phase 4 Wave 0 Summary, 04-03-PLAN.md: metadata_generator.py GREEN plan, update_clip_metadata()

### Community 87 - "destination_channels table"
Cohesion: 0.33
Nodes (6): destination_channels table, Migration idempotente via INFORMATION_SCHEMA + prepared statement, 06-multi-canal-migration.sql, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 7 — Validation Strategy, pytest test framework (clip-processor)

### Community 88 - "test_publisher.py"
Cohesion: 0.11
Nodes (17): _fetch_destination_channels(), _fetch_pending_clips_for_channel(), Retorna clips prontos para publicar filtrados por canal-destino. Faz fairness…, Reordena clips (já em ordem created_at ASC) intercalando por source_channel_id,…, Retorna canais-destino ativos de destination_channels., _round_robin_by_source_channel(), make_mock_quota(), Testes para publisher.py — publicação de clips pendentes. (+9 more)

### Community 89 - "clip-processor/src/downloader.py"
Cohesion: 0.40
Nodes (5): clip-processor/src/downloader.py, Guard de espaço em disco antes do download (<2GB), Retry de download: 3x com 60s entre tentativas, Extração de áudio ffmpeg para arquivos >24MB, _prepare_audio()

### Community 90 - "Phase 8 Research (Painel Laravel/Filament)"
Cohesion: 0.33
Nodes (6): docker exec / Docker socket bridge anti-pattern, Pattern 3: ponte HTTP interna clip-processor↔painel, Phase 8 Plan 07: internal_api.py GREEN Plan, Phase 8 Plan 07: internal_api.py GREEN Summary, Phase 8 Research (Painel Laravel/Filament), Sidecar HTTP interno em thread daemon (antes do ciclo do pipeline)

### Community 91 - "_discard_failed_download"
Cohesion: 0.20
Nodes (10): _clips_need_raw(), _discard_failed_download(), Marca o download como 'failed' e libera a vaga que ele ocupava na janela. Antes…, Diz se algum clip desse vídeo ainda precisa do arquivo bruto em disco.…, Download falho não pode deixar arquivo em disco nem local_path preenchido. A…, Arquivo parcial em disco é apagado ANTES do UPDATE, e local_path vira NULL., Sem arquivo em disco (falha antes de escrever nada), segue e limpa a coluna., Se o arquivo sobrevive à remoção, não limpa local_path — banco não divergir do… (+2 more)

### Community 92 - "Phase 8 Plan 05: SourceChannelResource Plan"
Cohesion: 0.40
Nodes (5): Filament Resource GET/HEAD-only routing pattern, App\Filament\Resources\SourceChannelResource, routes/web.php POST/PATCH source-channels REST routes, Phase 8 Plan 05: SourceChannelResource Plan, Phase 8 Plan 05: SourceChannelResource Summary

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
Cohesion: 0.10
Nodes (17): create_transcription_job(), _download_audio(), process_transcription_job(), Executa o ciclo completo de uma transcrição local (roda em thread de…, Cria o job no banco e dispara a thread de background que processa a…, Insere um novo job em transcription_jobs com status='pending' e retorna o id…, Monta um UPDATE dinâmico só com os campos passados (não sobrescreve os demais)., Baixa o áudio da URL via yt-dlp em formato wav para TRANSCRIPTS_DIR. Raises:… (+9 more)

### Community 103 - "_process_ai_pipeline"
Cohesion: 0.16
Nodes (10): _process_ai_pipeline(), Executa transcrição + seleção para um vídeo com status downloaded. Args: conn:…, AI-04: Testes de integração do pipeline de IA no rss_poller., Configura mock_db_conn para retornar canais e vídeos downloaded em fetchall().…, AI-04: poll_all_channels chama _process_ai_pipeline para cada vídeo com status…, AI-04: Falha no pipeline de IA de um vídeo não aborta os demais., AI-04: _process_ai_pipeline chama transcribe_video e select_moments em…, AI-04: Falha na transcrição (None) marca vídeo como failed e não chama… (+2 more)

### Community 109 - "transcription_job.py"
Cohesion: 0.22
Nodes (12): _audio_duration_seconds(), _merge_srt_chunks(), transcription_job.py — Worker de "Transcrição Local" (QUICK-1). Feature isolada…, Divide o wav em `num_chunks` pedaços de duração igual via ffmpeg (recorte por…, Roda whisper-cpp local sobre um wav, gerando `<out_prefix>.srt`. Raises:…, Soma `offset_seconds` a cada timestamp de um bloco .srt (não renumera — quem…, Concatena os .srt de cada pedaço, deslocando os timestamps pelo offset…, Roda whisper-cpp sobre o áudio baixado, gerando `<job_id>.srt` em… (+4 more)

### Community 110 - "clip-processor/src/main.py"
Cohesion: 0.22
Nodes (11): BlockingScheduler daemon pattern (APScheduler), clip-processor/src/db.py, clip-processor/src/main.py, clip-processor/src/rss_poller.py, Pitfall: container restart com vídeo em status downloading, 03-04-PLAN.md: AI pipeline integration plan, 03-04-SUMMARY.md: AI pipeline integration Summary, poll_all_channels(db_conn, redis_client) (+3 more)

### Community 111 - "Plano de migração — Oracle Cloud (Always Free)"
Cohesion: 0.18
Nodes (11): 1. Não fazer upgrade para Pay As You Go (a camada que realmente importa), 2. Provisionar só recursos com o selo "Always Free-eligible", 3. Orçamento com alerta em US$ 1, 4. Conferência após provisionar, Como o custo zero é garantido, Decisão tomada, Depois da migração, Fontes (+3 more)

### Community 113 - "run_ttl_once"
Cohesion: 0.21
Nodes (8): Executa 1 iteração do TTL: expira clipes >TTL_HOURS, avisa clipes WARN_HOURS-…, run_ttl_once(), Testes para ttl_worker.py — expiração automática de clips pending. Estado RED…, run_ttl_once: clips pending > TTL_HOURS são marcados rejected via UPDATE., run_ttl_once: clips entre WARN_HOURS e TTL_HOURS disparam notify() para Laravel., Redis SET NX False (já avisou): NÃO dispara notify() extra., TestExpire, TestWarn

### Community 114 - "rejeitar"
Cohesion: 0.17
Nodes (13): internal_api.reject_clip(clip_id) — calls src.rejeitar.rejeitar directly, Chama src.rejeitar.rejeitar(clip_id) diretamente. Preserva exit codes 0/1/2., reject_clip(), rejeitar.py — Rejeição manual de clip via comando /rejeitar do Telegram…, Marca o clip como rejected, remove o MP4 do disco, preserva raw video.…, rejeitar(), Testes para rejeitar.py — comando /rejeitar do Telegram. Estado RED até Plan…, rejeitar(123): executa UPDATE generated_clips SET status='rejected' WHERE… (+5 more)

### Community 119 - "Phase 6 Plan 07: workflows n8n completos + setup operacional + smoke E2E"
Cohesion: 0.27
Nodes (10): mysql/manual-workflow/approve-backlog.sql — helper opcional para backlog de pending, mysql/manual-workflow/approve-backlog.sql, Phase 6 Plan 07: workflows n8n completos + setup operacional + smoke E2E, Phase 6 Plan 07 Summary, Continue Here - Phase 6 Plan 06-07 (Telegram/n8n manual checkpoint), scripts/validate-phase6-n8n.py, telegram-n8n/SETUP.md (Cloudflare Tunnel + Telegram setWebhook), telegram-n8n/workflows/06-cron-resumo-diario.json (+2 more)

### Community 120 - "clip-processor/src/transcriber.py"
Cohesion: 0.22
Nodes (10): clip-processor/src/transcriber.py, Groq Whisper whisper-large-v3-turbo + verbose_json + timestamp_granularities segment + pt, 03-02-PLAN.md: transcriber.py GREEN plan, 03-02-SUMMARY.md: transcriber.py Summary, _process_ai_pipeline(), AI-01: transcrição via Groq Whisper, save_transcript(), Lookup de source_video_id INT via SELECT antes de INSERT em generated_clips (+2 more)

### Community 122 - "Quick Task 1: Transcrição Local Summary"
Cohesion: 0.15
Nodes (12): Accomplishments, Auto-fixed Issues, Decisions Made, Deviations from Plan, Files Created/Modified, Issues Encountered, Next Phase Readiness, Performance (+4 more)

### Community 123 - "toggle-group.tsx"
Cohesion: 0.43
Nodes (5): ToggleGroup(), ToggleGroupContext, ToggleGroupItem(), Toggle(), toggleVariants

### Community 124 - "mysql/init/06-multi-canal-migration.sql"
Cohesion: 0.28
Nodes (9): mysql/init/06-multi-canal-migration.sql, destination_channels table (slug, name, niche, youtube_channel_id, credit_template, active), generated_clips.destination_channel_id FK to destination_channels, INFORMATION_SCHEMA + prepared statements idempotent migration pattern, MCAN-01..04, COPY-01..03: requirements multi-canal (channel_slug, destination_channel_id, quota por canal, blacklist, watermark, credits), Phase 7 Plan 01: Schema Multi-Canal Migration, Phase 7 Plan 01 Summary, Phase 7 Plan 02: Extender testes multi-canal (RED state) (+1 more)

### Community 153 - "05-03 Plan: YouTube uploader"
Cohesion: 0.22
Nodes (9): clip-processor/requirements.txt, YouTubeUploader.upload_clip(clip), YOUTUBE_TOKEN_FILE (default /app/token.json), 05-03 Plan: YouTube uploader, 05-03 Summary: YouTubeUploader implemented, 05-04 Plan: Publisher and raw cleanup, 05-04 Summary: Publisher implemented, PROJECT_BRIEF.md — Canal de Cortes as-built brief (+1 more)

### Community 154 - "Phase 6 Plan 05: TTL Worker (expire 48h + warn 24h)"
Cohesion: 0.25
Nodes (9): CTRL-01: Telegram allowlist (chat_id 5760918317, silêncio para outros), CTRL-02: publisher.py seleciona clips 'approved' (não mais 'pending'), CTRL-05: TTL worker expira pending>48h, avisa 24h antes, CTRL-06: notificações proativas via Cloudflare Tunnel + n8n webhook, Phase 6 Plan 02: Publisher swap pending→approved + guard de status, Phase 6 Plan 02 Summary, Phase 6 Plan 05: TTL Worker (expire 48h + warn 24h), Phase 6 Plan 05 Summary (+1 more)

### Community 155 - "README.md"
Cohesion: 0.25
Nodes (4): Como atualizar estes documentos, Docs — Canal de Cortes, Estado atual em uma tela, Onde está cada coisa

### Community 156 - "TestProcessClipWithWatermark"
Cohesion: 0.33
Nodes (4): Testes de integração: process_clip aplica overlay_watermark com slug do canal-…, MCAN-02: process_clip chama overlay_watermark com watermark_path derivado do…, MCAN-02: destination_channel_slug NULL → os.rename é usado, overlay_watermark…, TestProcessClipWithWatermark

### Community 157 - "Backlog de bugs"
Cohesion: 0.22
Nodes (9): 1. FEITO — Órfãos de download nunca eram apagados, 2. ABERTO — `_raw.mp4` nunca é apagado (maior consumidor de disco), 3. SUSPEITA — Thumbnail não aplicada nos vídeos longos no YouTube, 4. ABERTO — Estados sem recuperação automática seguram arquivo em disco, 5. ABERTO — `_subtitled.mp4` órfão, 6. ABERTO — Painel não consegue apagar o backlog de download, 7. ABERTO — 4 testes de `test_pipeline_runner.py` falhando, 8. ABERTO — Docker Desktop travado sob pressão de disco (+1 more)

### Community 158 - "Sistema — `painel/`"
Cohesion: 0.22
Nodes (9): A regra da fronteira, Armadilhas conhecidas, Autenticação, Banco, Como ler o Dashboard, O que é, Páginas, Sistema — `painel/` (+1 more)

### Community 159 - "v1.0 — Pipeline Base"
Cohesion: 0.53
Nodes (6): v1.0 — Pipeline Base, MANUAL_APPROVAL_REQUIRED toggle, Phase 3: IA — Transcrição e Seleção, Phase 4: Processamento de Vídeo, Phase 5: Publicação e Automação Total, Phase 6: Controle Manual N8N + Telegram

### Community 160 - "clip-processor/src/db.py"
Cohesion: 0.50
Nodes (5): db.py: quem chama é responsável por fechar a conexão, clip-processor/src/db.py, INSERT IGNORE para idempotência de vídeos/canais, 02-02-PLAN: docker-compose + requirements + seed + db.py, 02-02-SUMMARY: db.py GREEN, seed 5 canais

### Community 161 - "Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)"
Cohesion: 0.25
Nodes (8): mysql/init/05-controle-manual-migration.sql, CTRL-03: /rejeitar <id> marca rejected + apaga MP4 mantém raw, Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons), Phase 6 Plan 01 Summary, Phase 6 Plan 03: Implementar rejeitar.py, Phase 6 Plan 03 Summary, Phase 6 Validation Strategy, Wave 0 scaffolding: stubs Python com NotImplementedError + testes RED antes de qualquer implementação

### Community 162 - "autoload-dev"
Cohesion: 0.67
Nodes (3): autoload-dev, psr-4, Tests\\

### Community 164 - "post-create-project-cmd"
Cohesion: 0.50
Nodes (4): post-create-project-cmd, @php artisan key:generate --ansi, @php artisan migrate --graceful --ansi, @php -r \"file_exists('database/database.sqlite') || touch('database/database.sqlite');\

### Community 168 - "clip-processor/src/publisher.py"
Cohesion: 0.36
Nodes (8): clip-processor/src/pipeline_runner.py, clip-processor/src/publisher.py, clip-processor/src/rejeitar.py, clip-processor/src/telegram_notifier.py, Phase 6 Plan 06: telegram_notifier + Cloudflare Tunnel, Phase 6 Plan 06 Summary, Status guard em UPDATE (WHERE id=%s AND status='X' + rowcount check) — defesa contra race condition, Webhook proxy pattern: clip-processor não conhece TELEGRAM_BOT_TOKEN, notifica via webhook interno do n8n

### Community 172 - "Fases"
Cohesion: 0.25
Nodes (8): Fase 0 — Conta e blindagem de cobrança  ⬜ NÃO INICIADA, Fase 1 — Corrigir os vazamentos antes de migrar  ⬜ NÃO INICIADA, Fase 2 — Provisionar a instância  ⬜ NÃO INICIADA, Fase 3 — Compose próprio, sem os outros projetos  ⬜ NÃO INICIADA, Fase 4 — Dados e segredos  ⬜ NÃO INICIADA, Fase 5 — Acesso ao painel  ⬜ NÃO INICIADA, Fase 6 — Cutover  ⬜ NÃO INICIADA, Fases

### Community 173 - "Mapa dos módulos"
Cohesion: 0.25
Nodes (8): Aquisição, Entrada manual, Inteligência, Interface com o painel, Mapa dos módulos, Orquestração, Produção de vídeo, Publicação

### Community 174 - "Rotas"
Cohesion: 0.33
Nodes (6): Canais, Dashboard — `DashboardController`, Outros, Públicas, sem CSRF, Rotas, Vídeos — `SourceVideoController`

### Community 176 - "04-04 Summary: Poller Integration Summary"
Cohesion: 0.40
Nodes (5): Migration Phase 3 usa INFORMATION_SCHEMA em vez de ADD COLUMN IF NOT EXISTS, Persistir arquivos renderizados no volume montado /app/videos, Raw source só removido quando todos clips do source video estão terminais, mysql/init/03-schema-migration.sql, 04-04 Summary: Poller Integration Summary

### Community 177 - "Sistema — `clip-processor`"
Cohesion: 0.40
Nodes (5): Artefatos em disco, O que o Redis guarda (e o que não guarda), O que é, Sistema — `clip-processor`, Testes

### Community 178 - "test_uploader.py"
Cohesion: 0.50
Nodes (3): make_uploader(), Testes para YouTubeUploader — upload de clips e thumbnails. Todas as chamadas…, Cria YouTubeUploader com credenciais e YouTube mockados.

### Community 179 - "Phase 6 Plan 04: Implementar processar.py"
Cohesion: 0.67
Nodes (3): CTRL-04: /processar <url> ingestão manual de vídeo YouTube, Phase 6 Plan 04: Implementar processar.py, Phase 6 Plan 04 Summary

## Ambiguous Edges - Review These
- `clip-processor/src/ttl_worker.py` → `clip-processor/src/telegram_notifier.py`  [AMBIGUOUS]
  .planning/phases/06-controle-manual-n8n-telegram/06-05-SUMMARY.md · relation: conceptually_related_to

## Knowledge Gaps
- **333 isolated node(s):** `force-download.sh script`, `$schema`, `style`, `rsc`, `tsx` (+328 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `clip-processor/src/ttl_worker.py` and `clip-processor/src/telegram_notifier.py`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `run_pipeline_once()` connect `run_pipeline_once` to `publish_pending_clips`, `publisher.py`, `rss_poller.py`, `notify`, `_download_pending_videos`, `run_ingest_cycle`, `get_db_connection`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `n8n/workflows/canaldecortes-pipeline.json` connect `run_pipeline_once` to `05-01 Plan: Publishing schema, skeletons and RED tests`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `05-06 Plan: n8n workflow and production checkpoint` connect `run_pipeline_once` to `Phase 6 Plan 07: workflows n8n completos + setup operacional + smoke E2E`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `QuotaManager` (e.g. with `TestCanUpload` and `TestLongoReservation`) actually correct?**
  _`QuotaManager` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `YouTubeUploader` (e.g. with `TestUploadClip` and `TestYouTubeUploaderChannelSlug`) actually correct?**
  _`YouTubeUploader` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `force-download.sh script`, `$schema`, `style` to the rest of the system?**
  _333 weakly-connected nodes found - possible documentation gaps or missing edges._