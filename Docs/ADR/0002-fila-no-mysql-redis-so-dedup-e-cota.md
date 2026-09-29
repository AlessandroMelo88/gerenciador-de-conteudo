# ADR-0002 — A fila mora no banco; Redis guarda só dedup, cota e idempotência

**Status:** aceito · **Data:** 27/07/2026 (registrado como ADR em 25/08/2026)

## Contexto

Incidente de 27/07/2026: HD 99 % cheio → MySQL caiu → pipeline travou → clip preso em `publishing`.
Durante o destravamento surgiu a ideia de "resetar a fila limpando o Redis". Apagar as chaves
`video:<id>` fez os vídeos deletados **voltarem** no poll RSS seguinte, e um `FLUSHALL` zeraria
também a cota diária (`CLAUDE.md`, seção "Reset de fila").

## Decisão

A fila é **exclusivamente** `source_videos` + `generated_clips` no banco. O Redis guarda apenas:
`video:<id>` (TTL 30 dias, "já visto"), `youtube_uploads:<data>[:<canal>|:<formato>]` (cota) e
chaves de idempotência de aviso (TTL 24 h). Nenhum estado de fila, ordem ou prioridade vai para o
Redis; nenhuma operação de "reset" toca no Redis por padrão.

## Consequências

- Purgar backlog = `DELETE` no banco **mantendo** as chaves de dedup.
- "Não sobe mais hoje" ≠ "fila travada": conferir `youtube_uploads:<hoje>` e resetar só essa chave.
- Recuperação de estado preso é responsabilidade do job `state_recovery` (banco), não de limpeza de cache.
- Redis pode ser perdido sem perda de trabalho — apenas re-ingestão de vídeos antigos dentro do
  filtro de frescor (`FRESHNESS_DAYS=1`).

## Atualização de retenção (28/09/2026)

A limpeza automática de mídia não exclui registros: remove arquivos locais seguros, arquiva a
transcrição no banco e preserva `source_videos`, `generated_clips` e as chaves de deduplicação.
A exclusão definitiva de registros continua sendo uma ação explícita do painel. O frescor agora é
configurado por canal-fonte (3 ou 1500 dias), com `FRESHNESS_DAYS=1500` como fallback legado.
