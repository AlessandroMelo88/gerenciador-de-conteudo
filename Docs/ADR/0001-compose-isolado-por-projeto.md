# ADR-0001 — Compose isolado por projeto

**Status:** aceito · **Data:** 25/08/2026

## Contexto

Até 25/08/2026 o projeto rodava no `docker-compose.yml` compartilhado de `wordpress/`, ao lado de
kelnab, feeb, placebeads, riodelux e gringo: mesmo `nginx`, `php`, `mysql` e `redis`, `.env` na raiz
de outro projeto, vhost `canaldecortes.local`. Qualquer `docker compose down` sem nome de serviço
derrubava todos; `docker system prune` já apagou o `clip-processor` inteiro junto com os logs
(`CLAUDE.md`, regra 4). O incidente de disco de 27/07/2026 e a migração para a Oracle exigem um
stack que suba sozinho.

## Decisão

`docker-compose.yml` **na raiz deste repositório**, projeto Compose `canaldecortes`, com serviços
exclusivos: `mysql:8.4` e `redis:7-alpine` em volumes nomeados **sem porta no host**; painel como
`php` (fpm) + `queue` + `scheduler` a partir de `docker/php/Dockerfile`; `nginx` próprio em
`${APP_PORT:-8088}`; `clip-processor` com healthcheck em `GET /health`; `panel-init` roda migrate e
cria o operador antes dos demais; `mysql-backup` opcional (perfil `backup`). Sem `container_name`,
sem mounts de outros projetos, `.env` lido da raiz deste repositório.

## Consequências

- `docker compose up -d` sobe o projeto inteiro em qualquer máquina com Docker; é o pré-requisito da
  fase 1 do `PLANO-ORACLE.md`.
- Acesso por `http://localhost:8088`, não mais por vhost. `docker/nginx/canaldecortes.conf` é copiado
  para a imagem, não bind-mountado de fora.
- `docker compose down -v` apaga os volumes de MySQL e Redis — proibido em instalação com dados
  (`RUNBOOK.md`).
- Editar `clip-processor/src/` continua exigindo rebuild (sem bind mount), como antes.

## Alternativas consideradas

- Continuar no compose compartilhado com `profiles` — não resolve prune/down acidentais nem a
  portabilidade para a Oracle.
- Um compose por serviço — fragmenta rede e healthchecks sem ganho.
