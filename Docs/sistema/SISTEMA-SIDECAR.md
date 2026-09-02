# Sidecar HTTP e controles de fila

A ponte painel → pipeline. Cobre `internal_api.py`, `queue_controls.py`, `rejeitar.py` e
`telegram_notifier.py`.

A visão conceitual da fronteira painel ↔ pipeline está em
[`../ARCHITECTURE.md`](../ARCHITECTURE.md) seção 3; o lado Laravel em
[`SISTEMA-PAINEL.md`](SISTEMA-PAINEL.md).

Verificado no código em **13/08/2026**.

---

## A regra

- Para **ler**, o painel vai direto na fonte (MySQL, Redis, disco).
- Para **agir sobre disco ou processo**, o painel **nunca** toca o filesystem do pipeline — chama o
  sidecar HTTP em `clip-processor:8090`.
- **Exceção:** transição de status simples o painel escreve direto no MySQL (ex.: `approve()` faz
  `UPDATE generated_clips SET status='approved'`).

Isso substituiu o padrão anterior de `docker exec` / socket do Docker.

**Consequência operacional:** o sidecar roda numa thread do **mesmo processo** do pipeline
([`main.py:159`](../clip-processor/src/main.py#L159)). Parar o container para mexer no pipeline derruba
o sidecar junto — o painel continua abrindo, mas "Apagar arquivo", "Purgar antigos", "Processar URL",
"Resolver canal" e os controles de fila passam a falhar.

---

## Rede e autenticação

Flask em `0.0.0.0:8090`, **sem porta publicada** — o serviço `clip-processor` no
`docker-compose.yml` não declara `ports`, então a 8090 só é alcançável pela rede docker `internal`.

Autenticação por token compartilhado no header `X-Internal-Token`, comparado com
`CLIP_PROCESSOR_INTERNAL_TOKEN` ([`internal_api.py:34`](../clip-processor/src/internal_api.py#L34)):

```python
return bool(INTERNAL_TOKEN) and request.headers.get('X-Internal-Token') == INTERNAL_TOKEN
```

É **fail-closed**: env var vazia ⇒ `bool('')` é falso ⇒ **toda rota responde 401**. Se o painel
começar a dar erro em todas as ações que passam pelo sidecar de uma vez, checar essa env var antes de
qualquer outra coisa.

`INTERNAL_TOKEN` é lido no **import do módulo** ([`:27`](../clip-processor/src/internal_api.py#L27)) —
mudar a env var exige restart do container, não só do painel.

**Não há rota de health check.** Não existe um `GET /internal/ping` para o painel saber se o sidecar
está vivo antes de tentar a ação.

---

## Rotas

Todas `POST`, todas com o mesmo check de auth no início.

| Rota | Body | Retorno | Códigos de erro |
|---|---|---|---|
| `/internal/resolve-channel` ([`:271`](../clip-processor/src/internal_api.py#L271)) | `{url}` | `{channel_id, channel_name, channel_handle}` | 422 se yt-dlp falhar |
| `/internal/process-url` ([`:301`](../clip-processor/src/internal_api.py#L301)) | `{url, format}` | `{exit_code}` — 0 ok, 2 URL inválida, 3 metadata falhou | 400 sem url, 500 |
| `/internal/reject-clip` ([`:286`](../clip-processor/src/internal_api.py#L286)) | `{clip_id}` | `{exit_code}` — 0 ok, 1 inexistente, 2 status inválido | 400, 500 |
| `/internal/delete-source-video` ([`:317`](../clip-processor/src/internal_api.py#L317)) | `{source_video_id}` | `{deleted..., freed_bytes}` | **422 se o arquivo estiver em uso** |
| `/internal/purge-old-videos` ([`:256`](../clip-processor/src/internal_api.py#L256)) | `{before_date}` | `{deleted_rows, freed_bytes}` | 400, 500 |
| `/internal/transcribe` ([`:332`](../clip-processor/src/internal_api.py#L332)) | `{url}` | `{job_id}` | 400, 500 |
| `/internal/videos/<id>/pause` ([`:347`](../clip-processor/src/internal_api.py#L347)) | — | `{paused, status, actions}` | 422 se não existir |
| `/internal/videos/<id>/resume` ([`:361`](../clip-processor/src/internal_api.py#L361)) | — | `{paused, status}` | 422 |
| `/internal/videos/reorder` ([`:375`](../clip-processor/src/internal_api.py#L375)) | `{ids: [...]}` | `{reordered}` | 400 lista vazia, 422 |
| `/internal/videos/<id>/prioritize` ([`:393`](../clip-processor/src/internal_api.py#L393)) | — | `{priority}` | 422 |

`resolve_channel` ([`:37`](../clip-processor/src/internal_api.py#L37)) roda
`yt-dlp --flat-playlist --skip-download --playlist-items 1 --dump-single-json <url>`, timeout 30 s,
**zero cota da YouTube Data API**. O `--playlist-items 1` é essencial: sem ele, uma URL de canal faz o
yt-dlp paginar todas as abas (videos/streams/shorts) antes de retornar, estourando o timeout em canais
grandes.

---

## As duas rotas que apagam

Distinção que já custou confusão: **uma apaga arquivo, a outra apaga linha do banco.**

### `delete_source_video_file` — só disco

[`internal_api.py:80`](../clip-processor/src/internal_api.py#L80). Cascata em disco de um vídeo: o
`.mp4` bruto, os clips gerados, as thumbnails e os parciais. Depois zera `local_path`.
**A linha do banco permanece.**

Antes de apagar, consulta `can_delete_raw` ([`queue_controls.py:152`](../clip-processor/src/queue_controls.py#L152)),
que recusa em dois casos:

1. `source_videos.status` em `('downloading', 'cutting')`;
2. existe clip do vídeo em `pending_cut` ou `cutting` (`_CLIP_STATUSES_NEED_RAW`,
   [`:10`](../clip-processor/src/queue_controls.py#L10)).

> ⚠️ **O primeiro caso é letra morta:** nenhum código escreve `cutting` em `source_videos` (ver
> [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md#cutting-e-publishing-em-source_videos-valores-mortos)).
> Só o **segundo** caso protege de verdade. Ao apagar raw por fora do painel, checar
> `generated_clips.status` na mão.

### `purge_old_videos` — apaga linha

[`internal_api.py:171`](../clip-processor/src/internal_api.py#L171). **Única ação do sistema que apaga
linha de `source_videos`**, e só por data (`before_date`).

**Também apaga as chaves Redis `video:<id>` de dedup**
([`:220`](../clip-processor/src/internal_api.py#L220)). Consequência: os vídeos purgados deixam de
estar "vistos" e **voltam a ser inseridos como `pending`** no próximo poll RSS. Não voltam a baixar
(`FRESHNESS_DAYS=1` barra publicado antes de ontem), mas o contador de backlog reenche.

Purgar trata o sintoma; a causa é o RSS ingerir mais do que a janela consome.

---

## Controles de fila

[`queue_controls.py`](../clip-processor/src/queue_controls.py). O pause é **cooperativo**: a coluna
`source_videos.paused` é uma bandeira que os workers consultam entre etapas
(`is_paused`, [`:21`](../clip-processor/src/queue_controls.py#L21)).

`pause_video` ([`:34`](../clip-processor/src/queue_controls.py#L34)) faz mais que setar a flag; age
conforme o estado atual:

| Estado ao pausar | Ação | `actions` retornado |
|---|---|---|
| `downloading` | `pkill -f 'yt-dlp.*<video_id>'`, volta para `pending`, zera `local_path`, `_cleanup_partial` | `download_aborted` |
| `transcribing` / `selecting` | nada além da flag — o worker checa entre etapas | `cooperative_hold` |
| qualquer, com clip em `cutting` | `pkill` do ffmpeg, clip volta para `pending_cut` | `clip_<id>_cut_aborted` |

Os `pkill` são best-effort ([`:187`](../clip-processor/src/queue_controls.py#L187),
[`:200`](../clip-processor/src/queue_controls.py#L200)) — `check=False`, exceção só gera log. O yt-dlp
roda **in-process** (`YoutubeDL`), então quem realmente aborta o download é o `progress_hook`
levantando `PauseAborted`, não o `pkill`.

`resume_video` ([`:96`](../clip-processor/src/queue_controls.py#L96)) só zera a flag — **não** reverte
nada que o pause tenha desfeito. Vídeo pausado durante o download volta a `pending` e recomeça do zero.

| Função | O que faz |
|---|---|
| `reorder_videos` ([`:114`](../clip-processor/src/queue_controls.py#L114)) | grava `queue_position` = índice na lista recebida |
| `prioritize_video` ([`:132`](../clip-processor/src/queue_controls.py#L132)) | `priority = MAX(priority) + 1` — cada chamada escala o contador global |

`prioritize_video` não tem teto: chamado muitas vezes, `priority` só cresce. Não é bug, mas explica
valores altos na coluna.

---

## Rejeição de clip

`rejeitar` ([`rejeitar.py:38`](../clip-processor/src/rejeitar.py#L38)), exposto em
`/internal/reject-clip`.

1. `SELECT clip_path, status`; não existe ⇒ exit 1;
2. status fora de `('pending', 'approved')` ⇒ exit 2 (terminal ou em trânsito);
3. `UPDATE ... SET status='rejected' WHERE id=%s AND status IN ('pending','approved')`
   ([`:77`](../clip-processor/src/rejeitar.py#L77)) — guard de corrida;
4. se afetou linha e `clip_path` existe, `os.remove(clip_path)`
   ([`:87`](../clip-processor/src/rejeitar.py#L87)).

**Apaga o MP4 final e preserva o raw do vídeo fonte** — decisão explícita, para permitir recortar
outro trecho do mesmo vídeo depois. Não apaga a thumbnail nem o `.srt`, e não zera `clip_path` no
banco: mais uma origem da divergência "coluna preenchida, arquivo ausente".

---

## Caminho inverso: eventos para o Telegram

`telegram_notifier.notify` ([`telegram_notifier.py:37`](../clip-processor/src/telegram_notifier.py#L37))
faz `POST {"event": ..., "payload": {...}}` em `LARAVEL_NOTIFY_URL`
(default `http://nginx/internal/pipeline-event`), timeout 5 s, com o header
`Host: LARAVEL_HOST_HEADER` (default `canaldecortes.local`) e o **mesmo** `X-Internal-Token`.

O header `Host` é **obrigatório**: sem ele o nginx serve o `default_server` em vez do vhost
`canaldecortes.local` e o evento se perde num 404 de outro projeto.

O token do Telegram fica centralizado no Laravel — o pipeline não conhece o bot.

| Evento | Disparado por |
|---|---|
| `upload_published` | [`publisher.py:190`](../clip-processor/src/publisher.py#L190), [`:225`](../clip-processor/src/publisher.py#L225) |
| `pipeline_failure` | cada estágio de `pipeline_runner.py` (`stage`, `error_msg` truncado em 500) |
| `clip_ttl_warning` | [`ttl_worker.py`](../clip-processor/src/ttl_worker.py) |
| `daily_summary` | `Schedule::call()` do Laravel (18h BRT), não do pipeline |

**Best-effort:** falha ali nunca propaga para o pipeline. Ausência de notificação no Telegram não é
prova de que o pipeline não rodou.
