# Roadmap: Canal de Cortes — Futebol & Esportes

## Overview

O pipeline é construído de baixo para cima: a infraestrutura Docker e o canal do YouTube são criados primeiro, depois a aquisição de vídeos, depois o processamento com IA, depois a edição final de vídeo e, por último, a publicação automatizada fecha o ciclo end-to-end. Cada fase entrega uma capacidade verificável antes da próxima começar — nenhuma fase depende de código da fase seguinte.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Infraestrutura Base** - Docker services, MySQL schema, canal do YouTube e secrets prontos
- [x] **Phase 2: Aquisição de Vídeos** - Monitor RSS, download yt-dlp, deduplicação e rastreamento de jobs (completed 2026-06-18)
- [x] **Phase 3: IA — Transcrição e Seleção** - Groq Whisper transcreve, Claude Haiku seleciona melhores momentos (completed 2026-06-18)
- [x] **Phase 4: Processamento de Vídeo** - FFmpeg corta, redimensiona 9:16, queima legendas e gera thumbnail + metadados (completed 2026-06-18)
- [x] **Phase 5: Publicação e Automação Total** - Upload YouTube API, quota management, agendamento e workflow n8n end-to-end (completed 2026-06-18)
- [x] **Phase 6: Controle Manual N8N + Telegram** - Bot Telegram para aprovação/rejeição manual de clips; publisher passa a publicar approved (completed 2026-06-21)
- [x] **Phase 7: Schema Multi-Canal + Python Pipeline** - Schema migrations, roteamento por nicho, quota por canal, watermark FFmpeg, créditos e blacklist (completed 2026-06-22)
- [x] **Phase 8: Painel Laravel/Filament** (completed 2026-07-02) - CRUD canais-fonte e destino, dashboard de pipeline, fila de aprovação e autenticação web
- [ ] **Phase 9: Bot Telegram no Laravel** - Migração do bot do n8n para Laravel com webhook, todos os 6 comandos e notificações do pipeline

## Phase Details

### Phase 1: Infraestrutura Base
**Goal**: Todos os serviços necessários rodam no Docker, o banco de dados está criado, o canal do YouTube está pronto para receber uploads e todas as credenciais estão configuradas
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. `docker-compose up` sobe n8n, clip-processor e whisper sem erros, ao lado dos serviços já existentes (nginx, PHP, MySQL, Redis)
  2. Banco `clips_automation` existe no MySQL com tabelas `source_channels`, `source_videos` e `generated_clips` verificáveis via SQL
  3. Canal do YouTube existe com conta verificada, banner e bio preenchidos — pronto para receber o primeiro vídeo
  4. Variáveis `.env` (Claude API key, YouTube OAuth credentials) estão carregadas e os serviços sobem sem erro de configuração faltando
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Estrutura de diretórios, docker-compose extension (n8n + clip-processor + whisper) e clip-processor Dockerfile
- [x] 01-02-PLAN.md — Schema SQL clips_automation (3 tabelas) e script validate-infra.sh
- [x] 01-03-PLAN.md — Gerar .env com secrets reais, subir serviços Docker e aplicar schema MySQL
- [x] 01-04-PLAN.md — Script OAuth YouTube, geração de token.json e verificação do canal

### Phase 2: Aquisição de Vídeos
**Goal**: O sistema detecta novos vídeos nos canais configurados, baixa automaticamente e registra cada job — sem reprocessar o que já foi processado
**Depends on**: Phase 1
**Requirements**: ACQU-01, ACQU-02, ACQU-03, ORC-02
**Success Criteria** (what must be TRUE):
  1. Ao adicionar um canal à tabela `source_channels`, novos vídeos são detectados via RSS dentro de 6 horas sem consumir cota da YouTube API
  2. Um vídeo detectado aparece baixado em 720p no diretório de trabalho dentro de minutos após a detecção
  3. Rodar o pipeline duas vezes no mesmo vídeo não resulta em download ou reprocessamento duplicado
  4. Cada vídeo tem um registro em `source_videos` com status `pending/downloading/downloaded/failed` atualizado em tempo real
