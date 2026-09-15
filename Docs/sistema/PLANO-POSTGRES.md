# Plano PostgreSQL — fase A (local) e fase B (produção)

Documento de progresso. **Se a sessão reiniciar, comece por aqui**: cada etapa vira um commit na branch
`feature/postgres-fase-a`, e o checklist abaixo é a fonte da verdade do que já foi feito.

Contexto e justificativa: [`PLANO-MESTRE.md`](PLANO-MESTRE.md#3-banco-de-dados--mysql-para-postgresql).
Fluxo de branch e deploy: [`../../DEPLOY.md`](../../DEPLOY.md).

Última atualização: **15/09/2026**.

---

## Decisões

| Decisão | Motivo |
|---|---|
| Branch `feature/postgres-fase-a`, merge na `master` só no fim | Se a VM de 12 GB não sair, a `master` continua rodando MySQL sem nada pela metade |
| Fase A (local) agora; fase B (produção) junto da VM A1 | O grosso do trabalho é a auditoria do SQL, que não depende de produção. Na instância nova o Postgres nasce vazio e os dados entram uma vez só |
| Banco local no container `postgres` já existente | Ele é compartilhado com kelnab e outros projetos — **usar banco e usuário próprios**, nunca mexer nos outros |
| MySQL continua intacto | Rollback é voltar as variáveis de ambiente |

**Regra de isolamento:** o container `postgres` da raiz `wordpress/` é compartilhado. Criar/alterar
apenas o banco `clips_automation` e o usuário `clips_user`.

---

## Situação apurada (15/09/2026)

| Item | Número |
|---|---|
| Banco de produção | 2,8 MB, ~3.000 linhas |
| Queries SQL no `clip-processor` | 85, em 17 módulos |
| Comparações booleanas `= 0` / `= 1` (quebram no Postgres) | 10 |
| `DATE_SUB(...)` sem desvio de driver | 2, em `watchdog.py` |
| Migrations do painel com SQL cru | 0 |
| Queries cruas no Laravel | 2 `selectRaw('status, count(*)')`, portáveis |

`db.py` já detecta o driver (`get_db_driver`), tem wrapper de cursor e trata `INSERT IGNORE` versus
`ON CONFLICT`. **Os testes do `clip-processor` usam mock de banco — eles não provam a migração.**
A validação real é um ciclo completo rodando contra o Postgres (etapa A6).

---

## Fase A — local

- [ ] **A1.** Banco e usuário próprios no Postgres local (`clips_automation` / `clips_user`)
- [ ] **A2.** `php artisan migrate` num Postgres vazio e comparação do schema com o MySQL (tabelas, colunas, tipos, índices, FKs)
- [ ] **A3.** Painel local sai do SQLite e passa para Postgres (`painel/.env`); `phpunit.xml` aponta para o Postgres local
- [ ] **A4.** Suíte do painel verde contra Postgres (`php artisan test`)
- [ ] **A5.** Auditoria das 85 queries do `clip-processor` e correção dos pontos não portáveis:
  - [ ] booleanos: helper único em vez de `= 0` / `= 1` espalhado (10 ocorrências)
  - [ ] `DATE_SUB` no `watchdog.py` (2)
  - [ ] conferir crases (`` `local_path` ``) — na inspeção parecem estar só em comentários
  - [ ] `scripts/local_download_worker.py`: `docker exec mysql mysql` vira `psql`, e `NOW() - INTERVAL 2 DAY` vira sintaxe ANSI
- [ ] **A6.** Ciclo real do `clip-processor` contra o Postgres local: poll → download → transcrição → seleção → corte
- [ ] **A7.** Testes do `clip-processor` e do worker verdes; teste novo que trave regressão de SQL não portável
- [ ] **A8.** Documentação: `BANCO-DE-DADOS.md`, `SISTEMA-CLIP-PROCESSOR.md` e `RUNBOOK.md` (8 comandos `mysql` viram `psql`)
- [ ] **A9.** Merge na `master` pela skill `finalizar-e-deploy` — **sem deploy de produção nesta fase**

## Fase B — produção (fazer junto da VM A1 de 12 GB)

- [ ] **B1.** Serviço `postgres` no compose de produção, ao lado do MySQL
- [ ] **B2.** Backup `mysqldump` e migrations no Postgres vazio
- [ ] **B3.** Carga dos dados (`pgloader`), conferência linha a linha por tabela
- [ ] **B4.** **Corrigir as sequences** (`setval`) — esquecer isso faz o primeiro insert colidir com id existente
- [ ] **B5.** Parar o pipeline, carga do delta, trocar variáveis, subir e validar um ciclo
- [ ] **B6.** MySQL parado com os dados intactos por alguns dias (rollback = voltar as variáveis)

---

## Como retomar depois de reiniciar a sessão

```bash
cd /Users/alessandrobm1/develop/server/wordpress/canaldecortes
git switch feature/postgres-fase-a
git log --oneline master..HEAD      # o que já foi feito
sed -n '/## Fase A/,/## Fase B/p' Docs/sistema/PLANO-POSTGRES.md   # checklist
```

Conexão local: `postgres://clips_user@127.0.0.1:5432/clips_automation` (senha em `painel/.env`, fora do git).
