# Banco de dados — `clips_automation`

Um único database MySQL 8.4 hospeda as tabelas do pipeline **e** as do painel Laravel.
Estados e transições ficam em [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md).

Verificado no SQL e no código em **13/08/2026**.

---

## As tabelas do pipeline não são migrations do Laravel

Elas nascem de **SQL bruto** em `mysql/init/01..07`, aplicado **à mão** via `docker exec`. O painel
apenas as mapeia com Eloquent e `$table` explícito.

Consequências que já morderam:

- `php artisan migrate:fresh` **não** reconstrói o schema do pipeline;
- por isso `RefreshDatabase` está desligado em `painel/tests/Pest.php` — os testes usam
  `DatabaseTransactions` sobre tabelas pré-existentes;
- migrar para outro servidor exige aplicar os `mysql/init/*` à mão se o dump não trouxer o schema
  (fase 4 do [`PLANO-ORACLE.md`](PLANO-ORACLE.md)).

`01-clips-schema.sql` contém `${CLIPS_DB_PASSWORD}` como **placeholder** — precisa de `envsubst`
antes de rodar ([`mysql/init/01-clips-schema.sql:5-8`](../mysql/init/01-clips-schema.sql#L5)).

### Ordem de aplicação

| Arquivo | O que faz |
|---|---|
| `01-clips-schema.sql` | database + `source_channels`, `source_videos`, `generated_clips` |
| `02-seed-channels.sql` | canais fonte iniciais |
| `03-schema-migration.sql` | `transcript_path`, `reason`; ENUM de clip ganha `pending_cut`/`cutting` |
| `04-publishing-migration.sql` | ENUM ganha `publishing`; `published_at`, `scheduled_for`, `upload_error` |
| `04-queue-controls.sql` | `priority`, `paused`, `queue_position` em `source_videos` |
| `05-controle-manual-migration.sql` | ENUM ganha `approved` e `rejected` |
| `06-multi-canal-migration.sql` | `destination_channels`; `target_niche`, `channel_handle`, `blacklisted`; `generated_clips.destination_channel_id` |
| `07-panel-oauth-flag-migration.sql` | `destination_channels.oauth_expired_flag` |

Há **dois** arquivos com prefixo `04`. Eles não dependem um do outro, mas a ordem alfabética
(`04-publishing` antes de `04-queue-controls`) é a que vale num `for f in mysql/init/*`.

Os `ALTER TABLE ... ADD COLUMN` são feitos com checagem em `INFORMATION_SCHEMA` + SQL dinâmico porque
o MySQL 8.4 do container **não aceita `ADD COLUMN IF NOT EXISTS`**. É por isso que os arquivos são
verbosos; a intenção é serem idempotentes.

---

## Tabelas

| Tabela | Origem | Papel |
|---|---|---|
| `source_channels` | `mysql/init/01`, `06` | canais monitorados via RSS |
| `source_videos` | `mysql/init/01`, `03`, `04-queue` | um registro por vídeo descoberto — **é a fila** |
| `generated_clips` | `mysql/init/01`, `03`, `04`, `05`, `06` | um registro por corte |
| `destination_channels` | `mysql/init/06`, `07` | canais próprios onde se publica |
| `niches` | **migration Laravel** (`2026_07_14_010214`) | domínio do painel; seeda `futebol` e `podcast` |
| `transcription_jobs` | **migration Laravel** (`2026_07_30_000000`) | Transcrição Local, isolada do pipeline |
| `users`, `sessions`, `cache`, `jobs` | migrations Laravel | painel |

### `source_channels`

[`mysql/init/01-clips-schema.sql:15`](../mysql/init/01-clips-schema.sql#L15) +
[`06-multi-canal-migration.sql:39-90`](../mysql/init/06-multi-canal-migration.sql#L39).

| Coluna | Tipo | Notas |
|---|---|---|
| `youtube_channel_id` | VARCHAR(64) UNIQUE | |
| `channel_name` | VARCHAR(255) | |
| `rss_url` | VARCHAR(512) | usado direto no `requests.get` |
| `active` | BOOLEAN default TRUE | filtro do poll |
| `target_niche` | VARCHAR(50) NULL | casa com `destination_channels.niche` |
| `channel_handle` | VARCHAR(100) NULL | usado nos créditos da descrição |
| `blacklisted` | BOOLEAN default FALSE, indexada | filtro do poll |

O poll exige `active = TRUE AND blacklisted = FALSE`
([`rss_poller.py:203`](../clip-processor/src/rss_poller.py#L203)).

### `source_videos`

[`mysql/init/01-clips-schema.sql:24`](../mysql/init/01-clips-schema.sql#L24).

| Coluna | Tipo | Notas |
|---|---|---|
| `youtube_video_id` | VARCHAR(64) **UNIQUE** | chave natural — o Python quase sempre busca por ela, não por `id` |
| `channel_id` | INT, FK → `source_channels` | |
| `title` | VARCHAR(500) | |
| `published_at` | TIMESTAMP | filtro de frescor (`FRESHNESS_DAYS`) e ordenação da fila |
| `status` | ENUM (9 valores) | ver [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md) |
| `local_path` | VARCHAR(1024) | `NOT NULL` ⇒ ocupa vaga da janela de download |
| `transcript_path` | VARCHAR(500) | `03-schema-migration` |
| `format` | ENUM(`curto`,`longo`) default `curto` | decidido na ingestão pela duração |
| `priority` | INT default 0 | `prioritize_video` grava `MAX(priority)+1` |
| `paused` | TINYINT(1) default 0 | pause cooperativo |
| `queue_position` | INT NULL | ordem manual do drag-and-drop |
| `created_at`, `updated_at` | TIMESTAMP | `updated_at` é `ON UPDATE CURRENT_TIMESTAMP` |

**`updated_at` é o que o recovery usa** para decidir se um `selecting` está travado
([`db.py:188`](../clip-processor/src/db.py#L188)). Qualquer `UPDATE` na linha, mesmo sem mudar
`status`, reseta esse relógio.

Ordenação canônica da fila (repetida em três queries):
`priority DESC, queue_position IS NULL, queue_position ASC, published_at DESC`.

### `generated_clips`

[`mysql/init/01-clips-schema.sql:52`](../mysql/init/01-clips-schema.sql#L52) + migrations 03/04/05/06.

| Coluna | Tipo | Notas |
|---|---|---|
| `source_video_id` | INT, FK → `source_videos` | |
| `destination_channel_id` | INT NULL, FK → `destination_channels` | resolvido por nicho na seleção |
| `clip_path`, `thumbnail_path` | VARCHAR(1024) | **zerados na finalização do vídeo fonte** |
| `title` | VARCHAR(200) | o uploader trunca em 100 antes de enviar |
| `description`, `tags` | TEXT | `tags` é string separada por vírgula |
| `score` | TINYINT | 0–10, da IA |
| `reason` | TEXT | justificativa da IA; virou a descrição no fallback determinístico |
| `start_time`, `end_time` | FLOAT | segundos no vídeo fonte |
| `status` | ENUM (8 valores) | default `pending_cut` |
| `youtube_video_id` | VARCHAR(64) | id **do clip publicado**, não do vídeo fonte |
| `published_at` | TIMESTAMP NULL | |
| `scheduled_for` | TIMESTAMP NULL | coluna existe; não encontrei nenhum código que a leia ou escreva |
| `upload_error` | TEXT NULL | truncado em 2000 chars por `_mark_clip_failed` |

Cuidado com `youtube_video_id`: existe nas duas tabelas com significados diferentes (fonte vs clip
publicado).

### `destination_channels`

[`mysql/init/06-multi-canal-migration.sql:13`](../mysql/init/06-multi-canal-migration.sql#L13).

| Coluna | Notas |
|---|---|
| `slug` | VARCHAR(50) UNIQUE — define `token-<slug>.json` e `watermark-<slug>.png` |
| `niche` | casa com `source_channels.target_niche` |
| `youtube_channel_id` | VARCHAR(50) UNIQUE NOT NULL — usado na chave Redis de cota |
| `credit_template` | TEXT — anexado à descrição no momento da publicação |
| `active` | filtro de `publish_pending_clips` |
| `oauth_expired_flag` | BOOLEAN default FALSE (`07-...`) — badge no painel, auto-limpo em upload OK |

O `slug` é acoplamento de **filesystem**: renomear um slug quebra o token OAuth e a marca d'água em
silêncio.

Os canais seedados têm `youtube_channel_id` **placeholder** (`UC_PLACEHOLDER_FUTEBOL`,
`UC_PLACEHOLDER_PODCAST`). Se ninguém trocou no banco, seguem inválidos — e a chave de cota é montada
com esse valor.

---

## Integridade referencial

**Nenhuma FK tem `ON DELETE CASCADE`.** Consequências:

- apagar `source_videos` com clips vinculados **falha por FK**;
- ordem correta em delete manual: **clips primeiro, depois vídeos**;
- sempre fazer backup antes (regra 5 do [`../CLAUDE.md`](../CLAUDE.md)).

```bash
docker exec mysql mysqldump -uroot -p"$P" clips_automation source_videos generated_clips > backup.sql
```

`niches` é a fonte dos selects do painel, mas **não há FK** ligando `source_channels.target_niche` /
`destination_channels.niche` a ela — seguem VARCHAR livre. Um nicho digitado errado não é rejeitado
pelo banco; só faz o clip nunca encontrar canal-destino.

---

## Divergência banco × disco (bug aberto)

**287 clips têm `clip_path` apontando para arquivo que não existe em disco.** Origem: limpeza apagou o
arquivo sem limpar a coluna. Detalhe e status em [`BUGS.md`](BUGS.md).

Efeito prático no pipeline: o uploader valida a existência do arquivo
([`uploader.py:133`](../clip-processor/src/uploader.py#L133)) e levanta `FileNotFoundError`, então o
clip vira `failed` na tentativa de publicar em vez de subir vazio.

Query para medir a divergência (só leitura):

```sql
SELECT id, status, clip_path FROM generated_clips
WHERE clip_path IS NOT NULL AND status IN ('pending','approved') ORDER BY id;
```
Depois conferir cada path com `docker exec clip-processor ls -l <path>` — não confiar na coluna.

---

## Acesso

| Serviço | Usuário | Database |
|---|---|---|
| `clip-processor` | `clips_user` (env `MYSQL_USER`) | `clips_automation` |
| `php` (painel) | ver `painel/.env` | `clips_automation` |

O `clip-processor` conecta via pymysql com `autocommit=False`, `charset=utf8mb4`,
`connect_timeout=10`, `cursorclass=DictCursor`
([`db.py:43`](../clip-processor/src/db.py#L43)). **Cada função faz commit explícito**; quem abre a
conexão é responsável por fechar.

A senha vem de `CLIPS_DB_PASSWORD` no `.env` da **raiz `wordpress/`** — não o `canaldecortes/.env`.