**Plans**: 4 plans

Plans:
- [x] 02-01-PLAN.md — Infraestrutura de testes pytest: pytest.ini, conftest.py com fixtures, 4 test_*.py em RED state (Wave 0)
- [x] 02-02-PLAN.md — docker-compose (volume + Redis env), requirements.txt, seed SQL de canais e db.py
- [x] 02-03-PLAN.md — Módulos principais: dedup.py, downloader.py e rss_poller.py (testes GREEN)
- [x] 02-04-PLAN.md — main.py daemon BlockingScheduler + checkpoint de verificação end-to-end

### Phase 3: IA — Transcrição e Seleção
**Goal**: Áudio de qualquer vídeo baixado é transcrito via Groq Whisper API e os melhores momentos são identificados pelo Claude Haiku antes de qualquer processamento de vídeo acontecer
**Depends on**: Phase 2
**Requirements**: AI-01, AI-02, AI-03
**Success Criteria** (what must be TRUE):
  1. Um vídeo em PT-BR processado pelo Groq Whisper API produz um arquivo JSON de transcrição com texto e timestamps por segmento
  2. A transcrição enviada ao Claude Haiku retorna uma lista estruturada de momentos com score 1-10, timestamps de início/fim e motivo para cada momento
  3. Apenas momentos com score maior ou igual a 7 avançam para a fila de corte — momentos com score inferior são descartados e registrados
**Plans**: 4 plans

Plans:
- [x] 03-01-PLAN.md — Wave 0: schema migration SQL (pending_cut, reason, transcript_path) + skeletons transcriber.py/selector.py + 11 testes em RED
- [x] 03-02-PLAN.md — transcriber.py: Groq Whisper API com timestamps, ffmpeg fallback para >25MB (AI-01 GREEN)
- [x] 03-03-PLAN.md — selector.py: Claude Haiku structured outputs, filtro score>=7, remoção de overlaps (AI-02+AI-03 GREEN)
- [x] 03-04-PLAN.md — Integração em rss_poller.py + checkpoint end-to-end

### Phase 4: Processamento de Vídeo
**Goal**: Cada momento selecionado pela IA vira um clip completo: cortado, no formato correto para Shorts, com legendas visíveis, thumbnail extraída e metadados prontos para publicação
**Depends on**: Phase 3
**Requirements**: VID-01, VID-02, VID-03, VID-04
**Success Criteria** (what must be TRUE):
  1. Um clip é cortado nos timestamps exatos da IA e exportado em 1080x1920 (9:16) compatível com YouTube Shorts
  2. As legendas geradas pelo Whisper aparecem queimadas no clip com fonte legível e bordas visíveis mesmo em fundo variado
  3. Uma thumbnail válida (frame extraído do clip) existe como arquivo de imagem pronto para upload
  4. Título (máximo 100 caracteres), descrição e tags otimizados para futebol/PT-BR foram gerados pelo Claude Haiku e estão associados ao clip
**Plans**: 4 plans

Plans:
- [x] 04-01-PLAN.md — Wave 0: skeletons video_processor.py/metadata_generator.py + testes RED para video, metadata e integração
- [x] 04-02-PLAN.md — video_processor.py: FFmpeg corta 1080x1920, queima legendas e extrai thumbnail (VID-01/02/03 GREEN)
- [x] 04-03-PLAN.md — metadata_generator.py: Claude Haiku gera título, descrição e tags SEO (VID-04 GREEN)
- [x] 04-04-PLAN.md — Integração em rss_poller.py + checkpoint end-to-end do clip renderizado

