# Runbook de operação

> Tipo: referência as-built · Atualizado: 2026-08-26
> Execute os comandos a partir da raiz do repositório.

Antes de apagar, purgar, restaurar ou alterar estados manualmente, leia
[`../CLAUDE.md`](../CLAUDE.md).

## Saúde

~~~bash
docker compose ps
docker compose logs --tail=100 clip-processor
docker compose logs --tail=100 clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
docker compose logs --tail=100 postgres php nginx
docker compose exec -T postgres pg_isready -U clips_user -d clips_automation
docker compose exec -T clip-processor python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8090/health').read().decode())"
~~~

O `panel-init` deve terminar com sucesso antes de `php`, `queue` e
`scheduler`. Verifique migrations:

~~~bash
docker compose exec php php artisan migrate:status
~~~

## Restart

Antes do restart, observe trabalho ativo:

~~~bash
docker compose exec -T postgres psql -U clips_user -d clips_automation -c "SELECT status, COUNT(*) FROM generated_clips WHERE status IN ('cutting','publishing') GROUP BY status;"
docker compose exec -T postgres psql -U clips_user -d clips_automation -c "SELECT status, COUNT(*) FROM source_videos WHERE status IN ('downloading','transcribing','selecting') GROUP BY status;"
~~~

- `cutting` pode ser interrompido; o boot devolve o clip para `pending_cut`.
- `publishing` pode já ter criado um vídeo no YouTube; confirme o ID antes de forçar
  reprocessamento.
- `transcribing` volta para `downloaded` pelo worker de manutenção após 2h se o raw existir;
  sem raw, vai para `failed`.
- `selecting` tem recovery periódico conforme idade e existência do raw.

O Compose atual monta `clip-processor/src` no sidecar e em cada worker. Depois de alterar Python,
recrie todos os processos do pipeline:

~~~bash
docker compose up -d --force-recreate clip-processor clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
~~~

Se alterar Dockerfile, dependências ou pacotes do sistema, faça rebuild:

~~~bash
docker compose up -d --build clip-processor clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
~~~

## Pipeline sem downloads

Verifique na ordem:

1. `PIPELINE_ENABLED`;
2. saúde do PostgreSQL e Redis;
3. ocupação das janelas: padrão 6 `curto` e 4 `longo`;
4. espaço livre em `/app/videos`;
5. `source_videos` em `pending` e `paused=false`;
6. `FRESHNESS_DAYS`;
7. parciais `.part`/`.ytdl` antigos.

~~~bash
docker compose exec -T clip-processor df -h /app/videos
docker compose logs --tail=200 clip-downloader clip-ai clip-renderer | grep -iE 'download|janela|disk|falha'
docker compose exec -T redis redis-cli ping
~~~

A limpeza automática remove artefatos de trabalho com mais de 1 h, mas não remove raw final.
Não apague `local_path` no banco antes de confirmar o arquivo no disco.

## Clips presos

Ações normais de recovery:

| Estado | Ação |
|---|---|
| fonte `downloading` | boot/job volta a `pending` |
| fonte `selecting` | após o limite, volta a `downloaded` ou vai para `failed` sem raw |
| clip `cutting` | somente boot volta a `pending_cut` |
| clip `publishing` | após 15 min volta a `pending`; confirme YouTube antes |
| fonte `transcribing` | ação manual; não há recovery automático |

Antes de uma alteração manual, liste ID, status, `updated_at`, `local_path`,
clips filhos e processos FFmpeg/yt-dlp. Faça backup quando a mudança puder perder dados.

## Publicação

Cheque janela, destinos, OAuth, SRT, quota e logs:

~~~bash
docker compose exec -T redis redis-cli --scan --pattern 'youtube_uploads:*'
docker compose logs --tail=300 clip-publisher clip-renderer | grep -iE 'PUB|oauth|upload|caption|thumbnail|processing'
~~~

Regras padrão:

- janela 19:00–22:00 no horário de São Paulo;
- total padrão 2/dia por destino, teto de 6;
- longos usam reserva própria;
- `MANUAL_APPROVAL_REQUIRED=true` exige `approved`;
- `YOUTUBE_WAIT_FOR_HD=true` mantém o vídeo privado até processamento/legenda;
- Redis fora do ar impede decisão de quota.

Não use `FLUSHALL`. Para investigar um contador, leia a chave exata do destino e da data.
Se um upload já criou vídeo e falhou na finalização, procure o `youtube_video_id` salvo
antes de reprocessar.

## Usuário, canal e OAuth

~~~bash
docker compose exec php php artisan painel:create-user
docker compose exec clip-processor python -m src.youtube_oauth --channel <slug>
~~~

O segredo OAuth precisa estar no volume `youtube/`, e o token fica em
`/app/youtube/token-<slug>.json`. O painel mostra `missing`,
`authorized` ou `expired` conforme arquivo e flag do banco.

## URLs manuais

O painel e o Telegram apenas enfileiram a URL. O caminho manual equivalente é:

~~~bash
docker compose exec clip-processor python -m src.processar <url>
~~~

O CLI usa `curto` por padrão. Para `longo`, use a tela Processar vídeo ou envie
`format=longo` à rota autenticada `/internal/process-url`.

## Disco e purga

Preferir ações do painel:

- apagar arquivos de uma fonte específica;
- purgar fontes anteriores a uma data;
- rejeitar clip pelo painel/Telegram.

Essas operações passam pelo sidecar e guardam clips em `pending_cut`/`cutting`.
Para lote, primeiro liste IDs, quantidade e tamanho; depois execute e confira banco e disco. Não
apague linhas de `source_videos` diretamente sem tratar `generated_clips`.

## Backup e restauração

Ative o backup periódico em outro disco quando possível:

~~~bash
docker compose --profile backup up -d postgres-backup
./scripts/backup-postgres.sh
~~~

Confirme gzip e checksum. Para restaurar:

~~~bash
docker compose stop clip-processor clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance queue scheduler
CONFIRM_RESTORE=I_UNDERSTAND ./scripts/restore-postgres.sh ./backups/postgres/SEU_BACKUP.sql.gz
docker compose start queue scheduler clip-processor clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
~~~

Restauração é destrutiva para o estado atual: confirme o arquivo e pare consumidores antes.
Detalhes de integridade estão em [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md).

## Testes e qualidade

~~~bash
make lint
make test-python
make test-php
make compose-check
~~~

Não use `make format` durante uma investigação sem revisar o diff: ele altera arquivos.
