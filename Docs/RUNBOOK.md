# Runbook de operação

Comandos do dia a dia, como diagnosticar e como reiniciar sem estragar nada.

**Antes de qualquer operação destrutiva, ler as 7 regras de [`../CLAUDE.md`](../CLAUDE.md).** Elas não
são teoria: cada uma nasceu de um incidente com perda de arquivo ou de log.

Verificado em **13/08/2026**.

---

## Convenções

- Todos os comandos rodam de `/Users/alessandrobm1/develop/server/wordpress/` (onde vive o
  `docker-compose.yml`), **não** de `canaldecortes/`.
- O `docker-compose.yml` é **compartilhado** com kelnab, feeb, placebeads, riodelux e gringo. Mexer
  apenas no serviço `clip-processor`. **Nunca** `docker compose down` sem nome de serviço.
- O `.env` que o compose lê é o da **raiz `wordpress/`**.

---

## Está tudo de pé?

```bash
docker compose ps clip-processor mysql redis
docker compose logs --tail=100 clip-processor
```

Sinais de saúde no log, por tag: `[ACQU]` ingestão/download, `[AI]` transcrição/seleção,
`[VID]` corte, `[PUB]` publicação, `[DB]`, `[QUEUE]`, `[DEDUP]`, `[NOTIFY]`.

Um ciclo saudável loga `Ciclo de ingestão finalizado` a cada 20 min.

---

## O container está rodando código velho?

**A armadilha mais recorrente do projeto.** Não há bind mount para `src/` — a imagem embute o código
no build. Em 13/08/2026 o container rodava código de 01/08 enquanto o host tinha commits de 12/08, e o
comportamento observado não correspondia a nenhuma versão do código que se estava lendo.

```bash
# data da imagem que o container está rodando
docker inspect clip-processor --format '{{.Created}} {{.Image}}'
# data do último commit no host
git -C canaldecortes log -1 --format='%ad %h %s' --date=iso
```

Divergiu ⇒ rebuild:

```bash
docker compose build clip-processor && docker compose up -d clip-processor
```

Conferir na dúvida se um arquivo específico dentro do container já tem a mudança:

```bash
docker exec clip-processor grep -n "MIN_SHORTFORM_SECONDS" /app/src/selector.py
```

**Sempre confirmar isso antes de investigar qualquer bug de pipeline.**

---

## Reiniciar o clip-processor com segurança

O container **não honra SIGTERM**: `scheduler.shutdown` não retorna e todo `docker stop` termina em
`Exited (137)` / SIGKILL (bug aberto, ver [`BUGS.md`](BUGS.md)). Ou seja, o processo pode morrer no
meio de um estágio, e `cutting`/`publishing` **não têm recuperação automática**.

Antes de reiniciar, ver se há trabalho em trânsito:

```bash
docker exec mysql mysql -uroot -p"$P" clips_automation -e "
SELECT status, COUNT(*) FROM generated_clips
WHERE status IN ('cutting','publishing') GROUP BY status;
SELECT status, COUNT(*) FROM source_videos
WHERE status IN ('downloading','transcribing') GROUP BY status;"
```

- Tudo zero ⇒ reiniciar à vontade.
- Tem `publishing` ⇒ **esperar**. Está no meio de um upload; matar agora deixa o clip preso para
  sempre (e talvez publicado no YouTube com registro `failed`).
- Tem `cutting` ⇒ preferir esperar; se não puder, anotar os ids para destravar depois.

```bash
docker compose up -d --force-recreate clip-processor   # ou build + up, se mudou código
```

Reiniciar **recupera** `downloading` e `selecting` no boot, então travamento nesses dois não é motivo
para esperar.

---

## Estado preso sem recuperação automática

`transcribing`, `generated_clips.cutting` e `generated_clips.publishing` não têm recovery — o que
travar ali fica preso para sempre e segura arquivo em disco.

Etapa 1, **listar** (nunca descobrir e alterar no mesmo comando):

```bash
docker exec mysql mysql -uroot -p"$P" clips_automation -e "
SELECT id, status, updated_at, TIMESTAMPDIFF(HOUR, updated_at, NOW()) AS h
FROM generated_clips WHERE status IN ('cutting','publishing') ORDER BY updated_at;"
```

Etapa 2, decidir pelo tempo parado. Sem update há horas, com o pipeline vivo nesse intervalo, é
travamento real.

| Preso em | Para onde devolver | Por quê |
|---|---|---|
| `generated_clips.cutting` | `pending_cut` | o corte recomeça do zero; o raw do vídeo fonte ainda está lá |
| `generated_clips.publishing` | **verificar no YouTube antes** | se o vídeo subiu, devolver a `pending` republica e duplica |
| `source_videos.transcribing` | `downloaded` | reprocessa a IA |

