# Graph Report - .  (2026-07-30)

## Corpus Check
- 333 files · ~304,322 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1951 nodes · 3474 edges · 150 communities (127 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 91 edges (avg confidence: 0.78)
- Token cost: 1,199,475 input · 0 output

## Community Hubs (Navigation)
- Publisher Credit & Upload Flow
- MySQL DB Access Layer (clip-processor)
- YouTube Quota Manager
- MySQL Migrations & Manual Workflow SQL
- RSS Poll & AI Pipeline Orchestration
- Panel: Active Window / Clip Queue UI
- Panel: App Shell & Sidebar Nav
- Panel: User Nav & Avatar UI
- Panel: Niche Combobox & Command UI
- Clip Selector (moment selection)
- Panel: Login & Site Header UI
- Infra Config (nginx, oauth flag, Redis conn)
- Internal API Sidecar (reject/resolve/purge)
- Laravel Framework Contracts & Testing Base
- Manual Ingest (/processar command)
- Clip Cutting (FFmpeg burn/cut/thumbnail)
- YouTube Uploader Tests
- Panel-Sidecar Bridge (ClipProcessorClient)
- Panel Build Tooling (Vite/Tailwind deps)
- Panel Chart Components
- Metadata Generator (Anthropic/Groq fallback)
- Video Dedup (Redis + MySQL fallback)
- Video Transcriber (Groq Whisper)
- shadcn/ui Components Config
- Docker Compose & Env Secrets
- Video Downloader (yt-dlp)
- YouTube Uploader (Google API)
- Pipeline Error Handling Tests
- Internal API Sidecar Tests (RED)
- Laravel Niche Controller & Middleware
- Laravel SourceVideo Controller
- Laravel Auth Controller
- Panel: Checkbox/Select UI Primitives
- TypeScript Config
- Panel Frontend Dependencies
- Planning Docs: Requirements & Milestones v1.0
- Pipeline Runner Download Cycle Tests
- Laravel App Service Provider
- Laravel Source Channel Controller
- Panel: Confirm Dialog UI
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 148
- Community 149

## God Nodes (most connected - your core abstractions)
1. `cn()` - 189 edges
2. `QuotaManager` - 39 edges
3. `YouTubeUploader` - 37 edges
4. `publish_pending_clips()` - 35 edges
5. `poll_all_channels()` - 25 edges
6. `process_clip()` - 23 edges
7. `GeneratedClip` - 23 edges
8. `run_pipeline_once()` - 22 edges
9. `get_db_connection()` - 20 edges
10. `make_redis()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `generate_metadata()` --implements--> `Fallback determinístico de metadata (não bloqueia pipeline)`  [EXTRACTED]
  clip-processor/src/metadata_generator.py → .planning/phases/04-processamento-de-video/04-03-SUMMARY.md
- `generate_metadata()` --implements--> `Pattern: Metadata Structured Outputs (Anthropic json schema)`  [EXTRACTED]
  clip-processor/src/metadata_generator.py → .planning/phases/04-processamento-de-video/04-RESEARCH.md
- `publish_pending_clips()` --rationale_for--> `Publisher legacy fallback when destination_channels empty`  [EXTRACTED]
  clip-processor/src/publisher.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-06-SUMMARY.md
- `overlay_watermark()` --rationale_for--> `Graceful degradation pattern: return input unchanged when optional dependency missing`  [EXTRACTED]
  clip-processor/src/video_processor.py → .planning/phases/07-schema-multi-canal-python-pipeline/07-05-SUMMARY.md
- `docker-compose.yml branding volume for clip-processor` --shares_data_with--> `overlay_watermark()`  [EXTRACTED]
  .planning/phases/07-schema-multi-canal-python-pipeline/07-07-PLAN.md → clip-processor/src/video_processor.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase 1 infrastructure setup flow: containers → schema → secrets → OAuth** — docker_compose_yml, clips_schema_sql, env_file, generate_token_py [EXTRACTED 1.00]
- **Phase 2 TDD flow: tests RED → db.py GREEN → dedup/downloader/rss_poller GREEN** — test_db_py, db_py, dedup_py, downloader_py, rss_poller_py [EXTRACTED 1.00]
- **ACQU-01/02/03 requirements mapped to rss_poller/downloader/dedup modules** — planning_requirements_acqu_01, planning_requirements_acqu_02, planning_requirements_acqu_03, rss_poller_py, downloader_py, dedup_py [EXTRACTED 1.00]
- **Phase 2 daemon assembly: main.py orchestrating rss_poller, db recovery, and scheduling** — clip_processor_src_main_py, clip_processor_src_rss_poller_py, clip_processor_src_db_py, apscheduler_blockingscheduler_pattern [EXTRACTED 1.00]
- **Phase 3 TDD cycle: skeletons, RED tests, then GREEN implementation of transcriber and selector wired into rss_poller** — clip_processor_tests_test_transcriber_py, clip_processor_tests_test_selector_py, clip_processor_src_transcriber_py, clip_processor_src_selector_py, process_ai_pipeline_function [EXTRACTED 1.00]
- **Phase 4 clip rendering: process_clip orchestrating cut, subtitles, thumbnail, and metadata** — process_clip_function, cut_clip_function, generate_srt_function, burn_subtitles_function, extract_thumbnail_function, generate_metadata_function [EXTRACTED 1.00]
- **Phase 4 clip processing pipeline: cut, subtitle, thumbnail, metadata** — clip_processor_src_video_processor_process_clip, clip_processor_src_metadata_generator_generate_metadata, clip_processor_src_rss_poller__process_pending_clips, generated_clips_status_pending_cut [EXTRACTED 1.00]
- **Phase 5 publishing pipeline: quota, upload, publisher, runner, n8n** — clip_processor_src_quota_manager, clip_processor_src_uploader, clip_processor_src_publisher, clip_processor_src_pipeline_runner_run_pipeline_once, n8n_workflows_canaldecortes_pipeline_json [EXTRACTED 1.00]
- **MySQL 8.4 idempotent migration pattern via INFORMATION_SCHEMA** — mysql_init_03_schema_migration, mysql_init_04_publishing_migration, decision_migration_mysql84_information_schema [INFERRED 0.85]
- **Phase 6 pipeline: pending clip → /aprovar → approved → publisher (guard) → publishing → published + notify** — ctrl_02_publisher_approved, clip_processor_src_publisher_py, telegram_n8n_workflows_06_router_json, clip_processor_src_telegram_notifier_py, status_guard_pattern [EXTRACTED 0.90]
- **Wave 0 scaffolding delivers migration + 4 stubs + RED tests + n8n skeletons that unblock Waves 1-3** — planning_phases_06_controle_manual_n8n_telegram_06_01_plan, 05_controle_manual_migration_sql, clip_processor_src_processar_py, clip_processor_src_rejeitar_py, clip_processor_src_ttl_worker_py, clip_processor_src_telegram_notifier_py [EXTRACTED 0.95]
- **3 proactive Telegram events (upload_published, pipeline_failure, clip_ttl_warning) routed through n8n webhook /notify** — clip_processor_src_publisher_py, clip_processor_src_pipeline_runner_py, clip_processor_src_ttl_worker_py, telegram_n8n_workflows_06_router_json [EXTRACTED 0.90]
- **Publisher multi-canal publication flow: per-channel quota, uploader, credits, watermark** — clip_processor_src_publisher_publish_pending_clips, clip_processor_src_quota_manager_quotamanager, clip_processor_src_uploader_youtubeuploader, clip_processor_src_metadata_generator_append_credits, clip_processor_src_video_processor_overlay_watermark [EXTRACTED 1.00]
- **Panel Laravel bootstrap: docker wiring, config, and clip-processor integration points** — painel_laravel_project, wordpress_docker_compose_yml, canaldecortes_nginx_conf, painel_config_services_clip_processor, painel_config_database_pipeline_connection [EXTRACTED 1.00]
- **OAuth expired flag lifecycle: producer (uploader), storage (migration), consumer (Laravel model)** — mysql_init_07_panel_oauth_flag_migration, oauth_expired_flag_column, painel_model_destinationchannel, clip_processor_src_uploader_youtubeuploader [EXTRACTED 1.00]
- **HTTP sidecar bridge pattern (Laravel ↔ clip-processor)** — painel_app_services_clipprocessorclient, clip_processor_src_internal_api, clip_processor_src_main, http_sidecar_pattern3 [EXTRACTED 1.00]
- **OAuth badge observability flow (uploader → flag → widget)** — clip_processor_src_uploader, google_auth_exceptions_refresherror, destination_channels_oauth_expired_flag, painel_app_filament_resources_destinationchannelresource [EXTRACTED 1.00]
- **Telegram bot migration from n8n to Laravel** — clip_processor_src_telegram_notifier, painel_app_http_controllers_telegramwebhookcontroller, painel_routes_console, clip_processor_src_ttl_worker [EXTRACTED 1.00]
- **Phase 9 Telegram-to-Laravel migration (research → plan → validation → n8n deprecation)** — planning_phases_09_bot_telegram_no_laravel_09_research_bot_telegram, planning_phases_09_bot_telegram_no_laravel_09_04_plan_telegram_checkpoint, planning_phases_09_bot_telegram_no_laravel_09_validation_phase9, planning_research_pitfalls_n8n_parallel_bot [INFERRED 0.85]
- **Filament-era documentation now stale vs as-built Inertia/React reality** — readme_canaldecortes, painel_readme, planning_research_architecture_v2, architecture_asbuilt_filament_removed_commit, architecture_asbuilt_dead_filament_dashboard [INFERRED 0.85]
- **Multi-channel YouTube quota isolation design and its pitfalls** — planning_research_pitfalls_shared_quota_pool, planning_research_architecture_quota_manager_channel_scoping, architecture_asbuilt_quota_window_roundrobin, planning_research_features_multichannel_youtube_publishing [INFERRED 0.85]

## Communities (150 total, 23 thin omitted)

### Community 0 - "Publisher Credit & Upload Flow"
Cohesion: 0.05
Nodes (59): Handle a usar no crédito: prioriza @handle real; cai para o nome do canal fonte…, resolve_credit_handle(), _fetch_destination_channels(), _fetch_pending_clips(), _fetch_pending_clips_for_channel(), _log(), _mark_clip_failed(), _mark_clip_published() (+51 more)

### Community 1 - "MySQL DB Access Layer (clip-processor)"
Cohesion: 0.06
Nodes (46): get_db_connection(), insert_video(), _log(), db.py — Módulo de acesso ao MySQL para o daemon clip-processor. Exporta: -…, Redefine vídeos presos em status 'downloading' de volta para 'pending'.…, Devolve vídeos presos em 'selecting' para 'downloaded' (reprocessa a IA).…, Loga mensagem com timestamp para stdout., Abre conexão com o MySQL usando variáveis de ambiente. Variáveis de ambiente… (+38 more)

### Community 2 - "YouTube Quota Manager"
Cohesion: 0.07
Nodes (32): datetime, QuotaManager, Controla uploads diarios do YouTube por data local de Sao_Paulo. Reserva de…, Janela + cota total, ignorando reserva por formato. Usado para decidir se o…, Retorna True se horario e quota (total + formato) permitirem upload., Incrementa contador diario (total e, se 'longo', o de formato) e garante TTL., dt_sp(), make_redis() (+24 more)

### Community 3 - "MySQL Migrations & Manual Workflow SQL"
Cohesion: 0.06
Nodes (58): mysql/init/05-controle-manual-migration.sql, mysql/init/06-multi-canal-migration.sql, mysql/manual-workflow/approve-backlog.sql — helper opcional para backlog de pending, APScheduler dentro do clip-processor (vs n8n cron) para TTL worker, clip-processor/src/pipeline_runner.py, clip-processor/src/processar.py, clip-processor/src/publisher.py, clip-processor/src/rejeitar.py (+50 more)

### Community 4 - "RSS Poll & AI Pipeline Orchestration"
Cohesion: 0.06
Nodes (34): _detect_format(), _extract_video_id(), _is_blocked_title(), _log(), poll_all_channels(), _process_ai_pipeline(), _process_pending_clips(), Processa clips com status pending_cut sem abortar o poll por falha isolada. (+26 more)

### Community 5 - "Panel: Active Window / Clip Queue UI"
Cohesion: 0.08
Nodes (33): ActiveWindowTable(), STATUS_LABEL, ClipQueueTabs(), FailuresTable(), PendingTable(), post(), QueuedTable(), useSelection() (+25 more)

### Community 6 - "Panel: App Shell & Sidebar Nav"
Cohesion: 0.06
Nodes (40): AppSidebar(), NavItem, navItems, NavUser(), Sheet(), SheetContent(), SheetDescription(), SheetFooter() (+32 more)

### Community 7 - "Panel: User Nav & Avatar UI"
Cohesion: 0.08
Nodes (35): Avatar(), AvatarBadge(), AvatarFallback(), AvatarGroup(), AvatarGroupCount(), AvatarImage(), Breadcrumb(), BreadcrumbEllipsis() (+27 more)

### Community 8 - "Panel: Niche Combobox & Command UI"
Cohesion: 0.08
Nodes (35): NicheCombobox(), slugify(), Command(), CommandDialog(), CommandEmpty(), CommandGroup(), CommandInput(), CommandItem() (+27 more)

### Community 9 - "Clip Selector (moment selection)"
Cohesion: 0.07
Nodes (33): _enforce_longform_duration(), insert_selected_moments(), _log(), _lookup_destination_channel_id(), _parse_moments(), selector.py — Seleção de momentos via IA com fallback automático. Prioridade em…, Garante duração mínima de MIN_LONGFORM_SECONDS para o modo 'longo'. O modelo…, Analisa transcrição e retorna momentos selecionados via IA. Fluxo de seleção de… (+25 more)

### Community 10 - "Panel: Login & Site Header UI"
Cohesion: 0.09
Nodes (21): LoginForm(), SiteHeader(), CardContent(), Field(), FieldContent(), FieldDescription(), FieldError(), FieldGroup() (+13 more)

### Community 11 - "Infra Config (nginx, oauth flag, Redis conn)"
Cohesion: 0.07
Nodes (34): canaldecortes/docker/nginx/canaldecortes.conf vhost, clip-processor não tem bind mount de src/ — exige rebuild+restart para refletir código, mysql/init/07-panel-oauth-flag-migration.sql (oauth_expired_flag idempotent migration), destination_channels.oauth_expired_flag column, config/database.php Redis 'pipeline' connection (DB 0), config/services.php clip_processor block (url/token), canaldecortes/painel/ — Laravel 13 + Filament 5.6.7 + Pest 4.7.4 project, App\Models\DestinationChannel Eloquent Model + getOauthStatusAttribute (+26 more)

### Community 12 - "Internal API Sidecar (reject/resolve/purge)"
Cohesion: 0.09
Nodes (31): internal_api.reject_clip(clip_id) — calls src.rejeitar.rejeitar directly, internal_api.resolve_channel(url) — yt-dlp channel resolution, _check_auth(), delete_source_video_file(), purge_old_videos(), internal_api.py — Sidecar HTTP interno consumido pelo painel Laravel.…, Limpa vídeos fonte com published_at anterior a `before_date` (formato 'YYYY-MM-…, Roda yt-dlp em modo metadata-only e extrai id/name/handle. Padrão yt-dlp:… (+23 more)

### Community 13 - "Laravel Framework Contracts & Testing Base"
Cohesion: 0.08
Nodes (14): Filament\Models\Contracts\FilamentUser interface, Illuminate\Console\Command, Illuminate\Database\Console\Seeds\WithoutModelEvents, Illuminate\Database\Seeder, Illuminate\Foundation\Auth\User, Illuminate\Foundation\Testing\TestCase, Illuminate\Notifications\Notifiable, CreatePainelUser (+6 more)

### Community 14 - "Manual Ingest (/processar command)"
Cohesion: 0.10
Nodes (21): fetch_metadata(), main(), _normalize_upload_date(), parse_video_id(), processar.py — Ingestão manual de vídeo YouTube via comando /processar do…, Entrypoint CLI. Exit codes: - 0: OK (inserido ou já existia) - 2: URL inválida…, Extrai videoId de 11 caracteres de uma URL YouTube. None se URL inválida.…, Converte 'YYYYMMDD' (formato yt-dlp) para 'YYYY-MM-DD HH:MM:SS' (TIMESTAMP… (+13 more)

### Community 15 - "Clip Cutting (FFmpeg burn/cut/thumbnail)"
Cohesion: 0.11
Nodes (18): _build_clip_context(), burn_subtitles(), cut_clip(), extract_thumbnail(), _fetch_clip(), _format_srt_time(), generate_srt(), process_clip() (+10 more)

### Community 16 - "YouTube Uploader Tests"
Cohesion: 0.10
Nodes (15): make_uploader(), make_youtube_mock(), Testes para YouTubeUploader — upload de clips e thumbnails. Todas as chamadas…, token_file inexistente deve levantar FileNotFoundError., Se thumbnail_path existir, thumbnails().set() deve ser chamado., Cria um mock do serviço YouTube que simula upload bem-sucedido., Falha no upload da thumbnail deve ser propagada ao caller., Tags em formato string separado por vírgula devem virar lista. (+7 more)

### Community 17 - "Panel-Sidecar Bridge (ClipProcessorClient)"
Cohesion: 0.13
Nodes (10): POST /internal/resolve-channel (sidecar endpoint), CreateSourceChannel Page, AjudaCommand, AprovarCommand, ClipesCommand, ProcessarCommand, RejeitarCommand, StatusCommand (+2 more)

### Community 18 - "Panel Build Tooling (Vite/Tailwind deps)"
Cohesion: 0.09
Nodes (23): concurrently, laravel-vite-plugin, devDependencies, concurrently, laravel-vite-plugin, tailwindcss, @tailwindcss/typography, @tailwindcss/vite (+15 more)

### Community 19 - "Panel Chart Components"
Cohesion: 0.12
Nodes (19): react, ChartConfig, ChartContainer(), ChartContext, ChartContextProps, ChartLegendContent(), ChartTooltipContent(), getPayloadConfigFromPayload() (+11 more)

### Community 20 - "Metadata Generator (Anthropic/Groq fallback)"
Cohesion: 0.15
Nodes (16): Anthropic structured outputs via output_config json_schema, _build_prompt(), generate_metadata(), _generate_via_anthropic(), _generate_via_groq(), _log(), _normalize_metadata(), metadata_generator.py — Geração de título, descrição e tags para YouTube.… (+8 more)

### Community 21 - "Video Dedup (Redis + MySQL fallback)"
Cohesion: 0.13
Nodes (15): is_seen(), _log(), mark_failed_redis(), dedup.py — Deduplicação de vídeos via Redis com fallback para MySQL. Exporta: -…, Loga mensagem com timestamp para stdout., Verifica se o vídeo já foi processado anteriormente. Consulta o Redis primeiro.…, Remove a chave do vídeo do Redis quando o download falha. Isso permite que o…, Testes ACQU-03: deduplicação via Redis com fallback para MySQL. Módulo alvo:… (+7 more)

### Community 22 - "Video Transcriber (Groq Whisper)"
Cohesion: 0.13
Nodes (15): _log(), _prepare_audio(), transcriber.py — Transcrição de vídeos via Groq Whisper API. Exporta: -…, Salva JSON de transcrição em disco e atualiza transcript_path no banco. Args:…, Extrai áudio MP3 de um arquivo de vídeo via ffmpeg. Args: video_path: caminho…, Transcreve um vídeo via Groq Whisper API. Args: video_id: youtube_video_id do…, save_transcript(), transcribe_video() (+7 more)

### Community 23 - "shadcn/ui Components Config"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 24 - "Docker Compose & Env Secrets"
Cohesion: 0.12
Nodes (20): ANTHROPIC_API_KEY intencionalmente vazia até Phase 3, clip-processor/Dockerfile, CLIP_PROCESSOR_INTERNAL_TOKEN env var, clip-processor service (build local), CLIPS_DB_PASSWORD como placeholder no SQL, docker-compose.yml (raiz wordpress/), .env (secrets reais), N8N_ENCRYPTION_KEY via ${VAR} nunca hardcoded (+12 more)

### Community 25 - "Video Downloader (yt-dlp)"
Cohesion: 0.14
Nodes (14): _cleanup_partial(), download_video(), _log(), downloader.py — Download de vídeos YouTube via yt-dlp com disk guard e retry.…, Loga mensagem com timestamp para stdout., Deleta arquivos .part gerados por download incompleto. Usa glob para encontrar…, Baixa um vídeo do YouTube em formato 720p mp4. Args: video_id: ID do vídeo…, Testes ACQU-02: download 720p, disk guard, partial cleanup. Módulo alvo:… (+6 more)

### Community 26 - "YouTube Uploader (Google API)"
Cohesion: 0.10
Nodes (17): Credentials, MediaFileUpload, uploader.py — Upload de clips para YouTube Data API v3. Exporta: -…, RefreshError, RED test para captura de RefreshError e persistência de oauth_expired_flag…, RefreshError em creds.refresh() deve setar oauth_expired_flag=TRUE em…, test_load_credentials_catches_refresh_error_and_flags_channel(), Default privacyStatus=private, configuravel por YOUTUBE_PRIVACY_STATUS (+9 more)

### Community 27 - "Pipeline Error Handling Tests"
Cohesion: 0.10
Nodes (11): HttpError, Sem injeção, deve criar e fechar a própria conexão., Erro em _download_pending_videos não deve propagar., Deve chamar poll → download → publish em ordem., Erro em _download_pending_videos não deve propagar., Conexões injetadas devem ser passadas para os sub-módulos., Conexão injetada não deve ser fechada pelo runner (responsabilidade do caller)., Erro em publish_pending_clips não deve propagar — scheduler continua. (+3 more)

### Community 28 - "Internal API Sidecar Tests (RED)"
Cohesion: 0.10
Nodes (11): client(), fixture, RED tests for internal_api sidecar (implementação GREEN no Plan 08-07)., POST /internal/process-url sem campo 'url' retorna 400., purge_old_videos apaga linhas sem clips e libera arquivo de linhas com clips…, POST /internal/process-url sem token retorna 401., POST /internal/process-url chama processar_main(url) e retorna {'exit_code': N}., test_process_url_calls_processar_main_and_returns_exit_code() (+3 more)

### Community 29 - "Laravel Niche Controller & Middleware"
Cohesion: 0.13
Nodes (9): Illuminate\Foundation\Configuration\Middleware, Illuminate\Http\Request, Illuminate\Http\Response, Inertia\Middleware, JsonResponse, NicheController, TelegramWebhookController, HandleInertiaRequests (+1 more)

### Community 30 - "Laravel SourceVideo Controller"
Cohesion: 0.14
Nodes (4): Illuminate\Http\JsonResponse, SourceVideoController, SourceVideo, ClipProcessorClient

### Community 31 - "Laravel Auth Controller"
Cohesion: 0.15
Nodes (6): Inertia\Response, AuthController, Controller, DocumentationController, ProcessVideoController, SettingsController

### Community 32 - "Panel: Checkbox/Select UI Primitives"
Cohesion: 0.13
Nodes (17): Checkbox(), Select(), SelectContent(), SelectGroup(), SelectItem(), SelectLabel(), SelectScrollDownButton(), SelectScrollUpButton() (+9 more)

### Community 33 - "TypeScript Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 34 - "Panel Frontend Dependencies"
Cohesion: 0.11
Nodes (19): clsx, @dnd-kit/core, @dnd-kit/modifiers, @fontsource-variable/geist, lucide-react, dependencies, clsx, @dnd-kit/core (+11 more)

### Community 35 - "Planning Docs: Requirements & Milestones v1.0"
Cohesion: 0.18
Nodes (16): v1.0 — Pipeline Base, MANUAL_APPROVAL_REQUIRED toggle, ACQU-01: Monitoramento RSS de canais, ACQU-02: Download automático 720p via yt-dlp, ACQU-03: Deduplicação Redis + MySQL UNIQUE, INFRA-01: Sistema roda em Docker, INFRA-02: Banco clips_automation com 3 tabelas, INFRA-03: Canal YouTube verificado (+8 more)

### Community 36 - "Pipeline Runner Download Cycle Tests"
Cohesion: 0.18
Nodes (10): _download_pending_videos(), Baixa vídeos com status 'pending', um por vez, atualizando status no DB., Testes para pipeline_runner.py — ciclo completo do pipeline., Download bem-sucedido deve atualizar status para downloaded com local_path., Download falho deve atualizar status para failed., Sem vídeos pending, não deve chamar download_video., Janela já cheia nos dois formatos não deve chamar download_video., Ordem fixa: repõe longos primeiro, depois curtos. (+2 more)

### Community 37 - "Laravel App Service Provider"
Cohesion: 0.14
Nodes (9): GuzzleHttp\Promise\PromiseInterface, Illuminate\Support\ServiceProvider, AppServiceProvider, static, TelegramHttpClientHandler, Phase 9 Plan 02: TelegramWebhookController + Commands Summary, Psr\Http\Message\ResponseInterface, Telegram\Bot\HttpClients\HttpClientInterface (+1 more)

### Community 38 - "Laravel Source Channel Controller"
Cohesion: 0.20
Nodes (6): Illuminate\Database\Eloquent\Factories\HasFactory, Illuminate\Database\Eloquent\Model, SourceChannelController, Niche, SourceChannel, SourceVideoFactory

### Community 39 - "Panel: Confirm Dialog UI"
Cohesion: 0.20
Nodes (14): ConfirmButtonProps, AlertDialog(), AlertDialogAction(), AlertDialogCancel(), AlertDialogContent(), AlertDialogDescription(), AlertDialogFooter(), AlertDialogHeader() (+6 more)

### Community 40 - "Community 40"
Cohesion: 0.18
Nodes (16): quota_manager.py — Limite diario e janela de horario para uploads YouTube.…, MAX_UPLOADS_PER_DAY clamped to <= 6, default 2, mysql/init/04-publishing-migration.sql, Pattern: clock injection para testes deterministas, 05-01 Plan: Publishing schema, skeletons and RED tests, 05-01 Summary: publishing migration + TDD suite, 05-02 Plan: Quota and schedule guard, 05-02 Summary: QuotaManager implemented (+8 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (17): rss_poller blacklist guard + target_niche SELECT extension, COPY-01 requirement: watermark burned into every clip, COPY-02 requirement: original channel credits in description, COPY-03 requirement: blacklisted channels never downloaded, Dual-layer blacklist guard pattern (SQL filter + Python loop guard), Graceful degradation pattern: return input unchanged when optional dependency missing, MCAN-01 requirement: OAuth token per destination channel, MCAN-02 requirement: destination_channel_id routing by niche (+9 more)

### Community 42 - "Community 42"
Cohesion: 0.12
Nodes (15): telegram_notifier.py — Cliente HTTP que publica eventos do pipeline para o…, Testes para telegram_notifier.py — cliente HTTP que dispara eventos para o…, notify() captura RequestException e retorna False sem propagar., notify() retorna False quando o endpoint retorna 4xx., notify() faz POST para LARAVEL_NOTIFY_URL — RED até Plan 09-03. Importa…, notify() inclui header Host para nginx routing — RED até Plan 09-03., test_failure_event(), test_http_4xx_returns_false() (+7 more)

### Community 43 - "Community 43"
Cohesion: 0.18
Nodes (13): OverviewCards(), Card(), CardAction(), CardDescription(), CardFooter(), CardHeader(), CardTitle(), ActiveWindowVideo (+5 more)

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (15): ARCHITECTURE.md (as-built, commit dca6e44), AI fallback chain (Claude → Groq → deterministic), niches table (only Laravel-migration-managed pipeline table), Quota, window and round-robin logic, source_videos.status state machine, CLAUDE.md — Canal de Cortes work instructions, Rules for destructive operations, metadata_generator.py Groq fallback fix (27/07/2026) (+7 more)

### Community 45 - "Community 45"
Cohesion: 0.15
Nodes (15): APScheduler jobs (ingest_cycle, publish_cycle, clip_pending_ttl), Boundary rule: painel reads directly, writes via sidecar, clip-processor service (as-built), internal_api.py sidecar (Flask, port 8090), CLIP_PROCESSOR_INTERNAL_TOKEN shared setup, Telegram Command classes (Status/Clipes/Aprovar/Rejeitar/Processar/Ajuda), Pitfall: CSRF blocking Telegram webhook (419), Pitfall: Python→Laravel via wrong Host header (404) (+7 more)

### Community 46 - "Community 46"
Cohesion: 0.13
Nodes (14): generated_clips.status state machine, list-pending-clips.sh, mark-published.sh, manual-workflow/README.md — manual clip publishing guide, n8n 06-router.json deactivation, Redis SET NX dedup pattern (tg:dedup:{update_id}), Pitfall: Blacklist Check Happens Too Late in the Pipeline, Pitfall: Filament Delete Button Deletes MySQL Row Without Deleting Files (+6 more)

### Community 47 - "Community 47"
Cohesion: 0.18
Nodes (15): burn_subtitles(), clip-processor/src/video_processor.py, clip-processor/tests/test_clip_pipeline.py, clip-processor/tests/test_video_processor.py, cut_clip(), extract_thumbnail(), generate_srt(), 04-02-PLAN.md: video_processor.py GREEN plan (+7 more)

### Community 48 - "Community 48"
Cohesion: 0.17
Nodes (15): output_config json_schema em vez de prefill para Claude Haiku 4.5, generate_metadata(), insert_selected_moments(), Algoritmo de remoção de overlap por score, 03-CONTEXT.md: Phase 3 Context, _process_ai_pipeline(), _remove_overlaps(), AI-01: transcrição via Groq Whisper (+7 more)

### Community 49 - "Community 49"
Cohesion: 0.21
Nodes (6): Marca destination_channels.oauth_expired_flag=TRUE para o slug atual. Best-…, Self-healing: reseta oauth_expired_flag=FALSE após upload bem-sucedido., Cliente fino para videos.insert + thumbnails.set., YouTubeUploader, Multi-canal extension via optional constructor param + None-guard retrocompat, Publisher legacy fallback when destination_channels empty

### Community 50 - "Community 50"
Cohesion: 0.18
Nodes (6): Illuminate\Database\Eloquent\Factories\Factory, DestinationChannelFactory, GeneratedClipFactory, SourceChannelFactory, static, UserFactory

### Community 52 - "Community 52"
Cohesion: 0.13
Nodes (15): scripts, dev, post-autoload-dump, post-create-project-cmd, post-update-cmd, pre-package-uninstall, Composer\\Config::disableProcessTimeout, Illuminate\\Foundation\\ComposerScripts::postAutoloadDump (+7 more)

### Community 53 - "Community 53"
Cohesion: 0.14
Nodes (12): burn_watermark() function design, Admin Panel (Laravel/Filament) feature spec, Copyright Protection feature spec, Multi-Channel YouTube Publishing feature spec, OAuth testing-mode token expiry warning (7 days), Pitfall: Content ID Claim Despite Watermark, Laravel 13 version choice (not 11), FFmpeg watermark filter_complex design (+4 more)

### Community 54 - "Community 54"
Cohesion: 0.15
Nodes (13): Filament removal commit dca6e44, painel/ — Laravel 13 + Inertia 3 + React 19 (Filament removed), clip-processor/requirements.txt, nginx bind mount painel fix (404 puro), painel/README.md (setup fresh 10 passos), routes/web.php raiz '/' redirect fix, YouTube OAuth authorization CLI flow (youtube_oauth.py), Phase 8 Plan 09: Checkpoint Final End-to-End Plan (+5 more)

### Community 55 - "Community 55"
Cohesion: 0.15
Nodes (14): clip-processor/src/selector.py, clip-processor/src/transcriber.py, clip-processor/tests/test_selector.py, clip-processor/tests/test_transcriber.py, Groq Whisper whisper-large-v3-turbo + verbose_json + timestamp_granularities segment + pt, mysql/init/03-schema-migration.sql, 03-01-PLAN.md: Wave 0 skeletons + RED tests, 03-01-SUMMARY.md: Wave 0 Summary (+6 more)

### Community 56 - "Community 56"
Cohesion: 0.14
Nodes (13): autoload-dev, psr-4, description, keywords, license, minimum-stability, name, prefer-stable (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.24
Nodes (8): Seleciona vídeos pendentes pra repor a janela de download ativo. Para cada…, _select_pending_videos(), Testes para _select_pending_videos — janela de download ativo (DOWNLOAD-01)., Janela vazia (occupied=0) deve buscar até o teto de cada formato., Formato já na janela cheia não gera nenhuma query SELECT (só o COUNT)., Déficit parcial (occupied=1 de janela 4) deve pedir LIMIT 3, não o teto inteiro., SELECT deve restringir a published_at de hoje ou ontem (FRESHNESS_DAYS=1)., TestSelectPendingVideos

### Community 58 - "Community 58"
Cohesion: 0.20
Nodes (12): Phase 8 Deferred Items, Filament $isLazy=false widget pattern, generated_clips.status ENUM (approved/rejected), mysql/init/05-controle-manual-migration.sql, App\Filament\Widgets\PendingApprovalWidget, App\Filament\Widgets\RecentFailuresWidget, App\Filament\Widgets\RecentUploadsWidget, PANEL-02 requirement (CRUD canal-destino + badge OAuth) (+4 more)

### Community 59 - "Community 59"
Cohesion: 0.21
Nodes (9): append_credits(), Adiciona linha de créditos ao final da descrição. Nunca sobrescreve conteúdo…, COPY-02: template vazio → retorna descrição sem modificação., COPY-02: handle vazio → retorna descrição sem modificação., Testes RED para append_credits (COPY-02)., COPY-02: template com {channel_handle} é substituído pelo handle real., TestAppendCredits, Phase 07 Plan 05: overlay_watermark e append_credits (COPY-01/02) (+1 more)

### Community 60 - "Community 60"
Cohesion: 0.24
Nodes (12): mysql/init/01-clips-schema.sql, db.py: quem chama é responsável por fechar a conexão, clip-processor/src/db.py, generated_clips table, INSERT IGNORE para idempotência de vídeos/canais, 01-02-PLAN: Schema SQL clips_automation e validate-infra.sh, 02-02-PLAN: docker-compose + requirements + seed + db.py, 02-02-SUMMARY: db.py GREEN, seed 5 canais (+4 more)

### Community 61 - "Community 61"
Cohesion: 0.32
Nodes (3): Illuminate\Http\RedirectResponse, DestinationChannelController, DestinationChannel

### Community 62 - "Community 62"
Cohesion: 0.22
Nodes (11): BlockingScheduler daemon pattern (APScheduler), clip-processor/src/db.py, clip-processor/src/main.py, clip-processor/src/rss_poller.py, Pitfall: container restart com vídeo em status downloading, 03-04-PLAN.md: AI pipeline integration plan, 03-04-SUMMARY.md: AI pipeline integration Summary, poll_all_channels(db_conn, redis_client) (+3 more)

### Community 63 - "Community 63"
Cohesion: 0.53
Nodes (10): AssertionError, assert_contains(), assert_has_node(), load_json(), main(), nodes_by_name(), validate_cron(), validate_docs() (+2 more)

### Community 64 - "Community 64"
Cohesion: 0.27
Nodes (11): _cleanup_partial() chamado fora do loop de retry, clip-processor/src/dedup.py, clip-processor/src/dedup.py, Dedup pattern: Redis NX → fallback MySQL → False, download_video(video_id, output_path), clip-processor/src/downloader.py, is_seen(video_id, redis_client, db_conn), 02-03-PLAN: dedup.py, downloader.py, rss_poller.py (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.24
Nodes (10): mock_db_conn(), mock_redis(), fixture, Fixtures compartilhadas para todos os testes do clip-processor. Fornece:…, MagicMock simulando redis.Redis. - .set() retorna True por padrão (NX success —…, MagicMock simulando conexão pymysql com suporte a context manager em cursor().…, Feed RSS Atom do YouTube com 2 entradas válidas. VideoIds: 'abc123def456' e…, ID de vídeo YouTube válido (11 caracteres). (+2 more)

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (10): Checkpoint humano: verificação end-to-end Phase 4, _process_pending_clips(conn), Migration Phase 3 usa INFORMATION_SCHEMA em vez de ADD COLUMN IF NOT EXISTS, Persistir arquivos renderizados no volume montado /app/videos, Raw source só removido quando todos clips do source video estão terminais, generated_clips.status = pending_cut, mysql/init/03-schema-migration.sql, 04-03 Summary: metadata_generator.py implementation (+2 more)

### Community 67 - "Community 67"
Cohesion: 0.24
Nodes (9): video_processor.py — Corte, legendas, thumbnail e processamento de clips.…, Pattern: FFmpeg Shorts Transform (crop/pad 1080x1920), Pattern: Patchable Directories (module constants for output folders), Pattern: Subtitle Burn-In (SRT from transcript segments), Phase 4 Research: Video Processing, VID-01: FFmpeg corta clip e resize 9:16 1080x1920, VID-02: Legendas Whisper queimadas no clip, VID-03: Thumbnail extraída de frame do clip (+1 more)

### Community 68 - "Community 68"
Cohesion: 0.22
Nodes (8): _log(), overlay_watermark(), Aplica watermark PNG no canto superior direito do clip via FFmpeg. Usa…, Testes RED para overlay_watermark (COPY-01)., COPY-01: wm_path existente → ffmpeg com -filter_complex e overlay=W-w-20:20., COPY-01: wm_path ausente → retorna input_path sem chamar subprocess., TestOverlayWatermark, FFmpeg dual-input pattern: -filter_complex overlay (clip first, watermark second)

### Community 69 - "Community 69"
Cohesion: 0.20
Nodes (10): require-dev, fakerphp/faker, laravel/pail, laravel/pao, laravel/pint, mockery/mockery, nunomaduro/collision, pestphp/pest (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.20
Nodes (10): 02-04-PLAN.md: Daemon main.py Plan, 02-04-SUMMARY.md: Daemon main.py Summary, 02-CONTEXT.md: Phase 2 Context, 02-RESEARCH.md: Phase 2 Research, 02-VALIDATION.md: Phase 2 Validation Strategy, pytest test infra (Phase 2 Wave 0), ACQU-01: monitorar canais via RSS a cada 6h, ACQU-02: baixar vídeos novos em 720p via yt-dlp (+2 more)

### Community 71 - "Community 71"
Cohesion: 0.28
Nodes (9): Dead code: painel/app/Filament/Pages/Dashboard.php orphan, env() outside config() pitfall in DashboardController, Section 10: Known divergences and technical debt, channel_blacklist table (research design), destination_channels table (research design), Phase 7: Schema Multi-Canal + Watermark + Copyright (research plan), Phase 8: Laravel/Filament Painel Base (research plan), Phase 9: Bot Telegram no Laravel + Migração do n8n (research plan) (+1 more)

### Community 72 - "Community 72"
Cohesion: 0.28
Nodes (8): generate_token(), main(), Helper CLI para gerar token OAuth YouTube por canal-destino. Uso: python -m…, Gera token OAuth para o canal-destino e salva em…, docker-compose.yml branding volume for clip-processor, Path, Phase 07 Plan 07: YouTube OAuth CLI + Branding Volume, Phase 07 Plan 07 Summary: YouTube OAuth CLI + Branding Volume (paused)

### Community 73 - "Community 73"
Cohesion: 0.22
Nodes (5): Deve chamar poll → download em ordem, sem publish., Erro em poll_all_channels não deve impedir tentativa de download., Sem injeção, deve criar e fechar a própria conexão., Conexão injetada não deve ser fechada pelo runner., TestRunIngestCycle

### Community 74 - "Community 74"
Cohesion: 0.33
Nodes (9): clip-processor/tests/conftest.py, 02-01-PLAN: pytest scaffold RED state (Wave 0), 02-01-SUMMARY: 17 testes RED criados, clip-processor/pytest.ini, TDD RED-GREEN-REFACTOR pattern (imports no topo causam ModuleNotFoundError), tests/test_db.py, tests/test_dedup.py, tests/test_downloader.py (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.33
Nodes (6): Accordion(), AccordionContent(), AccordionItem(), AccordionTrigger(), CHAIN, PageProps

### Community 76 - "Community 76"
Cohesion: 0.25
Nodes (8): BOT-01 requirement (webhook + allowlist + dedup), BOT-02 requirement (6 Telegram commands), BOT-03 requirement (pipeline-event notifications), PipelineEventTest.php (4 RED tests), TelegramCommandsTest.php (7 RED tests), TelegramWebhookTest.php (3 RED tests), Phase 9 Plan 01: Wave 0 SDK + Config + RED Tests Plan, irazasyed/telegram-bot-sdk ^3.16

### Community 78 - "Community 78"
Cohesion: 0.25
Nodes (5): Testes RED para suporte a channel_slug no YouTubeUploader (MCAN-01)., MCAN-01: channel_slug='futebol-em-cortes' → token_file='/app/youtube/token-…, Retrocompat: sem channel_slug, usa DEFAULT_TOKEN_FILE., Retrocompat: token_file explícito tem precedência sobre channel_slug., TestYouTubeUploaderChannelSlug

### Community 79 - "Community 79"
Cohesion: 0.25
Nodes (8): post-root-package-install, setup, composer install, npm install --ignore-scripts, npm run build, @php artisan key:generate, @php artisan migrate --force, @php -r \"file_exists('.env') || copy('.env.example', '.env');\

### Community 80 - "Community 80"
Cohesion: 0.36
Nodes (8): PANEL-01 requirement (CRUD canal-fonte sem SQL), PANEL-03 requirement (dashboard tempo real), PANEL-04 requirement (aprovar/rejeitar clip), PANEL-05 requirement (autenticação single-user), Phase 8 human checkpoint (7-step verification), Phase 8 Plan 04: Autenticação Summary, Phase 8 Context (Painel Laravel/Filament), Phase 8 Validation Strategy

### Community 81 - "Community 81"
Cohesion: 0.39
Nodes (8): PipelineEventTest.php, setWebhook registration to https://alessandromelo.com.br/telegramcanal, Phase 9-04 Plan: Telegram Bot Checkpoint, TelegramCommandsTest.php, TelegramWebhookTest.php, Artisan Schedule daily summary 18h BRT, Phase 9 Research: Bot Telegram no Laravel, Phase 9 Validation Strategy

### Community 82 - "Community 82"
Cohesion: 0.25
Nodes (7): Bot Telegram no Laravel (v2), Groq Whisper (API) em vez de Whisper local, Multi-canal com token OAuth por canal, Phase 7: Schema Multi-Canal + Python Pipeline, Phase 8: Painel Laravel/Filament, Phase 9: Bot Telegram no Laravel, recover_stuck_downloads só recupera 'downloading' → 'pending'

### Community 83 - "Community 83"
Cohesion: 0.29
Nodes (7): youtube/generate_token.py, OAuth app type 'installed' (Desktop App), não 'web', OAuth app publicado em Production, Pitfall: YouTube OAuth em modo Testing expira em 7 dias, 01-04-PLAN: OAuth YouTube e verificação do canal, 01-04-SUMMARY: OAuth e canal configurados, Canal YouTube "Futebol em Cortes"

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (7): pestphp/pest-plugin, php-http/discovery, config, allow-plugins, optimize-autoloader, preferred-install, sort-packages

### Community 85 - "Community 85"
Cohesion: 0.29
Nodes (7): require, inertiajs/inertia-laravel, irazasyed/telegram-bot-sdk, laravel/framework, laravel/tinker, php, tightenco/ziggy

### Community 86 - "Community 86"
Cohesion: 0.29
Nodes (6): private, $schema, scripts, build, dev, type

### Community 87 - "Community 87"
Cohesion: 0.33
Nodes (6): clip-processor/src/metadata_generator.py, clip-processor/tests/test_metadata_generator.py, 04-01-PLAN.md: Phase 4 Wave 0 skeletons + RED tests, 04-01-SUMMARY.md: Phase 4 Wave 0 Summary, 04-03-PLAN.md: metadata_generator.py GREEN plan, update_clip_metadata()

### Community 88 - "Community 88"
Cohesion: 0.33
Nodes (6): YouTubeUploader.upload_clip(clip), YOUTUBE_TOKEN_FILE (default /app/token.json), 05-03 Plan: YouTube uploader, 05-03 Summary: YouTubeUploader implemented, 05-04 Plan: Publisher and raw cleanup, 05-04 Summary: Publisher implemented

### Community 89 - "Community 89"
Cohesion: 0.33
Nodes (4): Testes de integração: process_clip aplica overlay_watermark com slug do canal-…, MCAN-02: process_clip chama overlay_watermark com watermark_path derivado do…, MCAN-02: destination_channel_slug NULL → os.rename é usado, overlay_watermark…, TestProcessClipWithWatermark

### Community 90 - "Community 90"
Cohesion: 0.40
Nodes (5): clip-processor/src/downloader.py, Guard de espaço em disco antes do download (<2GB), Retry de download: 3x com 60s entre tentativas, Extração de áudio ffmpeg para arquivos >24MB, _prepare_audio()

### Community 91 - "Community 91"
Cohesion: 0.40
Nodes (5): Workflow usa Execute Command com retry 3x e espera 15 minutos, n8n/workflows/canaldecortes-pipeline.json, n8n/workflows/README.md, 05-06 Plan: n8n workflow and production checkpoint, 05-06 Summary: n8n workflow importable, retry documented

### Community 92 - "Community 92"
Cohesion: 0.40
Nodes (5): docker exec / Docker socket bridge anti-pattern, Pattern 3: ponte HTTP interna clip-processor↔painel, App\Filament\Widgets\QuotaTodayWidget, Phase 8 Research (Painel Laravel/Filament), Pitfall: Redis connection('pipeline') vs default (DB0 vs DB1)

### Community 93 - "Community 93"
Cohesion: 0.50
Nodes (3): Filament\Pages\Dashboard, Illuminate\Contracts\Support\Htmlable, Dashboard

### Community 94 - "Community 94"
Cohesion: 0.40
Nodes (5): Filament Resource GET/HEAD-only routing pattern, App\Filament\Resources\SourceChannelResource, routes/web.php POST/PATCH source-channels REST routes, Phase 8 Plan 05: SourceChannelResource Plan, Phase 8 Plan 05: SourceChannelResource Summary

### Community 95 - "Community 95"
Cohesion: 0.40
Nodes (5): autoload, psr-4, App\\, Database\\Factories\\, Database\\Seeders\\

### Community 96 - "Community 96"
Cohesion: 0.40
Nodes (4): v2.0 — Painel + Multi-Canal, BOT-01: Bot Telegram migrado para Laravel, MCAN-01: Múltiplos canais destino com OAuth próprio, PANEL-01: Adicionar/remover canais-fonte via formulário web

### Community 97 - "Community 97"
Cohesion: 0.83
Nodes (3): mysql_exec(), mysql_exec_pretty(), list-pending-clips.sh script

### Community 100 - "Community 100"
Cohesion: 0.50
Nodes (3): youtube/assets/BRANDING.md — Futebol em Cortes visual identity, Banner generation prompt (2560x1440px), Logo generation prompt (scissors + play button, red/black/white)

### Community 103 - "Community 103"
Cohesion: 0.67
Nodes (3): extra, laravel, dont-discover

### Community 104 - "Community 104"
Cohesion: 0.67
Nodes (3): test, @php artisan config:clear --ansi @no_additional_args, @php artisan test

### Community 110 - "Community 110"
Cohesion: 1.00
Nodes (3): Resenha FC channel banner (2048x1152), Soccer-ball mascot with microphone (cartoon character), Resenha FC (brand/channel name)

## Ambiguous Edges - Review These
- `clip-processor/src/ttl_worker.py` → `clip-processor/src/telegram_notifier.py`  [AMBIGUOUS]
  .planning/phases/06-controle-manual-n8n-telegram/06-05-SUMMARY.md · relation: conceptually_related_to

## Knowledge Gaps
- **259 isolated node(s):** `force-download.sh script`, `$schema`, `style`, `rsc`, `tsx` (+254 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `clip-processor/src/ttl_worker.py` and `clip-processor/src/telegram_notifier.py`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `run_pipeline_once()` connect `MySQL DB Access Layer (clip-processor)` to `Publisher Credit & Upload Flow`, `Pipeline Runner Download Cycle Tests`, `RSS Poll & AI Pipeline Orchestration`, `Pipeline Error Handling Tests`, `Community 91`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Why does `n8n/workflows/canaldecortes-pipeline.json` connect `Community 91` to `Community 40`, `MySQL DB Access Layer (clip-processor)`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `05-06 Plan: n8n workflow and production checkpoint` connect `Community 91` to `MySQL Migrations & Manual Workflow SQL`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `QuotaManager` (e.g. with `TestCanUpload` and `TestQuotaManagerMultiCanal`) actually correct?**
  _`QuotaManager` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `YouTubeUploader` (e.g. with `TestUploadClip` and `TestYouTubeUploaderChannelSlug`) actually correct?**
  _`YouTubeUploader` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `force-download.sh script`, `$schema`, `style` to the rest of the system?**
  _259 weakly-connected nodes found - possible documentation gaps or missing edges._