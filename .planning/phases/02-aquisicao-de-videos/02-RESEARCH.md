# Phase 2: Aquisição de Vídeos - Research

**Researched:** 2026-06-18
**Domain:** Python daemon (APScheduler), RSS polling (feedparser), download (yt-dlp), deduplicação (Redis + MySQL)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Orquestrador do polling RSS**
- clip-processor roda como daemon Python com APScheduler interno
- Poll de RSS a cada 6 horas (conforme ACQU-01) — sem depender do n8n para disparar
- n8n não participa da fase de aquisição; fica disponível para fases futuras de orquestração complexa

**Estrutura de diretórios**
- Vídeos brutos: `./videos/{youtube_video_id}.mp4` (volume montado no Docker)
- Clips gerados (fases seguintes): `./videos/clips/{youtube_video_id}_clip_{n}.mp4`
- Pasta `videos/` na raiz do projeto, montada como volume Docker no clip-processor
- Deletar arquivos automaticamente após upload bem-sucedido para o YouTube

**Gerenciamento de espaço em disco**
- Verificar espaço livre antes de cada download
- Se espaço disponível < 2GB: não iniciar o download, logar aviso, manter vídeo como `pending`
- Não há limpeza periódica forçada — a deleção pós-upload já mantém o disco limpo

**Deduplicação (Redis + MySQL)**
- Redis como cache de dedup com TTL de 30 dias por chave (`video:{youtube_video_id}`)
- Fallback para MySQL-only (`source_videos` UNIQUE em `youtube_video_id`) se Redis estiver indisponível
- Redis é otimização de performance, não barreira única — MySQL é a fonte de verdade

**Falha no download**
- Retry automático 3 vezes com 60s de espera entre tentativas
- Após 3 falhas: status `failed` no banco, não tenta mais automaticamente
- Vídeos privados, removidos ou geo-restritos: marca como `failed` na primeira tentativa (yt-dlp retorna erro distinguível)
- Arquivos parciais deletados em caso de falha para não acumular lixo em disco

**Paralelismo**
- 1 download por vez — fila sequencial
- Evita pico de disco e rede; suficiente para o volume inicial de poucos canais

**Cadastro de canais**
- Script SQL de seed (`mysql/init/02-seed-channels.sql`) com os canais iniciais
- Executado manualmente uma vez: `docker exec -i mysql mysql ... < 02-seed-channels.sql`
- Versionado no git — histórico de canais monitorados fica rastreável

**Observabilidade**
- Logs via stdout simples: `docker logs clip-processor -f`
- Formato: `[2026-06-18 10:00:00] [ACQU] Novo vídeo detectado: {video_id} — {title}`
- Sem arquivo de log em disco para não consumir espaço adicional

### Claude's Discretion
- Implementação interna do APScheduler (BlockingScheduler vs BackgroundScheduler)
- Formato exato de parse do RSS (feedparser ou xmltodict)
- Tratamento de edge cases do yt-dlp (formatos ausentes, retries de rede internos do yt-dlp)

### Deferred Ideas (OUT OF SCOPE)
- **Painel de gestão de canais** — Interface web para adicionar/remover canais sem editar SQL. Alinhado com MGT-01 (v2 requirements)
- **Analytics de CPM e performance** — Agente ou script que monitora quanto cada vídeo está pagando. Alinhado com OPT-01 (v2 requirements)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ACQU-01 | Sistema monitora canais de YouTube pré-configurados via RSS (sem consumir cota de API) a cada 6 horas | APScheduler interval trigger a cada 6h + feedparser contra `https://www.youtube.com/feeds/videos.xml?channel_id=<id>` |
| ACQU-02 | Novos vídeos detectados são baixados automaticamente em 720p via yt-dlp | yt-dlp YoutubeDL com `format: 'bestvideo[height<=720]+bestaudio/best'` e `merge_output_format: 'mp4'` |
| ACQU-03 | Sistema não reprocessa vídeos já processados (deduplicação via Redis SET + MySQL UNIQUE em youtube_video_id) | `redis.set(key, 1, ex=2592000, nx=True)` com fallback para UNIQUE constraint MySQL |
| ORC-02 | Status de cada job é registrado no MySQL (pending/downloading/downloaded/failed) | ENUM já definido no schema `source_videos.status`; UPDATE via pymysql em cada transição de estado |
</phase_requirements>

