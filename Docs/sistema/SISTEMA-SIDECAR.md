# Sidecar HTTP interno

> Tipo: referência as-built · Atualizado: 2026-08-26
> Fonte: `clip-processor/src/internal_api.py` e
> `painel/app/Services/ClipProcessorClient.php`

O sidecar Flask escuta `0.0.0.0:8090` somente na rede Docker interna. Não há porta 8090
publicada no host.

## Autenticação

- `/health` é público e retorna `{"status":"ok"}`;
- todas as rotas `/internal/*` operacionais exigem `X-Internal-Token`;
- token vazio ou diferente de `CLIP_PROCESSOR_INTERNAL_TOKEN` falha fechado com HTTP 401;
- o painel usa o mesmo token via `services.clip_processor.token`;
- o processador autentica eventos enviados de volta ao painel com o mesmo header.

## Rotas do processador

| Método | Rota | Entrada | Efeito |
|---|---|---|---|
| POST | `/internal/resolve-channel` | `url` | resolve ID, nome e handle com yt-dlp; não baixa |
| POST | `/internal/process-url` | `url`, `format` | insere fonte `pending`; scheduler faz o resto |
| POST | `/internal/transcribe` | `url` | cria job de transcrição local e retorna `job_id` |
| POST | `/internal/reject-clip` | `clip_id` | rejeita `pending`/`approved` e remove MP4 final |
| POST | `/internal/delete-source-video` | `source_video_id` | remove arquivos associados e zera caminhos |
| POST | `/internal/purge-old-videos` | `before_date` | purga fontes antigas de acordo com guards |
| POST | `/internal/videos/{id}/pause` | — | pausa fonte e aborta trabalho quando possível |
| POST | `/internal/videos/{id}/resume` | — | retoma fonte |
| POST | `/internal/videos/reorder` | `ids[]` | grava `queue_position` |
| POST | `/internal/videos/{id}/prioritize` | — | aumenta `priority` |

Respostas usam JSON. Validação de entrada retorna 400; guards de operação normalmente retornam
422; falha inesperada retorna 500. `reject-clip` e `process-url` devolvem HTTP 200 com
`exit_code`, inclusive quando a operação reporta rejeição.

## Guards de destruição

`delete-source-video` verifica se o vídeo existe e se nenhum clip está em
`pending_cut` ou `cutting`. Remove MP4s finais/intermediários, thumbnails, raw,
transcrição e artefatos de download, mas preserva as linhas de banco e os clips.

`purge-old-videos`:

- apaga linhas antigas em `pending`, `failed` ou `downloaded` sem
  clips;
- remove raw de fontes antigas que não precisam mais dele;
- remove dedup Redis das linhas apagadas;
- não toca em fonte baixando/cortando nem em raw necessário a
  `pending_cut`/`cutting`.

A operação pode tocar muitos registros; liste o alvo e faça backup antes de executar.

## Controles da fila

`pause`:

- marca `paused=true`;
- em download, mata yt-dlp, remove parciais e volta para `pending`;
- em transcrição/seleção, mantém pausa cooperativa;
- em corte, mata FFmpeg quando possível e volta clips para `pending_cut`.

`resume` limpa a flag. `reorder` e `prioritize` alteram somente
ordenação, não executam o vídeo imediatamente.

## Eventos no sentido inverso

O processador faz POST para `LARAVEL_NOTIFY_URL` (padrão
`http://nginx/internal/pipeline-event`) com:

~~~json
{
  "event": "upload_published",
  "payload": {}
}
~~~

Eventos aceitos: `upload_published`, `pipeline_failure`,
`clip_ttl_warning` e `daily_summary`. O painel exige o mesmo token, formata a
mensagem e envia ao Telegram. A chamada é best-effort: falha de rede não derruba o pipeline.

O webhook `/telegramcanal` é uma entrada separada: exige
`X-Telegram-Bot-Api-Secret-Token` e allowlist de chat; não é uma rota do sidecar.

## Diagnóstico

~~~bash
docker compose ps
docker compose logs --tail=100 clip-processor
curl http://localhost:8090/health
~~~

O último comando só funciona se a porta for publicada manualmente; em operação normal use o painel
ou execute dentro da rede/container.
