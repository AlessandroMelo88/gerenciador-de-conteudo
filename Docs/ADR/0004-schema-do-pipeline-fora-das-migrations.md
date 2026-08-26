# ADR-0004 — Schema do pipeline em SQL bruto, fora das migrations do Laravel

**Status:** aceito · **Data:** 2026 (registrado como ADR em 25/08/2026)

## Contexto

O dono das tabelas do pipeline (`source_channels`, `source_videos`, `generated_clips`,
`destination_channels`, `transcription_jobs`...) é o daemon Python, que existiu antes do painel.
O painel Laravel apenas mapeia essas tabelas com Eloquent e `$table` explícito; suas migrations
criam só `users`, `sessions`, `cache`, `jobs` (e `niches`).

## Decisão

O schema do pipeline vive em `mysql/init/01..07*.sql`, aplicado pelo entrypoint do MySQL na criação
do volume (`docker-compose.yml`) ou manualmente via `docker exec`. Migrations do Laravel **não**
criam nem alteram essas tabelas. Alterações de schema entram como novo arquivo numerado em
`mysql/init/`, idempotente quando possível (`INSERT IGNORE`, `IF NOT EXISTS`, `PREPARE` guardado).

## Consequências

- `php artisan migrate:fresh` não reconstrói o pipeline; o CI aplica `mysql/init/*.sql` antes de `migrate`.
- As FKs de `generated_clips` **não** têm `ON DELETE CASCADE`: apagar `source_videos` com clips falha
  por FK — clips primeiro, vídeos depois (`CLAUDE.md`, regra 5).
- Enums de status são donos do Python; o painel deve espelhá-los (auditoria PHP, item A5 do TODO).
- A migração de motor de banco (ADR-0006) precisa reescrever esses arquivos, não as migrations.
