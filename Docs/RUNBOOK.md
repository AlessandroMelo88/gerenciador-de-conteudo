# Runbook de operação

Comandos do dia a dia, diagnóstico e reinício seguro do stack.

**Antes de qualquer operação destrutiva, leia as 7 regras de [`../CLAUDE.md`](../CLAUDE.md).**

Verificado em **26/08/2026**.

## Convenções

Todos os comandos partem da raiz deste repositório. O Compose é isolado, com PostgreSQL, Redis,
PHP-FPM, Nginx e clip-processor próprios. Não use `container_name`, não publique as portas do banco
ou Redis e nunca execute `docker compose down -v` em uma instalação com dados.

## Saúde dos serviços

```bash
docker compose ps postgres redis clip-processor php nginx
docker compose logs --tail=100 clip-processor
./scripts/validate-infra.sh
```

O `panel-init` deve terminar com sucesso antes de `php`, `queue` e `scheduler`. Ele aplica as migrations
Laravel, inclusive as tabelas do pipeline.

Para consultas rápidas no banco, use o próprio container PostgreSQL:

```bash
docker compose exec -T postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" --set=ON_ERROR_STOP=1 "$@"' \
  -- -c 'SELECT current_database(), current_user;'
```

## Código atualizado no clip-processor

Não há bind mount para `clip-processor/src/`; a imagem embute o código no build. Depois de alterar
Python, faça rebuild e reinicie somente o serviço:

```bash
docker compose build clip-processor
docker compose up -d clip-processor
docker compose exec -T clip-processor python -m pytest tests/ -q
```

## Reinício seguro

Antes de reiniciar, liste os estados em trânsito. O comando é somente leitura:

```bash
docker compose exec -T postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" --set=ON_ERROR_STOP=1 "$@"' \
  -- -c "
    SELECT status, COUNT(*) FROM generated_clips
    WHERE status IN ('cutting', 'publishing') GROUP BY status;
    SELECT status, COUNT(*) FROM source_videos
    WHERE status IN ('downloading', 'transcribing') GROUP BY status;
  "
```

Se houver `publishing`, aguarde ou confirme no YouTube antes de matar o processo: o upload pode ter
terminado sem o banco ter sido atualizado. Se houver `cutting`, prefira aguardar; se o processo for
reiniciado, o boot devolve esses clips para `pending_cut`. O recovery automático também cobre
`downloading`, `selecting` e `publishing` (com a ressalva do YouTube); consulte
[`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md) para os demais estados.

```bash
docker compose up -d --force-recreate clip-processor
```

## Estado preso

Primeiro liste e avalie o tempo sem atualização:

```bash
docker compose exec -T postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" --set=ON_ERROR_STOP=1 "$@"' \
  -- -c "
    SELECT id, status, updated_at,
           EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - updated_at)) / 3600 AS horas
    FROM generated_clips
    WHERE status IN ('cutting', 'publishing')
    ORDER BY updated_at;
  "
```

| Preso em | Ação após validar o caso | Observação |
|---|---|---|
| `generated_clips.cutting` | devolver a `pending_cut` | o corte recomeça; o raw precisa existir |
| `generated_clips.publishing` | conferir o YouTube antes | evita duplicar um upload já concluído |
| `source_videos.transcribing` | devolver a `downloaded` | reprocessa a etapa de IA |

Exemplo com ID explícito, somente depois da conferência:

```bash
docker compose exec -T postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" --set=ON_ERROR_STOP=1 "$@"' \
  -- -c "UPDATE generated_clips SET status = 'pending_cut' WHERE id = 123 AND status = 'cutting';"
```

## Pipeline sem novos downloads

Verifique, nesta ordem:

1. a ocupação da janela (`curto` = 6, `longo` = 4 por padrão);
2. `failed` com `local_path` preenchido, que pode manter uma vaga ocupada;
3. espaço livre no volume de vídeos;
4. o filtro de frescor (`FRESHNESS_DAYS`).

```bash
docker compose exec -T postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" --set=ON_ERROR_STOP=1 "$@"' \
  -- -c "
    SELECT sv.format, COUNT(DISTINCT sv.id) AS ocupando
    FROM source_videos sv
    LEFT JOIN generated_clips gc ON gc.source_video_id = sv.id
    WHERE sv.local_path IS NOT NULL
       OR sv.status IN ('downloading', 'downloaded', 'transcribing', 'selecting', 'cutting', 'publishing')
       OR gc.status IN ('pending_cut', 'pending', 'cutting', 'approved')
    GROUP BY sv.format;
  "
```

```bash
docker compose exec -T clip-processor df -h /app/videos
```

Nunca apague arquivos ou linhas só porque parecem antigos. Siga a lista em duas etapas e confirme que
o arquivo saiu antes de limpar `local_path`, conforme `CLAUDE.md`.

## Publicação no YouTube

Confira janela local (19h–22h), cota no Redis, clips publicáveis, canal-destino ativo e OAuth:

```bash
docker compose exec -T redis redis-cli keys 'youtube_uploads:*'
docker compose exec -T redis redis-cli get 'youtube_uploads:<channel_id>:<YYYY-MM-DD>'
docker compose logs --tail=200 clip-processor | grep -iE 'PUB|oauth|upload|thumbnail'
```

Não use `FLUSHALL`: isso apaga deduplicação e pode ressuscitar vídeos no próximo RSS. Para corrigir
somente uma cota, remova apenas a chave diária explicitamente identificada.

## Backup e restauração

O backup usa `pg_dump`, gzip e SHA-256. Aponte `POSTGRES_BACKUP_DIR` para outro disco ou armazenamento
sincronizado quando precisar de proteção contra falha física:

```bash
docker compose --profile backup up -d postgres-backup
./scripts/backup-postgres.sh
latest="$(find backups/postgres -name 'clips_automation_*.sql.gz' -type f -print | sort | tail -n 1)"
gzip -t "$latest"
(cd backups/postgres && sha256sum -c "$(basename -- "${latest}.sha256")")
```

Para restaurar, pare o processamento e confirme explicitamente. O script valida o gzip e o checksum
antes de enviar o dump:

```bash
docker compose stop clip-processor queue scheduler
CONFIRM_RESTORE=I_UNDERSTAND ./scripts/restore-postgres.sh ./backups/postgres/SEU_BACKUP.sql.gz
docker compose start queue scheduler clip-processor
```

As FKs não usam `ON DELETE CASCADE`; faça backup antes de `DELETE` em massa e remova clips antes dos
vídeos de origem.

## Usuário e OAuth

```bash
docker compose exec php php /var/www/html/painel/artisan painel:create-user
docker compose exec php php /var/www/html/painel/artisan painel:reset-password email@exemplo.com
docker compose exec clip-processor python -m src.youtube_oauth --channel <slug>
```

Senhas nunca são exibidas. O token OAuth é salvo como `/app/youtube/token-<slug>.json`.

## Qualidade

```bash
make setup
make hooks
make format
make ci
```

`make ci` executa lint, mypy, testes Python, validação do Compose, hadolint quando instalado e build
do frontend. Os testes PHP devem rodar em um banco de teste isolado; veja
[`DESENVOLVIMENTO.md`](DESENVOLVIMENTO.md).