### Phase 5: Publicação e Automação Total
**Goal**: Clips processados são publicados automaticamente no YouTube respeitando cota e horários, o pipeline completo roda do RSS ao upload sem intervenção manual, e vídeos brutos são limpos após sucesso
**Depends on**: Phase 4
**Requirements**: PUB-01, PUB-02, PUB-03, PUB-04, ORC-01
**Success Criteria** (what must be TRUE):
  1. Um clip com metadados prontos é publicado no YouTube com título, descrição, tags e thumbnail via YouTube Data API v3 sem intervenção manual
  2. O sistema nunca excede 6 uploads por dia — quando o limite é atingido, uploads adicionais ficam na fila para o próximo dia
  3. Uploads são agendados automaticamente entre 19h e 22h horário de Brasília
  4. Após um upload bem-sucedido, o vídeo bruto original é deletado do disco e o status do job muda para `published`
  5. O workflow n8n dispara automaticamente a cada ciclo (RSS poll → download → transcrição → seleção → corte → upload) com retry em caso de falha em qualquer etapa
**Plans**: 6 plans

Plans:
- [x] 05-01-PLAN.md — Wave 0: migration de publicação, skeletons quota/uploader/publisher/runner e testes RED
- [x] 05-02-PLAN.md — QuotaManager: limite diário Redis e janela 19h-22h America/Sao_Paulo
- [x] 05-03-PLAN.md — YouTubeUploader: upload de MP4 + thumbnail via YouTube Data API v3 usando token OAuth
- [x] 05-04-PLAN.md — Publisher: status pending → publishing → published, quota guard e cleanup seguro do raw source
- [x] 05-05-PLAN.md — Pipeline runner e integração do publisher ao daemon APScheduler
- [x] 05-06-PLAN.md — Workflow n8n com retry e checkpoint de upload privado end-to-end

### Phase 6: Controle Manual N8N + Telegram

**Goal**: Operador aprova ou rejeita clipes pré-cortados via comandos no Telegram orquestrados pelo n8n; pipeline continua autônomo até a aprovação, e o publisher passa a publicar apenas clipes com status `approved`, respeitando quota e janela horária existentes.
**Depends on**: Phase 5
**Requirements**: CTRL-01, CTRL-02, CTRL-03, CTRL-04, CTRL-05, CTRL-06
**Success Criteria** (what must be TRUE):
  1. Bot Telegram responde aos comandos `/status`, `/clipes`, `/aprovar <id>`, `/rejeitar <id>`, `/processar <url>` e `/ajuda` quando enviados pelo `chat_id` da allowlist; mensagens de outros chats são ignoradas silenciosamente.
  2. Migration adiciona `approved` e `rejected` ao ENUM `generated_clips.status`; `publisher.py` seleciona apenas clipes `approved` (em vez de `pending`) respeitando quota máx 2/dia e janela 19h-22h America/Sao_Paulo.
  3. `/aprovar <id>` muda status de `pending` para `approved`; `/rejeitar <id>` muda para `rejected` e apaga o MP4 do clip, mantendo o vídeo bruto.
  4. `/processar <url>` baixa metadata do YouTube, insere/atualiza `source_videos` com status `pending` (idempotente), e o pipeline existente cuida do resto sem bypass de regras.
  5. Worker de TTL converte clipes `pending` em `rejected` após 48h; bot envia aviso 24h antes da expiração.
  6. n8n recebe webhook do Telegram via Cloudflare Tunnel (sem ngrok, sem porta aberta); allowlist hardcoded `chat_id=5760918317` filtra acesso.
  7. Bot envia notificações proativas em 3 eventos apenas: upload publicado com sucesso, falha crítica no pipeline, e resumo diário às 18h BRT (skip se 0 pendentes).
**Plans**: 7 plans

Plans:
- [x] 06-01-PLAN.md — Wave 0: migration SQL ENUM + 4 skeletons Python + 5 testes RED + 2 esqueletos n8n + .env.example (CTRL-01..06)
- [x] 06-02-PLAN.md — publisher.py: swap 'pending' → 'approved' + guard de status no UPDATE (CTRL-02)
- [x] 06-03-PLAN.md — rejeitar.py: UPDATE com guard + delete MP4 + preserva raw video (CTRL-03)
- [x] 06-04-PLAN.md — processar.py: parse URL + yt-dlp metadata + upsert idempotente (CTRL-04)
- [x] 06-05-PLAN.md — ttl_worker.py: expire 48h + warn 24h idempotente + integração APScheduler (CTRL-05)
- [x] 06-06-PLAN.md — telegram_notifier.py + integração publisher/pipeline_runner + cloudflared no docker-compose (CTRL-06)
- [x] 06-07-PLAN.md — Workflows n8n completos (router 6 comandos + cron 18h) + SETUP.md + checkpoints operacionais (CTRL-01, CTRL-03, CTRL-04, CTRL-06)

