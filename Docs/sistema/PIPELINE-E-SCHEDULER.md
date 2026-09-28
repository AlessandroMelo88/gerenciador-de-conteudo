# Pipeline e workers

> Tipo: referência as-built · Atualizado: 2026-09-02
> Fonte: `clip-processor/src/worker.py`, `rss_poller.py` e `docker-compose.yml`

## Deployment atual

O Compose separa o processamento em um container HTTP e seis workers:

| Serviço | Etapa | Cadência padrão | Cardinalidade |
|---|---|---:|---:|
| `clip-processor` | sidecar HTTP do painel | contínuo | 1 |
| `clip-poller` | descoberta RSS/yt-dlp e deduplicação | 20 min | 1 |
| `clip-downloader` | download dos vídeos fonte | 30 s | 1 |
| `clip-ai` | transcrição + seleção de momentos | 10 s | 1 |
| `clip-renderer` | corte vertical 1080×1920, legenda e metadata | 10 s | 1 |
| `clip-publisher` | upload e publicação no YouTube | 10 min | 1 |
| `clip-maintenance` | recovery e TTL | 30 min | 1 |

Cada worker abre sua própria conexão PostgreSQL, compartilha somente o volume de
vídeos e usa uma chave Redis exclusiva (`lock:pipeline_stage:<etapa>`). O
renderer pode executar enquanto poller, downloader e IA avançam nas filas.
O `clip-processor` deixou de iniciar o scheduler legado: ele serve apenas o
sidecar em `0.0.0.0:8090`.

Com `PIPELINE_ENABLED=false`, o sidecar continua disponível e apenas o worker
de manutenção segue ativo.

## Contratos de fila

As tabelas PostgreSQL continuam sendo a fila durável:

~~~text
source_videos.pending       -> clip-downloader -> downloaded
source_videos.downloaded    -> clip-ai        -> selecting + generated_clips.pending_cut
generated_clips.pending_cut -> clip-renderer   -> pending
generated_clips.pending     -> clip-publisher  -> published
~~~

`process_clip` mantém a transição atômica `pending_cut -> cutting`, então um
render não duplica o mesmo clip. A publicação continua singleton por destino,
com quota diária e `MIN_UPLOAD_INTERVAL_MINUTES=60`.

As cadências podem ser sobrescritas por serviço com `WORKER_INTERVAL_SECONDS`.
O lock por etapa tem TTL configurável em `WORKER_LOCK_TTL_SECONDS` e a liberação
usa token, evitando que um worker antigo apague a trava de outro processo.

## Ordem e paralelismo

O poller executa somente descoberta. Ele não faz transcrição, seleção nem
renderização. Isso permite o seguinte fluxo simultâneo:

1. `clip-poller` insere novas fontes `pending`;
2. `clip-downloader` repõe as janelas de download por formato;
3. `clip-ai` drena fontes baixadas;
4. `clip-renderer` drena clips selecionados;
5. `clip-publisher` publica respeitando cota e cadência.

Falha em uma etapa não impede as demais; o próximo worker retoma pelo status
persistido. O `poll_all_channels` legado continua disponível para testes e
execuções manuais, com flags para desabilitar IA e cortes.

## Recovery

O recovery periódico não toca em `cutting` porque um render legítimo pode durar
mais que 30 minutos. A rotina de boot do `clip-renderer` recebe
`recover_cutting=true` porque, após reiniciar o processo, não há FFmpeg antigo
válido.

| Estado | Ação |
|---|---|
| fonte `downloading` | volta para `pending` |
| fonte `transcribing` | volta para `downloaded` após 2h se houver raw; sem raw vai para `failed` |
| fonte `selecting` com raw | volta para `downloaded` após o limite |
| fonte `selecting` sem raw | vai para `failed` após o limite |
| clip `publishing` sem update por 15 min | volta para `pending` |
| clip `cutting` no boot do renderer | volta para `pending_cut` |

## Alteração e deploy

O Dockerfile copia os entrypoints e o Compose monta
`./clip-processor/src:/app/src`. Após mudar Python, recrie o sidecar e os workers:

~~~bash
docker compose up -d --force-recreate clip-processor clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
~~~

Faça rebuild quando mudar Dockerfile, dependências ou pacotes do sistema:

~~~bash
docker compose up -d --build clip-processor clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
~~~

Não é necessário reiniciar PostgreSQL ou Redis para uma alteração somente no processador.
