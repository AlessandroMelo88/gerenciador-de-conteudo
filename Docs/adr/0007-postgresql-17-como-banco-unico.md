# ADR-0007 — PostgreSQL 17 como banco único do painel e do clip-processor

**Status:** Aceita · **Data:** 17/09/2026 (migração), registrada como ADR em 30/09/2026

> Adaptada do "ADR-0006 — Motor de banco" do Ricardo, que dizia **PostgreSQL 16** e um compose
> isolado. A produção real é PostgreSQL 17. A busca vetorial que depende do pgvector tem o seu
> próprio registro: [ADR-0001](0001-busca-vetorial-nas-transcricoes.md).

## Contexto

O pipeline compartilhava o MySQL legado com o painel e dependia de SQL de bootstrap separado das
migrations (ADR-0005). Isso duplicava a definição do schema, dificultava testes em banco descartável
e mantinha daemon, painel e scripts com contratos diferentes.

## Decisão

O runtime usa **PostgreSQL 17** como banco único do painel Laravel (`pgsql`/`pdo_pgsql`) e do
`clip-processor` (`psycopg2`). A imagem é `canaldecortes-postgres:pg17-vector` (`docker/postgres/Dockerfile`:
`postgres:17-alpine` + pgvector). Produção: VM A1, dados do banco em volume próprio, vídeos em
`/mnt/videos`. A migração de dados foi feita com `scripts/migrar_mysql_para_postgres.py`
(`Docs/sistema/MIGRACAO-A1.md`).

## Consequências

- Backup diário na A1 em `/mnt/videos/backups` (14 dias) e cópia puxada para o Mac. Restauração com
  [`scripts/restore-postgres.sh`](../../scripts/restore-postgres.sh): exige `CONFIRM_RESTORE=I_UNDERSTAND`,
  confere o `.sha256` quando existe e aceita `.sql.gz` ou `.dump` (`pg_dump -Fc`).
- FKs continuam sem `ON DELETE CASCADE`; remoções operacionais validam dependências e cruzam banco
  com disco antes de apagar arquivos (`CLAUDE.md`, regras 3 e 5).
- Trocar a tag da imagem sobre um volume existente **não** é migração de versão maior: exige backup
  validado e `pg_upgrade` ou dump/restore.
- Rollback: restaurar o último backup validado; nunca `docker compose down -v`.
- Testes PHP rodam contra Postgres descartável (CI: `pgvector/pgvector:pg17`; local:
  `scripts/dev-pgvector.sh`), nunca contra produção.
