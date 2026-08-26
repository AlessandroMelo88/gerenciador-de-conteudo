# ADR-0006 — Motor de banco do pipeline

**Status:** aceito · **Data:** 26/08/2026

## Contexto

O pipeline compartilhava o MySQL legado com o painel e dependia de SQL de bootstrap separado das
migrations. Isso duplicava a definição do schema, dificultava `migrate:fresh`/CI e mantinha o daemon,
o painel e os scripts operacionais com contratos diferentes.

## Decisão

O runtime usa **PostgreSQL 16** como banco único do painel Laravel e do `clip-processor`:

- Laravel usa `pgsql`/`pdo_pgsql`; Python usa `psycopg2`.
- O serviço `panel-init` executa as migrations antes de iniciar PHP, fila e scheduler.
- Backups e restaurações usam `pg_dump`/`psql`, com checksum SHA-256 e confirmação explícita para
  restaurações.
- O utilitário [`scripts/migrations/migrate-mysql-to-postgres.py`](../../scripts/migrations/migrate-mysql-to-postgres.py)
  é uma ponte única para dados existentes: exige confirmação, preserva IDs, recalibra sequences e
  não apaga a origem.
- FKs continuam sem `ON DELETE CASCADE`; remoções operacionais devem validar dependências e cruzar
  banco com disco antes de apagar arquivos.

## Consequências

- O Compose é autocontido e não publica PostgreSQL nem Redis no host.
- O schema do pipeline e o schema do painel podem ser recriados juntos em banco descartável.
- A migração exige janela operacional, backup validado e conferência de contagens antes do cutover.
- As imagens do painel precisam ser reconstruídas quando migrations ou código Laravel mudarem; o
  worker também precisa de rebuild quando `clip-processor/src` mudar.

## Rollback

Em caso de falha, interromper os consumidores, restaurar o último backup PostgreSQL validado com
`scripts/restore-postgres.sh` e manter a origem MySQL intacta até a validação pós-cutover. Não usar
`docker compose down -v` como mecanismo de rollback.

## Relação com outras decisões

Este ADR substitui a decisão de motor implícita em ADR-0001 e a estratégia de schema registrada em
ADR-0004. A regra específica de ownership por migrations está detalhada no ADR-0007.
