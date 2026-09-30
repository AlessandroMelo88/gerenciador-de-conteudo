# clip-processor

> Tipo: referência as-built · Atualizado: 2026-09-29
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
| `selector.py` | seleção por janelas temporais, duração, status factual inconclusivo e anti-duplicidade |
| `video_processor.py` | corte, SRT, composição vertical, watermark e thumbnail |
| `publisher.py` | roteamento, quota, upload e finalização |
| `internal_api.py` | ponte HTTP do painel |

Os módulos editoriais e de mídia permanecem os mesmos; somente o ponto de
execução foi separado para que um render lento não segure download ou IA.

## Fluxo executado

~~~text
clip-poller       -> source_videos.pending
clip-downloader  -> source_videos.downloaded
clip-ai          -> transcribing once, selecting curto + longo -> generated_clips.pending_cut
clip-renderer    -> cutting -> generated_clips.pending
clip-publisher   -> publishing -> published
clip-maintenance -> recovery + TTL
~~~

Todos usam PostgreSQL como fila durável e o diretório compartilhado configurado
por `VIDEOS_DIR` (no Docker, `/app/videos`). Cada etapa possui uma trava Redis própria com token e TTL; uma
instância por etapa é o perfil ativo. `process_clip` ainda faz a transição
atômica `pending_cut -> cutting` como segunda proteção contra duplicidade.

## Contratos mantidos

- `PIPELINE_ENABLED=false` pausa todos os workers de negócio, mas mantém o
  sidecar e a manutenção disponíveis.
- `FRESHNESS_DAYS=1500` é fallback; cada canal-fonte configura 3 ou 1500 dias no painel.
- Uma entrada RSS vira uma fonte deduplicada, com `generate_both_formats=true`. A transcrição é
  compartilhada; o seletor cria até três Shorts e tenta um vídeo longo contínuo de pelo menos 420 s
  quando a transcrição tem material suficiente. Cada linha de `generated_clips` armazena seu formato,
  usado pelo renderer, gerador de metadados, quota e publisher.
- O processamento das seleções e dos renders segue as filas dos workers existentes; ambos os formatos
  são gerados na mesma passagem da fonte, sem iniciar duas cópias da fonte ou transcrever duas vezes.
- O gerador usa o assunto específico no título e no início da descrição, sem repetição artificial de
  palavras-chave, hashtags genéricas ou promessa de viralização. Descrições ficam abaixo de 3.500
  caracteres; caracteres ASCII rejeitados pela API são normalizados e o limite UTF-8 é verificado
  na borda do upload (5.000 bytes, incluindo créditos). Tags respeitam o teto efetivo de 500
  caracteres da API, incluindo espaços e separadores.
- Metadados ajudam a relevância em busca, mas não garantem alcance. O repositório ainda não consulta
  impressões, CTR ou retenção do YouTube Analytics para ajustar títulos, thumbnails ou seleção.
- `AI_PROVIDER=groq` usa `GROQ_CHAT_MODEL=openai/gpt-oss-20b`; outro provider precisa ser configurado e ativado explicitamente.
- Shorts duram de 30 a 45 segundos por padrão. `SHORTS_MAX_DURATION_SECONDS`
  permite configurar um teto maior para testes.
- `MAX_UPLOADS_PER_DAY=6`, `MAX_LONGO_UPLOADS_PER_DAY=3` e
  `MAX_CURTO_UPLOADS_PER_DAY=3` são aplicados por destino. Longos são liberados
  às 06h, 14h e 22h; Shorts às 12h e 20h, no horário de São Paulo.
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

## Workers diretos no Linux/macOS

O mesmo pipeline pode rodar no host com cron, sem Docker para os workers. A
configuração de serviços, diretórios, horários, logs e remoção segura do bloco
de cron está em [EXECUCAO-NATIVA-CRON.md](EXECUCAO-NATIVA-CRON.md).
