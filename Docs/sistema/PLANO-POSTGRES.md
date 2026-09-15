# Plano PostgreSQL — fase A (local) e fase B (produção)

Documento de progresso. **Se a sessão reiniciar, comece por aqui**: cada etapa vira um commit na branch
`feature/postgres-fase-a`, e o checklist abaixo é a fonte da verdade do que já foi feito.

Contexto e justificativa: [`PLANO-MESTRE.md`](PLANO-MESTRE.md#3-banco-de-dados--mysql-para-postgresql).
Fluxo de branch e deploy: [`../../DEPLOY.md`](../../DEPLOY.md).

Última atualização: **15/09/2026** — A1 a A4 concluídas; falta o ciclo real do pipeline (A6).

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

O container `php` local também é compartilhado (feeb, kelnab, riodelux, placebeads) e é construído pelo
`wordpress/Dockerfile`, fora deste projeto. Como ele não tem `pdo_pgsql`, a fase A usa uma **imagem
própria** construída do `canaldecortes/Dockerfile.php` — o mesmo arquivo que vai para produção. Assim
nada do ambiente dos outros projetos é alterado, e a correção já nasce pronta para a fase B.

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

- [x] **A1.** Banco e usuário próprios no Postgres local — `clips_automation` com owner `clips_user`, criado em 15/09/2026 no container `postgres` (17.2). Outros bancos do container intocados
- [x] **A2.** Migrations num Postgres vazio e comparação com a produção: **122 colunas dos dois lados, idênticas**, depois do alinhamento de `reason`/`scheduled_for`
  - [x] **A2.0 — obstáculo encontrado:** a imagem PHP não tem `pdo_pgsql` (`could not find driver`). Só `pdo_mysql` e `pdo_sqlite`
  - [x] `Dockerfile.php` (o do projeto, usado em produção) ganhou `libpq-dev` + `pdo_pgsql`/`pgsql`
  - [x] imagem local `canaldecortes-php:pg` construída a partir dele
  - [x] **as 9 migrations rodaram limpas no Postgres vazio**
  - [x] comparação de schema: produção (122 colunas) x migrations (122) — divergem em **2 colunas**
- [x] **A3.** Painel local saiu do SQLite: `painel/.env` e `phpunit.xml` apontam para o Postgres local
- [x] **A4.** Suíte do painel verde contra Postgres: **45 testes, 115 asserções**, na imagem `canaldecortes-php:pg`
- [ ] **A5.** Auditoria das 85 queries do `clip-processor` e correção dos pontos não portáveis:
  - [x] booleanos: `= 0`/`= 1` viraram `TRUE`/`FALSE`, que funciona nos dois bancos (10 ocorrências, sem ramo por driver)
  - [x] `DATE_SUB` no `watchdog.py`: corte de tempo calculado em Python e passado como parâmetro (2)
  - [ ] conferir crases (`` `local_path` ``) — na inspeção parecem estar só em comentários
  - [x] `scripts/local_download_worker.py`: `NOW() - INTERVAL 2 DAY` virou corte calculado em Python
  - [ ] `scripts/local_download_worker.py`: `docker exec mysql mysql` precisa virar `psql` (fase B)
- [ ] **A6.** Ciclo real do `clip-processor` contra o Postgres local: poll → download → transcrição → seleção → corte
- [ ] **A7.** Testes do `clip-processor` e do worker verdes; teste novo que trave regressão de SQL não portável
- [ ] **A8.** Documentação: `BANCO-DE-DADOS.md`, `SISTEMA-CLIP-PROCESSOR.md` e `RUNBOOK.md` (8 comandos `mysql` viram `psql`)
- [ ] **A9.** Merge na `master` pela skill `finalizar-e-deploy` — **sem deploy de produção nesta fase**

### Divergência encontrada na A2 (importante para a fase B)

As tabelas do pipeline na produção nasceram de **SQL cru**, não das migrations, e duas colunas de
`generated_clips` ficaram com nome diferente:

| Produção (real) | Migration dizia | Quem usa |
|---|---|---|
| `reason` | `rejection_reason` | `clip-processor`, 22 lugares |
| `scheduled_for` | `scheduled_at` | ninguém escreve; só constava no `$fillable` do model |

A produção é a fonte da verdade: a migration e o `GeneratedClip` foram alinhados para `reason` e
`scheduled_for`. Para a produção isso é inócuo (a migration já consta como aplicada); para um banco
novo — o Postgres — é o que impede o `clip-processor` de quebrar. **O resto do schema bate coluna a
coluna.**

### Falhas de teste pré-existentes encontradas (não são da migração)

- `test_rss_poller`: o código passa `niche=` para `select_moments` e o teste esperava a chamada sem
  esse argumento. Teste alinhado.
- `test_selector::test_shortform_under_30s_discarded`: o teste espera que um momento de 20 s seja
  **descartado**, mas `_filter_shortform_duration` hoje **estica** momentos de 15 s ou mais até os 30 s
  (o de 20 s virou 45–75 s). Ou o código ou o teste está errado — **decisão de produto, não toquei**.

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
