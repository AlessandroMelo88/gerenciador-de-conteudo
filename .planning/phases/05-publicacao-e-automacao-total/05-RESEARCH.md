# Phase 5 Research: Publicacao e Automacao Total

## Objetivo

Fechar o ciclo do Canal de Cortes: clips com `generated_clips.status = 'pending'` devem ser publicados no YouTube, respeitando quota diaria, janela de horario em America/Sao_Paulo, cleanup de videos brutos e orquestracao n8n com retry.

## Contexto Atual

- Phase 4 entrega clips prontos em `/app/videos/clips` e thumbnails em `/app/videos/thumbnails`.
- `generated_clips` ja possui `clip_path`, `thumbnail_path`, `title`, `description`, `tags`, `youtube_video_id` e `status`.
- Fluxo atual de clip: `pending_cut -> cutting -> pending`.
- `source_videos.status` ja inclui `publishing` e `published`.
- OAuth ja foi feito por `youtube/generate_token.py`; em Docker, `youtube/token.json` e montado como `/app/token.json`.
- MySQL 8.4 do projeto nao aceita `ADD COLUMN IF NOT EXISTS`; migrations devem usar `INFORMATION_SCHEMA` + prepared statements.

## YouTube Upload

Implementar `clip-processor/src/uploader.py` usando `google-api-python-client`:

- Carregar credenciais de `/app/token.json` por `google.oauth2.credentials.Credentials.from_authorized_user_file`.
- Renovar token expirado com `google.auth.transport.requests.Request` quando houver `refresh_token`.
- Construir service via `googleapiclient.discovery.build('youtube', 'v3', credentials=creds)`.
- Upload com `videos().insert(part='snippet,status', body=..., media_body=MediaFileUpload(..., resumable=True))`.
- Thumbnail via `thumbnails().set(videoId=..., media_body=MediaFileUpload(...))`.
- Testes devem mockar o service inteiro; nenhum teste chama API real.

Politica de privacidade:

- `YOUTUBE_PRIVACY_STATUS` configuravel.
- Default inicial recomendado: `private`, para checkpoint seguro.
- Producao pode mudar para `public` depois do primeiro upload validado.

## Quota e Horario

YouTube Data API cobra aproximadamente 1600 unidades por `videos.insert`; a quota diaria padrao costuma ser 10.000 unidades. O requisito de produto limita em no maximo 6 uploads/dia.

Implementar `quota_manager.py` com Redis:

- Chave diaria por fuso: `youtube_uploads:{YYYY-MM-DD}` usando America/Sao_Paulo.
- `MAX_UPLOADS_PER_DAY` configuravel, mas limitado a `<= 6`.
- Default operacional do projeto: 2 uploads/dia, respeitando decisao anterior de comecar com 1-2 uploads/dia para reduzir risco de spam.
- `can_upload()` retorna false quando fora da janela 19:00-22:00 ou quota atingida.
- `record_upload()` incrementa contador com TTL ate a proxima meia-noite em Sao_Paulo.
- Se quota ou horario bloquear, clips permanecem `pending`.

## Publicador

Implementar `publisher.py`:

- Buscar clips `pending` com `clip_path`, `thumbnail_path`, `title`, `description`, `tags`.
- Validar existencia de arquivo antes de tentar upload.
- Transicionar `generated_clips.status` para `publishing` antes do upload.
- Em sucesso: salvar `youtube_video_id`, `published_at`, status `published`, registrar quota e atualizar `source_videos`.
- Em falha de API/arquivo: status `failed`, `upload_error` preenchido.
- Em bloqueio de horario/quota: nao mudar status definitivo.

Cleanup:

- Nao apagar o video bruto apos o primeiro clip se ainda houver outros clips do mesmo `source_video_id` em `pending_cut`, `cutting`, `pending` ou `publishing`.
- Apagar `source_videos.local_path` somente quando todos os clips daquele video estiverem em estados terminais (`published` ou `failed`) e pelo menos um clip tiver sido publicado.
- Manter `clip_path` e `thumbnail_path`, pois sao artefatos publicados/auditaveis.

## Orquestracao n8n

O daemon atual ja executa o ciclo via APScheduler. Para satisfazer ORC-01 sem adicionar uma API web nova, a Phase 5 deve extrair o ciclo para `pipeline_runner.run_pipeline_once()` e expor um comando CLI idempotente. O n8n pode executar esse comando com retry/backoff no ambiente Docker.

Artefatos esperados:

- `clip-processor/src/pipeline_runner.py` com `run_pipeline_once(db_conn=None, redis_client=None)`.
- `main.py` usa `run_pipeline_once()` no boot e no scheduler.
- Workflow JSON importavel em `n8n/workflows/canaldecortes-pipeline.json`.
- README do workflow descreve credenciais, retry e como validar o import.

## Validation Architecture

Testes unitarios devem cobrir:

- Quota diaria, TTL ate meia-noite e janela 19h-22h com clock injetado.
- Uploader com service mockado, incluindo metadata, tags, privacyStatus e thumbnail.
- Publisher com banco fake/mocks: status transitions, quota bloqueada, falha de upload, cleanup seguro.
- Runner integra a ordem RSS -> IA/video existente -> publisher sem duplicar conexoes.

Checkpoint manual:

- Rodar suite pytest.
- Aplicar migration Phase 5.
- Importar workflow n8n.
- Fazer upload de um clip fixture com `YOUTUBE_PRIVACY_STATUS=private`.
- Confirmar video no YouTube Studio, thumbnail aplicada, status `published` no banco e raw source removido apenas quando seguro.