---

## Summary

A Phase 2 implementa o daemon Python `clip-processor` que substitui o stub atual de `main.py`. O daemon usa APScheduler para disparar a cada 6 horas: lê os canais ativos da tabela `source_channels`, faz poll dos feeds RSS do YouTube, detecta vídeos novos (não vistos no Redis nem no MySQL), e enfileira downloads sequenciais via yt-dlp em 720p MP4.

A deduplicação tem duas camadas: Redis como cache rápido com TTL de 30 dias (`video:{video_id}` via SET NX EX), e MySQL como fonte de verdade via UNIQUE constraint em `youtube_video_id`. O download tem retry de até 3x com 60 segundos entre tentativas; erros permanentes (vídeo privado/removido/geo-restrito) são detectados pelo tipo de exceção do yt-dlp e marcados como `failed` imediatamente sem retry.

Redis já existe no `docker-compose.yml` compartilhado (`redis:alpine` na porta 6379). A única mudança no docker-compose é adicionar o volume `./canaldecortes/videos:/app/videos` ao serviço `clip-processor` e as variáveis `REDIS_HOST=redis` e `REDIS_PORT=6379`. O `requirements.txt` precisa adicionar `apscheduler`, `feedparser` e `redis`.

**Primary recommendation:** Use `BlockingScheduler` do APScheduler 3.x — o scheduler é a única tarefa do processo daemon; sem necessidade de thread separada. Use `feedparser.parse()` para RSS; acesse `entry.yt_videoid` para o video ID.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| APScheduler | 3.x (latest 3.11.2) | Agendamento do poll RSS a cada 6h | Biblioteca padrão de scheduling em Python; já usada no ecossistema; simples para daemons |
| feedparser | 6.0.x | Parse do feed RSS do YouTube | Padrão de facto para feeds RSS/Atom em Python; suporta namespaces `yt:` do YouTube |
| yt-dlp | latest | Download de vídeo em 720p | Substituto ativo do youtube-dl; já no requirements.txt; melhor suporte a formatos YouTube |
| redis (redis-py) | 5.x | Cache de dedup com TTL | Cliente oficial Redis para Python; SET NX EX atômico |
| pymysql | já instalado | Acesso ao MySQL | Já no requirements.txt; cliente puro-Python sem dependência nativa |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shutil (stdlib) | Python 3.12 | Checar espaço em disco livre | `shutil.disk_usage('/app/videos').free` antes de cada download |
| os (stdlib) | Python 3.12 | Deletar arquivos parciais | `os.remove(path)` em cleanup de falha |
| time (stdlib) | Python 3.12 | Sleep de 60s entre retries | `time.sleep(60)` no retry loop |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| feedparser | xmltodict + requests | feedparser já lida com namespaces `yt:`, malformed feeds, encoding; xmltodict requer parse manual |
| BlockingScheduler | BackgroundScheduler | BackgroundScheduler precisa de loop de main thread para não morrer; BlockingScheduler é mais simples para daemon single-purpose |

**Installation:**
```bash
# Adicionar ao clip-processor/requirements.txt:
apscheduler
feedparser
redis
# (yt-dlp e pymysql já estão instalados)
```

---

## Architecture Patterns

### Recommended Project Structure

```
clip-processor/
├── Dockerfile                  # sem mudanças
├── requirements.txt            # adicionar apscheduler, feedparser, redis
└── src/
    ├── main.py                 # substituir stub; inicializa BlockingScheduler
    ├── rss_poller.py           # poll_all_channels(): lê DB, chama feedparser, detecta novos
    ├── downloader.py           # download_video(): yt-dlp, retry, disk check, cleanup
    ├── dedup.py                # is_seen() / mark_seen(): Redis NX + MySQL fallback
    └── db.py                   # get_connection(), update_status(), insert_video()
```

