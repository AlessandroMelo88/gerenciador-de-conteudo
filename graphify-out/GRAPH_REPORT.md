# Graph Report - gerenciador-de-conteudo  (2026-08-25)

## Corpus Check
- 393 files · ~363,820 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2708 nodes · 4484 edges · 206 communities (172 shown, 34 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 85 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `213a0762`
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
- providers.php
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
- page-header.tsx
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
- @dnd-kit/core
- shadcn
- ziggy-js
- @tailwindcss/typography
- backup-mysql.sh
- backup-postgres.sh
- restore-mysql.sh
- restore-postgres.sh
- clip-processor

## God Nodes (most connected - your core abstractions)
1. `cn()` - 199 edges
2. `react` - 49 edges
3. `QuotaManager` - 42 edges
4. `publish_pending_clips()` - 36 edges
5. `YouTubeUploader` - 36 edges
6. `ClipProcessorClient` - 32 edges
7. `get_db_connection()` - 31 edges
8. `poll_all_channels()` - 25 edges
9. `process_clip()` - 23 edges
10. `GeneratedClip` - 23 edges

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

## Communities (206 total, 34 thin omitted)

### Community 0 - "SourceVideos.tsx"
Cohesion: 0.05
Nodes (41): categories, correctness, perf, suspicious, env, browser, es2024, ignorePatterns (+33 more)

### Community 1 - "publish_pending_clips"
Cohesion: 0.05
Nodes (58): _fetch_destination_channels(), _fetch_pending_clips(), _fetch_pending_clips_for_channel(), _has_longo_waiting(), _log(), _mark_clip_failed(), _mark_clip_published(), _maybe_finalize_source_video() (+50 more)

### Community 2 - "db.py"
Cohesion: 0.05
Nodes (40): insert_video(), _log(), db.py — Módulo de acesso ao PostgreSQL para o daemon clip-processor.  Exporta:, Redefine vídeos presos em status 'downloading' de volta para 'pending'.      Exe, Devolve vídeos presos em 'selecting' para 'downloaded' (reprocessa a IA).      ', Loga mensagem com timestamp para stdout., Atualiza o status de um vídeo na tabela source_videos.      `local_path=None` si, Insere um novo vídeo na tabela source_videos com status 'pending'.      Usa ON C (+32 more)

### Community 3 - "SourceChannels.tsx"
Cohesion: 0.08
Nodes (28): ActiveWindowTable(), postAction(), SortableRow(), STATUS_LABEL, useSelection(), VideoActions(), VideoCells(), VideoTable() (+20 more)

### Community 4 - "QuotaManager"
Cohesion: 0.27
Nodes (6): datetime, QuotaManager, Controla uploads diarios do YouTube por data local de Sao_Paulo.      MAX_LONGO_, Janela + cota total, ignorando reserva por formato.          Usado para decidir, Retorna True se horario e quota (total + formato/reserva) permitirem upload., Incrementa contador diario (total e, se 'longo', o de formato) e garante TTL.

### Community 5 - "Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel"
Cohesion: 0.05
Nodes (63): mysql/init/05-controle-manual-migration.sql, mysql/init/06-multi-canal-migration.sql, mysql/manual-workflow/approve-backlog.sql — helper opcional para backlog de pending, APScheduler dentro do clip-processor (vs n8n cron) para TTL worker, clip-processor/src/pipeline_runner.py, clip-processor/src/processar.py, clip-processor/src/publisher.py, clip-processor/src/rejeitar.py (+55 more)

### Community 6 - "rss_poller.py"
Cohesion: 0.05
Nodes (42): is_seen(), _log(), mark_failed_redis(), dedup.py — Deduplicação de vídeos via Redis com fallback para PostgreSQL.  Expor, Loga mensagem com timestamp para stdout., Verifica se o vídeo já foi processado anteriormente.      Consulta o Redis prime, Remove a chave do vídeo do Redis quando o download falha.      Isso permite que, _detect_format() (+34 more)

### Community 7 - "insert_selected_moments"
Cohesion: 0.06
Nodes (37): _enforce_longform_duration(), _filter_shortform_duration(), insert_selected_moments(), _log(), _lookup_destination_channel_id(), _normalize_scores(), _parse_moments(), selector.py — Seleção de momentos via IA com fallback automático.  Prioridade em (+29 more)

### Community 8 - "User.php"
Cohesion: 0.08
Nodes (14): Filament\Models\Contracts\FilamentUser interface, Illuminate\Console\Command, Illuminate\Database\Console\Seeds\WithoutModelEvents, Illuminate\Database\Seeder, Illuminate\Foundation\Auth\User, Illuminate\Foundation\Testing\TestCase, Illuminate\Notifications\Notifiable, CreatePainelUser (+6 more)

### Community 9 - "Phase 08 Plan 03: Eloquent Models, Factories, RED tests (Laravel side)"
Cohesion: 0.06
Nodes (52): AssertionError, canaldecortes/docker/nginx/canaldecortes.conf vhost, generate_token(), main(), Helper CLI para gerar token OAuth YouTube por canal-destino.  Uso:     python -m, Gera token OAuth para o canal-destino e salva em /app/youtube/token-{slug}.json., docker-compose.yml branding volume for clip-processor, clip-processor não tem bind mount de src/ — exige rebuild+restart para refletir código (+44 more)

### Community 10 - "internal_api.py"
Cohesion: 0.23
Nodes (21): internal_api.resolve_channel(url) — yt-dlp channel resolution, _check_auth(), delete_source_video_file(), internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.  Endpoints, Roda yt-dlp em modo metadata-only e extrai id/name/handle.      Padrão yt-dlp: -, Apaga o arquivo bruto (.mp4), clips gerados (videos/clips/), thumbnails e arquiv, resolve_channel(), _route_delete_source_video() (+13 more)

### Community 11 - "selector.py"
Cohesion: 0.05
Nodes (39): 10. **`_log()` reimplementado 12×, `flush` inconsistente, tags duplas e nenhum traceback**, 11. **Sem `config.py`: env parseada em import por 7 módulos, com defaults divergentes**, 12. **`publisher.py`: dois loops de publicação quase idênticos e código morto**, 13. **`pipeline_runner.py`: ciclo de vida de conexão e try/except+notify copiados 3×/6×**, 14. **Duas funções chamadas `_cleanup_partial` com garantias opostas, importadas como privadas entre módulos**, 15. **Escritas em `generated_clips` espalhadas por 8 módulos; `db.py` só conhece `source_videos`**, 16. **`select_moments`: filtro de Short curto é código morto e pós-processamento duplicado**, 17. **yt-dlp invocado de 3 jeitos diferentes; duas regex de video id** (+31 more)

### Community 12 - "DestinationChannels.tsx"
Cohesion: 0.06
Nodes (56): ConfirmButton(), Niche, NicheCombobox(), slugify(), Command(), CommandDialog(), CommandEmpty(), CommandGroup() (+48 more)

### Community 13 - "processar.py"
Cohesion: 0.10
Nodes (21): fetch_metadata(), main(), _normalize_upload_date(), parse_video_id(), processar.py — Ingestão manual de vídeo YouTube via comando /processar do Telegr, Entrypoint CLI. Exit codes:       - 0: OK (inserido ou já existia)       - 2: UR, Extrai videoId de 11 caracteres de uma URL YouTube. None se URL inválida.      S, Converte 'YYYYMMDD' (formato yt-dlp) para 'YYYY-MM-DD HH:MM:SS' (TIMESTAMPTZ). (+13 more)

### Community 14 - "devDependencies"
Cohesion: 0.07
Nodes (29): concurrently, laravel-vite-plugin, oxlint, devDependencies, concurrently, laravel-vite-plugin, oxlint, prettier (+21 more)

### Community 15 - "field.tsx"
Cohesion: 0.10
Nodes (21): AppSidebar(), SiteHeader(), Field(), FieldContent(), FieldDescription(), FieldError(), FieldLegend(), FieldSeparator() (+13 more)

### Community 16 - "publisher.py"
Cohesion: 0.08
Nodes (30): Blacklist guard (source_channels.blacklisted), COPY-01: watermark queimado via FFmpeg, COPY-02: descrição inclui créditos do canal original, COPY-03: canais blacklistados bloqueados no RSS poller, credit_template / channel_handle credits, generated_clips.destination_channel_id FK, MCAN-01: múltiplos canais YouTube com OAuth próprio, MCAN-02: campo niche determina canal-destino (+22 more)

### Community 17 - "05-01 Plan: Publishing schema, skeletons and RED tests"
Cohesion: 0.12
Nodes (22): quota_manager.py — Limite diario e janela de horario para uploads YouTube.  Expo, YouTubeUploader.upload_clip(clip), MAX_UPLOADS_PER_DAY clamped to <= 6, default 2, YOUTUBE_TOKEN_FILE (default /app/token.json), mysql/init/04-publishing-migration.sql, Pattern: clock injection para testes deterministas, 05-01 Plan: Publishing schema, skeletons and RED tests, 05-01 Summary: publishing migration + TDD suite (+14 more)

### Community 18 - "Telegram\Bot\Commands\Command"
Cohesion: 0.12
Nodes (11): POST /internal/resolve-channel (sidecar endpoint), CreateSourceChannel Page, AjudaCommand, AprovarCommand, ClipesCommand, ProcessarCommand, RejeitarCommand, StatusCommand (+3 more)

### Community 19 - "TestUploadClip"
Cohesion: 0.11
Nodes (12): make_youtube_mock(), token_file inexistente deve levantar FileNotFoundError., Se thumbnail_path existir, thumbnails().set() deve ser chamado., Cria um mock do serviço YouTube que simula upload bem-sucedido., Falha no upload da thumbnail deve ser propagada ao caller., Tags em formato string separado por vírgula devem virar lista., YOUTUBE_PRIVACY_STATUS do env deve ser usado no upload., Upload bem-sucedido deve retornar o youtube_video_id. (+4 more)

### Community 20 - "uploader.py"
Cohesion: 0.13
Nodes (13): Credentials, MediaFileUpload, uploader.py — Upload de clips para YouTube Data API v3.  Exporta:   - YouTubeUpl, Default privacyStatus=private, configuravel por YOUTUBE_PRIVACY_STATUS, destination_channels.oauth_expired_flag column, google.auth.exceptions.RefreshError, Fallback determinístico de metadata (não bloqueia pipeline), App\Filament\Resources\DestinationChannelResource (+5 more)

### Community 21 - "generate_metadata"
Cohesion: 0.13
Nodes (19): Anthropic structured outputs via output_config json_schema, _build_prompt(), generate_metadata(), _generate_via_anthropic(), _generate_via_groq(), _log(), _normalize_metadata(), metadata_generator.py — Geração de título, descrição e tags para YouTube.  Expor (+11 more)

### Community 22 - "process_clip"
Cohesion: 0.12
Nodes (16): _build_clip_context(), cut_clip(), extract_thumbnail(), _fetch_clip(), process_clip(), Extrai um frame do clip como thumbnail JPG., Processa um registro de generated_clips com status pending_cut.      Pipeline: c, Corta um trecho do vídeo fonte.      fmt='curto' (padrão): converte pra vertical (+8 more)

### Community 23 - "test_internal_api.py"
Cohesion: 0.08
Nodes (15): purge_old_videos(), Limpa vídeos fonte com published_at anterior a `before_date` (formato 'YYYY-MM-D, client(), fixture, RED tests for internal_api sidecar (implementação GREEN no Plan 08-07)., POST /internal/process-url com format='longo' repassa fmt='longo' pro processar_, POST /internal/process-url sem campo 'url' retorna 400., purge_old_videos apaga linhas sem clips e libera arquivo de linhas com clips (+7 more)

### Community 24 - "is_seen"
Cohesion: 0.05
Nodes (36): 10. Riscos e mitigação, 11. Fora de escopo neste plano, 1. Situação atual (verificada em 13/08/2026), 2. Versões confirmadas (regra `docs-first`), 3. Por onde o prompt deve trafegar — decisão, 4.1 `ai_prompts` — o *slot*, 4.2 `ai_prompt_versions` — histórico imutável, 4.3 `generated_clips.ai_prompt_version_id` (+28 more)

### Community 25 - "transcribe_video"
Cohesion: 0.13
Nodes (15): _log(), _prepare_audio(), transcriber.py — Transcrição de vídeos via Groq Whisper API.  Exporta:   - trans, Salva JSON de transcrição em disco e atualiza transcript_path no banco.      Arg, Extrai áudio MP3 de um arquivo de vídeo via ffmpeg.      Args:         video_pat, Transcreve um vídeo via Groq Whisper API.      Args:         video_id: youtube_v, save_transcript(), transcribe_video() (+7 more)

### Community 26 - "DestinationChannel"
Cohesion: 0.13
Nodes (10): Illuminate\Foundation\Configuration\Middleware, Illuminate\Http\JsonResponse, Illuminate\Http\Request, Illuminate\Http\Response, Inertia\Middleware, DestinationChannelController, TelegramWebhookController, HandleInertiaRequests (+2 more)

### Community 27 - "components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 28 - "docker-compose.yml (raiz wordpress/)"
Cohesion: 0.12
Nodes (20): ANTHROPIC_API_KEY intencionalmente vazia até Phase 3, clip-processor/Dockerfile, CLIP_PROCESSOR_INTERNAL_TOKEN env var, clip-processor service (build local), CLIPS_DB_PASSWORD como placeholder no SQL, docker-compose.yml (raiz wordpress/), .env (secrets reais), N8N_ENCRYPTION_KEY via ${VAR} nunca hardcoded (+12 more)

### Community 29 - "download_video"
Cohesion: 0.08
Nodes (25): _cleanup_partial(), cleanup_stale_downloads(), download_video(), _log(), downloader.py — Download de vídeos YouTube via yt-dlp com disk guard e retry.  E, Baixa um vídeo do YouTube em formato 720p mp4.      Returns:         True se dow, Loga mensagem com timestamp para stdout., Deleta artefatos de trabalho do yt-dlp gerados por download incompleto.      O g (+17 more)

### Community 30 - "Illuminate\Http\RedirectResponse"
Cohesion: 0.17
Nodes (3): Illuminate\Http\RedirectResponse, DashboardController, GeneratedClip

### Community 31 - "SourceChannel"
Cohesion: 0.15
Nodes (7): Illuminate\Database\Eloquent\Factories\HasFactory, Illuminate\Database\Eloquent\Model, NicheController, SourceChannelController, Niche, SourceChannel, SourceVideoFactory

### Community 32 - "Illuminate\Http\Request"
Cohesion: 0.15
Nodes (6): Inertia\Response, AuthController, Controller, DocumentationController, ProcessVideoController, SettingsController

### Community 33 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 34 - "video_processor.py"
Cohesion: 0.14
Nodes (15): burn_subtitles(), _format_srt_time(), generate_srt(), video_processor.py — Corte, legendas, thumbnail e processamento de clips.  Expor, Queima legendas SRT no clip usando FFmpeg.      Alignment=2 (rodapé-centro), est, Gera arquivo SRT relativo ao início do clip a partir dos segmentos Whisper., TestSubtitles, Pattern: FFmpeg Shorts Transform (crop/pad 1080x1920) (+7 more)

### Community 35 - "Phase 1: Infraestrutura Base"
Cohesion: 0.18
Nodes (16): v1.0 — Pipeline Base, MANUAL_APPROVAL_REQUIRED toggle, ACQU-01: Monitoramento RSS de canais, ACQU-02: Download automático 720p via yt-dlp, ACQU-03: Deduplicação Redis + MySQL UNIQUE, INFRA-01: Sistema roda em Docker, INFRA-02: Banco clips_automation com 3 tabelas, INFRA-03: Canal YouTube verificado (+8 more)

### Community 36 - "Phase 7 Context: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.15
Nodes (17): rss_poller blacklist guard + target_niche SELECT extension, COPY-01 requirement: watermark burned into every clip, COPY-02 requirement: original channel credits in description, COPY-03 requirement: blacklisted channels never downloaded, Dual-layer blacklist guard pattern (SQL filter + Python loop guard), Graceful degradation pattern: return input unchanged when optional dependency missing, MCAN-01 requirement: OAuth token per destination channel, MCAN-02 requirement: destination_channel_id routing by niche (+9 more)

### Community 37 - "run_pipeline_once"
Cohesion: 0.05
Nodes (37): A1. `/internal/pipeline-event` é fail-open quando o token está vazio (e a comparação não é constant-time), A2. `ConnectionException` não é `RuntimeException` — clip-processor fora do ar vira página 500, A3. Guard `canDelete` diverge entre Dashboard e Vídeos, e os docblocks mentem sobre a cascata do sidecar, A4. `tests/Feature/ExampleTest.php` grava usuário com senha `password` no banco real a cada `php artisan test`, A5. Strings mágicas de status em 30+ pontos → Enums PHP, A6. `env()` fora de `config/` **(já catalogado: ARCHITECTURE §10 item 10; SISTEMA-PAINEL "Armadilhas" 1)**, Alta, B10. `NicheController` sem feedback e sem ciclo de vida (+29 more)

### Community 38 - "TelegramHttpClientHandler.php"
Cohesion: 0.14
Nodes (8): GuzzleHttp\Promise\PromiseInterface, Illuminate\Support\ServiceProvider, AppServiceProvider, static, TelegramHttpClientHandler, Psr\Http\Message\ResponseInterface, Telegram\Bot\HttpClients\HttpClientInterface, Laravel Http adapter for SDK (enables Http::fake())

### Community 39 - "confirm-button.tsx"
Cohesion: 0.15
Nodes (16): ConfirmButtonProps, LoginForm(), AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent(), AlertDialogDescription(), AlertDialogFooter() (+8 more)

### Community 40 - "notify"
Cohesion: 0.05
Nodes (45): _download_pending_videos(), _log(), pipeline_runner.py — Uma execucao completa do pipeline.  Usado pelo daemon e pel, Baixa vídeos com status 'pending', um por vez, atualizando status no DB., Executa RSS/download/AI/video e depois publicacao.      Falhas isoladas sao loga, Roda só a publicação de clips aprovados, sem RSS/download/AI.      Existe pra dr, Roda RSS/download/AI (poll_all_channels + _download_pending_videos), sem publish, run_ingest_cycle() (+37 more)

### Community 41 - "TranscriptionController.php"
Cohesion: 0.36
Nodes (3): TranscriptionController, TranscriptionJob, Symfony\Component\HttpFoundation\StreamedResponse

### Community 42 - "_download_pending_videos"
Cohesion: 0.18
Nodes (8): Cursor fake cujo fetchone cai num default depois da lista informada.          Os, Download bem-sucedido deve atualizar status para downloaded com local_path., Download falho deve marcar failed já limpando local_path (libera a vaga)., Sem vídeos pending, não deve chamar download_video., Janela já cheia nos dois formatos não deve chamar download_video., Ordem fixa: repõe longos primeiro, depois curtos., Importar main.py não deve iniciar o scheduler (coalesce = True verificado via im, TestDownloadPendingVideos

### Community 43 - "chart.tsx"
Cohesion: 0.23
Nodes (10): ChartConfig, ChartContext, ChartContextProps, ChartLegendContent(), ChartTooltipContent(), getPayloadConfigFromPayload(), INITIAL_DIMENSION, THEMES (+2 more)

### Community 44 - "utils.ts"
Cohesion: 0.18
Nodes (15): OverviewCards(), quotaTone(), Badge(), badgeVariants, Card(), CardAction(), CardContent(), CardDescription() (+7 more)

### Community 45 - "ARCHITECTURE.md (as-built, commit dca6e44)"
Cohesion: 0.15
Nodes (15): ARCHITECTURE.md (as-built, commit dca6e44), AI fallback chain (Claude → Groq → deterministic), niches table (only Laravel-migration-managed pipeline table), Quota, window and round-robin logic, source_videos.status state machine, CLAUDE.md — Canal de Cortes work instructions, Rules for destructive operations, metadata_generator.py Groq fallback fix (27/07/2026) (+7 more)

### Community 46 - "process_clip"
Cohesion: 0.18
Nodes (15): burn_subtitles(), clip-processor/src/video_processor.py, clip-processor/tests/test_clip_pipeline.py, clip-processor/tests/test_video_processor.py, cut_clip(), extract_thumbnail(), generate_srt(), 04-02-PLAN.md: video_processor.py GREEN plan (+7 more)

### Community 47 - "dependencies"
Cohesion: 0.08
Nodes (25): class-variance-authority, cmdk, @dnd-kit/sortable, @fontsource-variable/geist, @inertiajs/react, lucide-react, dependencies, class-variance-authority (+17 more)

### Community 48 - "select_moments"
Cohesion: 0.17
Nodes (15): output_config json_schema em vez de prefill para Claude Haiku 4.5, generate_metadata(), insert_selected_moments(), Algoritmo de remoção de overlap por score, 03-CONTEXT.md: Phase 3 Context, _process_ai_pipeline(), _remove_overlaps(), AI-01: transcrição via Groq Whisper (+7 more)

### Community 49 - "YouTubeUploader"
Cohesion: 0.21
Nodes (6): Marca destination_channels.oauth_expired_flag=TRUE para o slug atual.          B, Self-healing: reseta oauth_expired_flag=FALSE após upload bem-sucedido., Cliente fino para videos.insert + thumbnails.set., YouTubeUploader, Multi-canal extension via optional constructor param + None-guard retrocompat, Publisher legacy fallback when destination_channels empty

### Community 50 - "scripts"
Cohesion: 0.13
Nodes (16): scripts, post-autoload-dump, post-root-package-install, post-update-cmd, pre-package-uninstall, setup, composer install, Illuminate\\Foundation\\ComposerScripts::postAutoloadDump (+8 more)

### Community 51 - "painel/README.md (setup fresh 10 passos)"
Cohesion: 0.22
Nodes (9): Filament removal commit dca6e44, painel/ — Laravel 13 + Inertia 3 + React 19 (Filament removed), clip-processor/requirements.txt, CLIP_PROCESSOR_INTERNAL_TOKEN shared setup, painel/README.md (setup fresh 10 passos), YouTube OAuth authorization CLI flow (youtube_oauth.py), Filament 5.x version choice (not 3), PROJECT_BRIEF.md — Canal de Cortes as-built brief (+1 more)

### Community 52 - "clip-processor/src/selector.py"
Cohesion: 0.15
Nodes (14): clip-processor/src/selector.py, clip-processor/src/transcriber.py, clip-processor/tests/test_selector.py, clip-processor/tests/test_transcriber.py, Groq Whisper whisper-large-v3-turbo + verbose_json + timestamp_granularities segment + pt, mysql/init/03-schema-migration.sql, 03-01-PLAN.md: Wave 0 skeletons + RED tests, 03-01-SUMMARY.md: Wave 0 Summary (+6 more)

### Community 53 - "composer.json"
Cohesion: 0.14
Nodes (13): autoload-dev, psr-4, description, extra, laravel, dont-discover, license, minimum-stability (+5 more)

### Community 54 - "_select_pending_videos"
Cohesion: 0.24
Nodes (8): Seleciona vídeos pendentes pra repor a janela de download ativo.      Para cada, _select_pending_videos(), Testes para _select_pending_videos — janela de download ativo (DOWNLOAD-01)., Janela vazia (occupied=0) deve buscar até o teto de cada formato., Formato já na janela cheia não gera nenhuma query SELECT (só o COUNT)., Déficit parcial (occupied=1 de janela 4) deve pedir LIMIT 3, não o teto inteiro., SELECT deve restringir a published_at de hoje ou ontem (FRESHNESS_DAYS=1)., TestSelectPendingVideos

### Community 55 - "mysql/init/01-clips-schema.sql"
Cohesion: 0.24
Nodes (12): mysql/init/01-clips-schema.sql, db.py: quem chama é responsável por fechar a conexão, clip-processor/src/db.py, generated_clips table, INSERT IGNORE para idempotência de vídeos/canais, 01-02-PLAN: Schema SQL clips_automation e validate-infra.sh, 02-02-PLAN: docker-compose + requirements + seed + db.py, 02-02-SUMMARY: db.py GREEN, seed 5 canais (+4 more)

### Community 56 - "app-shell.tsx"
Cohesion: 0.33
Nodes (6): Accordion(), AccordionContent(), AccordionItem(), AccordionTrigger(), CHAIN, PageProps

### Community 57 - ".planning/research/PITFALLS.md"
Cohesion: 0.17
Nodes (11): n8n 06-router.json deactivation, Pitfall: CSRF blocking Telegram webhook (419), Redis SET NX dedup pattern (tg:dedup:{update_id}), TelegramWebhookController::handle, Pitfall: Blacklist Check Happens Too Late in the Pipeline, Pitfall: Filament Delete Button Deletes MySQL Row Without Deleting Files, Pitfall: Laravel Writes Conflict with Python Pipeline Mid-Transaction, Pitfall: n8n Still Running Telegram Bot in Parallel After Migration (+3 more)

### Community 58 - ".planning/research/FEATURES.md"
Cohesion: 0.20
Nodes (9): irazasyed/telegram-bot-sdk ^3.16, burn_watermark() function design, Admin Panel (Laravel/Filament) feature spec, Copyright Protection feature spec, Multi-Channel YouTube Publishing feature spec, OAuth testing-mode token expiry warning (7 days), Telegram Bot in Laravel feature spec, Laravel 13 version choice (not 11) (+1 more)

### Community 59 - "cn"
Cohesion: 0.05
Nodes (71): react, NavItem, navItems, NavUser(), Avatar(), AvatarBadge(), AvatarFallback(), AvatarGroup() (+63 more)

### Community 60 - "internal_api.py sidecar (Flask, port 8090)"
Cohesion: 0.22
Nodes (10): APScheduler jobs (ingest_cycle, publish_cycle, clip_pending_ttl), Boundary rule: painel reads directly, writes via sidecar, clip-processor service (as-built), internal_api.py sidecar (Flask, port 8090), Telegram Command classes (Status/Clipes/Aprovar/Rejeitar/Processar/Ajuda), Pitfall: Python→Laravel via wrong Host header (404), POST /internal/pipeline-event (Laravel endpoint), POST /internal/process-url (Python sidecar) (+2 more)

### Community 61 - "validate-phase6-n8n.py"
Cohesion: 0.06
Nodes (35): 10. **`Tabs key={defaultTab}` remonta as abas e perde a aba escolhida**, 11. **Mapas de status/label/cor duplicados entre cliente e servidor, indexados por texto de exibição**, 12. **Constantes da janela de download hardcoded no cliente enquanto o servidor já as envia**, 13. **~30 URLs literais `/painel/...`, `ziggy-js` instalado e `@routes` injetado sem uso**, 14. **`clip-queue-tabs.tsx`: duas tabelas 80 % iguais e quatro barras de ação em massa iguais**, 15. **`ChannelDialog` em `DestinationChannels.tsx`: um `useForm` por linha, valores iniciais congelados, upload encadeado sem feedback**, 16. **Copiar para a área de transferência: três implementações e duas células clicáveis inacessíveis**, 17. **Acessibilidade de formulários e controles** (+27 more)

### Community 62 - "Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan"
Cohesion: 0.06
Nodes (41): Phase 8 Deferred Items, BOT-01 requirement (webhook + allowlist + dedup), BOT-02 requirement (6 Telegram commands), BOT-03 requirement (pipeline-event notifications), docker exec / Docker socket bridge anti-pattern, Filament $isLazy=false widget pattern, generated_clips.status ENUM (approved/rejected), Pattern 3: ponte HTTP interna clip-processor↔painel (+33 more)

### Community 63 - "clip-processor/src/rss_poller.py"
Cohesion: 0.27
Nodes (11): _cleanup_partial() chamado fora do loop de retry, clip-processor/src/dedup.py, clip-processor/src/dedup.py, Dedup pattern: Redis NX → fallback MySQL → False, download_video(video_id, output_path), clip-processor/src/downloader.py, is_seen(video_id, redis_client, db_conn), 02-03-PLAN: dedup.py, downloader.py, rss_poller.py (+3 more)

### Community 64 - "append_credits"
Cohesion: 0.21
Nodes (9): append_credits(), Adiciona linha de créditos ao final da descrição.      Nunca sobrescreve conteúd, Testes RED para append_credits (COPY-02)., COPY-02: template com {channel_handle} é substituído pelo handle real., COPY-02: template vazio → retorna descrição sem modificação., COPY-02: handle vazio → retorna descrição sem modificação., TestAppendCredits, Phase 07 Plan 05: overlay_watermark e append_credits (COPY-01/02) (+1 more)

### Community 65 - "conftest.py"
Cohesion: 0.24
Nodes (10): mock_db_conn(), mock_redis(), fixture, Fixtures compartilhadas para todos os testes do clip-processor. Fornece: mock_re, MagicMock simulando redis.Redis.      - .set() retorna True por padrão (NX succe, MagicMock simulando conexão pymysql com suporte a context manager em cursor()., Feed RSS Atom do YouTube com 2 entradas válidas.      VideoIds: 'abc123def456' e, ID de vídeo YouTube válido (11 caracteres). (+2 more)

### Community 66 - "input-group.tsx"
Cohesion: 0.28
Nodes (8): InputGroup(), InputGroupAddon(), inputGroupAddonVariants, InputGroupButton(), inputGroupButtonVariants, InputGroupInput(), InputGroupText(), InputGroupTextarea()

### Community 67 - "publisher.py"
Cohesion: 0.06
Nodes (26): ADR-0001 — Compose isolado por projeto, Alternativas consideradas, Consequências, Contexto, Decisão, ADR-0002 — A fila mora no banco; Redis guarda só dedup, cota e idempotência, Consequências, Contexto (+18 more)

### Community 68 - "queue_controls.py"
Cohesion: 0.24
Nodes (14): get_db_connection(), Abre conexão com o PostgreSQL usando variáveis de ambiente.      Variáveis de am, _cleanup_partial(), _kill_ffmpeg_for_clip(), _kill_ytdlp_for(), _log(), pause_video(), prioritize_video() (+6 more)

### Community 69 - "overlay_watermark"
Cohesion: 0.22
Nodes (8): _log(), overlay_watermark(), Aplica watermark PNG no canto superior direito do clip via FFmpeg.      Usa -fil, Testes RED para overlay_watermark (COPY-01)., COPY-01: wm_path existente → ffmpeg com -filter_complex e overlay=W-w-20:20., COPY-01: wm_path ausente → retorna input_path sem chamar subprocess., TestOverlayWatermark, FFmpeg dual-input pattern: -filter_complex overlay (clip first, watermark second)

### Community 70 - "require-dev"
Cohesion: 0.18
Nodes (11): require-dev, fakerphp/faker, larastan/larastan, laravel/pail, laravel/pao, laravel/pint, mockery/mockery, nunomaduro/collision (+3 more)

### Community 71 - "02-04-PLAN.md: Daemon main.py Plan"
Cohesion: 0.20
Nodes (10): 02-04-PLAN.md: Daemon main.py Plan, 02-04-SUMMARY.md: Daemon main.py Summary, 02-CONTEXT.md: Phase 2 Context, 02-RESEARCH.md: Phase 2 Research, 02-VALIDATION.md: Phase 2 Validation Strategy, pytest test infra (Phase 2 Wave 0), ACQU-01: monitorar canais via RSS a cada 6h, ACQU-02: baixar vídeos novos em 720p via yt-dlp (+2 more)

### Community 72 - ".planning/research/ARCHITECTURE.md (v2.0 research, superseded)"
Cohesion: 0.28
Nodes (9): Dead code: painel/app/Filament/Pages/Dashboard.php orphan, env() outside config() pitfall in DashboardController, Section 10: Known divergences and technical debt, channel_blacklist table (research design), destination_channels table (research design), Phase 7: Schema Multi-Canal + Watermark + Copyright (research plan), Phase 8: Laravel/Filament Painel Base (research plan), Phase 9: Bot Telegram no Laravel + Migração do n8n (research plan) (+1 more)

### Community 73 - "youtube_oauth.py"
Cohesion: 0.07
Nodes (30): 1. Confirmar qual provider respondeu, 1. Qual IA, e por quê, 2. Confirmar as keys dentro do container, 2. Os prompts, na íntegra, 3. Palavras-chave e frases-chave, por formato, 3. Ver o filtro de 30s agindo, 4. Conferir a duração dos clips no banco, 4. Regras de duração (+22 more)

### Community 74 - "run_ingest_cycle"
Cohesion: 0.14
Nodes (14): dt_sp(), make_redis(), Helper: mock Redis com contador configurável., Helper: datetime no fuso São Paulo., Deve permitir upload dentro da janela e abaixo da quota., Deve negar upload antes das 19h., Deve negar upload às 22h ou depois., Deve negar upload à meia-noite. (+6 more)

### Community 75 - "02-01-PLAN: pytest scaffold RED state (Wave 0)"
Cohesion: 0.33
Nodes (9): clip-processor/tests/conftest.py, 02-01-PLAN: pytest scaffold RED state (Wave 0), 02-01-SUMMARY: 17 testes RED criados, clip-processor/pytest.ini, TDD RED-GREEN-REFACTOR pattern (imports no topo causam ModuleNotFoundError), tests/test_db.py, tests/test_dedup.py, tests/test_downloader.py (+1 more)

### Community 76 - "Phase 8 Context (Painel Laravel/Filament)"
Cohesion: 0.12
Nodes (9): DrawerContent(), DrawerDescription(), DrawerFooter(), DrawerHeader(), DrawerOverlay(), DrawerTitle(), Tooltip(), TooltipProvider() (+1 more)

### Community 78 - "TestYouTubeUploaderChannelSlug"
Cohesion: 0.25
Nodes (5): Testes RED para suporte a channel_slug no YouTubeUploader (MCAN-01)., MCAN-01: channel_slug='futebol-em-cortes' → token_file='/app/youtube/token-futeb, Retrocompat: sem channel_slug, usa DEFAULT_TOKEN_FILE., Retrocompat: token_file explícito tem precedência sobre channel_slug., TestYouTubeUploaderChannelSlug

### Community 79 - "setup"
Cohesion: 0.12
Nodes (16): Backup e restauração, Comandos do painel, Convenções, Diagnosticar falhas de upload, Espaço em disco, Estado preso sem recuperação automática, Está tudo de pé?, Nada sobe para o YouTube (+8 more)

### Community 80 - "Phase 9-04 Plan: Telegram Bot Checkpoint"
Cohesion: 0.39
Nodes (8): PipelineEventTest.php, setWebhook registration to https://alessandromelo.com.br/telegramcanal, Phase 9-04 Plan: Telegram Bot Checkpoint, TelegramCommandsTest.php, TelegramWebhookTest.php, Artisan Schedule daily summary 18h BRT, Phase 9 Research: Bot Telegram no Laravel, Phase 9 Validation Strategy

### Community 81 - "Phase 7: Schema Multi-Canal + Python Pipeline"
Cohesion: 0.25
Nodes (7): Bot Telegram no Laravel (v2), Groq Whisper (API) em vez de Whisper local, Multi-canal com token OAuth por canal, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 8: Painel Laravel/Filament, Phase 9: Bot Telegram no Laravel, recover_stuck_downloads só recupera 'downloading' → 'pending'

### Community 82 - "01-RESEARCH.md"
Cohesion: 0.29
Nodes (7): youtube/generate_token.py, OAuth app type 'installed' (Desktop App), não 'web', OAuth app publicado em Production, Pitfall: YouTube OAuth em modo Testing expira em 7 dias, 01-04-PLAN: OAuth YouTube e verificação do canal, 01-04-SUMMARY: OAuth e canal configurados, Canal YouTube "Futebol em Cortes"

### Community 83 - "config"
Cohesion: 0.29
Nodes (7): pestphp/pest-plugin, php-http/discovery, config, allow-plugins, optimize-autoloader, preferred-install, sort-packages

### Community 84 - "require"
Cohesion: 0.29
Nodes (7): require, inertiajs/inertia-laravel, irazasyed/telegram-bot-sdk, laravel/framework, laravel/tinker, php, tightenco/ziggy

### Community 85 - "GeneratedClip"
Cohesion: 0.18
Nodes (6): Illuminate\Database\Eloquent\Factories\Factory, DestinationChannelFactory, GeneratedClipFactory, SourceChannelFactory, static, UserFactory

### Community 86 - "clip-processor/src/metadata_generator.py"
Cohesion: 0.33
Nodes (6): clip-processor/src/metadata_generator.py, clip-processor/tests/test_metadata_generator.py, 04-01-PLAN.md: Phase 4 Wave 0 skeletons + RED tests, 04-01-SUMMARY.md: Phase 4 Wave 0 Summary, 04-03-PLAN.md: metadata_generator.py GREEN plan, update_clip_metadata()

### Community 87 - "destination_channels table"
Cohesion: 0.33
Nodes (6): destination_channels table, Migration idempotente via INFORMATION_SCHEMA + prepared statement, 06-multi-canal-migration.sql, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 7 — Validation Strategy, pytest test framework (clip-processor)

### Community 88 - "test_publisher.py"
Cohesion: 0.12
Nodes (16): Cota diária e janela horária, Fallback legado, Finalização do vídeo fonte, Guard de corrida com a rejeição, Janela horária, Limites, OAuth por canal-destino, Ordem da fila: round-robin por canal fonte (+8 more)

### Community 89 - "clip-processor/src/downloader.py"
Cohesion: 0.40
Nodes (5): clip-processor/src/downloader.py, Guard de espaço em disco antes do download (<2GB), Retry de download: 3x com 60s entre tentativas, Extração de áudio ffmpeg para arquivos >24MB, _prepare_audio()

### Community 90 - "Phase 8 Research (Painel Laravel/Filament)"
Cohesion: 0.13
Nodes (12): Antes de qualquer coisa, Branches, Changelog, Commits, Contribuindo, Documentação, Versões, ADR-0005 — Lint e formatação bloqueantes, baseline para dívida antiga, tipos informativos (+4 more)

### Community 91 - "_discard_failed_download"
Cohesion: 0.20
Nodes (10): _clips_need_raw(), _discard_failed_download(), Marca o download como 'failed' e libera a vaga que ele ocupava na janela.      A, Diz se algum clip desse vídeo ainda precisa do arquivo bruto em disco.      `pro, Download falho não pode deixar arquivo em disco nem local_path preenchido., Arquivo parcial em disco é apagado ANTES do UPDATE, e local_path vira NULL., Sem arquivo em disco (falha antes de escrever nada), segue e limpa a coluna., Se o arquivo sobrevive à remoção, não limpa local_path — banco não divergir do d (+2 more)

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
Cohesion: 0.11
Nodes (15): create_transcription_job(), process_transcription_job(), Executa o ciclo completo de uma transcrição local (roda em thread de background), Cria o job no banco e dispara a thread de background que processa a transcrição., Insere um novo job em transcription_jobs com status='pending' e retorna o id ger, Monta um UPDATE dinâmico só com os campos passados (não sobrescreve os demais)., start_transcription_job(), update_job() (+7 more)

### Community 103 - "_process_ai_pipeline"
Cohesion: 0.16
Nodes (8): AI-04: Testes de integração do pipeline de IA no rss_poller., Configura mock_db_conn para retornar canais e vídeos downloaded em fetchall()., AI-04: poll_all_channels chama _process_ai_pipeline para cada vídeo com status d, AI-04: Falha no pipeline de IA de um vídeo não aborta os demais., AI-04: _process_ai_pipeline chama transcribe_video e select_moments em sequência, AI-04: Falha na transcrição (None) marca vídeo como failed e não chama select_mo, AI-04: Pipeline atualiza status: transcribing → (save) → selecting., TestAIPipelineIntegration

### Community 109 - "transcription_job.py"
Cohesion: 0.18
Nodes (14): _audio_duration_seconds(), _download_audio(), _merge_srt_chunks(), transcription_job.py — Worker de "Transcrição Local" (QUICK-1).  Feature isolada, Divide o wav em `num_chunks` pedaços de duração igual via ffmpeg (recorte por te, Roda whisper-cpp local sobre um wav, gerando `<out_prefix>.srt`.      Raises:, Soma `offset_seconds` a cada timestamp de um bloco .srt (não renumera — quem, Concatena os .srt de cada pedaço, deslocando os timestamps pelo offset acumulado (+6 more)

### Community 110 - "clip-processor/src/main.py"
Cohesion: 0.22
Nodes (11): BlockingScheduler daemon pattern (APScheduler), clip-processor/src/db.py, clip-processor/src/main.py, clip-processor/src/rss_poller.py, Pitfall: container restart com vídeo em status downloading, 03-04-PLAN.md: AI pipeline integration plan, 03-04-SUMMARY.md: AI pipeline integration Summary, poll_all_channels(db_conn, redis_client) (+3 more)

### Community 111 - "Plano de migração — Oracle Cloud (Always Free)"
Cohesion: 0.11
Nodes (19): 1. Não fazer upgrade para Pay As You Go (a camada que realmente importa), 2. Provisionar só recursos com o selo "Always Free-eligible", 3. Orçamento com alerta em US$ 1, 4. Conferência após provisionar, Como o custo zero é garantido, Decisão tomada, Depois da migração, Fase 0 — Conta e blindagem de cobrança  ⬜ NÃO INICIADA (+11 more)

### Community 113 - "run_ttl_once"
Cohesion: 0.14
Nodes (14): Artefatos em disco, `_cleanup_partial` — por download (no `except`), `cleanup_stale_downloads` — varredura de órfãos, Dedup, Descoberta e download, Descoberta via RSS, Detecção de formato, `_discard_failed_download` (13/08/2026) (+6 more)

### Community 114 - "rejeitar"
Cohesion: 0.19
Nodes (12): internal_api.reject_clip(clip_id) — calls src.rejeitar.rejeitar directly, Chama src.rejeitar.rejeitar(clip_id) diretamente. Preserva exit codes 0/1/2., reject_clip(), Marca o clip como rejected, remove o MP4 do disco, preserva raw video.      Comp, rejeitar(), Testes para rejeitar.py — comando /rejeitar do Telegram.  Estado RED até Plan 06, rejeitar(123): executa UPDATE generated_clips SET status='rejected' WHERE id=123, rejeitar apaga clip_path mas NÃO toca source_videos.local_path (raw). (+4 more)

### Community 119 - "Phase 6 Plan 07: workflows n8n completos + setup operacional + smoke E2E"
Cohesion: 0.15
Nodes (13): 1. Setup do host (uma vez), 2. Comandos do dia a dia, 3. O que cada ferramenta cobre, 4. pre-commit e CI, 5. Testes PHP — cuidado com o banco, 6. Políticas, 7. Versionamento e release, 8. Pendências conhecidas (25/08/2026) (+5 more)

### Community 120 - "clip-processor/src/transcriber.py"
Cohesion: 0.15
Nodes (12): private, $schema, scripts, build, check, dev, format, format:check (+4 more)

### Community 122 - "Quick Task 1: Transcrição Local Summary"
Cohesion: 0.15
Nodes (12): Accomplishments, Auto-fixed Issues, Decisions Made, Deviations from Plan, Files Created/Modified, Issues Encountered, Next Phase Readiness, Performance (+4 more)

### Community 123 - "toggle-group.tsx"
Cohesion: 0.47
Nodes (4): ToggleGroup(), ToggleGroupContext, Toggle(), toggleVariants

### Community 124 - "mysql/init/06-multi-canal-migration.sql"
Cohesion: 0.17
Nodes (12): As três armadilhas que pegam todo mundo, Como atualizar estes documentos, Como o sistema funciona, por subsistema, Corrigido em 12–13/08/2026, Docs — Canal de Cortes, Estado atual em uma tela, Infra, O que o sistema é, em um parágrafo (+4 more)

### Community 129 - "providers.php"
Cohesion: 0.32
Nodes (11): bool_value(), connect_mysql(), connect_postgres(), fetch_mysql_rows(), main(), migrate_table(), mysql_table_exists(), postgres_columns() (+3 more)

### Community 153 - "05-03 Plan: YouTube uploader"
Cohesion: 0.18
Nodes (11): Acesso, As tabelas do pipeline não são migrations do Laravel, Banco de dados — `clips_automation`, `destination_channels`, Divergência banco × disco (bug aberto), `generated_clips`, Integridade referencial, Ordem de aplicação (+3 more)

### Community 154 - "Phase 6 Plan 05: TTL Worker (expire 48h + warn 24h)"
Cohesion: 0.18
Nodes (11): Armadilha recorrente: editar código não muda nada sem rebuild, Conexões, Entrypoint, Jobs agendados, O que cada ciclo executa, Onde mexer, Pipeline e scheduler, `run_ingest_cycle` (20 min) (+3 more)

### Community 157 - "Backlog de bugs"
Cohesion: 0.17
Nodes (12): 10. ABERTO — 287 clips com `clip_path` apontando para arquivo inexistente, 11. ABERTO — Container não honra SIGTERM, todo `docker stop` vira SIGKILL, 1. FEITO — Órfãos de download nunca eram apagados, 2. FEITO — `_raw.mp4` nunca era apagado, 3. SUSPEITA — Thumbnail não aplicada nos vídeos longos no YouTube, 4. PARCIAL — Estados sem recuperação automática seguram arquivo em disco, 5. FEITO — `_subtitled.mp4` órfão, 6. ABERTO — Painel não consegue apagar o backlog de download (+4 more)

### Community 158 - "Sistema — `painel/`"
Cohesion: 0.13
Nodes (15): A regra da fronteira, Armadilhas conhecidas, Autenticação, Banco, Canais, Como ler o Dashboard, Dashboard — `DashboardController`, O que é (+7 more)

### Community 159 - "v1.0 — Pipeline Base"
Cohesion: 0.20
Nodes (6): Testes RED para suporte a channel_id no QuotaManager (MCAN-03, MCAN-04)., MCAN-03: _key() deve incluir channel_id quando fornecido.          QuotaManager(, Retrocompat: _key() sem channel_id retorna 'youtube_uploads:2026-06-18'., MCAN-04: Dois QuotaManager com channel_id diferentes usam keys Redis distintas., MCAN-04: Quota atingida no canal A não bloqueia canal B., TestQuotaManagerMultiCanal

### Community 160 - "clip-processor/src/db.py"
Cohesion: 0.20
Nodes (10): A regra, As duas rotas que apagam, Caminho inverso: eventos para o Telegram, Controles de fila, `delete_source_video_file` — só disco, `purge_old_videos` — apaga linha, Rede e autenticação, Rejeição de clip (+2 more)

### Community 161 - "Phase 6 Plan 01: Wave 0 Scaffolding (migration + stubs + RED tests + n8n skeletons)"
Cohesion: 0.20
Nodes (10): Abortar um corte em andamento, Artefatos em disco, Buraco que sobra, Corte e pós-produção de vídeo, Corte por formato, Legendas, Marca d'água, Metadata do clip (+2 more)

### Community 162 - "autoload-dev"
Cohesion: 0.22
Nodes (6): HttpError, Exception, RefreshError, RED test para captura de RefreshError e persistência de oauth_expired_flag (impl, RefreshError em creds.refresh() deve setar oauth_expired_flag=TRUE em     destin, test_load_credentials_catches_refresh_error_and_flags_channel()

### Community 164 - "post-create-project-cmd"
Cohesion: 0.50
Nodes (4): post-create-project-cmd, @php artisan key:generate --ansi, @php artisan migrate --graceful --ansi, @php -r \"file_exists('database/database.sqlite') || touch('database/database.sqlite');\

### Community 165 - "tw-animate-css"
Cohesion: 0.22
Nodes (5): Segundo upload não deve redefinir o TTL., TTL deve ser o número de segundos até meia-noite em SP., record_upload deve chamar INCR no Redis., Primeiro upload do dia deve definir TTL até meia-noite., TestRecordUpload

### Community 166 - "page-header.tsx"
Cohesion: 0.22
Nodes (9): A terceira query (`local_path IS NULL` → `failed`), `cutting` e `publishing` em `source_videos`: valores mortos, Estados e transições do pipeline, Estados × ocupação da janela de download, Estados terminais e o que sobra em disco, `generated_clips.status`, O que fazer com o que não tem recuperação, Recuperação automática: o que tem e o que não tem (+1 more)

### Community 168 - "clip-processor/src/publisher.py"
Cohesion: 0.22
Nodes (9): Binário e modelo, Chunking, Conversão para áudio acima de 24 MB, Formato do transcript salvo, Pipeline principal — Groq Whisper, Progresso, Sem fallback, Transcrição (+1 more)

### Community 169 - "zod"
Cohesion: 0.25
Nodes (4): Testes para QuotaManager — controle de quota e janela de publicação., Com MAX=5 / LONGO=2 e 3 uploads, curto bloqueia se ainda há longo na fila., Sem longo na fila, curto pode usar o restante da cota total., TestLongoReservation

### Community 171 - "sonner"
Cohesion: 0.25
Nodes (6): Popover(), PopoverContent(), PopoverDescription(), PopoverHeader(), PopoverTitle(), PopoverTrigger()

### Community 172 - "Fases"
Cohesion: 0.73
Nodes (5): cmd_preview(), cmd_release(), load_fragments(), main(), render()

### Community 173 - "Mapa dos módulos"
Cohesion: 0.40
Nodes (5): generated_clips.status state machine, list-pending-clips.sh, mark-published.sh, manual-workflow/README.md — manual clip publishing guide, Pitfall: Filament Auto-Generated Resources Break on ENUM Columns

### Community 174 - "Rotas"
Cohesion: 0.40
Nodes (4): CHANGELOG.d — fragmentos de release notes, Comandos, Conteúdo, Nome do arquivo

### Community 176 - "04-04 Summary: Poller Integration Summary"
Cohesion: 0.20
Nodes (10): Checkpoint humano: verificação end-to-end Phase 4, _process_pending_clips(conn), Migration Phase 3 usa INFORMATION_SCHEMA em vez de ADD COLUMN IF NOT EXISTS, Persistir arquivos renderizados no volume montado /app/videos, Raw source só removido quando todos clips do source video estão terminais, generated_clips.status = pending_cut, mysql/init/03-schema-migration.sql, 04-03 Summary: metadata_generator.py implementation (+2 more)

### Community 177 - "Sistema — `clip-processor`"
Cohesion: 0.13
Nodes (15): Aquisição — [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md), Base, Configuração, Editar código exige rebuild, Inteligência — [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md), [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md), Interface com o painel — [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md), Mapa dos módulos, O que o Redis guarda (e o que não guarda) (+7 more)

### Community 178 - "test_uploader.py"
Cohesion: 0.50
Nodes (3): make_uploader(), Testes para YouTubeUploader — upload de clips e thumbnails. Todas as chamadas Yo, Cria YouTubeUploader com credenciais e YouTube mockados.

### Community 179 - "Phase 6 Plan 04: Implementar processar.py"
Cohesion: 0.67
Nodes (3): keywords, framework, laravel

### Community 181 - "@fontsource-variable/geist"
Cohesion: 0.67
Nodes (3): dev, Composer\\Config::disableProcessTimeout, npx concurrently -c \"#93c5fd,#c4b5fd,#fb7185,#fdba74\" \"php artisan serve\" \"php artisan queue:listen --tries=1 --timeout=0\" \"php artisan pail --timeout=0\" \"npm run dev\" --names=server,queue,logs,vite --kill-others

### Community 182 - "@inertiajs/react"
Cohesion: 0.67
Nodes (3): test, @php artisan config:clear --ansi @no_additional_args, @php artisan test

## Ambiguous Edges - Review These
- `clip-processor/src/ttl_worker.py` → `clip-processor/src/telegram_notifier.py`  [AMBIGUOUS]
  .planning/phases/06-controle-manual-n8n-telegram/06-05-SUMMARY.md · relation: conceptually_related_to

## Knowledge Gaps
- **671 isolated node(s):** `clip-processor`, `force-download.sh script`, `$schema`, `typescript`, `jsx-a11y` (+666 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `clip-processor/src/ttl_worker.py` and `clip-processor/src/telegram_notifier.py`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `run_pipeline_once()` connect `notify` to `publish_pending_clips`, `db.py`, `queue_controls.py`, `Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel`, `rss_poller.py`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `n8n/workflows/canaldecortes-pipeline.json` connect `Phase 6 Research — Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel` to `notify`, `05-01 Plan: Publishing schema, skeletons and RED tests`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `QuotaManager` (e.g. with `TestCanUpload` and `TestLongoReservation`) actually correct?**
  _`QuotaManager` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `YouTubeUploader` (e.g. with `TestUploadClip` and `TestYouTubeUploaderChannelSlug`) actually correct?**
  _`YouTubeUploader` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `clip-processor`, `force-download.sh script`, `$schema` to the rest of the system?**
  _671 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `SourceVideos.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.047619047619047616 - nodes in this community are weakly interconnected._