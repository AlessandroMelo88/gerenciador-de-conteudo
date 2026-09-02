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
| **`ABSOLUTE_MAX_UPLOADS_PER_DAY`** | **6** | — |
| `DEFAULT_MAX_LONGO_UPLOADS_PER_DAY` | 2 | `MAX_LONGO_UPLOADS_PER_DAY` |

`_resolve_limit` ([`:105`](../clip-processor/src/quota_manager.py#L105)) faz
`max(0, min(valor, 6))`: **existe um teto rígido de 6 uploads/dia por canal no código**, independente
da env var. Setar `MAX_UPLOADS_PER_DAY=20` não tem efeito acima de 6.

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

`_is_upload_window` ([`:122`](../clip-processor/src/quota_manager.py#L122)): **19h ≤ hora < 22h** em
São Paulo. Bypass total com `UPLOAD_WINDOW_BYPASS=true`.

Fora da janela, `has_capacity` retorna `False` e **nada publica** — o `publish_cycle` roda a cada
20 min o dia inteiro, mas só faz trabalho útil nessas 3 horas.

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
