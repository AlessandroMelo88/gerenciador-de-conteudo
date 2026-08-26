# ADR-0006 — Motor de banco do pipeline

**Status:** em andamento (não decidido neste documento) · **Data:** 25/08/2026

## Contexto

O pipeline nasceu em MySQL 8.4 (`mysql/init/*.sql`, `pymysql` no daemon, `pdo_mysql` no painel).
O `README.md` de 25/08/2026 afirma explicitamente "MySQL 8.4, não PostgreSQL" e proíbe SQLite pelas
escritas concorrentes de painel, fila e worker.

No mesmo dia, uma frente de trabalho paralela começou a migrar o daemon e o painel para
**PostgreSQL** (`psycopg2`, `RETURNING id`, `COUNT(*) FILTER`, booleanos `TRUE/FALSE`,
`postgres/init/`, `scripts/*-postgres.sh`, `config/database.php` com default `pgsql`). Esse trabalho
ainda não estava commitado quando este ADR foi escrito.

## O que precisa constar aqui quando a decisão fechar

- Motivação concreta (o que o MySQL não atendia).
- Plano de migração de dados (`scripts/migrate-mysql-to-postgres.py`) e de rollback.
- Impacto nas regras operacionais de `CLAUDE.md` (backups, FKs sem cascade, `DELETE` em massa) e
  no `RUNBOOK.md` (backup/restore passam a ser `pg_dump`/`psql`).
- Atualização de ADR-0004 (os `mysql/init` deixam de ser a fonte do schema) e do CI (`php-tests`
  usa serviço MySQL e aplica `mysql/init/*.sql`).
- Confirmação de que a suíte Python passa com o novo driver (em 25/08/2026 ela falhava na coleta no
  host por `psycopg2` ausente no venv).

Até lá, `README.md`, `ARCHITECTURE.md` e `BANCO-DE-DADOS.md` descrevem o MySQL, que é o que roda.
