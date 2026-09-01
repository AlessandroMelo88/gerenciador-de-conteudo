# Arquitetura — Canal de Cortes

> Tipo: referência as-built · Atualizado: 2026-08-27

Este documento explica as fronteiras e o fluxo do sistema em execução. O índice por subsistema está
em [`Docs/README.md`](Docs/README.md). Em conflito, código, migrations, Compose e
[`.env.example`](.env.example) são a fonte de verdade, nessa ordem.

## Visão geral

O projeto é um pipeline orientado a banco. O `clip-processor` executa descoberta, download,
transcrição, seleção, corte e publicação. O `painel` fornece UI, autenticação, configuração,
aprovação e operações administrativas. PostgreSQL guarda a fila e o estado; Redis apoia deduplicação,
cotas e avisos idempotentes.

~~~text
YouTube RSS/URL + Telegram
          │
          ▼
   clip-processor ── FFmpeg / IA / YouTube API
          │
          ├── PostgreSQL: fila, estado, metadata
          ├── Redis: dedup, cota, TTL de avisos
          └── sidecar HTTP :8090
                         ▲
                         │ X-Internal-Token
                    painel ── navegador :8088
~~~

## Topologia Docker

O [`docker-compose.yml`](docker-compose.yml) é exclusivo deste projeto. PostgreSQL, Redis
e o sidecar não publicam portas no host; o painel fica em `APP_PORT`, default `8088`.

| Serviço | Papel |
|---|---|
| `clip-processor` | Scheduler Python, pipeline completo e API interna na porta 8090 |
| `panel-init` | Executa migrations antes do painel |
| `postgres` | PostgreSQL 16; database do pipeline e do painel |
| `redis` | Redis 7; dedup, quotas e avisos |
| `php` | PHP-FPM do Laravel |
| `queue` | Worker de jobs Laravel |
| `scheduler` | Scheduler Laravel; resumo diário às 18:00 |
| `nginx` | HTTP do painel |
| `postgres-backup` | Serviço opcional do perfil `backup` |

Volumes compartilhados permitem ao painel visualizar arquivos e ao processador consumi-los:
`videos/`, `assets/`, `branding/` e `youtube/`. A imagem copia o código Python,
mas o Compose atual também monta `./clip-processor/src:/app/src`; em desenvolvimento, alterar Python exige
restart do worker, não rebuild. Dockerfile, dependências ou pacotes do sistema continuam exigindo
rebuild.

## Fronteira painel ↔ processador

O painel lê PostgreSQL e arquivos compartilhados para dashboard, preview e configuração. Operações que
tocam fila Python, disco ou processos passam pelo sidecar autenticado com
`CLIP_PROCESSOR_INTERNAL_TOKEN`.

| Método | Rota |
|---|---|
| GET | `/health` (pública) |
| POST | `/internal/purge-old-videos` |
| POST | `/internal/resolve-channel` |
| POST | `/internal/reject-clip` |
| POST | `/internal/process-url` |
| POST | `/internal/delete-source-video` |
| POST | `/internal/transcribe` |
| POST | `/internal/videos/{id}/pause` |
| POST | `/internal/videos/{id}/resume` |
| POST | `/internal/videos/reorder` |
| POST | `/internal/videos/{id}/prioritize` |

Todas as rotas POST falham fechadas sem token válido. O processador envia eventos ao painel em
`LARAVEL_NOTIFY_URL`; o painel traduz `upload_published`, `pipeline_failure`,
`clip_ttl_warning` e `daily_summary` em notificações Telegram quando configurado.

## Fluxo de dados

~~~text
RSS → dedup → source_videos.pending
   → download → downloaded
   → transcribe → transcribing
   → select → selecting
   → generated_clips.pending_cut
   → FFmpeg → pending ou approved
   → quota/OAuth → publishing → published
~~~

- `rss_poller.poll_all_channels` descobre vídeos e também dispara o processamento posterior
  dos vídeos baixados.
