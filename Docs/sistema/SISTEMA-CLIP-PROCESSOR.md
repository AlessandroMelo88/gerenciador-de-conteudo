# clip-processor

> Tipo: referência as-built · Atualizado: 2026-09-02
> Código: `clip-processor/src`

O processador é dividido por etapa no Compose. O container `clip-processor`
serve somente o sidecar HTTP autenticado; os serviços `clip-poller`,
`clip-downloader`, `clip-ai`, `clip-renderer`, `clip-publisher` e
`clip-maintenance` executam o pipeline em processos separados.

## Mapa de módulos

| Módulo | Responsabilidade |
|---|---|
| `worker.py` | loop, sinais e locks Redis por etapa |
| `sidecar.py` | entrypoint Flask sem pipeline |
| `rss_poller.py` | descoberta, dedup e funções de drenagem de IA/render |
| `pipeline_runner.py` | janela e download das fontes |
| `db.py` | conexão, status, inserção e recovery |
| `downloader.py` | yt-dlp, retry, disk guard e parciais |
| `transcriber.py` | legendas manuais PT-BR + Groq Whisper |
| `selector.py` | seleção, duração, fact-check e anti-duplicidade |
| `video_processor.py` | corte, SRT, composição vertical, watermark e thumbnail |
| `publisher.py` | roteamento, quota, upload e finalização |
| `internal_api.py` | ponte HTTP do painel |

Os módulos editoriais e de mídia permanecem os mesmos; somente o ponto de
execução foi separado para que um render lento não segure download ou IA.

## Fluxo executado

~~~text
clip-poller       -> source_videos.pending
clip-downloader  -> source_videos.downloaded
clip-ai          -> transcribing/selecting -> generated_clips.pending_cut
clip-renderer    -> cutting -> generated_clips.pending
clip-publisher   -> publishing -> published
clip-maintenance -> recovery + TTL
~~~

Todos usam PostgreSQL como fila durável e o volume compartilhado
`/app/videos`. Cada etapa possui uma trava Redis própria com token e TTL; uma
instância por etapa é o perfil ativo. `process_clip` ainda faz a transição
atômica `pending_cut -> cutting` como segunda proteção contra duplicidade.

## Contratos mantidos

- `PIPELINE_ENABLED=false` pausa todos os workers de negócio, mas mantém o
  sidecar e a manutenção disponíveis.
- `AUTO_INGEST_FORMAT=curto` mantém o destino Hacker Libertário no contrato de
  Shorts: 9:16, 1080×1920 e 30 segundos exatos.
- `MAX_UPLOADS_PER_DAY=6` e `MIN_UPLOAD_INTERVAL_MINUTES=60` permanecem
  aplicados por destino; publicação não é paralelizada.
- o worker de IA recupera `transcribing` antigo para `downloaded` quando há raw;
  sem raw, marca `failed` depois de duas horas.
- o renderer recupera `cutting` somente no boot, nunca durante um encode ativo.

## Operação

~~~bash
docker compose ps
docker compose logs -f clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
docker compose exec -T clip-processor python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8090/health').read().decode())"
~~~

Após alteração em Python, recrie todos os processos do pipeline:

~~~bash
docker compose up -d --force-recreate clip-processor clip-poller clip-downloader clip-ai clip-renderer clip-publisher clip-maintenance
~~~

Mudanças no Dockerfile, dependências ou pacotes do sistema exigem `--build`.
Não use `FLUSHALL` para destravar a fila; investigue o status no PostgreSQL e
a chave Redis específica da etapa.
