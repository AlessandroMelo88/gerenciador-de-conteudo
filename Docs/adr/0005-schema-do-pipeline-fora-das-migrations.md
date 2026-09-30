# ADR-0005 — Schema do pipeline em SQL bruto, fora das migrations do Laravel

**Status:** Substituída pela prática atual · **Data:** 2026 (registrada como ADR em 25/08/2026, revisada em 30/09/2026)

## Contexto

O dono original das tabelas do pipeline (`source_channels`, `source_videos`, `generated_clips`,
`destination_channels`, `transcription_jobs`...) foi o daemon Python, que existiu antes do painel,
com o schema em SQL de bootstrap do MySQL (`mysql/init/*.sql`). O painel Laravel apenas mapeava as
tabelas com Eloquent.

## Decisão (histórica)

O schema do pipeline vivia em SQL aplicado na criação do volume do MySQL, e as migrations do Laravel
não criavam nem alteravam essas tabelas.

## Situação atual

Com a migração para PostgreSQL (17/09/2026) o bootstrap em SQL do MySQL deixou de ser usado. Hoje
`2026_07_13_000000_create_clips_core_tables.php` cria `destination_channels`, `source_channels`,
`source_videos` e `generated_clips` (guardado por `Schema::hasTable`), e as demais migrations em
`painel/database/migrations/` evoluem o schema. O detalhe está em
[`../sistema/BANCO-DE-DADOS.md`](../sistema/BANCO-DE-DADOS.md).

## Consequências que continuam valendo

- As FKs de `generated_clips` **não** têm `ON DELETE CASCADE`: apagar `source_videos` com clips falha
  por FK — clips primeiro, vídeos depois (`CLAUDE.md`, regra 5).
- Os enums de status são donos do Python; o painel deve espelhá-los.
- Alterar schema exige migration guardada (`hasTable`/`hasColumn`) para ser segura em produção, onde
  as tabelas já existem.