```bash
# exemplo, com id explícito — nunca UPDATE sem WHERE id
docker exec mysql mysql -uroot -p"$P" clips_automation -e "
UPDATE generated_clips SET status='pending_cut' WHERE id=123 AND status='cutting';"
```

Para `publishing`, conferir primeiro se o upload aconteceu: `SELECT youtube_video_id FROM
generated_clips WHERE id=...`. Preenchido ⇒ o upload passou e o que falhou foi depois (provavelmente a
thumbnail); marcar `published`, não `pending`.

---

## O pipeline parou de baixar

Cadeia de causas em ordem de probabilidade:

**1. A janela está cheia de linha morta.** A janela conta muito mais que "tem arquivo"
(ver [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md#estados--ocupação-da-janela-de-download)):

```bash
docker exec mysql mysql -uroot -p"$P" clips_automation -e "
SELECT sv.format, COUNT(DISTINCT sv.id) AS ocupando
FROM source_videos sv LEFT JOIN generated_clips gc ON gc.source_video_id = sv.id
WHERE sv.local_path IS NOT NULL
   OR sv.status IN ('downloading','downloaded','transcribing','selecting','cutting','publishing')
   OR gc.status IN ('pending_cut','pending','cutting','approved')
GROUP BY sv.format;"
```

`curto ≥ 6` ou `longo ≥ 4` ⇒ déficit zero, nada baixa. Descobrir **qual** estado está segurando e
destravar (seção anterior).

**2. `failed` com `local_path` preenchido.** Era o caso dos 58 vídeos / 4.1 GB. `_discard_failed_download`
corrige daqui pra frente; para o resíduo antigo:

```bash
docker exec mysql mysql -uroot -p"$P" clips_automation -e "
SELECT COUNT(*), SUM(local_path IS NOT NULL) FROM source_videos WHERE status='failed';"
```

Apagar **o arquivo antes** do `UPDATE`, com caminho absoluto, e conferir que saiu (regra 2 do
CLAUDE.md).

**3. Disco abaixo de 2 GB livres.** O disk guard aborta o download e mede o **disco real**:

```bash
docker exec clip-processor df -h /app/videos
```

**4. Filtro de frescor.** `pending` com `published_at` anterior a ontem **nunca** baixa. Backlog alto
com janela vazia e nada baixando geralmente é isso — e não é bug.

```bash
docker exec mysql mysql -uroot -p"$P" clips_automation -e "
SELECT DATE(published_at) >= CURDATE() - INTERVAL 1 DAY AS fresco, COUNT(*)
FROM source_videos WHERE status='pending' GROUP BY fresco;"
```

---

## Nada sobe para o YouTube

Na ordem:

| Checar | Como | Nota |
|---|---|---|
| Estamos na janela horária? | hora local SP entre 19h e 22h | fora dela nada publica; `UPLOAD_WINDOW_BYPASS=true` ignora |
| A cota do dia acabou? | `docker exec redis redis-cli keys 'youtube_uploads:*'` e `get` na chave de hoje | teto rígido de **6/dia por canal** no código |
| Há clip publicável? | `SELECT status, COUNT(*) FROM generated_clips GROUP BY status;` | publicável = `pending` ou `approved`, conforme `MANUAL_APPROVAL_REQUIRED` |
| O OAuth expirou? | `SELECT slug, oauth_expired_flag FROM destination_channels;` | badge no painel; regerar com `youtube_oauth.py` |
| O canal-destino está ativo? | `SELECT slug, active FROM destination_channels;` | sem canal ativo cai no fluxo legado |
| `privacyStatus` | `YOUTUBE_PRIVACY_STATUS` no `.env` | default **`private`** — sobe e não aparece |

Reset **só** do contador de cota travado, sem tocar no dedup:

```bash
docker exec redis redis-cli del "youtube_uploads:<channel_id>:$(date +%F)"
```

**Nunca `FLUSHALL`.** Isso apaga as chaves `video:*` de dedup e **ressuscita todo o backlog** no
próximo poll, além de zerar a cota.

---

## Diagnosticar falhas de upload

```bash
docker exec mysql mysql -uroot -p"$P" clips_automation -e "
SELECT id, status, LEFT(upload_error, 200) FROM generated_clips
WHERE status='failed' ORDER BY id DESC LIMIT 20;"

docker compose logs clip-processor | grep -i thumb
```

`upload_error` mencionando thumbnail com `youtube_video_id` preenchido = o vídeo **subiu** e o clip foi
marcado `failed` só por causa da thumbnail
(ver [`SISTEMA-PUBLICACAO.md`](SISTEMA-PUBLICACAO.md#thumbnail-sem-trycatch-próprio)).

---

## Espaço em disco

```bash
docker exec clip-processor df -h /app/videos
docker exec clip-processor du -sh /app/videos /app/videos/clips /app/videos/thumbnails
```

Maiores consumidores, em ordem histórica: `<clip_id>_raw.mp4`, os `.mp4` brutos dos vídeos fonte, os
clips finais. Os `_raw`/`_subtitled` passaram a ser apagados na finalização do vídeo fonte desde
12/08/2026; resíduo anterior a isso ainda pode estar lá.

Limpeza segura, em **duas etapas** (regra 1 do CLAUDE.md):

```bash
# etapa 1 — materializa o alvo e confere contagem + tamanho
comm -23 disco.txt manter.txt > alvos.txt && wc -l < alvos.txt && du -ch $(cat alvos.txt)
# etapa 2 — só então apaga a partir da lista revisada
tr '\n' '\0' < alvos.txt | xargs -0 rm -f
```

Contagem inesperada (muito maior, ou zero) ⇒ **parar e investigar**, não ajustar o comando até "dar
certo".

Ao montar `manter.txt`, extrair o **id** (prefixo numérico antes de `.` ou `_`) e comparar com
`SELECT id FROM generated_clips`. Comparar **nome de arquivo** contra as colunas marca `.srt` e
`_raw.mp4` como órfãos e apaga arquivo de clip vivo — eles não estão em coluna nenhuma.

---

## Backup antes de DELETE em massa

```bash
docker exec mysql mysqldump -uroot -p"$P" clips_automation source_videos generated_clips > backup_$(date +%Y%m%d_%H%M).sql
```

As FKs **não** têm `ON DELETE CASCADE`: apagar `source_videos` com clips vinculados falha por FK.
Ordem correta: **clips primeiro, depois vídeos**.

---

## Redis: o que é seguro apagar

| Chave | Conteúdo | Apagar é seguro? |
|---|---|---|
| `video:<id>` | dedup, TTL 30 dias | **NÃO** — os vídeos deletados voltam no próximo poll |
| `youtube_uploads:<...>:<data>` | cota diária | sim, se o objetivo é liberar upload hoje |
| `clip_warned:<id>` | idempotência do aviso de TTL | sim, no pior caso reavisa |

**A fila não mora no Redis.** Fila = MySQL. Purgar de vez = apagar linhas do MySQL **mantendo** as
chaves de dedup.

---

## Nunca podar Docker às cegas

`docker system prune -f` remove containers **parados**, e `docker image prune -af` remove a imagem que
ficou órfã em seguida. Foi assim que o `clip-processor` desapareceu por completo — junto com os logs
que diriam por que ele havia caído.

Antes de podar: `docker ps -a` e `docker compose ps`. Serviço do projeto parado ⇒
**investigar (`docker compose logs`) antes**. Preferir alvo específico a `prune` genérico.

Sob pressão de disco (SSD acima de ~85%) o Docker Desktop já ficou pendurado em `docker ps`
indefinidamente. Sem Docker não há banco nem log — é o modo de falha que **esconde todos os outros**.
Liberar espaço pode não bastar; exige restart do Docker Desktop.

---

## Comandos do painel

Rodam no container `php`, dentro de `painel/`:

```bash
docker exec -it php php /var/www/html/painel/artisan painel:create-user      # senha >= 10 chars
docker exec -it php php /var/www/html/painel/artisan painel:reset-password email@exemplo.com
```

Não existe registro público. O reset pela UI exige apenas 8 chars — inconsistência conhecida.

Com `config:cache` ativo, `env()` fora de `config/` retorna `null` **em silêncio** e o painel passa a
mostrar cota diferente da que o publisher usa. Se os números divergirem, é o primeiro suspeito.

---

## OAuth de um canal-destino

CLI interativo, dentro do container:

```bash
docker exec -it clip-processor python -m src.youtube_oauth
```

Gera `/app/youtube/token-<slug>.json`. O `<slug>` tem que ser exatamente o
`destination_channels.slug` — o uploader monta o caminho a partir dele.

---

## Testes

```bash
docker exec clip-processor python -m pytest tests/ -q         # pipeline
docker exec php php /var/www/html/painel/artisan test        # painel (Pest)
```

Rodar a suíte do pipeline **dentro do container**: o host não tem as dependências do sidecar (`flask`),
o que faz teste falhar por ambiente e não por código. Ver [`BUGS.md`](BUGS.md).
