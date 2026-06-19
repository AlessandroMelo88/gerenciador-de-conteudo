---
phase: 06-controle-manual-n8n-telegram
plan: 04
subsystem: api

tags: [telegram, n8n, yt-dlp, mysql, regex, idempotency, manual-ingest, ctrl-04]

requires:
  - phase: 06-controle-manual-n8n-telegram
    provides: "Plan 06-01 — stub processar.py (YOUTUBE_URL_RE + assinaturas) + test_processar.py em RED + ENUM source_videos com status='pending'"
  - phase: 02-aquisicao-de-videos
    provides: "db.py (get_db_connection), pymysql DictCursor, schema source_videos/source_channels com FK channel_id"
provides:
  - "parse_video_id(url) — extrai ID 11 chars de URLs canônicas (watch?v=, youtu.be, /shorts, /embed, /v)"
  - "fetch_metadata(video_id) — yt-dlp metadata-only (skip_download=True, sem quota YouTube Data API)"
  - "upsert_source_video(conn, meta) — SELECT-then-INSERT idempotente, retorna (status, created)"
  - "_normalize_upload_date — converte 'YYYYMMDD' (yt-dlp) para 'YYYY-MM-DD HH:MM:SS' (TIMESTAMP MySQL)"
  - "main(url) — CLI entrypoint com exit codes (0=ok, 2=url inválida, 3=metadata falhou)"
  - "Pseudo-channel automático (active=FALSE) quando canal de origem não está em source_channels"
affects: [06-07-n8n-flows]

tech-stack:
  added: []
  patterns:
    - "yt-dlp metadata-only com skip_download=True para extrair info de vídeo sem consumir quota nem baixar mídia"
    - "SELECT-then-INSERT em vez de INSERT...ON DUPLICATE KEY: necessário para retornar status atual ao chamador"
    - "Pseudo-channel manual:UCxxx com active=FALSE — preserva FK quando vídeo vem de canal fora do pool RSS"
    - "Exit codes CLI (2=input inválido, 3=metadata externa falhou) — n8n router roteia mensagem de erro amigável por código"

key-files:
  created: []
  modified:
    - clip-processor/src/processar.py

key-decisions:
  - "Pseudo-channel manual:UCxxx com active=FALSE preserva FK quando vídeo manual vem de canal fora do pool RSS — RSS poller não vai polar, mas FK fica válida"
  - "SELECT-then-INSERT (não INSERT...ON DUPLICATE KEY): necessário para retornar (status_atual, created_bool) ao chamador para mensagem Telegram"
  - "Novo vídeo manual entra como status='pending' (não bypassa pipeline) — daemon APScheduler cuida do resto: download → transcribe → select → cut → publishing"
  - "fetch_metadata captura Exception genérica de yt-dlp (DownloadError, ExtractorError, etc.) e retorna exit code 3 — Plan 06-07 deve mostrar erro amigável (vídeo privado/region-locked/inexistente)"
  - "_normalize_upload_date converte 'YYYYMMDD' do yt-dlp para 'YYYY-MM-DD HH:MM:SS' do TIMESTAMP MySQL; aceita None (coluna permite NULL)"
  - "Título truncado em 500 chars coerente com schema VARCHAR(500) de source_videos.title"
  - "main usa try/finally para garantir conn.close() mesmo se upsert lançar"

patterns-established:
  - "Phase 6 CLI entrypoints (processar, rejeitar): __main__ guard + sys.exit(main(...)) — chamáveis via docker exec por n8n executeCommand"
  - "yt-dlp metadata-only via YoutubeDL({'skip_download': True}).extract_info(url, download=False) — sem consumo de quota YouTube Data API"
  - "Operações idempotentes Phase 6: SELECT antes de INSERT para podermos retornar o estado pré-existente ao chamador"

requirements-completed: [CTRL-04]

duration: 7min
completed: 2026-06-19
---

# Phase 6 Plan 04: /processar — ingestão manual de vídeo YouTube via Telegram

