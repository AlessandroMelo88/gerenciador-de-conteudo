---
phase: 02-aquisicao-de-videos
plan: "03"
subsystem: acquisition
tags: [redis, pymysql, yt-dlp, feedparser, requests, deduplication, rss, python, pytest, tdd]

# Dependency graph
requires:
  - phase: 02-aquisicao-de-videos plan 01
    provides: pytest scaffold com test_dedup.py, test_downloader.py, test_rss_poller.py em RED state
  - phase: 02-aquisicao-de-videos plan 02
    provides: db.py com insert_video, get_db_connection; docker-compose com Redis vars

provides:
  - dedup.py com is_seen() (Redis NX + MySQL fallback) e mark_failed_redis()
  - downloader.py com download_video() (720p, disk guard, retry 3x, cleanup .part)
  - rss_poller.py com poll_all_channels() (feedparser + is_seen + insert_video)
  - 17 testes total passando GREEN (5 dedup, 5 downloader, 3 rss_poller, 4 db)

affects:
  - 02-04 (daemon main.py usa poll_all_channels, download_video e is_seen)
  - 03-transcricao (usa download_video para obter arquivo local antes de transcrever)

# Tech tracking
tech-stack:
  added:
    - yt-dlp (instalado localmente para testes; já em requirements.txt do container)
    - feedparser (instalado localmente para testes)
    - requests (instalado localmente para testes)
  patterns:
    - "Redis NX SET com TTL 30 dias para deduplicação rápida (O(1) por vídeo)"
    - "Fallback MySQL para Redis: RedisError não aborta o poll — consulta source_videos"
    - "glob.glob para cleanup de .part: único ponto de limpeza fora do loop de retry"
    - "Retry transiente: 3 tentativas com sleep(60), cleanup após todas as tentativas"
    - "Erro permanente (private/removed/unavailable/geo): retorna False após 1 tentativa"
    - "rss_poller usa requests.get + feedparser.parse(response.text) — permite mock de HTTP"
    - "poll_all_channels: resiliência por canal com try/except individual, não aborta todo o poll"
    - "Injeção de dependência: db_conn e redis_client opcionais → None cria conexão de produção"

key-files:
  created:
    - clip-processor/src/dedup.py
    - clip-processor/src/downloader.py
    - clip-processor/src/rss_poller.py

key-decisions:
  - "_cleanup_partial() chamado uma única vez após loop de retry (não por tentativa) — satisfaz test_partial_cleanup assert_called_once"
  - "rss_poller.py usa requests.get + feedparser.parse(response.text) em vez de feedparser.parse(url) diretamente — permite mock de HTTP nos testes"
  - "poll_all_channels aceita db_conn e redis_client opcionais: None em produção cria conexão nova; injetados nos testes para isolamento"

patterns-established:
  - "Dedup pattern: Redis NX → fallback MySQL → False (vídeo novo)"
  - "Downloader pattern: disk guard → retry loop → cleanup fora do loop"
  - "Poller pattern: busca canais → HTTP get → feedparser → dedup → insert"

requirements-completed:
  - ACQU-01
  - ACQU-02
  - ACQU-03

# Metrics
duration: ~10min (excluindo 4min de testes com time.sleep real)
completed: 2026-06-18
---

# Phase 2 Plan 03: Módulos Core do Daemon Summary

**dedup.py (Redis NX + MySQL fallback), downloader.py (yt-dlp 720p com disk guard e retry 3x), rss_poller.py (feedparser + is_seen + insert_video) implementados com 17/17 testes GREEN**

## Performance

- **Duration:** ~10 min (+ ~4 min para testes com time.sleep real)
- **Started:** 2026-06-18T14:24:04Z
- **Completed:** 2026-06-18T14:35:24Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- dedup.py: is_seen() com Redis NX SET (TTL 30 dias) e fallback automático para MySQL em caso de RedisError
- downloader.py: download_video() com verificação de disco (mínimo 2GB), retry 3x para erros transientes, cleanup .part único após falha
- rss_poller.py: poll_all_channels() integra feedparser + dedup + db, com resiliência por canal e injeção de dependência para testes

## Task Commits

