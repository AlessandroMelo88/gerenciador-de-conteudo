# clip-processor

> Tipo: referência as-built · Atualizado: 2026-08-27
> Código: `clip-processor/src`

Daemon Python responsável por todo o pipeline e pelo sidecar HTTP. A imagem copia o código e o
Compose atual monta `clip-processor/src` em `/app/src`; alterações Python exigem restart do
serviço, enquanto mudanças de dependências ou do Dockerfile exigem rebuild.

## Mapa de módulos

| Módulo | Responsabilidade |
|---|---|
| `main.py` | scheduler, boot, recovery, sidecar e `PIPELINE_ENABLED` |
| `pipeline_runner.py` | ciclos, janela de download e descarte seguro de falhas |
| `rss_poller.py` | RSS, dedup, classificação, transcrição, seleção e render pendente |
| `dedup.py` | Redis `SET NX` + fallback PostgreSQL |
| `downloader.py` | yt-dlp, retry, disk guard e limpeza de parciais |
| `transcriber.py` | legendas manuais PT-BR + Groq Whisper |
| `transcription_job.py` | transcrição local assíncrona com whisper.cpp |
| `selector.py` | prompts, seleção, fact-check, duração, bordas e duplicidade |
| `prompt_profiles.py` | normalização e compatibilidade dos perfis de prompt do PostgreSQL |
| `fact_check_prompt.py` | instruções factuais compartilhadas |
| `metadata_generator.py` | título, descrição, tags e `thumbnail_text` |
| `video_processor.py` | corte, SRT, legenda queimada, watermark e thumbnail |
| `subtitle_detector.py` | OCR do rodapé × transcrição para não legendar o que já vem legendado |
| `video_quality.py` | opções comuns de encoder |
| `media_assets.py` | resolução de assets filesystem/DB |
| `media_composer.py` | intro, conteúdo, outro, música e card relacionado |
| `related_video.py` | link e thumbnail de vídeo relacionado |
| `publisher.py` | elegibilidade, roteamento, quota, upload e finalização |
| `quota_manager.py` | quota Redis, janela 19:00–22:00 e reserva de longos |
| `uploader.py` | YouTube Data API, legenda oficial, HD, privacidade e thumbnail |
| `youtube_oauth.py` | geração de token por canal-destino |
| `queue_controls.py` | pause, resume, reorder, prioritize e guards de raw |
| `rejeitar.py` | rejeição de clip e remoção do MP4 final |
| `internal_api.py` | sidecar Flask autenticado |
| `ttl_worker.py` | alerta/rejeição por TTL |
| `telegram_notifier.py` | eventos do processador para o Laravel |
| `db.py` | conexão, status, inserção e recovery |
| `processar.py` | ingestão manual de URL |

## Ciclo executado

~~~text
main.py
 ├─ run_ingest_cycle (20 min)
 │   ├─ rss_poller.poll_all_channels
 │   │   ├─ RSS + dedup + insert pending
 │   │   ├─ downloaded → transcribe → resolve perfil → select
 │   │   └─ pending_cut → process_clip
 │   └─ pipeline_runner._download_pending_videos
 ├─ run_publish_only (20 min)
 │   └─ publisher.publish_pending_clips
 ├─ run_ttl_once (1 h)
 └─ run_recovery_once (30 min)
~~~

No boot, `run_pipeline_once` executa ingestão e publicação imediatas. O scheduler usa
`America/Sao_Paulo`, `max_instances=1` e `coalesce=true`.

## Contratos internos

- cada função de produção pode abrir sua própria conexão PostgreSQL;
- testes injetam conexão, Redis e clientes de IA;
- funções de estágio registram logs em stdout;
- falhas de canal/clip são isoladas quando possível;
- a fila usa status no PostgreSQL;
- caminhos de arquivo são absolutos dentro do container;
- notificações são best-effort.

## Dados e Redis

Tabelas centrais: `source_channels`, `source_videos`,
`generated_clips`, `destination_channels`, `prompt_profiles`, `media_assets`,
`transcription_jobs` e `niches`.

O canal-fonte fornece o perfil da seleção. O canal-destino fornece o perfil de metadata e
thumbnail; a inserção de momentos procura destino com o mesmo `prompt_profile_id`. Perfis ativos
incompatíveis com o nicho são descartados, e linhas legadas sem perfil usam somente o fallback
compatível por nicho.

Redis guarda:

- `video:<youtube_id>`: dedup, TTL 30 dias;
- `youtube_uploads:*`: quota;
- `clip_warned:<id>`: alerta TTL idempotente.

Não use Redis como fila e não use `FLUSHALL` para destravar o pipeline.

## Configuração importante

| Variável | Uso |
|---|---|
| `PIPELINE_ENABLED` | pausa ingestão/publicação sem desligar sidecar |
| `GROQ_API_KEY` | Whisper e fallback/uso normal de LLM |
| `ANTHROPIC_API_KEY` | caminho Anthropic da seleção/metadata/thumbnail |
| banco `prompt_profiles` | prompts editoriais por nicho/canal; seed em migration |
| `DOWNLOAD_WINDOW_CURTO/LONGO` | ocupação máxima por formato |
| `FRESHNESS_DAYS` | idade aceita para download automático |
| `MANUAL_APPROVAL_REQUIRED` | `pending` direto ou aprovação |
| `BURNED_SUBTITLE_DETECTION` | habilita OCR para evitar queimar legenda já gravada; padrão `true` |
| `MAX_UPLOADS_PER_DAY` | quota total, clamp de 0 a 6 |
| `YOUTUBE_WAIT_FOR_HD` | espera de processamento antes de visibilidade final |
| `YOUTUBE_PROCESSING_TIMEOUT_SECONDS` | limite da espera HD; padrão 900 |
| `YOUTUBE_PROCESSING_POLL_SECONDS` | intervalo de consulta ao YouTube; padrão 10 |
| `CLIP_PROCESSOR_INTERNAL_TOKEN` | autenticação do sidecar/eventos |

## Onde alterar

- prompts: [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md);
- estados: [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md);
- publicação: [`SISTEMA-PUBLICACAO.md`](SISTEMA-PUBLICACAO.md);
- mídia: [`SISTEMA-VIDEO.md`](SISTEMA-VIDEO.md);
- operações HTTP: [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md);
- banco: [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md).

Para alterar Python no Compose atual:

~~~bash
docker compose restart clip-processor
~~~

Se mudar Dockerfile, dependências ou pacotes do sistema, faça rebuild:

~~~bash
docker compose up -d --build clip-processor
~~~
