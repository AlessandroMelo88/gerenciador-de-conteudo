# Descoberta e download

Como o vídeo entra na fila e como sai do YouTube para o disco. Cobre `rss_poller.py` (parte de
descoberta), `dedup.py`, `downloader.py` e a parte de download do `pipeline_runner.py`.

Verificado no código em **13/08/2026**.

---

## Descoberta via RSS

`poll_all_channels` ([`rss_poller.py:177`](../clip-processor/src/rss_poller.py#L177)) varre os canais
de `source_channels` com `active = TRUE AND blacklisted = FALSE`
([`:200-205`](../clip-processor/src/rss_poller.py#L200)). Um `try/except` por canal — falha de um não
aborta os demais ([`:255`](../clip-processor/src/rss_poller.py#L255)).

Por entrada do feed, nesta ordem:

| # | Passo | Onde | Se falhar |
|---|---|---|---|
| 1 | `GET` no `rss_url`, timeout 30s, `feedparser.parse` | [`:222`](../clip-processor/src/rss_poller.py#L222) | HTTP ≠ 200 ⇒ pula o canal |
| 2 | extrai o `video_id` (`yt_videoid`, fallback regex `v=([A-Za-z0-9_-]{11})`) | [`_extract_video_id`, :73](../clip-processor/src/rss_poller.py#L73) | sem id ⇒ pula a entrada |
| 3 | dedup: já vi esse vídeo? | [`dedup.is_seen`, :26](../clip-processor/src/dedup.py#L26) | visto ⇒ pula |
| 4 | filtro de título por keyword | [`_is_blocked_title`, :33](../clip-processor/src/rss_poller.py#L33) | bloqueado ⇒ pula |
| 5 | detecção de formato via yt-dlp metadata | [`_detect_format`, :54](../clip-processor/src/rss_poller.py#L54) | erro ⇒ assume `curto` |
| 6 | `INSERT IGNORE ... status='pending'` | [`db.py:101`](../clip-processor/src/db.py#L101) | — |

### Filtro de título

Lista literal em [`rss_poller.py:27`](../clip-processor/src/rss_poller.py#L27), match por substring no
título em minúsculas: `aposta`, `apostas`, `bet `, `bets `, `betting`, `odds`, `cassino`, `casino`,
`tigrinho`, `crash game`, `blaze`, `esportebet`, `pixbet`, `sportingbet`.

Note os espaços em `'bet '` e `'bets '` — evita casar com "Betis", "Bet365" fica de fora do match por
não ter espaço depois. Substring simples: um título com "aposta" em qualquer contexto é bloqueado.

### Detecção de formato

`_detect_format` ([`rss_poller.py:54`](../clip-processor/src/rss_poller.py#L54)) roda yt-dlp em
metadata-only e compara a duração real do vídeo fonte com
`MIN_LONGFORM_SECONDS = 420` ([`selector.py:61`](../clip-processor/src/selector.py#L61)):

| Duração do vídeo fonte | `format` |
|---|---|
| ≥ 420 s (7 min) | `longo` |
| < 420 s, ou falha ao consultar metadados | `curto` |

O corte é em **7 minutos**, não 10. Falha de rede/vídeo indisponível cai em `curto` sem abortar a
ingestão.

### Dedup

`is_seen` ([`dedup.py:26`](../clip-processor/src/dedup.py#L26)): `SET NX` em `video:<id>` no Redis com
TTL de 30 dias (`REDIS_TTL`, [`dedup.py:19`](../clip-processor/src/dedup.py#L19)). Chave já existia ⇒
visto. `RedisError` ⇒ fallback para `SELECT` em `source_videos`.

**Apagar as chaves `video:*` faz os vídeos deletados voltarem** no próximo poll. `purge_old_videos`
do sidecar apaga essas chaves de propósito ([`internal_api.py:220`](../clip-processor/src/internal_api.py#L220)),
o que faz o backlog reenchear — ver [`BUGS.md`](BUGS.md).

`mark_failed_redis` ([`dedup.py:69`](../clip-processor/src/dedup.py#L69)) está definida e **nunca é
chamada**. Efeito: download que falha deixa a chave `video:<id>` no Redis por 30 dias, então o RSS
não re-ingere o vídeo nesse período.

---

## Janela de download

O pipeline **não** baixa tudo que descobre. Ele mantém um número fixo de vídeos com arquivo em disco,
**por formato**, e as duas janelas não se canibalizam.

| Constante | Default | Env var | Onde |
|---|---|---|---|
| `DOWNLOAD_WINDOW_CURTO` | 6 | `DOWNLOAD_WINDOW_CURTO` | [`pipeline_runner.py:35`](../clip-processor/src/pipeline_runner.py#L35) |
| `DOWNLOAD_WINDOW_LONGO` | 4 | `DOWNLOAD_WINDOW_LONGO` | [`pipeline_runner.py:36`](../clip-processor/src/pipeline_runner.py#L36) |
| `FRESHNESS_DAYS` | 1 | — (constante, não é env) | [`pipeline_runner.py:41`](../clip-processor/src/pipeline_runner.py#L41) |

Nenhuma das duas `DOWNLOAD_WINDOW_*` está declarada no `docker-compose.yml`, então em produção valem
os defaults 6 e 4.

`_select_pending_videos` ([`pipeline_runner.py:44`](../clip-processor/src/pipeline_runner.py#L44)),
por formato:

1. conta a **ocupação** — quantos vídeos daquele formato ocupam a janela agora;
2. `deficit = max(0, window - occupied)`; se zero, não baixa nada daquele formato nesta rodada;
3. busca exatamente `deficit` vídeos `pending`, `paused = 0`, `DATE(published_at) >= hoje - 1 dia`,
   ordenados por `priority DESC, queue_position IS NULL, queue_position ASC, published_at DESC`.

A definição de "ocupa a janela" está em
[`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md#estados--ocupação-da-janela-de-download) — é mais
larga que "tem arquivo em disco" e é o ponto onde estado preso vira pipeline parado.

### O filtro de frescor morde

`published_at` mais velho que hoje/ontem **nunca baixa**, mesmo com a janela vazia e o backlog cheio.
Vídeo `pending` antigo fica `pending` para sempre sem ser lixo de verdade — considerar isso antes de
classificar `pending` velho como backlog descartável.

A ordenação é `published_at DESC`: a notícia mais recente ganha, não a descoberta mais antiga.

---

## Download

`download_video` ([`downloader.py:119`](../clip-processor/src/downloader.py#L119)).

| Aspecto | Valor | Onde |
|---|---|---|
| formato | `bestvideo[height<=720]+bestaudio/best`, merge em mp4 | [`:153`](../clip-processor/src/downloader.py#L153) |
| saída | `/app/videos/<video_id>.mp4` | [`:126`](../clip-processor/src/downloader.py#L126) |
| disk guard | aborta se restarem < 2 GB (`MIN_FREE_BYTES`) | [`:30`](../clip-processor/src/downloader.py#L30), [`:128`](../clip-processor/src/downloader.py#L128) |
| tentativas | 3, com 60 s entre elas | [`:162`](../clip-processor/src/downloader.py#L162) |
| erros permanentes | `private`, `removed`, `unavailable`, `geo` — sem retry | [`:31`](../clip-processor/src/downloader.py#L31), [`:177`](../clip-processor/src/downloader.py#L177) |
| abort por pause | `progress_hooks` + check entre tentativas, levanta `PauseAborted` | [`:136`](../clip-processor/src/downloader.py#L136) |

O disk guard mede o **disco real**, não o que o banco acha. Por isso órfão não limpo virava bloqueio
de download: 4 GB de `.part` esquecido derrubava o espaço livre abaixo de 2 GB e nenhum download
começava.

`download_video` retorna `bool`. `False` cobre tanto falha quanto pause — quem distingue os dois é
`_download_pending_videos`, relendo a coluna `paused`
([`pipeline_runner.py:176-186`](../clip-processor/src/pipeline_runner.py#L176)):

- pausado ⇒ volta para `pending`;
- não pausado ⇒ `_discard_failed_download`.

### `_discard_failed_download` (13/08/2026)

[`pipeline_runner.py:110`](../clip-processor/src/pipeline_runner.py#L110). Antes desta correção o
download falho só rodava `update_status(..., 'failed')`: o `.mp4` meio baixado ficava no disco e
`local_path` continuava preenchido, então a contagem da janela considerava o vídeo ocupando slot
**para sempre**. Com 58 `failed` acumulados o déficit virou 0 e o pipeline parou de baixar — 4.1 GB
presos.

A ordem do código segue a regra 2 de operações destrutivas do [`../CLAUDE.md`](../CLAUDE.md):

1. se algum clip do vídeo está em `pending_cut`/`cutting` (`_clips_need_raw`,
   [`:90`](../clip-processor/src/pipeline_runner.py#L90)), só marca `failed` e **preserva** o raw —
   ele ainda é insumo do corte;
2. senão, apaga o arquivo com caminho absoluto (`_cleanup_partial` do `queue_controls`);
3. **confere** que o arquivo saiu (`os.path.exists`);
4. só então `update_status(..., 'failed', clear_local_path=True)`.

Se a remoção falhar, `local_path` é **mantido**: banco e disco divergentes são pior que uma vaga
presa. `clear_local_path` é um parâmetro próprio de `update_status`
([`db.py:57`](../clip-processor/src/db.py#L57)) porque `local_path=None` significa "não mexe na
coluna" nas chamadas antigas.

---

## Limpeza de artefatos de download

Dois mecanismos, com escopos diferentes.

### `_cleanup_partial` — por download (no `except`)

[`downloader.py:53`](../clip-processor/src/downloader.py#L53). Globa o **prefixo sem extensão**
(`/app/videos/<video_id>.*`) e apaga o que casar com `_WORK_ARTIFACT_RE`
([`:39`](../clip-processor/src/downloader.py#L39)):

`.part`, `.part-FragN.part`, `.ytdl`, `.temp.{mp4,mkv,webm}`, `.fNNN.{mp4,webm,m4a}`

O glob é sobre o prefixo porque o yt-dlp põe o sufixo de formato **antes** do `.mp4`
(`QFDWHS3Oy3E.f298.mp4.part`). A versão antiga globava `output_path + '*.part'` e nunca casava com os
streams separados.

Existe **outro** `_cleanup_partial` em [`queue_controls.py:172`](../clip-processor/src/queue_controls.py#L172),
com assinatura e comportamento diferentes: recebe `youtube_video_id` (não um path) e apaga
exatamente `<id>.mp4`, `<id>.mp4.part` e `<id>.mp4.ytdl`. É esse que `_discard_failed_download` e
`pause_video` usam — ele apaga o `.mp4` final, o do downloader não. Não confundir os dois.

### `cleanup_stale_downloads` — varredura de órfãos

[`downloader.py:72`](../clip-processor/src/downloader.py#L72). Rede de segurança para quando
`_cleanup_partial` nunca roda: container morto, OOM, MySQL fora derrubando o processo. Nesses casos o
`except` não executa e um `.part` de 1.4 GB fica órfão indefinidamente.

- `STALE_AFTER_HOURS = 1` ([`:45`](../clip-processor/src/downloader.py#L45)) — **1 hora**, não 6.
- Só o **primeiro nível** de `/app/videos` (`clips/` e `thumbnails/` têm outro ciclo de vida).
- Só nomes que casam com `_WORK_ARTIFACT_RE` — um `<video_id>.mp4` completo nunca casa, então não há
  risco de apagar raw vivo.
- Chamada no **início** de `_download_pending_videos`
  ([`pipeline_runner.py:152`](../clip-processor/src/pipeline_runner.py#L152)), antes de ocupar disco
  novo, justamente porque o disk guard mede o disco real.

---

## Entrada manual de URL

`processar.py` ([`main`, :155](../clip-processor/src/processar.py#L155)), exposto pelo sidecar em
`POST /internal/process-url`. Enfileira a URL como `pending` — **não** bypassa o pipeline; o vídeo
ainda passa pela janela, pela IA e pelo corte normalmente.

Usa SELECT-then-INSERT em vez de `INSERT ... ON DUPLICATE KEY`
([`:88`](../clip-processor/src/processar.py#L88)) e cria o `source_channel` se ele não existir
([`:116`](../clip-processor/src/processar.py#L116)).

Exit codes: `0` ok, `2` URL inválida, `3` metadata falhou
([`:168`](../clip-processor/src/processar.py#L168), [`:177`](../clip-processor/src/processar.py#L177)).

> **Não confirmado:** se o `published_at` de uma URL manual antiga é filtrado por `FRESHNESS_DAYS`
> como qualquer outro `pending` — o código de `_select_pending_videos` não abre exceção para entrada
> manual, o que sugere que **sim**, mas não foi testado na prática.

---

## Artefatos em disco

| Padrão | Onde | Está no banco? |
|---|---|---|
| `<youtube_id>.mp4` | `videos/` | `source_videos.local_path` |
| `<youtube_id>_transcript.json` | `videos/` | `source_videos.transcript_path` |
| `<youtube_id>_audio.mp3` | `videos/` | não — temporário da transcrição, apagado no `finally` |
| `.part`, `.ytdl`, `.temp.mp4`, `.fNNN.*` | `videos/` | não — varridos após 1 h |

Artefatos de clip em [`SISTEMA-VIDEO.md`](SISTEMA-VIDEO.md#artefatos-em-disco).

**Ao cruzar banco × disco, filtrar pelo id**, nunca pelo nome do arquivo — regra 3 do
[`../CLAUDE.md`](../CLAUDE.md).