### Phase 7: Schema Multi-Canal + Python Pipeline

**Goal**: O pipeline Python publica clips no canal YouTube correto por nicho, com quota independente por canal, watermark queimado em todo clip, créditos do canal original na descrição e canais blacklistados bloqueados antes do download
**Depends on**: Phase 6
**Requirements**: MCAN-01, MCAN-02, MCAN-03, MCAN-04, COPY-01, COPY-02, COPY-03
**Success Criteria** (what must be TRUE):
  1. Um clip de canal-fonte com `niche='futebol'` é publicado no canal YouTube de futebol; um clip de canal-fonte com `niche='podcast'` é publicado no canal de podcasts — roteamento verificável via `destination_channel_id` na tabela `generated_clips`
  2. Cada canal-destino tem contador de quota Redis independente (`youtube_uploads:{channel_id}:{date}`); atingir 3 uploads no canal A não bloqueia uploads do canal B
  3. Todo clip exportado pelo FFmpeg contém o watermark/logo do canal visível em posição fixa no vídeo — verificável assistindo o arquivo MP4 antes do upload
  4. A descrição gerada pelo Claude para qualquer clip inclui a linha de créditos com o handle do canal original ("Créditos: @canal") — verificável no campo `description` da tabela `generated_clips`
  5. Canal configurado na blacklist (ex: Globo, SBT, Band, ESPN, Liga/Conmebol) não tem nenhum vídeo baixado — `rss_poller.py` filtra canais blacklistados antes do download e eles não aparecem em `source_videos`
**Plans**: 7 plans

Plans:
- [ ] 07-01-PLAN.md — Migration SQL: destination_channels + ALTER source_channels (target_niche, channel_handle, blacklisted) + ALTER generated_clips (destination_channel_id FK) + seed 2 canais
- [ ] 07-02-PLAN.md — Wave 0 tests RED: estender 6 arquivos de teste com novos testes falhando para MCAN/COPY
- [ ] 07-03-PLAN.md — QuotaManager com channel_id + YouTubeUploader com channel_slug (MCAN-01, MCAN-03, MCAN-04)
- [ ] 07-04-PLAN.md — rss_poller: blacklist guard + target_niche no SELECT (COPY-03, MCAN-02)
- [ ] 07-05-PLAN.md — video_processor: overlay_watermark() + metadata_generator: append_credits() (COPY-01, COPY-02)
- [ ] 07-06-PLAN.md — selector: destination_channel_id no INSERT + video_processor: integração watermark + publisher: loop multi-canal (MCAN-01..04, COPY-01..02)
- [ ] 07-07-PLAN.md — youtube_oauth helper CLI + volume branding no docker-compose + checkpoint visual watermark (MCAN-01, COPY-01)

### Phase 8: Painel Laravel/Filament

**Goal**: Operador gerencia canais-fonte e canais-destino, monitora o status do pipeline e aprova ou rejeita clips — tudo via painel web com autenticação, sem precisar de SQL ou Telegram
**Depends on**: Phase 7
**Requirements**: PANEL-01, PANEL-02, PANEL-03, PANEL-04, PANEL-05
**Success Criteria** (what must be TRUE):
  1. Operador acessa o painel com usuário/senha e é redirecionado para login se tentar acessar sem autenticação — nenhuma rota do painel é pública
  2. Operador adiciona um canal-fonte via formulário (URL do YouTube ou channel_id) e o canal aparece imediatamente na tabela `source_channels` sem precisar executar SQL
  3. Operador adiciona um canal-destino com campo `niche` via formulário; o painel exibe badge de status OAuth (authorized / expired / missing) para cada canal-destino
  4. Dashboard mostra lista de `source_videos` e `generated_clips` com status atualizado automaticamente a cada 5 segundos — operador vê o avanço de um vídeo no pipeline sem recarregar a página
  5. Operador clica em "Aprovar" ou "Rejeitar" num clip da fila no painel; o status muda em `generated_clips` da mesma forma que `/aprovar` e `/rejeitar` do Telegram fazem
