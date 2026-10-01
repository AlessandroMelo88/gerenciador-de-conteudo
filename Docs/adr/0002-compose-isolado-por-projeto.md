# ADR-0002 — Compose isolado por projeto (proposta não adotada)

**Status:** Rejeitada (não adotada) · **Data da proposta:** 25/08/2026 · **Revisada:** 30/09/2026

> Proposta feita em `release/rico` (Ricardo) e trazida para cá só como registro. A produção
> **não** funciona assim. O texto original falava em MySQL 8.4 e PostgreSQL 16; a produção é
> PostgreSQL 17 (`canaldecortes-postgres:pg17-vector`, com pgvector) desde 17/09/2026.

## Contexto

O projeto roda ao lado de kelnab, feeb, placebeads, riodelux e gringo no `docker-compose.yml`
compartilhado de `wordpress/` (mesmo `nginx`, `php` e `redis`). Um `docker compose down` sem nome de
serviço derruba todos, e um `docker system prune` já apagou o `clip-processor` junto com os logs
(`CLAUDE.md`, regra 4). A proposta era um compose próprio, com projeto Compose `canaldecortes`,
`nginx` em porta própria e volumes exclusivos, para o stack subir sozinho em qualquer máquina.

## Decisão

**Não adotar agora.** A regra vigente é a do `CLAUDE.md`: o compose da raiz `wordpress/` é
compartilhado, e só se mexe no serviço `clip-processor` e nos paths sob `canaldecortes/`. Em
produção (VM A1) o stack do projeto sobe pelo compose do próprio projeto com PostgreSQL 17 e vídeos
em `/mnt/videos` (`Docs/planos/MIGRACAO-A1.md`); a portabilidade que a proposta buscava foi
resolvida pela migração para a A1, não por um compose novo.

## Consequências

- O risco de `down`/`prune` acidental continua tratado por regra de trabalho (`CLAUDE.md`, regra 4),
  não por isolamento de infraestrutura.
- Ferramentas de desenvolvimento (Makefile, pre-commit, CI) **não** dependem de compose: o CI usa
  serviços do GitHub Actions e os testes PHP locais usam o Postgres avulso de
  `scripts/dev-pgvector.sh`.
- Se um dia o isolamento for retomado, é um ADR novo que substitui este.

## Alternativas consideradas

- Compose compartilhado com `profiles` — não resolve prune/down acidentais.
- Um compose por serviço — fragmenta rede e healthchecks sem ganho.
