# PROJECT_BRIEF — Canal de Cortes

> Tipo: resumo executivo as-built · Atualizado: 2026-08-26

## Objetivo

Monitorar canais do YouTube, transformar vídeos em cortes curtos ou longos com IA e publicar em
canais de destino, com fila persistente, quotas, aprovação opcional e painel de operação.

## Fluxo

~~~text
RSS/URL → PostgreSQL → download → transcrição → seleção IA → FFmpeg
→ metadata/thumbnail → aprovação opcional → quota/OAuth → YouTube
~~~

## Stack

| Camada | Tecnologia |
|---|---|
| Processador | Python, APScheduler, yt-dlp, FFmpeg, psycopg2, Redis |
| IA | Anthropic Claude, Groq Whisper e Groq LLM |
| Painel | Laravel 13, Inertia, React 19, TypeScript, Tailwind 4, shadcn/ui |
| Dados | PostgreSQL 16 + migrations Laravel; Redis 7 auxiliar |
| Deploy local | Docker Compose, PHP-FPM, Nginx |

## Regras de negócio

- fonte menor que 420 s → `curto`; fonte a partir de 420 s → `longo`;
- `curto`: até 3 trechos, 30–180 s, vertical, com legenda oficial e legenda queimada — a queima é
  dispensada quando o vídeo fonte já traz legenda gravada no quadro;
- `longo`: 1 trecho, 420–1200 s, horizontal, com legenda oficial sem queimar e intro/outro/música;
- publicidade, duplicidade, cortes sem contexto e score abaixo de 7 são rejeitados;
- nicho da fonte roteia para destinos compatíveis;
- aprovação manual é controlada por `MANUAL_APPROVAL_REQUIRED`;
- quota padrão: até 2 uploads/dia por destino, teto de 6; janela padrão 19:00–22:00;
- clips pendentes expiram por TTL configurável; alertas são idempotentes via Redis.

## Código-chave

- pipeline: `clip-processor/src/main.py`, `pipeline_runner.py`, `rss_poller.py`;
- IA: `selector.py`, `fact_check_prompt.py`, `metadata_generator.py`;
- mídia: `video_processor.py`, `media_composer.py`, `media_assets.py`;
- publicação: `publisher.py`, `uploader.py`, `youtube_oauth.py`;
- operação: `internal_api.py`, `queue_controls.py`, `ttl_worker.py`;
- dados: `painel/database/migrations/`.

## Referências

- arquitetura: [`ARCHITECTURE.md`](ARCHITECTURE.md);
- índice: [`Docs/README.md`](Docs/README.md);
- prompts: [`Docs/SISTEMA-IA-SELECAO.md`](Docs/SISTEMA-IA-SELECAO.md);
- operação: [`Docs/RUNBOOK.md`](Docs/RUNBOOK.md);
- desenvolvimento: [`Docs/DESENVOLVIMENTO.md`](Docs/DESENVOLVIMENTO.md).