- `pipeline_runner.run_ingest_cycle` executa ingestão/download/IA/corte.
- `pipeline_runner.run_publish_only` publica clips elegíveis.
- `publisher.publish_pending_clips` roteia por nicho, intercala canais-fonte e aplica quota.
- `publisher` finaliza a fonte quando todos os clips estão terminais e há pelo menos um
  publicado; então remove artefatos que não são mais necessários.

Estados e recovery estão detalhados em [`Docs/ESTADOS-E-TRANSICOES.md`](Docs/ESTADOS-E-TRANSICOES.md).

## Formatos

| Formato | Regra da fonte | Seleção | Render |
|---|---|---|---|
| `curto` | menos de 420 s | até 3 trechos de 30–180 s | vertical 1080×1920, legenda oficial e queimada (não queima se a fonte já vem legendada) |
| `longo` | 420 s ou mais | 1 trecho contínuo de 420–1200 s | horizontal, legenda oficial sem queimar |

O curto usa fundo desfocado/escurecido, vídeo principal e marca d’água quando disponível. O longo
exige intro, encerramento e música; os assets são resolvidos em `assets/channels/<slug>` e
`assets/audio`, com fallback registrado em `media_assets`. A thumbnail recebe uma
frase literal da transcrição.

## IA

| Etapa | Primeiro caminho | Fallback |
|---|---|---|
| Transcrição principal | legendas manuais PT-BR do YouTube | Groq Whisper `whisper-large-v3-turbo` |
| Seleção | Anthropic `claude-haiku-4-5` | Groq `openai/gpt-oss-20b` |
| Metadata | Anthropic `claude-haiku-4-5` | Groq quando a chave Anthropic não está configurada |
| Texto da thumbnail | Anthropic | Groq; sem fallback local |

O catálogo dos prompts, perfis por nicho, contratos JSON, roteamento e validações está em
[`Docs/SISTEMA-IA-SELECAO.md`](Docs/SISTEMA-IA-SELECAO.md). O texto editorial específico vem de
`prompt_profiles`; edição livre e versionamento por prompt ainda são plano futuro.

## Scheduler e recovery

| Job | Frequência | Escopo |
|---|---:|---|
| ingestão | 20 min | RSS, download, transcrição, seleção e corte |
| publicação | 20 min | clips elegíveis |
| TTL | 1 h | alerta/rejeição de pendências antigas |
| recovery | 30 min | downloads, seleções e publicações presas |
| recovery de corte | boot | `cutting` volta para `pending_cut` |

No boot, o processador recupera downloads/seleções/publicações, recupera cortes interrompidos, sobe o
sidecar e executa um ciclo inicial quando `PIPELINE_ENABLED=true`. Com `false`, o
sidecar permanece disponível, mas ingestão e publicação ficam pausadas.

## Persistência

As migrations em `painel/database/migrations` definem `source_channels`,
`source_videos`, `destination_channels`, `generated_clips`,
`media_assets`, `niches`, `transcription_jobs` e tabelas Laravel.
A fila é PostgreSQL, não Redis.

Chaves Redis principais:

- `video:<youtube_id>`: vídeo já visto; TTL padrão de 30 dias;
- `youtube_uploads:<channel>:<date>`: quota diária;
- `clip_warned:<clip_id>`: evita repetir alerta de TTL.

Arquivos temporários e finais ficam nos diretórios montados. Antes de apagar algo, confira a chave
do registro no banco e os estados `pending_cut`/`cutting`; o raw ainda é necessário
enquanto um clip precisa ser cortado.

## Limites e decisões

- PostgreSQL é o único banco operacional atual.
- Redis não é uma fila.
- Sem migrations novas, alterar apenas o código não altera o schema.
- No Compose atual, alteração em `clip-processor/src` exige restart; alteração no Dockerfile,
  dependências ou pacotes do sistema exige rebuild e restart.
- `PLANO-ORACLE.md`, `PLANO-PROMPTS-EDITAVEIS.md` e `.planning/` são
  planejamento; não descrevem o runtime.
