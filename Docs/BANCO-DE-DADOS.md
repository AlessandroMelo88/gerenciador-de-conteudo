# Banco de dados — `clips_automation`

O projeto usa um único banco **PostgreSQL 16** para o painel Laravel e o pipeline Python. A fonte
de verdade do schema é `painel/database/migrations`; não há SQL de bootstrap duplicando as migrations.
O serviço `panel-init` executa `php artisan migrate` antes de liberar PHP, fila e scheduler.

Estados e transições ficam em [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md).

## Ciclo de vida do schema

As tabelas do pipeline são migrations Laravel, assim como as tabelas do painel:

| Migration | Responsabilidade |
|---|---|
| `2026_08_26_000000_create_source_channels_table` | canais monitorados via RSS |
| `2026_08_26_000001_create_source_videos_table` | vídeos descobertos e fila de download |
| `2026_08_26_000002_create_destination_channels_table` | canais próprios de publicação |
| `2026_08_26_000003_create_generated_clips_table` | cortes gerados e seus estados |
| `2026_08_26_000004_add_pipeline_updated_at_triggers` | `updated_at` automático para escritas do Python |
| `2026_08_26_000005_seed_pipeline_channels` | canais iniciais, sem sobrescrever configuração do operador |
| `2026_08_26_000006_create_media_assets_table` | biblioteca de intros, encerramentos e músicas por escopo |

As migrations `niches` e `transcription_jobs` seguem no mesmo diretório e pertencem ao domínio do
painel. A migration de adoção verifica a existência das quatro tabelas do pipeline para não destruir
nem recriar um volume PostgreSQL que já tenha sido inicializado pela versão anterior.

Comandos:

```bash
docker compose run --rm panel-init
docker compose exec php php artisan migrate:status
```

`php artisan migrate:fresh` reconstrói todo o schema, inclusive o pipeline. Só deve ser usado em um
banco descartável, nunca em uma instalação com dados.

## Tabelas

### `source_channels`

Representa canais monitorados pelo RSS. `youtube_channel_id` é único; `active` controla o monitoramento;
`blacklisted` impede ingestão; `target_niche` roteia o vídeo para um canal-destino; e `channel_handle`
é usado na atribuição da descrição.

### `source_videos`

É a fila persistida do pipeline. A chave natural é `youtube_video_id`; `channel_id` referencia
`source_channels`; `format` é `curto` ou `longo`; `status` acompanha a máquina de estados; `local_path`
indica o arquivo bruto; `priority`, `paused` e `queue_position` controlam a fila; e `published_at`
serve para o filtro de frescor e para a ordenação.

Ordenação canônica da fila:
`priority DESC, queue_position IS NULL, queue_position ASC, published_at DESC`.

### `destination_channels`

Representa os canais próprios onde os cortes são publicados. O `slug` vincula o registro ao token OAuth
`youtube/token-<slug>.json` e à marca d'água. `active` habilita o destino e `oauth_expired_flag` é
atualizado pelo uploader quando o refresh do token falha.

### `generated_clips`

Representa os cortes derivados de `source_videos`. Guarda metadados, intervalos de corte, arquivos,
destino, estado de publicação e eventual erro de upload. As FKs não usam `ON DELETE CASCADE`: antes de
remover um vídeo, remova ou trate seus clips explicitamente. Os campos `start_time` e `end_time` também
formam o histórico anti-repetição: a seleção consulta todos os intervalos válidos do mesmo vídeo fonte,
e a inserção bloqueia candidatos com mais de 0,5 s de sobreposição.

### `media_assets`

Biblioteca de pós-produção compartilhada pelo painel e pelo `clip-processor`. `kind` aceita `intro`,
`outro` ou `music`; `destination_channel_id` e `format` podem ficar nulos para criar um fallback
global. `priority` resolve empates dentro do mesmo escopo, `active` permite pausar sem perder o arquivo,
`duration_seconds` controla imagens de abertura/fechamento e `music_volume` controla a trilha.

`path` é relativo ao disk Laravel `branding`, montado como `/app/branding` no worker. Esses registros
continuam como fallback legado: a biblioteca canônica por diretório fica em `assets/channels` e
`assets/audio`. A FK do canal usa `ON DELETE SET NULL` para que apagar um canal transforme seus assets
em configurações globais, nunca em arquivos órfãos.

Índices relevantes:

- `source_videos(status, format)` e `source_videos(published_at)` para reposição da janela;
- `generated_clips(source_video_id, status)` para recuperação e finalização;
- `generated_clips(destination_channel_id, status)` para a fila de publicação;
- `source_channels(blacklisted)` para o polling.

## Donos das operações

| Serviço | Conexão | Responsabilidade |
|---|---|---|
| Laravel | `pgsql` via Eloquent/Query Builder | painel, migrations e transições operacionais |
| clip-processor | `psycopg2` | ingestão, processamento, recuperação e publicação |
| Redis | database configurado | deduplicação, cota e idempotência de avisos; não é a fila |

O `updated_at` de `source_videos`, `destination_channels` e `generated_clips` é atualizado por trigger
PostgreSQL, inclusive quando a alteração vem do Python.

## Migração do banco legado

O utilitário excepcional MySQL → PostgreSQL está em
[`scripts/migrations/migrate-mysql-to-postgres.py`](../scripts/migrations/migrate-mysql-to-postgres.py).
Ele não participa do Compose nem do startup normal. Instale as dependências isoladas de
`scripts/migrations/requirements.txt`, faça backup validado da origem e confirme explicitamente a
operação com `CONFIRM_MIGRATION=I_UNDERSTAND`. O script preserva IDs, faz upsert e recalibra sequences;
a origem não é apagada.

## Backup e restauração

O serviço opcional `postgres-backup` usa `pg_dump`, gzip e SHA-256:

```bash
./scripts/backup-postgres.sh
CONFIRM_RESTORE=I_UNDERSTAND ./scripts/restore-postgres.sh \
  ./backups/postgres/clips_automation_DATA.sql.gz
```

Pare `clip-processor`, `queue` e `scheduler` antes de restaurar. Verifique o checksum quando existir
e nunca execute `docker compose down -v` em uma instalação com dados.