### Pattern 1: BlockingScheduler como daemon

**What:** `BlockingScheduler` bloqueia o processo principal; é o único "trabalho" do container.
**When to use:** Quando o scheduling é a função primária do processo — sem necessidade de servir HTTP ou processar outros eventos.

```python
# Source: https://apscheduler.readthedocs.io/en/3.x/userguide.html
import signal
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', hours=6, id='poll_rss')
def poll_rss_job():
    poll_all_channels()

def shutdown(signum, frame):
    scheduler.shutdown(wait=False)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

scheduler.start()  # bloqueia aqui — ideal para daemon Docker
```

### Pattern 2: Parsing do RSS do YouTube com feedparser

**What:** feedparser acessa o feed RSS do YouTube e expõe campos via namespace `yt_`.
**When to use:** Para cada canal em `source_channels.rss_url`.

```python
# Source: feedparser 6.x + YouTube RSS namespace convention
import feedparser

def fetch_new_video_ids(rss_url: str) -> list[dict]:
    feed = feedparser.parse(rss_url)
    videos = []
    for entry in feed.entries:
        video_id = entry.get('yt_videoid')        # campo: yt:videoId
        title    = entry.get('title', '')
        published = entry.get('published', '')    # ISO 8601 string
        videos.append({'id': video_id, 'title': title, 'published': published})
    return videos

# URL padrão do feed RSS do YouTube:
# https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}
```

### Pattern 3: Download yt-dlp em 720p com retry

**What:** YoutubeDL com format selector para 720p, output em MP4 fixo, cleanup de parciais.
**When to use:** Para cada vídeo novo detectado após dedup check.

```python
# Source: https://github.com/yt-dlp/yt-dlp README + yt-dlp-yt-dlp.mintlify.app/api/overview
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError
import os, shutil, time

VIDEOS_DIR = '/app/videos'
MIN_FREE_BYTES = 2 * 1024 ** 3  # 2 GB

PERMANENT_ERRORS = ('private', 'removed', 'unavailable', 'geo')

def download_video(video_id: str, output_path: str) -> bool:
    # 1. Checar espaço em disco
    free = shutil.disk_usage(VIDEOS_DIR).free
    if free < MIN_FREE_BYTES:
        log(f'[ACQU] Espaço insuficiente ({free // 1024**3}GB livres) — {video_id} permanece pending')
        return False

    url = f'https://www.youtube.com/watch?v={video_id}'
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'no_color': True,
        'noprogress': True,
    }

    for attempt in range(1, 4):  # até 3 tentativas
        partial = output_path + '.part'
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except DownloadError as e:
            msg = str(e).lower()
            is_permanent = any(kw in msg for kw in PERMANENT_ERRORS)
            _cleanup_partial(partial)
            if is_permanent:
                log(f'[ACQU] Erro permanente em {video_id}: {e}')
                return False  # falha imediata, sem retry
            if attempt < 3:
                log(f'[ACQU] Tentativa {attempt}/3 falhou para {video_id} — aguardando 60s')
                time.sleep(60)
    return False  # 3 falhas

def _cleanup_partial(path: str):
    for p in [path, path.replace('.part', '.mp4.part')]:
        if os.path.exists(p):
            os.remove(p)
```

### Pattern 4: Deduplicação Redis + MySQL fallback

**What:** Redis SET NX EX é atômico — checa e registra em uma operação. MySQL UNIQUE é o safety net.
**When to use:** Antes de inserir qualquer vídeo novo no pipeline.