**`processar.py` implementado com regex YouTube canônico, yt-dlp metadata-only (skip_download=True), upsert idempotente em source_videos como status='pending' e pseudo-channel automático com active=FALSE para canais fora do pool RSS.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-06-19T20:17:00Z
- **Completed:** 2026-06-19T20:24:58Z
- **Tasks:** 1 (auto, tdd=true)
- **Files modified:** 1 (clip-processor/src/processar.py)

## Accomplishments

- **parse_video_id**: regex unificado cobre 5 formatos canônicos (watch?v=, youtu.be, /shorts, /embed, /v). 11 chars `[A-Za-z0-9_-]`. URLs malformadas retornam None.
- **fetch_metadata**: yt-dlp scrapa página pública (skip_download=True, sem download de mídia, sem consumo de quota YouTube Data API). Retorna dict com youtube_video_id, title (trunc 500), channel_id (UC...), published_at normalizado.
- **upsert_source_video**: SELECT-then-INSERT idempotente. Resolve/cria channel_id interno (FK). Vídeo novo entra com status='pending'. Vídeo existente retorna status atual sem mexer.
- **Pseudo-channel automático**: se `meta['channel_id']` não está em `source_channels`, cria linha com `channel_name='manual:UCxxx'`, `rss_url` derivada, `active=FALSE` — RSS poller ignora, FK fica válida.
- **main**: CLI entrypoint com exit codes (0=ok, 2=URL inválida, 3=metadata yt-dlp falhou). try/finally garante `conn.close()`.
- **7/7 testes GREEN** localmente (Python 3.13) e dentro do container (Python 3.12, `docker exec clip-processor pytest`).
- **Smoke check**: `docker exec clip-processor python -c "from src.processar import parse_video_id; print(parse_video_id('https://youtube.com/shorts/dQw4w9WgXcQ'))"` imprime `dQw4w9WgXcQ`.

## Task Commits

1. **Task 1: Implementar processar.py — parse URL + yt-dlp metadata + upsert idempotente** — `819daa5` (feat)

_Plan metadata commit segue após este SUMMARY._

## Files Created/Modified

### Modificados

- `clip-processor/src/processar.py` — Substituiu stub Phase 6 (NotImplementedError) por implementação completa: regex YOUTUBE_URL_RE (já presente desde Plan 06-01), parse_video_id, _normalize_upload_date (helper privado), fetch_metadata (yt-dlp), upsert_source_video (pseudo-channel + SELECT-then-INSERT), main (CLI com exit codes).

## Decisions Made

- **Pseudo-channel `manual:UCxxx` com `active=FALSE`**: se o vídeo vem de canal fora do pool RSS, ainda assim precisamos de um FK válido em `source_videos.channel_id`. Criar uma linha "fantasma" em `source_channels` com `active=FALSE` resolve sem mexer no comportamento do RSS poller.
- **SELECT-then-INSERT (não INSERT...ON DUPLICATE KEY)**: o chamador precisa saber o status atual do vídeo para a mensagem do bot ("já existia — status=downloaded" vs "inserido — status=pending"). `INSERT...ON DUPLICATE KEY` não retorna isso facilmente.
- **status='pending' (não bypassa pipeline)**: decisão registrada em 06-CONTEXT.md — manual ingest só dispara o pipeline normal; download/transcribe/select/cut/publish acontecem pelos mesmos jobs APScheduler.
- **Exception genérica em fetch_metadata**: yt-dlp pode levantar várias subclasses (DownloadError, ExtractorError, GeoRestrictedError). Captura tudo e retorna exit code 3. Plan 06-07 (router n8n) mapeia exit code 3 → mensagem amigável "vídeo privado/region-locked/inexistente".
- **_normalize_upload_date**: yt-dlp retorna `upload_date='20260619'`. Schema é TIMESTAMP. Convertido para `'2026-06-19 00:00:00'` (meia-noite UTC). Aceita None (coluna permite NULL).
- **Title truncado em 500 chars**: coerente com `VARCHAR(500)` em `source_videos.title` (confirmado em `mysql/init/01-clips-schema.sql`).
- **try/finally em main**: garante `conn.close()` mesmo se `upsert_source_video` lançar. Sem with porque pymysql Connection não é context manager em todas as versões da família 1.x.

