# ADR-0003 — A fila mora no banco; Redis guarda só dedup, cota e idempotência

**Status:** Aceita · **Data:** 27/07/2026 (registrada como ADR em 25/08/2026, revisada em 30/09/2026)

## Contexto

Incidente de 27/07/2026: HD 99 % cheio → o banco (então MySQL) caiu → pipeline travou → clip preso
em `publishing`. Durante o destravamento surgiu a ideia de "resetar a fila limpando o Redis". Apagar
as chaves `video:<id>` fez os vídeos deletados **voltarem** no poll RSS seguinte, e um `FLUSHALL`
zeraria também a cota diária (`CLAUDE.md`, seção "Reset de fila").

## Decisão

A fila é **exclusivamente** `source_videos` + `generated_clips` no banco (PostgreSQL 17 em produção).
O Redis guarda apenas: `video:<id>` (TTL 30 dias, "já visto"), `youtube_uploads:<data>[:<canal>|:<formato>]`
(cota) e chaves de idempotência de aviso (TTL 24 h). Nenhum estado de fila, ordem ou prioridade vai
para o Redis; nenhuma operação de "reset" toca no Redis por padrão.

## Consequências

- Purgar backlog = `DELETE` no banco **mantendo** as chaves de dedup.
- "Não sobe mais hoje" ≠ "fila travada": conferir `youtube_uploads:<hoje>` e resetar só essa chave.
- Recuperação de estado preso é responsabilidade das rotinas de recuperação do `clip-processor`
  (`run_recovery_once`), não de limpeza de cache.
- Redis pode ser perdido sem perda de trabalho — apenas re-ingestão de vídeos antigos dentro do
  filtro de frescor (`FRESHNESS_DAYS=1`).