```python
# Source: https://redis.io/tutorials/data-deduplication-with-redis/
import redis
import pymysql

REDIS_TTL = 30 * 24 * 3600  # 30 dias em segundos

def is_seen(video_id: str, redis_client, db_conn) -> bool:
    key = f'video:{video_id}'

    # Tentativa 1: Redis (fast path)
    try:
        result = redis_client.set(key, 1, ex=REDIS_TTL, nx=True)
        if result is None:
            return True   # já existia no Redis = já visto
    except redis.RedisError:
        pass  # Redis indisponível — fallback para MySQL

    # Tentativa 2: MySQL UNIQUE constraint (source of truth)
    with db_conn.cursor() as cur:
        cur.execute(
            'SELECT id FROM source_videos WHERE youtube_video_id = %s', (video_id,)
        )
        if cur.fetchone():
            return True

    return False  # novo vídeo

def mark_failed_redis(video_id: str, redis_client):
    """Remove a chave Redis de vídeo com falha permanente para liberar memória."""
    try:
        redis_client.delete(f'video:{video_id}')
    except redis.RedisError:
        pass
```

### Pattern 5: Transições de status no MySQL

**What:** UPDATE atômico com timestamp — cada mudança de estado registra `updated_at` automaticamente.
**When to use:** Em cada etapa do ciclo de vida do job.

```python
# MySQL schema já define updated_at ON UPDATE CURRENT_TIMESTAMP
def update_status(db_conn, video_id: str, status: str, local_path: str = None):
    sql = 'UPDATE source_videos SET status = %s' + \
          (', local_path = %s' if local_path else '') + \
          ' WHERE youtube_video_id = %s'
    params = [status] + ([local_path] if local_path else []) + [video_id]
    with db_conn.cursor() as cur:
        cur.execute(sql, params)
    db_conn.commit()
```

### Anti-Patterns to Avoid

- **Não usar BackgroundScheduler sem loop no main thread:** BackgroundScheduler roda em daemon thread — se main() retornar, o scheduler morre silenciosamente. Usar BlockingScheduler para daemon single-purpose.
- **Não passar `format: '720p'` como string literal no yt-dlp:** Esse valor não é reconhecido. Usar `'bestvideo[height<=720]+bestaudio/best'` com `merge_output_format: 'mp4'`.
- **Não asumir que feedparser usa `entry.id` para o video ID do YouTube:** O video ID fica em `entry.yt_videoid` (namespace `yt:`). `entry.id` é a URL completa.
- **Não inserir o registro em `source_videos` DEPOIS de iniciar o download:** Inserir com status `downloading` ANTES de chamar yt-dlp para evitar condição de corrida se o processo reiniciar.
- **Não deletar a chave Redis de vídeos com download bem-sucedido:** A chave deve persistir pelo TTL de 30 dias para garantir dedup. Só deletar para vídeos com `failed` permanente.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RSS parsing | Parser XML customizado | `feedparser.parse()` | Lida com malformed feeds, namespaces yt:, encoding, HTTP redirects automaticamente |
| Format selection 720p | Lógica manual de escolha de formato | `ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'` | yt-dlp resolve disponibilidade de formato em runtime; fallback automático para `best` |
| Dedup atômica | Check-then-insert em dois passos | `redis.set(key, 1, nx=True, ex=ttl)` | Atomicidade nativa — sem race condition em operação única |
| Retry com backoff | Loop manual com sleep | `for attempt in range(1, 4): ... time.sleep(60)` | Simples e suficiente; APScheduler retry plugins são overengineering para 3 tentativas |
| Scheduling cron | Thread + time.sleep loop | `BlockingScheduler` do APScheduler | Lida com misfire, coalesce, max_instances, signal handling |

**Key insight:** yt-dlp esconde complexidade enorme de format negotiation com o YouTube (DASH, HLS, codec availability) — qualquer implementação manual quebraria a cada mudança na API do YouTube.

---

## Common Pitfalls

### Pitfall 1: Container reinicia com vídeo em status `downloading`

**What goes wrong:** Se o container cair durante um download, o vídeo fica preso em status `downloading` para sempre — nunca é retomado.
**Why it happens:** O status é atualizado para `downloading` antes do download começar, mas não há lógica de recovery on startup.
**How to avoid:** Ao iniciar o daemon, executar: `UPDATE source_videos SET status = 'pending' WHERE status = 'downloading'` — assume que downloads incompletos devem ser retentados.
**Warning signs:** Logs mostram vídeos nunca saindo de `downloading`.