## Deviations from Plan

None - plan executed exactly as written. A única adaptação foi a inclusão de `_normalize_upload_date` (helper privado não documentado nas <interfaces>), necessária porque o schema usa TIMESTAMP e o yt-dlp retorna 'YYYYMMDD' — isto está documentado em "Decisões" mas não conta como deviation no sentido das Rules 1-4 (não é bug fix, missing critical, blocking ou architectural — é conversão de formato esperada).

## Issues Encountered

- **Container `clip-processor` não monta `src/` do host**: `docker-compose` monta apenas `videos/` e `youtube/token.json`. Para validar dentro do container, foi necessário `docker cp clip-processor/src/processar.py clip-processor:/app/src/processar.py`. Testes rodaram tanto localmente (Python 3.13) quanto dentro do container (Python 3.12) — ambos GREEN. Para CI/CD, o ideal é rebuildar a imagem após cada plan que mexe em `src/`, ou montar `./clip-processor/src:/app/src` em um docker-compose.override.yml de dev (não está no escopo deste plan).

## User Setup Required

Nenhum nesta wave. `yt-dlp` já está em `requirements.txt` desde Phase 2; nenhum `pip install` adicional necessário. Quando Plan 06-07 ativar o router, o canal e o `pseudo:UC...` aparecerão automaticamente em `source_channels` na primeira invocação de `/processar`.

## Next Phase Readiness

- **Plan 06-07 (n8n flows)**: pode usar `docker exec clip-processor python -m src.processar {{ $('Parse Comando').first().json.arg }}` no node executeCommand do output `processar` do Switch. Mapeamento de exit codes para mensagens Telegram:
  - **0** → "OK: <video_id> {inserido|já existia} — status=<status> — título=\"<title>\""
  - **2** → "Erro: URL inválida. Use formato https://youtu.be/ID, https://youtube.com/watch?v=ID ou https://youtube.com/shorts/ID."
  - **3** → "Erro: não consegui buscar metadados (vídeo privado, region-locked, removido ou ID inexistente)."
- **Caveat para Plan 06-07**: stdout do `processar.py` contém o título com aspas dentro — n8n precisa escapar antes de mandar para o Telegram (markdown_v2 ou plain text).
- **Plan 06-05 (ttl_worker)** e **Plan 06-06 (telegram_notifier)** seguem independentes — este plan não afeta nenhum deles.

## Self-Check: PASSED

Verificações realizadas:

- `clip-processor/src/processar.py` existe e contém 5 funções públicas (`parse_video_id`, `_normalize_upload_date`, `fetch_metadata`, `upsert_source_video`, `main`) + 1 constante `YOUTUBE_URL_RE` + guard `__main__`.
- `pytest tests/test_processar.py` localmente: 7/7 GREEN (TestParseVideoId 5 + TestUpsertSourceVideo 2).
- `docker exec clip-processor pytest tests/test_processar.py`: 7/7 GREEN (após `docker cp` do arquivo).
- Smoke check `parse_video_id('https://youtu.be/dQw4w9WgXcQ') == 'dQw4w9WgXcQ'` no container — confirmado.
- Smoke check `parse_video_id('https://youtube.com/shorts/dQw4w9WgXcQ')` imprime `dQw4w9WgXcQ` — confirmado.
- Commit `819daa5` presente em `git log --oneline` com mensagem `feat(06-04): implement processar.py for manual YouTube ingest (CTRL-04)`.
- Nenhuma regressão em testes não relacionados: full suite mostra 93 passed + 11 failed, onde os 11 failed são todos do RED state esperado de Plans 06-02 (publisher), 06-05 (ttl_worker), 06-06 (telegram_notifier).

---
*Phase: 06-controle-manual-n8n-telegram*
*Completed: 2026-06-19*
