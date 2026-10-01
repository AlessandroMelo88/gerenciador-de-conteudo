# Publicação no YouTube

Quem decide *o que* publicar, *quando* e *para onde*. Cobre `publisher.py`, `quota_manager.py`,
`uploader.py`, `youtube_oauth.py` e `ttl_worker.py`.

Verificado no código em **13/08/2026**.

---

## Quem é publicável

`_publishable_status()` ([`publisher.py:21`](../clip-processor/src/publisher.py#L21)):

| `MANUAL_APPROVAL_REQUIRED` | Status publicável | Efeito |
|---|---|---|
| `true` | `approved` | exige aprovação do operador no painel |
| qualquer outro (default `false`) | `pending` | publica direto, sem revisão humana |

`approved` **nunca é escrito pelo Python** — vem exclusivamente do painel. Com
`MANUAL_APPROVAL_REQUIRED=false` a fila de aprovação do painel fica vazia porque nada para em
`pending` por muito tempo.

Além do status, o clip precisa ter `clip_path IS NOT NULL` e `title IS NOT NULL`
([`publisher.py:121-122`](../clip-processor/src/publisher.py#L121)).

---

## Roteamento fonte → destino

Por **nicho**: `source_channels.target_niche` casa com `destination_channels.niche`. A resolução
acontece na seleção de momentos (`_lookup_destination_channel_id`,
[`selector.py:269`](../clip-processor/src/selector.py#L269)) e o resultado fica gravado em
`generated_clips.destination_channel_id`.

`publish_pending_clips` ([`publisher.py:33`](../clip-processor/src/publisher.py#L33)) itera os canais
de `destination_channels WHERE active = TRUE` ([`:89`](../clip-processor/src/publisher.py#L89)) e, para
cada um, instancia `QuotaManager` e `YouTubeUploader` **independentes** — cota é por canal-destino.

### Fallback legado

Se `destination_channels` não tiver nenhum canal ativo, cai num caminho legado
([`publisher.py:53-57`](../clip-processor/src/publisher.py#L53)) que usa um único uploader/quota e
busca clips sem filtrar por destino (`_fetch_pending_clips`,
[`:238`](../clip-processor/src/publisher.py#L238)). Nesse modo o token OAuth vem de
`YOUTUBE_TOKEN_FILE` / `/app/token.json`, não de `token-<slug>.json`.

---

## Ordem da fila: round-robin por canal fonte

`_fetch_pending_clips_for_channel` ([`publisher.py:99`](../clip-processor/src/publisher.py#L99)) busca
em `created_at ASC` e depois passa por `_round_robin_by_source_channel`
([`:130`](../clip-processor/src/publisher.py#L130)), que intercala por `source_channels.id`
preservando a ordem relativa dentro de cada canal.

Por que existe: uma leva represada — dezenas de vídeos presos em `selecting` por semanas que
destravam de uma vez — furaria a fila FIFO e monopolizaria a cota diária por dias, enquanto canais com
volume menor ficam represados atrás. Com round-robin, nenhum canal fonte publica dois clips seguidos
enquanto houver clip pendente de outro canal.

### Revezamento na hora de publicar (01/10/2026)

O round-robin acima só define a ordem inicial da lista. Em cada vaga, `publish_pending_clips` filtra
os clips que a cota deixa publicar (`can_upload`: total, formato e reserva do longo) e escolhe com
`_pick_next_by_rotation` o clip do **canal-fonte que publicou há mais tempo** (ou nunca) naquele
canal-destino. O histórico vem de `_fetch_source_channel_last_upload` (`MAX(published_at)` por
`source_videos.channel_id`) e é atualizado na própria rodada. Empate (inclusive sem canal-fonte
distinguível) mantém a ordem da lista. Não há limite fixo por canal-fonte por dia: a diversidade vem só
do revezamento. O revezamento nunca fura a cota: se o canal preferido só tem `longo` e a cota de longo
acabou, vale o próximo elegível.

---

## Cota diária e janela horária

[`quota_manager.py`](../clip-processor/src/quota_manager.py). Contadores no **Redis**, data em
`America/Sao_Paulo`, TTL até a meia-noite local (`_seconds_until_next_midnight`,
[`:136`](../clip-processor/src/quota_manager.py#L136)).

| Chave Redis | Conteúdo |
|---|---|
| `youtube_uploads:<channel_id>:<YYYY-MM-DD>` | total do dia naquele canal-destino |
| `youtube_uploads:<channel_id>:<YYYY-MM-DD>:longo` | quantos `longo` no dia |
| `youtube_uploads:<YYYY-MM-DD>` | total do dia quando não há `channel_id` (fallback legado) |

Montagem das chaves em [`_key`, :127](../clip-processor/src/quota_manager.py#L127) e
[`_format_key`, :133](../clip-processor/src/quota_manager.py#L133).

### Limites

| Constante | Valor | Env var |
|---|---|---|
| `DEFAULT_MAX_UPLOADS_PER_DAY` | 2 | `MAX_UPLOADS_PER_DAY` |
| **`ABSOLUTE_MAX_UPLOADS_PER_DAY`** (teto de segurança) | **10** | `ABSOLUTE_MAX_UPLOADS_PER_DAY` |
| `DEFAULT_MAX_LONGO_UPLOADS_PER_DAY` | 2 | `MAX_LONGO_UPLOADS_PER_DAY` |
| teto de curtos no dia | sem teto | `MAX_CURTO_UPLOADS_PER_DAY` |
| espaçamento mínimo entre uploads | 0 (desligado) | `MIN_UPLOAD_SPACING_MINUTES` |
| longos aguardando por canal | 0 (sem teto) | `MAX_LONGOS_PENDENTES_POR_CANAL` |

`_resolve_limit` faz `max(0, min(valor, teto_absoluto))`. Até 30/09/2026 o teto era 6 fixo no código;
agora é 10 por padrão e sobrescrevível por `ABSOLUTE_MAX_UPLOADS_PER_DAY`. O limite que vale em produção
continua sendo `MAX_UPLOADS_PER_DAY` (padrão 2) — o teto só impede erro de digitação.

**Cota por formato.** `MAX_CURTO_UPLOADS_PER_DAY` limita os curtos (curtos do dia = total − longos);
sem a env não há teto de curto (comportamento anterior). `MAX_LONGO_UPLOADS_PER_DAY` limita os longos.
Os dois são clampados no total, então curtos + longos nunca passam de `MAX_UPLOADS_PER_DAY`.
Rollout do canal de futebol: `MAX_UPLOADS_PER_DAY=10`, `MAX_LONGO_UPLOADS_PER_DAY=4`,
`MAX_CURTO_UPLOADS_PER_DAY=6` (rampa sugerida no plano: começar em 6 = 2 longos + 4 curtos).

`_resolve_longo_limit` ([`:110`](../clip-processor/src/quota_manager.py#L110)) clampa o limite de
`longo` no total (`min(valor, max_uploads_per_day)`).

### Reserva de slot para `longo`

`can_upload` ([`:59`](../clip-processor/src/quota_manager.py#L59)):

- clip `longo`: publica se `longo_count < max_longo_per_day`;
- clip `curto`: se houver `longo` publicável esperando na fila (`longo_waiting=True`), o teto do curto
  passa a ser `max_uploads_per_day − (max_longo_per_day − longo_count)`. Sem `longo` na fila a
  reserva desaparece e o curto usa o total.

`longo_waiting` é calculado por `_has_longo_waiting` ([`publisher.py:151`](../clip-processor/src/publisher.py#L151))
sobre os clips **restantes** daquele canal na rodada atual.

`has_capacity` ([`:45`](../clip-processor/src/quota_manager.py#L45)) ignora a reserva de formato e
existe para distinguir dois casos: cota total esgotada (para o ciclo do canal,
[`publisher.py:83`](../clip-processor/src/publisher.py#L83)) versus só pular este clip porque a
reserva de formato o bloqueia.

### Janela horária

`_is_upload_window`: `UPLOAD_WINDOWS` = **12h–14h** e **19h–22h** (hora < fim) em São Paulo, 5 h no
total. Bypass total com `UPLOAD_WINDOW_BYPASS=true`. (`LONG_UPLOAD_HOURS` não existe no código: o longo
usa as mesmas janelas.)

Fora da janela, `has_capacity` retorna `False` e **nada publica** — o `publish_cycle` roda a cada
20 min o dia inteiro, mas só faz trabalho útil nessas 5 horas.

**10 uploads cabem?** Sim: são 15 ciclos de 20 min dentro das janelas (6 no almoço, 9 à noite). Sem
espaçamento, porém, o publisher publica **em rajada**: num único ciclo ele publica todos os clips que a
cota permitir (até 10 de uma vez no primeiro ciclo da janela do almoço). Para espaçar, use
`MIN_UPLOAD_SPACING_MINUTES` (recomendado 15): grava em Redis
(`...:last_upload_ts`) o instante do último upload e `has_capacity` recusa até passar o intervalo, o
que limita a 1 upload por ciclo. Resultado com 10/dia: o dia enche cedo — 6 uploads entre 12h e 13h40
e 4 entre 19h e 20h. Não há divisão por janela; se quiser mais peso à noite, é evolução futura.
Default 0 = comportamento anterior.

### Teto de longos aguardando aprovação

`db.longo_teto_atingido(conn, destination_channel_id)` (env `MAX_LONGOS_PENDENTES_POR_CANAL`, padrão 0 =
sem teto; rollout 4) conta longos do canal em `pending_cut`/`cutting`/`pending`/`approved`. **Ainda não
é chamado por ninguém**: o ponto certo é o fluxo de download/seleção (rss_poller/pipeline_runner),
antes de baixar um vídeo `format='longo'` para o canal. Barrar ali evita raw em disco e clip em
`pending_cut` (que seguraria o raw, bug 17); barrar em `process_clip` não serve.

### Sem fallback de Redis

Diferente do dedup, a cota **não** tem fallback para MySQL. Redis fora do ar ⇒
`self.redis_client.get(...)` levanta ⇒ a publicação para. Contador travado ≠ fila travada: se o
sintoma é "não sobe mais hoje", conferir `youtube_uploads:<hoje>` e resetar **só** essa chave, nunca
o dedup.

---

## Upload

`YouTubeUploader.upload_clip` ([`uploader.py:86`](../clip-processor/src/uploader.py#L86)):

1. valida `clip_path` e `title`, e que a thumbnail existe se `thumbnail_path` estiver preenchido
   ([`:89`](../clip-processor/src/uploader.py#L89));
2. `videos.insert(part='snippet,status')` com upload resumível
   ([`:101`](../clip-processor/src/uploader.py#L101));
3. limpa `oauth_expired_flag` ([`:112`](../clip-processor/src/uploader.py#L112));
4. `thumbnails().set(videoId=...)` se houver thumbnail ([`:120`](../clip-processor/src/uploader.py#L120)).

Corpo do vídeo (`_build_video_body`, [`:218`](../clip-processor/src/uploader.py#L218)):

| Campo | Valor |
|---|---|
| `title` | truncado em **100 chars** |
| `categoryId` | `17` (Sports), fixo |
| `privacyStatus` | `YOUTUBE_PRIVACY_STATUS`, default **`private`** |
| `selfDeclaredMadeForKids` | `false` |

`tags` aceita string separada por vírgula ou lista (`_parse_tags`,
[`:232`](../clip-processor/src/uploader.py#L232)).

O default `private` importa: sem `YOUTUBE_PRIVACY_STATUS=public` no `.env`, o pipeline funciona
inteiro e **nada aparece publicamente no canal**.

### Thumbnail sem try/except próprio

O `thumbnails().set` roda **depois** do `videos.insert` e **fora** de qualquer `try` local. Se ele
levantar, o vídeo já subiu mas a exceção propaga para o publisher, que marca o clip como `failed`
([`publisher.py:303`](../clip-processor/src/publisher.py#L303)) com o motivo em `upload_error` — ou
seja, **clip publicado no YouTube com registro `failed` no banco**.

Hipótese principal para a suspeita de "thumbnail não aplicada nos longos": 403 do
`thumbnails().set`, que exige canal verificado. Ver [`BUGS.md`](BUGS.md).

---

## OAuth por canal-destino

| Item | Valor |
|---|---|
| Token por canal | `/app/youtube/token-<slug>.json` ([`uploader.py:78`](../clip-processor/src/uploader.py#L78)) |
| Token legado | `YOUTUBE_TOKEN_FILE` ou `/app/token.json` ([`:15`](../clip-processor/src/uploader.py#L15)) |
| Scope | `https://www.googleapis.com/auth/youtube.upload` ([`:16`](../clip-processor/src/uploader.py#L16)) |
| Geração | CLI interativo [`youtube_oauth.py`](../clip-processor/src/youtube_oauth.py) |
| Client secrets | `YOUTUBE_CLIENT_SECRETS=/app/youtube/client_secret.json` (compose) |

O scope é **só upload**. Nada no pipeline lê estatística ou comentário do canal.

`_load_credentials` ([`:137`](../clip-processor/src/uploader.py#L137)) faz refresh quando o token está
expirado. Se o refresh falhar com `RefreshError`:
`_flag_expired` ([`:152`](../clip-processor/src/uploader.py#L152)) grava
`destination_channels.oauth_expired_flag = TRUE` (o painel mostra o badge) e **re-lança**. Um upload
bem-sucedido limpa a flag sozinho (`_clear_expired`, [`:175`](../clip-processor/src/uploader.py#L175)).

Ambos são best-effort: se o `channel_slug` for `None` (uso legado) a gravação é silenciosamente
ignorada, e falha do MySQL só gera log.

---

## Guard de corrida com a rejeição

`_transition_to_publishing` ([`publisher.py:275`](../clip-processor/src/publisher.py#L275)) faz
`UPDATE ... SET status='publishing' WHERE id=%s AND status=<publicável>` e só segue se
`rowcount > 0`. Sem isso, um clip rejeitado no painel entre a leitura da fila e o upload subiria mesmo
assim.

---

## Finalização do vídeo fonte

`_maybe_finalize_source_video` ([`publisher.py:314`](../clip-processor/src/publisher.py#L314)) roda
após cada publicação bem-sucedida. Só age quando **as duas** condições valem:

- nenhum clip do vídeo em estado não-terminal (`pending_cut`, `cutting`, `pending`, `approved`,
  `publishing` — [`publisher.py:18`](../clip-processor/src/publisher.py#L18)); **e**
- ao menos um clip `published`.

Aí, na ordem ([`:331-371`](../clip-processor/src/publisher.py#L331)):

1. apaga o `.mp4` bruto do vídeo fonte;
2. apaga, de cada clip, `clip_path`, `<prefix>_raw.mp4`, `<prefix>_subtitled.mp4` e a thumbnail;
3. `UPDATE generated_clips SET clip_path = NULL, thumbnail_path = NULL`;
4. `UPDATE source_videos SET status='published', local_path=NULL`.

Essa cascata é de 12/08/2026 (commit `5009112`) e é o que resolveu o acúmulo de `_raw.mp4`. Todos os
`os.remove` são `try/except OSError: pass` — falha de remoção é silenciosa, e o `UPDATE` que zera as
colunas roda de qualquer forma. É o caminho que produz divergência banco × disco na direção
"coluna nula, arquivo presente".

Se **nenhum** clip publicar (todos `failed`/`rejected`), nada é apagado: o vídeo fica em `selecting`
com o raw em disco. Estado que só sai dali via recovery ou à mão.

---

## TTL de clip pendente

[`ttl_worker.py`](../clip-processor/src/ttl_worker.py), job `clip_pending_ttl` (1 h).

| Constante | Default | Env var |
|---|---|---|
| `TTL_HOURS` | 48 | `CLIP_PENDING_TTL_HOURS` |
| `WARN_HOURS` | 24 | `CLIP_PENDING_WARN_HOURS` |

- Clip `pending` com `created_at` mais velho que 48 h ⇒ `rejected`
  ([`:51`](../clip-processor/src/ttl_worker.py#L51)).
- Clip na janela [24 h, 48 h) recebe **um** aviso no Telegram, idempotente via chave Redis
  `clip_warned:<id>`.

Com `MANUAL_APPROVAL_REQUIRED=false` isso quase nunca dispara — clip `pending` é publicado no ciclo
seguinte. Passa a importar quando a aprovação manual está ligada ou quando a cota está travada por
dias.

Atenção: o TTL rejeita por **`created_at`**, não por tempo em `pending`. Um clip que ficou 40 h preso
em `cutting` e só depois virou `pending` já entra quase expirado.

## Coleta de métricas (views) e tela "Métricas"

Depois de publicado, o clip passa a ser medido: `clip-processor/src/metrics_collector.py` (job `metrics_collector`,
de hora em hora) chama `videos.list` part=`statistics` (até 50 ids por chamada) e grava **uma linha por clip por
coleta** em `clip_metrics` (`generated_clip_id`, `collected_at`, `views`, `likes`, `comments`). A FK tem
`ON DELETE CASCADE`: apagar um clip leva as medições junto (as demais FKs de `generated_clips` não têm cascade).

| Idade do clip | Frequência |
|---|---|
| menos de 7 dias | a cada 6 h |
| 7 a 30 dias | 1 vez por dia |
| mais de 30 dias | não mede mais |

- **Credencial:** a mesma do upload — `/app/youtube/token-{slug}.json` do canal-destino do clip (clip sem canal usa
  o token legado). O escopo `youtube.force-ssl` que o token já tem cobre a leitura; **nada novo a configurar**.
  Token expirado (`RefreshError`) liga `oauth_expired_flag` como no upload e o canal é pulado até renovar.
- **Cota:** `videos.list` custa 1 unidade/chamada, no projeto GCP de cada canal (10.000/dia). Com ~10 clips/dia
  medidos a cada 6 h são poucas dezenas de chamadas por dia. Teto de segurança: `METRICS_MAX_CALLS_PER_CHANNEL_DAY` (200).
- **Falha de API/banco** é só logada (`[METRICS]`); nunca derruba o pipeline. `METRICS_COLLECTOR_ENABLED=false` desliga o job.
- **Tela:** `/painel/metricas` (menu "Métricas"): views médias por formato (Short × longo) no 1º dia e aos 7 dias,
  ranking de canal-fonte por views por clip e a lista de clips com menos de 50 views após 2 dias no ar.
  Sem medições, mostra "ainda sem dados: a primeira coleta roda em até 6 h".