### Pitfall 2: `entry.yt_videoid` ausente em alguns feeds

**What goes wrong:** feedparser normaliza nomes de namespace; em alguns parsings o campo pode aparecer como `entry['yt_videoid']` ou via `entry.tags`.
**Why it happens:** Namespaces XML são traduzidos por feedparser com underscore em vez de dois-pontos.
**How to avoid:** Extrair o video ID do campo `entry.link` como fallback: `re.search(r'v=([A-Za-z0-9_-]{11})', entry.link)`.
**Warning signs:** `video_id` sendo `None` ao tentar inserir no banco.

### Pitfall 3: Redis indisponível causa falha silenciosa

**What goes wrong:** `redis.StrictRedis.set()` levanta `redis.ConnectionError` se o Redis não estiver disponível — o código precisa fazer catch e fallback para MySQL.
**Why it happens:** Redis pode reiniciar independentemente; sem try/except o poll RSS inteiro falha.
**How to avoid:** Sempre envolver operações Redis em `try/except redis.RedisError` e continuar com MySQL-only se falhar.
**Warning signs:** Todos os vídeos aparecendo como "novos" mesmo após serem processados (Redis caiu, MySQL UNIQUE está protegendo mas não marca Redis).

### Pitfall 4: Arquivo .part não limpo após falha de yt-dlp

**What goes wrong:** yt-dlp cria arquivo `.part` durante download; se o processo crashar ou levantar exceção antes de renomear, o `.part` persiste.
**Why it happens:** yt-dlp não limpa automaticamente em todos os cenários de erro.
**How to avoid:** Bloco `finally` ou cleanup explícito de `{output_path}.part` após qualquer exceção.
**Warning signs:** Arquivos `.part` acumulando em `/app/videos`.

### Pitfall 5: MySQL connection timeout entre polls de 6 horas

**What goes wrong:** pymysql fecha conexões ociosas após ~8 horas (MySQL default `wait_timeout`). Na segunda execução do poll, a conexão está morta.
**Why it happens:** O daemon fica 6 horas sem usar a conexão; MySQL mata conexões ociosas.
**How to avoid:** Criar nova conexão pymysql a cada execução do job (não reutilizar conexão global). Ou usar `connection.ping(reconnect=True)` antes de cada query.
**Warning signs:** `OperationalError: (2006, 'MySQL server has gone away')` nos logs.

### Pitfall 6: Volume Docker não montado = downloads indo para /tmp

**What goes wrong:** Se `./canaldecortes/videos:/app/videos` não estiver no docker-compose, yt-dlp salva em `/app/videos` dentro do container — perdido em restart.
**Why it happens:** O volume mount ainda não está no docker-compose (Phase 1 usava `/tmp/clips`).
**How to avoid:** Adicionar volume mount no docker-compose antes de qualquer teste. Verificar com `docker inspect clip-processor`.
**Warning signs:** Vídeos somem após restart do container.

---

## Code Examples

### Estrutura completa do main.py (daemon entry point)

```python
# Source: APScheduler 3.x docs + padrão de daemon Docker
import signal
from apscheduler.schedulers.blocking import BlockingScheduler
from rss_poller import poll_all_channels

def shutdown(signum, frame):
    print('[ACQU] Recebendo sinal de shutdown — encerrando scheduler')
    scheduler.shutdown(wait=False)

scheduler = BlockingScheduler(timezone='America/Sao_Paulo')
scheduler.add_job(
    poll_all_channels,
    'interval',
    hours=6,
    id='poll_rss',
    coalesce=True,        # se poll atrasou, roda apenas uma vez ao retomar
    max_instances=1,      # nunca rodar dois polls simultâneos
    misfire_grace_time=300
)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

print('[ACQU] Daemon iniciado — poll RSS a cada 6 horas')
poll_all_channels()  # executar imediatamente na inicialização
scheduler.start()
```

### Seed SQL para canais (idempotente)