**Plans**: 9/9 plans

Plans:
- [x] 08-01-PLAN.md — Docker wiring + Laravel/Filament/Pest bootstrap + config (Wave 1)
- [x] 08-02-PLAN.md — Python Wave 0: SQL migration `oauth_expired_flag` + internal_api.py skeleton + testes RED (Wave 1)
- [x] 08-03-PLAN.md — Laravel Wave 0: Eloquent Models + Factories + 6 test skeletons RED (Wave 2)
- [x] 08-04-PLAN.md — Auth (PANEL-05): CreatePainelUser/ResetPainelPassword + AdminPanelProvider login/profile + register 404 (Wave 3)
- [x] 08-05-PLAN.md — Source Channel Resource + ClipProcessorClient (PANEL-01) (Wave 3)
- [x] 08-06-PLAN.md — Destination Channel Resource + OAuth badge + uploader.py RefreshError capture (PANEL-02) (Wave 3)
- [x] 08-07-PLAN.md — internal_api.py GREEN + main.py Flask thread + docker-compose env token (PANEL-01, PANEL-04) (Wave 3)
- [x] 08-08-PLAN.md — Dashboard 4 widgets + Aprovar/Rejeitar actions (PANEL-03, PANEL-04) (Wave 4)
- [x] 08-09-PLAN.md — E2E checkpoint humano + README setup consolidado (Wave 5)

### Phase 9: Bot Telegram no Laravel

**Goal**: O bot Telegram roda dentro do Laravel via webhook e responde a todos os comandos do v1, com deduplicação de update_id, eliminando a dependência do n8n e do Cloudflare Tunnel para o bot
**Depends on**: Phase 8
**Requirements**: BOT-01, BOT-02, BOT-03
**Success Criteria** (what must be TRUE):
  1. Enviar `/status` ou qualquer dos 6 comandos do v1 ao bot resulta em resposta do Laravel — o n8n não está envolvido no fluxo do bot e o Cloudflare Tunnel pode ser desativado sem quebrar o bot
  2. Enviar o mesmo update_id duas vezes (simulando retry do Telegram) não executa o comando duas vezes — a deduplicação via Redis rejeita o duplicado silenciosamente
  3. O pipeline Python envia notificações (upload publicado, falha crítica, resumo diário) via endpoint interno do Laravel (`POST /internal/pipeline-event`), que por sua vez entrega a mensagem no Telegram — `telegram_notifier.py` não chama a API do Telegram diretamente
**Plans**: 4 plans

Plans:
- [ ] 09-01-PLAN.md — SDK install + CSRF config + Wave 0 RED tests (3 PHP + 2 Python)
- [ ] 09-02-PLAN.md — TelegramWebhookController + 6 Command classes + /internal/pipeline-event
- [ ] 09-03-PLAN.md — Python migration (telegram_notifier + ttl_worker + internal_api) + Artisan Schedule
- [ ] 09-04-PLAN.md — Checkpoint humano: setWebhook + verificação bot + desativação n8n

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infraestrutura Base | 4/4 | Complete | 2026-06-18 |
| 2. Aquisição de Vídeos | 4/4 | Complete | 2026-06-18 |
| 3. IA — Transcrição e Seleção | 4/4 | Complete | 2026-06-18 |
| 4. Processamento de Vídeo | 4/4 | Complete | 2026-06-18 |
| 5. Publicação e Automação Total | 6/6 | Complete | 2026-06-18 |
| 6. Controle Manual N8N + Telegram | 7/7 | Complete | 2026-06-21 |
| 7. Schema Multi-Canal + Python Pipeline | 7/7 | Complete   | 2026-06-22 |
| 8. Painel Laravel/Filament | 9/9 | Complete | 2026-07-02 |
| 9. Bot Telegram no Laravel | 0/? | Not started | - |