1. **Task 1: dedup.py — deduplicação Redis + MySQL** — `d0e0624` (feat)
2. **Task 2: downloader.py — download yt-dlp com retry e disk guard** — `494a618` (feat)
3. **Task 3: rss_poller.py — monitor RSS e inserção de vídeos novos** — `c91361d` (feat)

## Files Created/Modified

- `clip-processor/src/dedup.py` — is_seen() com Redis NX + fallback MySQL; mark_failed_redis() para retry
- `clip-processor/src/downloader.py` — download_video() com VIDEOS_DIR, MIN_FREE_BYTES, PERMANENT_ERRORS, _cleanup_partial()
- `clip-processor/src/rss_poller.py` — poll_all_channels() com requests.get + feedparser + integração dedup/db

## Decisions Made

- `_cleanup_partial()` chamado uma vez fora do loop de retry (não por tentativa): satisfaz `test_partial_cleanup` que usa `assert_called_once_with` — cleanup de arquivo .part não precisa acontecer a cada retry, apenas ao final
- `rss_poller.py` usa `requests.get(rss_url) + feedparser.parse(response.text)` em vez de `feedparser.parse(url)`: permite mock de `src.rss_poller.requests.get` nos testes sem precisar interceptar HTTP
- `poll_all_channels` aceita `db_conn=None, redis_client=None`: em produção cria conexões próprias por chamada (evita timeout MySQL 6h); em testes recebe conexões mockadas para isolamento total

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] yt-dlp não instalado localmente**
- **Found during:** Task 2 (verificação pytest test_downloader.py)
- **Issue:** `ModuleNotFoundError: No module named 'yt_dlp'` ao importar src.downloader
- **Fix:** `pip3 install yt-dlp --break-system-packages`
- **Files modified:** Nenhum (instalação local para testes; requirements.txt já contém yt-dlp)
- **Verification:** 5/5 testes downloader passaram após instalação
- **Committed in:** 494a618 (Task 2 commit)

**2. [Rule 3 - Blocking] feedparser e requests não instalados localmente**
- **Found during:** Task 3 (verificação pytest test_rss_poller.py)
- **Issue:** Módulos necessários para rss_poller.py não disponíveis localmente
- **Fix:** `pip3 install feedparser requests --break-system-packages`
- **Files modified:** Nenhum (instalação local; requirements.txt já listava feedparser)
- **Verification:** 3/3 testes rss_poller passaram após instalação
- **Committed in:** c91361d (Task 3 commit)

**3. [Rule 1 - Bug] _cleanup_partial() chamado por tentativa causava assert_called_once_with falhar**
- **Found during:** Task 2 (test_partial_cleanup falhava com "Called 3 times")
- **Issue:** Implementação original chamava cleanup a cada iteração do loop de retry; test_partial_cleanup usa glob mock que sempre retorna o mesmo arquivo, causando 3 chamadas a os.remove
- **Fix:** Mover _cleanup_partial() para fora do loop: chamado uma única vez após todas as tentativas (ou após erro permanente)
- **Files modified:** clip-processor/src/downloader.py
- **Verification:** test_partial_cleanup passou com `assert_called_once_with`
- **Committed in:** 494a618 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (2 Rule 3 blocking — dependências locais; 1 Rule 1 bug — lógica cleanup)
**Impact on plan:** Todos os auto-fixes necessários para execução local dos testes. Sem impacto na funcionalidade de produção (container Docker usa requirements.txt).

## Issues Encountered

- `test_partial_cleanup` e `test_retry_transient_error` não mockam `time.sleep` — testes levam ~120s cada com sleep real (total ~4 min). Comportamento esperado dado que o mock não foi incluído no scaffold de testes do Plano 01. Não foi corrigido para não alterar os contratos de teste estabelecidos.

## User Setup Required

None — módulos são código Python puro; dependências já definidas em requirements.txt para o container Docker.

## Next Phase Readiness

- dedup.py, downloader.py e rss_poller.py prontos para integração no daemon (02-04)
- Suite completa: 17 testes GREEN (test_db, test_dedup, test_downloader, test_rss_poller)
- Módulos importam sem erros: `from src.dedup import is_seen, mark_failed_redis; from src.downloader import download_video; from src.rss_poller import poll_all_channels`

---
*Phase: 02-aquisicao-de-videos*
*Completed: 2026-06-18*