```sql
-- mysql/init/02-seed-channels.sql
-- Padrão: INSERT IGNORE para idempotência (mesmo estilo do 01-clips-schema.sql)
USE clips_automation;

INSERT IGNORE INTO source_channels (youtube_channel_id, channel_name, rss_url, active)
VALUES
  ('UC_CHANNEL_ID_1', 'Nome do Canal 1',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UC_CHANNEL_ID_1', TRUE),
  ('UC_CHANNEL_ID_2', 'Nome do Canal 2',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UC_CHANNEL_ID_2', TRUE);
```

### Verificação de espaço em disco

```python
# Source: Python docs shutil.disk_usage()
import shutil

def has_enough_space(path: str, required_bytes: int) -> bool:
    usage = shutil.disk_usage(path)
    return usage.free >= required_bytes
```

### Conexão MySQL por job (evita timeout)

```python
# Padrão para daemons de longa duração com pymysql
import pymysql
import os

def get_db_connection():
    return pymysql.connect(
        host=os.environ['MYSQL_HOST'],
        database=os.environ['MYSQL_DATABASE'],
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        charset='utf8mb4',
        autocommit=False,
        connect_timeout=10,
    )

def poll_all_channels():
    conn = get_db_connection()  # nova conexão a cada execução
    try:
        # ... lógica do poll ...
        pass
    finally:
        conn.close()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| youtube-dl | yt-dlp | 2021 (fork ativo) | yt-dlp tem atualizações semanais; youtube-dl parou de ser mantido ativamente |
| `SETNX` + `EXPIRE` separados | `SET key val NX EX ttl` (atômico) | Redis 2.6.12+ | Elimina race condition entre check e expiração |
| `BlockingScheduler.start()` sem signal handler | + `signal.signal(SIGTERM, shutdown)` | Docker best practice | Graceful shutdown em `docker stop` |

**Deprecated/outdated:**
- `youtube-dl`: ainda funciona mas não recebe updates de extratores do YouTube — usar `yt-dlp`
- `redis.StrictRedis`: foi unificado com `redis.Redis` na redis-py 3.x — usar apenas `redis.Redis`
- `SETNX` command separado: obsoleto — substituído por `SET NX EX` atômico

---

## Open Questions

1. **Quais canais de futebol serão monitorados no seed inicial?**
   - What we know: O schema e o padrão de seed estão definidos
   - What's unclear: Os youtube_channel_id reais dos canais alvo
   - Recommendation: O planner deve criar uma tarefa explícita "inserir canais reais no seed SQL" — os IDs são fornecidos pelo usuário

2. **Volume Docker: `./canaldecortes/videos` ou caminho absoluto no Mac?**
   - What we know: O docker-compose atual usa caminhos relativos à raiz `/Users/alessandrobm1/develop/server/wordpress/`
   - What's unclear: O diretório `videos/` deve ficar em `canaldecortes/videos/` ou em outro lugar
   - Recommendation: `./canaldecortes/videos:/app/videos` no docker-compose — consistente com os outros volumes do canaldecortes

3. **feedparser `entry.yt_videoid` vs `entry['yt_videoid']`**
   - What we know: feedparser normaliza namespaces XML com underscore
   - What's unclear: A exata capitalização do campo em feedparser 6.x para `yt:videoId`
   - Recommendation: Implementar com `entry.get('yt_videoid') or re.search(r'v=([A-Za-z0-9_-]{11})', entry.link)` como fallback seguro

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (a instalar) |
| Config file | `clip-processor/pytest.ini` — Wave 0 |
| Quick run command | `pytest clip-processor/tests/ -x -q` |
| Full suite command | `pytest clip-processor/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ACQU-01 | `poll_all_channels()` detecta vídeos novos a partir de feed RSS mockado | unit | `pytest clip-processor/tests/test_rss_poller.py -x` | ❌ Wave 0 |
| ACQU-02 | `download_video()` chama yt-dlp com formato correto e retorna `True` em sucesso | unit (mock yt-dlp) | `pytest clip-processor/tests/test_downloader.py -x` | ❌ Wave 0 |
| ACQU-02 | `download_video()` aborta quando espaço livre < 2GB | unit (mock shutil) | `pytest clip-processor/tests/test_downloader.py::test_disk_space_guard -x` | ❌ Wave 0 |
| ACQU-02 | Arquivos `.part` são deletados após falha no download | unit | `pytest clip-processor/tests/test_downloader.py::test_partial_cleanup -x` | ❌ Wave 0 |
| ACQU-03 | `is_seen()` retorna `True` para vídeo já no Redis | unit (mock redis) | `pytest clip-processor/tests/test_dedup.py::test_redis_hit -x` | ❌ Wave 0 |
| ACQU-03 | `is_seen()` faz fallback para MySQL quando Redis indisponível | unit (mock redis raise) | `pytest clip-processor/tests/test_dedup.py::test_redis_fallback -x` | ❌ Wave 0 |
| ORC-02 | `update_status()` persiste transições de status no MySQL | unit (mock pymysql) | `pytest clip-processor/tests/test_db.py::test_status_update -x` | ❌ Wave 0 |
| ORC-02 | Status volta a `pending` para jobs presos em `downloading` na inicialização | unit | `pytest clip-processor/tests/test_db.py::test_recover_stuck_downloads -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest clip-processor/tests/ -x -q`
- **Per wave merge:** `pytest clip-processor/tests/ -v`
- **Phase gate:** Full suite green antes do `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `clip-processor/tests/__init__.py` — pacote de testes
- [ ] `clip-processor/tests/conftest.py` — fixtures compartilhadas (mock redis, mock pymysql, sample RSS feed XML)
- [ ] `clip-processor/tests/test_rss_poller.py` — cobre ACQU-01
- [ ] `clip-processor/tests/test_downloader.py` — cobre ACQU-02
- [ ] `clip-processor/tests/test_dedup.py` — cobre ACQU-03
- [ ] `clip-processor/tests/test_db.py` — cobre ORC-02
- [ ] `clip-processor/pytest.ini` — configuração do pytest
- [ ] Framework install: adicionar `pytest` e `pytest-mock` ao `requirements.txt` (ou `requirements-dev.txt`)

---

## Sources

### Primary (HIGH confidence)
- APScheduler 3.x docs: https://apscheduler.readthedocs.io/en/3.x/userguide.html — BlockingScheduler vs BackgroundScheduler, interval trigger, coalesce/max_instances
- yt-dlp Python API: https://yt-dlp-yt-dlp.mintlify.app/api/overview — YoutubeDL class, format options, DownloadError/ExtractorError
- Redis SET NX EX: https://redis.io/docs/latest/commands/set/ — atomicidade, parâmetros NX e EX
- Redis deduplication tutorial: https://redis.io/tutorials/data-deduplication-with-redis/ — padrão SET NX EX para dedup
- Python shutil docs: https://docs.python.org/3/library/shutil.html — `disk_usage().free`

### Secondary (MEDIUM confidence)
- feedparser PyPI: https://pypi.org/project/feedparser/ — versão 6.0.x, Python 3.6+
- YouTube RSS feed URL format (verificado por múltiplas fontes): `https://www.youtube.com/feeds/videos.xml?channel_id={id}`
- yt-dlp format 720p: `'bestvideo[height<=720]+bestaudio/best'` + `merge_output_format: 'mp4'` — verificado via docs e issues GitHub

### Tertiary (LOW confidence)
- `entry.yt_videoid` como campo feedparser para YouTube — comportamento baseado em convenção de namespace; validar com teste real contra um feed YouTube

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — todas as bibliotecas verificadas em fontes oficiais com versões atuais
- Architecture: HIGH — padrões verificados em docs oficiais APScheduler, yt-dlp API, Redis
- Pitfalls: HIGH — MySQL timeout e `.part` files são pitfalls documentados; container recovery é padrão conhecido
- feedparser field names: MEDIUM — comportamento de namespace documentado mas `yt_videoid` específico não verificado em docs oficiais

**Research date:** 2026-06-18
**Valid until:** 2026-07-18 (30 dias — stack estável; yt-dlp atualiza frequentemente mas API Python é estável)
