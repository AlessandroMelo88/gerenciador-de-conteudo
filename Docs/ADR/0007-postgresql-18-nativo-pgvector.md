# ADR-0007 — PostgreSQL 18 nativo para o cron do Hacker Libertário

**Status:** aceito · **Data:** 29/09/2026

## Contexto

O cron do Hacker Libertário executa `scripts/run_native_worker.py` pela `.venv` local e carrega as
variáveis do `.env` do repositório. O runner direciona o host padrão do PostgreSQL para `127.0.0.1`.
Em consulta somente leitura feita em 29/09/2026, essa conexão chegou à base `clips_automation` no
PostgreSQL 18.3 (Homebrew). A extensão `vector` não estava disponível nem habilitada nessa instância.

Esse runtime é distinto dos outros ambientes:

- Produção na VM A1 está documentada com PostgreSQL 17.
- O Compose deste repositório declara `postgres:17-alpine`, mas o container observado em execução
  usa `postgres:16-alpine` e contém um volume próprio. O cron nativo não se conecta a esse serviço.

## Decisão

Manter PostgreSQL 18 nativo como banco do cron local e instalar nele uma versão compatível do
pgvector. Não regredir o cron para PostgreSQL 17 e não iniciar um banco vetorial separado nesta
etapa. PostgreSQL permanece como fonte canônica de vídeos, metadados, transcrições e trechos; os
vetores são um índice derivado e regenerável.

A instalação do pgvector e a criação do índice ainda estão pendentes. Não declarar a busca vetorial
ativa antes de confirmar a extensão na base `clips_automation` e validar uma consulta real.

## Consequências

- A indexação de transcrições deve rodar localmente, em lotes idempotentes, pelo worker/cron nativo.
  Reprocessar somente trechos novos ou cujo texto ou versão do modelo mudou.
- A busca pode usar pgvector junto com a busca textual do PostgreSQL; não exige uma chamada remota de
  LLM por consulta.
- Qdrant pode ser avaliado mais tarde se medições do corpus real demonstrarem necessidade operacional.
- Produção PostgreSQL 17 e Compose continuam ambientes separados. Antes de atualizar o volume do
  Compose para outra versão principal, criar e validar backup e seguir `pg_upgrade` ou dump/restore;
  trocar a tag da imagem sobre um volume existente não é migração.

## Alternativas consideradas

- Regredir o cron nativo para PostgreSQL 17: rejeitada, pois o runtime já está em PostgreSQL 18.3 e
  pgvector oferece suporte à versão 18.
- Ativar PostgreSQL com pgvector e Qdrant ao mesmo tempo: adiada até haver uma medição que justifique
  manter e sincronizar dois índices.

Referências: [worker nativo](../../scripts/run_native_worker.py),
[execução via cron](../sistema/EXECUCAO-NATIVA-CRON.md) e
[pgvector — versões e instalação](https://github.com/pgvector/pgvector).
