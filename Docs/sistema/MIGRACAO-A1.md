# Migração para a VM A1 + PostgreSQL — como ficou

Executada em **17/09/2026**. Documento as-built: o que está no ar, como voltar atrás e o que falta.
Plano original: [`PLANO-MESTRE.md`](PLANO-MESTRE.md#4-infraestrutura--migrar-para-a1-flex-12-gb)
e [`PLANO-POSTGRES.md`](PLANO-POSTGRES.md).

## Em resumo

| Antes | Agora |
|---|---|
| `E2.1.Micro` 1 OCPU / 1 GB, São Paulo | `A1.Flex` 2 OCPU / 12 GB ARM, **Ashburn (US East)** |
| MySQL 8.4 | PostgreSQL 17 |
| 48 GB de disco para tudo | 46,6 GB de boot + **150 GB** só para vídeos (`/mnt/videos`) |
| IP `147.15.124.191` | IP reservado `129.80.236.185` |
| conta Oracle `alessandrobm1988` | conta Oracle `moneyandchill1` |
| `APP_DEBUG=true`, `APP_ENV=local` | `APP_DEBUG=false`, `APP_ENV=production` |
| sem backup | `pg_dump` diário, cópia puxada para o Mac |

## Servidor

```
ssh -i ~/.ssh/oracle-a1-2026-09-16.key ubuntu@129.80.236.185
```

| Item | Valor |
|---|---|
| Projeto | `/home/ubuntu/canaldecortes` (sem git; o código chega pelo `deploy.sh`) |
| Vídeos | `/mnt/videos/videos` — block volume de 150 GB, montado por UUID com `nofail` |
| Containers | `nginx`, `php`, `postgres`, `redis`, `clip-processor` |
| Firewall | 22, 80 e 443 na Security List **e** no `iptables` da imagem (persistido) |
| Segredos | `.env` e `painel/.env` regerados: senha do Postgres e `CLIP_PROCESSOR_INTERNAL_TOKEN` novos. Chaves de API, Telegram e `APP_KEY` mantidos |
| Custo | Always Free. Orçamento `alerta-custo` de US$ 5 com alerta em 1% real e 100% previsto |

## Tráfego até a troca do DNS

O DNS de `toolscut.alessandromelo.com.br` é da **Cloudflare** e ainda aponta para a Micro. Para não
depender dessa troca na hora da virada, o nginx da Micro virou **proxy para a A1**:

```
Cloudflare → Micro (nginx, só repassa) → A1 (painel + pipeline + Postgres)
```

**Pendente do operador:** na Cloudflare, trocar o registro A de `toolscut` para `129.80.236.185`
(mantendo o proxy laranja ligado). Depois disso a Micro não recebe mais nada.

## Backup

- A1: `/home/ubuntu/backup-postgres.sh`, cron às 06:15 UTC, grava em `/mnt/videos/backups`, retém 14 dias
- Mac: launchd `com.canaldecortes.backup-pull` (09:00 e ao carregar) copia para
  `~/Backups/canaldecortes-postgres/` — cópia **fora da Oracle**, exigência do plano

Restaurar: `gunzip -c arquivo.sql.gz | docker exec -i postgres psql -U clips_user -d clips_automation`.

## Worker de download no Mac

`scripts/local_download_worker.py` agora fala com a A1 via `psql` e envia vídeos para
`/mnt/videos/videos`. O YouTube bloqueia IP de datacenter, então download continua no Mac.

## Rollback (enquanto a Micro existir)

A Micro está com `clip-processor` e `php` **parados**, e `mysql`, `redis` e `nginx` de pé, com os dados
de 17/09/2026 16:28 UTC intactos.

1. Na A1: `docker compose stop clip-processor`
2. Na Micro: `cp docker/nginx/canaldecortes.conf.mysql-micro docker/nginx/canaldecortes.conf`,
   `docker exec nginx nginx -s reload`, `docker compose start php clip-processor`
3. `git revert` dos commits de `deploy.sh` e do worker, e recarregar o launchd do worker

Tudo que foi publicado ou aprovado na A1 depois da virada **não volta** para o MySQL sozinho.

## Como foi feita (para repetir ou auditar)

1. VM, IP reservado, block volume, Security List e orçamento pelo console
2. Disco formatado (`ext4`, label `videos`), Docker 29 + Compose instalados, reboot de teste
3. Projeto copiado da Micro por rsync; imagens `php` e `clip-processor` compiladas em ARM
4. `php artisan migrate` no Postgres vazio
5. Carga: `mysqldump` da Micro → MySQL temporário na A1 → `scripts/migrar_mysql_para_postgres.py`
   (trunca, converte booleanos, acerta sequences, confere contagem)
6. Testes contra uma cópia do banco: painel inteiro (todas as rotas GET), todas as gravações do
   pipeline e um **corte real** com ffmpeg + legenda + capa + título via Groq
7. Virada: worker do Mac parado, `clip-processor` da Micro parado, painel em manutenção (503),
   dump final e segunda carga, delta de vídeos, `dump.rdb` do Redis copiado (10.328 chaves
   `video:*` de dedup), `deploy.sh` na A1, nginx da Micro virando proxy, worker religado

Contagem final idêntica: 1 usuário, 3 nichos, 33 canais fonte, 3 destinos, 1.546 vídeos, 157 clips.

## Encontrado na migração

- **2 queries só-MySQL** que quebravam no Postgres e os testes com mock não pegavam:
  `ttl_worker` (`NOW() - INTERVAL 48 HOUR`) e `purge_old_videos` (`DELETE sv FROM`). Corrigidas.
- **Produção rodava com `APP_DEBUG=true`**: erro mostrava a página de debug do Laravel. Corrigido na A1.
- **O agendador do Laravel nunca rodou em produção** (não há cron chamando `schedule:run`): o resumo
  diário das 18h no Telegram e o `db:backup` das 03:15 nunca executaram. Não foi ligado na A1 —
  ligar muda comportamento (mensagem diária no Telegram); decisão do operador.
- `deploy.sh` envia `painel/.env.bak-sqlite` e `painel/database/database.sqlite` ao servidor (o
  exclude só pega `.env` exato). Fora da pasta pública, não é servido pela web.
- O log `Clip N pulado: status mudou durante seleção` é normal com aprovação manual: o publisher
  lista clips `pending` junto com `approved` e pula os `pending`. Já aparecia 1.458 vezes na Micro.

## O que falta

- [ ] **Cloudflare:** registro A de `toolscut` → `129.80.236.185`
- [ ] Alguns dias rodando; então desligar a Micro (ela é da outra conta e fica livre para outro uso)
- [ ] Reverter as adaptações para 1 GB: ffmpeg single-thread/ultrafast (`6ce2e78`), dashboard limitado
- [ ] `RUNBOOK.md` e `BANCO-DE-DADOS.md` ainda citam comandos `mysql`
- [ ] **Risco de conta:** a A1 está numa segunda conta Always Free; a Oracle permite uma por pessoa.
  O backup no Mac é a proteção contra perder a conta
