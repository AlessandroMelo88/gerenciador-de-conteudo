# Banco de dados

> Tipo: referência as-built · Atualizado: 2026-09-29
> Cron nativo local do Hacker Libertário: PostgreSQL 18.3 (Homebrew), `clips_automation`.
> Produção: PostgreSQL 17. Compose local: imagem declarada 17; container observado em 16.15.

Os ambientes são separados. Nesta máquina, o cron usa o worker Python nativo e conecta a
`127.0.0.1:5432`; ele não usa o serviço PostgreSQL do Compose. A extensão `vector` não estava
disponível na instância nativa verificada em 29/09/2026. A decisão e o trabalho pendente estão em
[ADR-0007](../ADR/0007-postgresql-18-nativo-pgvector.md). O painel e os workers do Compose usam o
serviço definido em `docker-compose.yml`; produção permanece na VM A1.

## Migrations

| Arquivo | Responsabilidade |
|---|---|
| `0001_*` | `users`, sessões, cache, jobs e falhas Laravel |
| `2026_07_14_010214_*` | `niches` e seeds iniciais |
| `2026_07_30_000000_*` | `transcription_jobs` |
| `2026_08_26_000000_*` | `source_channels` |
| `2026_08_26_000001_*` | `source_videos` |
| `2026_08_26_000002_*` | `destination_channels` |
| `2026_08_26_000003_*` | `generated_clips` |
| `2026_08_26_000004_*` | trigger PostgreSQL para `updated_at` |
| `2026_08_26_000005_*` | canais iniciais, sem sobrescrever seeds do operador |
| `2026_08_26_000006_*` | `media_assets` |
| `2026_08_27_000000_*` | `prompt_profiles`, FKs de perfil nos canais e seed editorial |

As migrations de adoção saem sem recriar tabela já existente. Em banco descartável,
`migrate:fresh` remove e recria tudo; nunca use em instalação com dados.

~~~bash
docker compose run --rm panel-init
docker compose exec php php artisan migrate:status
~~~

## Tabelas de domínio

| Tabela | Chave/relacionamento | Campos operacionais |
|---|---|---|
| `source_channels` | `youtube_channel_id` único | nome, RSS, nicho, handle, ativo, blacklist |
| `source_videos` | `youtube_video_id` único; pertence a source channel | título, publicação, status, formato manual legado, `generate_both_formats`, caminho raw, texto/dados da transcrição, prioridade, pausa, posição, frescor por canal-fonte |
| `destination_channels` | `slug` e ID YouTube únicos | nome, nicho, crédito, ativo, flag OAuth |
| `generated_clips` | pertence a source video; destino opcional | formato de saída (`curto`/`longo`), intervalo, score, motivo, metadata, paths, YouTube ID, quota/status |
| `media_assets` | destino nullable para legado; `nullOnDelete` | intro/outro/music, formato, duração, volume, prioridade, ativo; novos envios exigem canal |
| `niches` | `slug` único | label dos selects do painel |
| `prompt_profiles` | `slug` único; referenciado pelos canais | nicho canônico, aliases, cinco prompts editoriais e ativo |
| `transcription_jobs` | independente da fila de clips | URL, status, progresso, SRT, erro |

Não há FK entre `niches` e as colunas textuais
`source_channels.target_niche`/`destination_channels.niche`. A aplicação usa
essas strings para roteamento.

`source_channels.prompt_profile_id` e `destination_channels.prompt_profile_id` são FKs
opcionais para `prompt_profiles` com `nullOnDelete`. Em canais novos, o painel exige um perfil
ativo compatível com o nicho; a migration associa automaticamente os canais legados de futebol,
tecnologia/conteúdo de inteligência e podcast. O Python mantém fallback seguro somente para linhas
legadas sem perfil.

`prompt_profiles` contém `selection_short_prompt`, `selection_long_prompt`,
`metadata_short_prompt`, `metadata_long_prompt` e `thumbnail_prompt`. A seed é idempotente por
`slug`; adicionar um novo canal de nicho exige adicionar seu perfil e aliases antes de associá-lo.

## Estados persistidos

`source_videos.status`:

~~~text
pending, downloading, downloaded, transcribing, selecting,
cutting, publishing, published, failed
~~~

`generated_clips.status`:

~~~text
pending_cut, pending, cutting, publishing,
published, failed, approved, rejected
~~~

`transcription_jobs.status`:

~~~text
pending, downloading, transcribing, done, failed
~~~

Detalhes e escritores de cada transição estão em
[`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md).

## Índices e timestamps

Índices principais:

- `source_channels.blacklisted`;
- `source_videos(status, format)` e `source_videos(published_at)`;
- `generated_clips(source_video_id, status)`;
- `generated_clips(destination_channel_id, status)`;
- `media_assets(kind, active)` e índice de escopo por destino/formato.

Triggers atualizam `updated_at` em `source_videos`,
`destination_channels` e `generated_clips`, inclusive em updates feitos pelo
Python. `source_channels` mantém apenas `created_at`.

## Donos das escritas

| Dono | Escreve |
|---|---|
| Laravel | migrations, usuários, configuração de canais/nichos/assets, aprovação/rejeição e jobs locais |
| clip-processor | ingestão, status da fonte, clips, metadata, publicação, OAuth flag e recovery |
| Redis Python | dedup, quota e idempotência de alertas |
| Redis Laravel | cache e leitura da quota; não substitui as tabelas da fila |

O Laravel usa `QUEUE_CONNECTION=database` por padrão; isso grava jobs em
`jobs`. O pipeline Python não usa essa fila para seus estados.

## Integridade e limpeza

As FKs de source videos e generated clips não têm cascade de exclusão. Para apagar fonte com clips,
trate os filhos explicitamente. A limpeza operacional de arquivos locais preserva as linhas de
`source_videos` e `generated_clips`, suas transcrições e metadados pesquisáveis; apagar um arquivo não
é excluir o histórico do banco.

Ao cruzar banco e disco, use o ID do registro e o estado do clip. Arquivos `.srt` e
intermediários podem não aparecer em colunas próprias.

## Migração legada

`scripts/migrations/migrate-mysql-to-postgres.py` é utilitário excepcional e não participa
do Compose. Use somente com backup validado, dependências isoladas e
`CONFIRM_MIGRATION=I_UNDERSTAND`. A origem não é apagada.

## Backup e restauração

O perfil `backup` gera dump comprimido e checksum:

~~~bash
./scripts/backup-postgres.sh
(cd backups/postgres && sha256sum -c SEU_BACKUP.sql.gz.sha256)
~~~

Para restaurar, pare consumidores, confirme o arquivo e use a confirmação explícita:

~~~bash
docker compose stop clip-processor queue scheduler
CONFIRM_RESTORE=I_UNDERSTAND ./scripts/restore-postgres.sh ./backups/postgres/SEU_BACKUP.sql.gz
docker compose start queue scheduler clip-processor
~~~

Confirme o checksum e nunca remova `postgres_data` ou use
`docker compose down -v` em uma instalação com dados. O runbook reúne a sequência
operacional completa.
