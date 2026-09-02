# Phase 6: Controle Manual N8N + Telegram - Research

**Researched:** 2026-06-19
**Domain:** Telegram bot + n8n orchestration + MySQL schema evolution + Cloudflare Tunnel exposure
**Confidence:** HIGH (n8n nodes, Telegram API, ENUM migration), MEDIUM (Cloudflare Tunnel + n8n exact compose), HIGH (Python/yt-dlp patterns, pytest mocks)

## Summary

A fase 6 adiciona uma camada de moderação humana ao pipeline autônomo: o publisher (que hoje publica `pending`) passa a publicar `approved`, e novos estados (`approved`, `rejected`) são incluídos no ENUM `generated_clips.status`. O operador opera o sistema via comandos no Telegram, roteados por workflows n8n que recebem updates por webhook seguro (Cloudflare Tunnel apontando para `localhost:5678`). Um worker de TTL converte `pending` em `rejected` após 48h.

A abordagem alinha-se com as decisões registradas em `06-CONTEXT.md`: apenas 6 comandos no v1, sem inline keyboard, sem dashboard web, sem bypass de quota. Toda a infra n8n + clip-processor + MySQL + Redis já está em pé desde Phase 5 — esta fase entrega 1 migration, 1 serviço cloudflared, 1 workflow n8n principal (substituindo `01-telegram-handler.json`), pequenas mudanças cirúrgicas em `publisher.py` e novos módulos em `clip-processor/src/` (telegram_bot.py, ttl_worker.py).

**Primary recommendation:** Use **Telegram Trigger node nativo do n8n** com filtro embutido "Restrict to Chat IDs" (fix PR #27643, mar/2026) — não construir webhook genérico nem fazer parsing manual de chat_id. Use **Cloudflare Tunnel via container `cloudflare/cloudflared:latest`** no mesmo docker-compose, com token via `.env`. Coloque o **TTL worker como APScheduler job dentro do clip-processor** (consistente com Phase 5, não acrescenta serviço novo). Mantenha o `publisher.py` com mudança mínima: trocar literal `'pending'` por `'approved'` no SELECT e nada mais.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Comandos v1 (apenas 6):**
- `/status` — métricas do pipeline (clips gerados hoje, quota usada, próximo upload agendado)
- `/clipes` — lista enxuta dos clips com status `pending`, formato `<id> | <título> | <duração>s`, máximo 10
- `/aprovar <id>` — muda status do clip de `pending` para `approved` (um por vez, sem lote)
- `/rejeitar <id>` — muda status para `rejected`, apaga o MP4 do clip, **mantém o raw video** para recorte futuro
- `/processar <url>` — força download e pipeline de um vídeo arbitrário (inclusive de canais não monitorados): insere em `source_videos` com status `pending`, escapando do RSS
- `/ajuda` — lista os comandos

Comandos **excluídos do v1**: `/buscar`, `/trending`, `/fila`, `/publicar`, `/canal`.

**Schema MySQL — novos status:** Migration adiciona dois valores ao ENUM `generated_clips.status`:
- `approved` — clip aprovado pelo operador, na fila para publicação
- `rejected` — clip rejeitado pelo operador (via comando) ou pelo TTL (auto)

Fluxos válidos:
- `pending → approved → publishing → published` (caminho feliz)
- `pending → rejected` (rejeição manual ou TTL)

`publisher.py` muda a query de seleção: hoje pega `pending`, passa a pegar `approved`.

**Manual × Automação (o bot é alavanca, não bypass):**
- **Quota:** máx 2 uploads/dia (configurável até 6) — `/aprovar` não força upload imediato
- **Janela horária:** 19h-22h America/Sao_Paulo — clips approved entram na fila e saem na próxima janela
- **Ordem:** publisher escolhe o próximo approved seguindo a lógica já existente (FIFO por created_at)
- Não existe `/publicar` ou bypass de quota

**TTL de pending:**
- Clips em `pending` viram `rejected` automaticamente após **48 horas**
- Aviso proativo do bot **24 horas antes** da expiração
- Worker de TTL roda periodicamente (definir na pesquisa → recomendação abaixo: APScheduler)

**Segurança e acesso:**
- **Allowlist hardcoded:** apenas `chat_id=5760918317` é autorizado
- Comandos vindos de outros chats retornam silêncio (sem mensagem)
- **Exposição do webhook:** Cloudflare Tunnel apontando para `http://localhost:5678` do n8n
- Sem ngrok, sem IP público direto, sem porta aberta no firewall

**Notificações proativas (3 situações apenas):**
1. **Upload publicado com sucesso** — "✓ Clip <id> publicado: <url do YouTube>"
2. **Falha crítica no pipeline** — falhas em download/transcribe/select/cut/upload com detalhe do erro
3. **Resumo diário às 18h BRT** — "X clips aguardando aprovação" (skip se X=0)

**Workflows n8n existentes:**
- `01-telegram-handler.json` — **reaproveitar** como base do roteador de webhook
- `02-busca-videos.json`, `03-tendencias.json`, `04-notificador-fila.json` — **descartar** (fora do escopo v1, mas manter arquivos como referência histórica)

**/processar <url> — comportamento:**
- Aceita URL do YouTube (padrão `youtube.com/watch?v=<id>` ou `youtu.be/<id>`)
- Extrai `youtube_video_id`, busca metadata pública (título, channel_id) via YouTube Data API
- Insere/atualiza linha em `source_videos` com status `pending`
- Idempotente: se o vídeo já existe, retorna o status atual sem duplicar
- Pipeline normal cuida do resto; **não bypassa** nenhuma regra

### Claude's Discretion

- Formato visual exato das mensagens do bot (emojis, quebras de linha, Markdown vs HTML)
- Layout do `/status` (quais métricas, ordem)
- Mensagem de erro padrão quando id inválido em `/aprovar`/`/rejeitar`
- Implementação técnica do worker de TTL (cron n8n vs APScheduler no clip-processor)
- Estrutura interna dos workflows n8n (quantos sub-workflows, como reusar o roteador)
- Logging/auditoria das ações do bot (level, destino — stdout, arquivo, MySQL)

### Deferred Ideas (OUT OF SCOPE)

- `/buscar <tema>` — descoberta ativa por tema via YouTube Data API search.list
- `/trending` — top assuntos em alta no futebol BR via Google Trends RSS
- `/fila` — visão da fila de upload (substituível por /clipes + /status)
- `/publicar` — upload imediato bypassando janela horária
- `/canal <URL>` — adicionar canal RSS via Telegram
- Inline keyboard de aprovar/rejeitar (1-tap UX)
- Thumbnail do clip anexada em /clipes
- Aprovação em lote (`/aprovar all` ou `/aprovar 1 2 3`)
- Cleanup imediato do raw video em /rejeitar
- Logging/auditoria em MySQL (tabela clip_approvals)
- Dashboard web de aprovação (alternativa ao Telegram)
- Notificações OPT-04 mais ricas (email + Telegram)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CTRL-01 | Bot aceita `/status`, `/clipes`, `/aprovar <id>`, `/rejeitar <id>`, `/processar <url>`, `/ajuda` somente do `chat_id` da allowlist; outros chats ignorados silenciosamente | "Architecture Pattern 1: Telegram Trigger com Restrict to Chat IDs" + "Architecture Pattern 2: Router via Switch node" + Code Examples #1-#6 (workflow JSON) |
| CTRL-02 | ENUM `generated_clips.status` ganha `approved` e `rejected`; `publisher.py` passa a publicar `approved` respeitando quota e janela horária | "Standard Stack" (MySQL 8.4 idempotent migration), "Architecture Pattern 3: Schema migration (05-controle-manual-migration.sql)", `publisher.py` swap descrito em "Pitfall 1" |
| CTRL-03 | `/aprovar <id>` muda pending→approved; `/rejeitar <id>` muda para rejected, apaga MP4, **mantém raw video** | Code Example #3 (n8n MySQL update node com guard `WHERE status='pending'`), Code Example #4 (rejeitar com DELETE MP4 via clip-processor endpoint), "Pitfall 2: race condition aprovar↔rejeitar" |
| CTRL-04 | `/processar <url>` insere/atualiza vídeo arbitrário em `source_videos` como `pending` (idempotente) sem bypassar regras | "Architecture Pattern 4: /processar via yt-dlp metadata + INSERT...ON DUPLICATE KEY", Code Example #5 (regex extractor + idempotent upsert) |
| CTRL-05 | Worker de TTL converte clipes `pending` em `rejected` após 48h; aviso 24h antes via Telegram | "Architecture Pattern 5: APScheduler TTL job no clip-processor" + Code Example #7 (ttl_worker.py com 2 estágios: warn 24h, expire 48h) |
| CTRL-06 | n8n recebe webhook via Cloudflare Tunnel; bot envia notificações proativas em 3 eventos | "Architecture Pattern 6: Cloudflare Tunnel via docker-compose" + Code Example #8 (cloudflared service) + Code Example #9 (n8n env vars WEBHOOK_URL) + "Architecture Pattern 7: Notificações proativas via HTTP POST para n8n webhook interno" |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| n8n | 1.100.0 (já pinado) | Roteador de comandos, sub-workflows e cron diário | Já é o orquestrador de Phase 5; reutiliza credenciais "Telegram Canal de Cortes" e "MySQL Canal de Cortes" |
| `n8n-nodes-base.telegramTrigger` | bundled | Receber updates do Telegram com filtro de chat_id nativo | PR #27643 (mar/2026) consolidou "Restrict to Chat IDs" como allowlist real (drops eventos sem id válido) — substitui parsing manual no Code node |
| `n8n-nodes-base.telegram` | bundled | sendMessage (acks, notificações, respostas) | API estável; chatId via expressão `={{ $json.message.chat.id }}` |
| `n8n-nodes-base.mySql` (typeVersion 2) | bundled | UPDATE/SELECT em `generated_clips` e `source_videos` | Já usado em `01-telegram-handler.json`; credencial "MySQL Canal de Cortes" já existe |
| `n8n-nodes-base.switch` | bundled | Roteador de comandos (substitui os IF encadeados do skeleton atual) | 1 node vs N IFs; performance + legibilidade |
| `n8n-nodes-base.scheduleTrigger` | bundled | Resumo diário 18h BRT (cron) | Honra `GENERIC_TIMEZONE=America/Sao_Paulo` já configurado |
| `n8n-nodes-base.executeCommand` | bundled | Chamar `docker exec clip-processor python -m src.cli ...` para /processar e /rejeitar (delete de arquivo) | Padrão já estabelecido em `canaldecortes-pipeline.json` |
| `cloudflare/cloudflared` | `:latest` (pin recomendado quando estabilizar) | Expor `n8n:5678` via Cloudflare Tunnel | Eliminação de ngrok; tunnel é outbound-only — sem port forward |
| Telegram Bot API | atual (HTTPS) | setWebhook com `secret_token` | Verificação `X-Telegram-Bot-Api-Secret-Token` impede spoof |
| pymysql + DictCursor | já em `requirements.txt` | Mudanças no `publisher.py` e novos módulos | Padrão db.py estabelecido (Phase 2) |
| APScheduler | já em `requirements.txt` | TTL worker como job cron dentro do clip-processor | Mesmo `BlockingScheduler` de `main.py` (Phase 2/5); adicionar `CronTrigger(minute='0,30')` ou `IntervalTrigger(hours=1)` |
| yt-dlp | já em `requirements.txt` | `/processar` — metadata-only via `YoutubeDL({'skip_download': True}).extract_info(url, download=False)` | Evita custar quota YouTube Data API só para puxar título/channel_id |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `re` (stdlib) | — | Parse de URL do YouTube em `/processar` | Regex coberto na Pitfall 3 |
| google-api-python-client | já em `requirements.txt` (uploader) | Fallback caso yt-dlp falhe na metadata (vídeo unlisted permite metadata via API key) | Apenas se `extract_info` retornar erro — mantém o caminho gratuito como default |
| pytest-mock | já em `requirements.txt` | Mocks de connections/cursor/requests em `test_telegram_bot.py`, `test_ttl_worker.py` | Conftest existente já cobre `mock_db_conn` e `mock_redis` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Telegram Trigger node nativo | Webhook node + Code parser (atual skeleton) | Webhook genérico exige reimplementar verificação de `X-Telegram-Bot-Api-Secret-Token` no Code node; Trigger node já valida internamente |
| Cloudflare Tunnel container `cloudflared` | `cloudflared` instalado no host como serviço | Container mantém tudo no docker-compose — consistente com o resto da stack; host service adiciona dependência fora do compose |
| APScheduler TTL no clip-processor | n8n cron workflow rodando query SQL direto | APScheduler já está no `main.py`; n8n cron exige criar mais 1 workflow + duplica timezone config; APScheduler ganha por consistência (Decisão: APScheduler) |
| yt-dlp metadata para /processar | YouTube Data API `videos.list` | yt-dlp é grátis e tira pressão da quota; API custa 1 unit/chamada (irrelevante mas adiciona dependência de `YOUTUBE_API_KEY`) |
| Switch node | IF node encadeado (skeleton atual) | Skeleton tem 4-5 IFs em paralelo — Switch reduz para 1 node e simplifica diagrama |

**Installation:**
- Não há `pip install` adicional — todas as dependências Python já estão em `requirements.txt` (Phase 2/5)
- Adicionar serviço `cloudflared` em `/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml`
- Adicionar variáveis em `.env`:
  ```env
  TELEGRAM_BOT_TOKEN=
  TELEGRAM_CHAT_ID_ALLOWED=5760918317
  TELEGRAM_WEBHOOK_SECRET=
  CLOUDFLARE_TUNNEL_TOKEN=
  N8N_WEBHOOK_URL=https://n8n.<seudominio>.com.br
  CLIP_PENDING_TTL_HOURS=48
  CLIP_PENDING_WARN_HOURS=24
  ```

## Architecture Patterns

### Recommended Project Structure

```
clip-processor/
├── src/
│   ├── main.py                  # MOD: adiciona job TTL ao scheduler
│   ├── publisher.py             # MOD: 'pending' → 'approved' no SELECT
│   ├── ttl_worker.py            # NOVO: warn 24h, expire 48h (1 job APScheduler)
│   ├── telegram_notifier.py     # NOVO: HTTP POST para webhook n8n (resumo, sucesso, falha)
│   ├── processar.py             # NOVO: parse YouTube URL + yt-dlp metadata + upsert source_videos
│   └── pipeline_runner.py       # MOD opcional: hook de notificação ao publisher (chama notifier)
└── tests/
    ├── test_publisher.py        # MOD: trocar 'pending' por 'approved' nos asserts
    ├── test_ttl_worker.py       # NOVO
    ├── test_telegram_notifier.py# NOVO
    └── test_processar.py        # NOVO

mysql/init/
└── 05-controle-manual-migration.sql  # NOVO: ALTER ENUM (idempotente)

telegram-n8n/workflows/
├── 06-router.json               # NOVO: substitui 01-telegram-handler.json
├── 06-cron-resumo-diario.json   # NOVO: schedule trigger 18h BRT
└── (01-04 ficam para referência histórica, não importados)

# raiz do compose (fora do canaldecortes/):
docker-compose.yml               # MOD: adiciona serviço cloudflared + env do n8n
.env / .env.example              # MOD: 6 novas variáveis
```

### Pattern 1: Telegram Trigger node com Restrict to Chat IDs (allowlist nativa)

**What:** O Trigger node recebe updates direto da API do Telegram e dropa silenciosamente updates fora da allowlist. Substitui o `n8n-nodes-base.webhook` + Code parser do skeleton.

**When to use:** Em todos os fluxos de comando (router principal). Mantém o `webhook` genérico só onde o n8n não tem cobertura (não é o caso aqui).

**Example:**
```json
{
  "parameters": {
    "updates": ["message"],
    "additionalFields": {
      "restrictToChatIds": "={{ $env.TELEGRAM_CHAT_ID_ALLOWED }}",
      "restrictToUserIds": ""
    }
  },
  "id": "telegram-trigger",
  "name": "Telegram Trigger",
  "type": "n8n-nodes-base.telegramTrigger",
  "typeVersion": 1.2,
  "credentials": {
    "telegramApi": { "id": "telegram-canal-decortes", "name": "Telegram Canal de Cortes" }
  }
}
```
Source: https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.telegramtrigger/ + PR #27643

### Pattern 2: Roteador via Switch node + Set node de parsing

**What:** Substitui os 4-5 IFs encadeados por 1 Switch node que decide o output baseado no comando.

**When to use:** Roteamento de comandos do bot. Cada output do Switch leva a um sub-fluxo (`/status`, `/clipes`, `/aprovar`, etc.).

**Example:**
```json
{
  "parameters": {
    "jsCode": "const text = ($input.first().json.message?.text || '').trim();\nconst parts = text.split(/\\s+/);\nconst command = (parts[0] || '').toLowerCase();\nconst arg = parts.slice(1).join(' ').trim();\nreturn [{ json: { command, arg, raw: text, chatId: $input.first().json.message.chat.id } }];"
  },
  "name": "Parse Comando",
  "type": "n8n-nodes-base.code"
},
{
  "parameters": {
    "rules": {
      "values": [
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/status" }] }, "outputKey": "status" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/clipes" }] }, "outputKey": "clipes" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/aprovar" }] }, "outputKey": "aprovar" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/rejeitar" }] }, "outputKey": "rejeitar" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/processar" }] }, "outputKey": "processar" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/ajuda" }] }, "outputKey": "ajuda" }
      ]
    },
    "fallbackOutput": "ajuda"
  },
  "name": "Switch Comando",
  "type": "n8n-nodes-base.switch",
  "typeVersion": 2
}
```

### Pattern 3: Migration idempotente do ENUM (MySQL 8.4)

**What:** Estender o ENUM `generated_clips.status` adicionando `approved` e `rejected`. MySQL trata "adicionar valores ao fim do ENUM" como **operação de metadado** (sem table rebuild) desde que o storage size não mude — verdadeiro aqui, pois o número total de valores fica abaixo do limite que muda 1→2 bytes (255 e 65535 respectivamente).

**When to use:** Wave 0 da fase. Migration roda **antes** do swap em `publisher.py` — garante backward compatibility (publisher antigo continua publicando `pending` durante deploy, novo publisher passa a publicar `approved` após reinício do container).

**Example:**
```sql
-- mysql/init/05-controle-manual-migration.sql
-- Idempotente: re-rodar não faz nada se ENUM já contém os valores
USE clips_automation;

-- ALTER ENUM: adicionar approved e rejected no fim (metadata-only operation no MySQL 8.4)
-- A ordem do ENUM importa para sort; mantemos publishing antes para preservar pipeline atual
ALTER TABLE generated_clips
  MODIFY COLUMN status ENUM(
    'pending_cut', 'pending', 'cutting', 'publishing', 'published', 'failed',
    'approved', 'rejected'
  ) DEFAULT 'pending_cut';
```

Source: MySQL 8.0 Reference Manual §15.1.9 (ALTER TABLE) — "Modifying the definition of an ENUM or SET column by adding new enumeration or set members to the end of the list of valid member values is supported, as long as the storage size of the data type does not change."

### Pattern 4: `/processar <url>` — yt-dlp metadata + upsert idempotente

**What:** Parse da URL em `youtube_video_id`, busca metadata via yt-dlp (sem download), faz INSERT...ON DUPLICATE KEY UPDATE em `source_videos`. O pipeline normal (poll + download + transcribe + ...) cuida do resto.

**When to use:** Comando `/processar`. Roda via `docker exec clip-processor python -m src.processar <url>` chamado do n8n `executeCommand` node.

**Example:**
```python
# clip-processor/src/processar.py
import re, sys, yt_dlp
from src.db import get_db_connection

YOUTUBE_URL_RE = re.compile(
    r'(?:youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|embed\/|v\/)|youtu\.be\/)'
    r'(?P<id>[A-Za-z0-9_-]{11})'
)

def parse_video_id(url: str) -> str | None:
    m = YOUTUBE_URL_RE.search(url)
    return m.group('id') if m else None

def fetch_metadata(video_id: str) -> dict:
    opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
    return {
        'youtube_video_id': info['id'],
        'title': info.get('title', '')[:500],
        'channel_id': info.get('channel_id'),  # YouTube external channel id (UC...)
        'published_at': info.get('upload_date'),  # YYYYMMDD
    }

def upsert_source_video(conn, meta: dict) -> tuple[str, bool]:
    """Retorna (status_atual, created_bool)."""
    with conn.cursor() as cur:
        # Resolver channel_id interno (FK). Se canal não está em source_channels, criar uma linha pseudo.
        cur.execute(
            'SELECT id FROM source_channels WHERE youtube_channel_id = %s',
            (meta['channel_id'],)
        )
        row = cur.fetchone()
        if row:
            internal_channel_id = row['id']
        else:
            cur.execute(
                'INSERT INTO source_channels (youtube_channel_id, channel_name, rss_url, active) '
                'VALUES (%s, %s, %s, FALSE)',
                (meta['channel_id'], f'manual:{meta["channel_id"]}',
                 f'https://www.youtube.com/feeds/videos.xml?channel_id={meta["channel_id"]}')
            )
            internal_channel_id = cur.lastrowid

        # Verificar se já existe
        cur.execute(
            'SELECT status FROM source_videos WHERE youtube_video_id = %s',
            (meta['youtube_video_id'],)
        )
        existing = cur.fetchone()
        if existing:
            return (existing['status'], False)

        cur.execute(
            'INSERT INTO source_videos '
            '(youtube_video_id, channel_id, title, published_at, status) '
            'VALUES (%s, %s, %s, %s, %s)',
            (meta['youtube_video_id'], internal_channel_id, meta['title'],
             meta['published_at'], 'pending')
        )
    conn.commit()
    return ('pending', True)


def main(url: str) -> int:
    video_id = parse_video_id(url)
    if not video_id:
        print(f'ERRO: URL inválida: {url}')
        return 2
    try:
        meta = fetch_metadata(video_id)
    except Exception as exc:
        print(f'ERRO: metadata falhou para {video_id}: {exc}')
        return 3
    conn = get_db_connection()
    try:
        status, created = upsert_source_video(conn, meta)
        verb = 'inserido' if created else 'já existia'
        print(f'OK: {video_id} {verb} — status={status} — título={meta["title"]}')
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ''))
```

### Pattern 5: TTL worker como APScheduler job no clip-processor

**What:** Adicionar um `IntervalTrigger(hours=1)` (ou `CronTrigger(minute=0)`) ao mesmo `BlockingScheduler` de `main.py`. O job:
1. Faz UPDATE em massa: `generated_clips` onde `status='pending'` e `created_at < NOW() - INTERVAL 48 HOUR` → vira `rejected`
2. Lista clipes onde `status='pending'` e `48h - 24h <= idade < 48h` que ainda não receberam warn, envia warn via HTTP para n8n webhook interno

**Decisão (APScheduler vs n8n cron):** APScheduler ganha porque:
- Consistente com o resto do pipeline (Phase 5 já estabeleceu APScheduler como local para jobs autônomos)
- Sem duplicar timezone config (já está em `BlockingScheduler(timezone='America/Sao_Paulo')`)
- Operacional: 1 daemon para acompanhar logs, 1 sinal de SIGTERM para encerrar
- Permite testes pytest diretos (mock Redis/DB) sem subir n8n

**When to use:** Job `ttl_worker` registrado no scheduler de `main.py`.

**Example:**
```python
# clip-processor/src/ttl_worker.py
import os, requests
from datetime import datetime, timedelta
from src.db import get_db_connection

TTL_HOURS = int(os.environ.get('CLIP_PENDING_TTL_HOURS', 48))
WARN_HOURS = int(os.environ.get('CLIP_PENDING_WARN_HOURS', 24))
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', '')  # ex.: https://n8n.dom.com.br/webhook/notify

def run_ttl_once(conn=None):
    own = conn is None
    if own:
        conn = get_db_connection()
    try:
        # 1) Expirar
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE generated_clips "
                "SET status='rejected' "
                "WHERE status='pending' AND created_at < NOW() - INTERVAL %s HOUR",
                (TTL_HOURS,)
            )
            expired = cur.rowcount
        conn.commit()

        # 2) Listar a punto de expirar (entre 24h e 48h, ainda pending)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title FROM generated_clips "
                "WHERE status='pending' "
                "AND created_at < NOW() - INTERVAL %s HOUR "
                "AND created_at > NOW() - INTERVAL %s HOUR",
                (WARN_HOURS, TTL_HOURS)
            )
            soon_to_expire = cur.fetchall()

        # Idempotência do warn: usar Redis SET com TTL = WARN_HOURS para não warn duas vezes
        # (ou adicionar coluna `warned_at` na migration; v1 mantém Redis para evitar mais ALTER)
        # ...
        return {'expired': expired, 'warned': len(soon_to_expire)}
    finally:
        if own:
            conn.close()
```

E em `main.py`:
```python
from src.ttl_worker import run_ttl_once

scheduler.add_job(
    run_ttl_once,
    'interval',
    hours=1,
    id='clip_pending_ttl',
    coalesce=True,
    max_instances=1,
)
```

### Pattern 6: Cloudflare Tunnel via container `cloudflared`

**What:** Adicionar serviço ao docker-compose principal (`/Users/alessandrobm1/develop/server/wordpress/docker-compose.yml`) que conecta-se ao Cloudflare Zero Trust e tunelliza para `n8n:5678`. Após criar o Tunnel no dashboard CF, copiar o token para `.env`.

**When to use:** Quando precisar expor o webhook do Telegram externamente sem abrir porta. Cloudflare termina TLS; tunnel é outbound-only — não há porta inbound no host.

**Example:**
```yaml
# docker-compose.yml (snippet)
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    restart: unless-stopped
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
    networks:
      - internal
    depends_on:
      - n8n

  n8n:
    image: n8nio/n8n:1.100.0
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - GENERIC_TIMEZONE=America/Sao_Paulo
      - TZ=America/Sao_Paulo
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - WEBHOOK_URL=${N8N_WEBHOOK_URL}    # <-- novo: URL pública do tunnel
      - N8N_HOST=${N8N_HOST:-localhost}   # <-- opcional: hostname público
      - N8N_PROTOCOL=https                # <-- novo
    volumes:
      - ./canaldecortes/n8n/data:/home/node/.n8n
    networks:
      - internal
    depends_on:
      - mysql
```

No dashboard Cloudflare Zero Trust:
1. **Networks → Tunnels → Create a Tunnel** (escolher cloudflared)
2. Copiar o token (formato `eyJhIjoiNW...`) para `.env` como `CLOUDFLARE_TUNNEL_TOKEN`
3. **Public Hostname**: subdomain.dominio.com.br → Service: `http://n8n:5678` (usa DNS interno do compose)
4. n8n exigirá `WEBHOOK_URL=https://subdomain.dominio.com.br` para gerar URLs corretas no Telegram Trigger

Source: https://dev.to/kfuras/self-host-n8n-with-cloudflare-zero-trust-and-docker-3e0f

### Pattern 7: Notificações proativas — clip-processor → n8n webhook interno

**What:** O `publisher.py` (e `pipeline_runner.py` em falhas críticas) chama `telegram_notifier.send(event_type, payload)` que POSTa para um **webhook n8n interno** (não exposto via Cloudflare, escutando em `http://n8n:5678/webhook/notify` na rede interna do compose). O workflow n8n recebe o evento e formata + envia via Telegram.

**Why webhook interno vs Telegram API direto:** Manter toda a formatação de mensagens e credencial do bot no n8n (centralização). Clip-processor não precisa conhecer `TELEGRAM_BOT_TOKEN`.

**When to use:** 3 eventos definidos pela decisão:
1. Upload publicado com sucesso (chamado de `publisher._mark_clip_published`)
2. Falha crítica no pipeline (download/transcribe/select/cut/upload) — usa o `except Exception` já existente em `pipeline_runner.py`
3. Aviso de TTL 24h (chamado pelo `ttl_worker`)

**Example:**
```python
# clip-processor/src/telegram_notifier.py
import os, requests

N8N_NOTIFY_URL = os.environ.get('N8N_NOTIFY_URL', 'http://n8n:5678/webhook/notify')

def notify(event_type: str, payload: dict, timeout: float = 5.0) -> bool:
    """Envia evento para o webhook n8n. Não levanta exceções (best-effort)."""
    try:
        resp = requests.post(
            N8N_NOTIFY_URL,
            json={'event': event_type, 'payload': payload},
            timeout=timeout,
        )
        return resp.status_code < 400
    except requests.RequestException as exc:
        print(f'[NOTIFY] warn: falha ao notificar {event_type}: {exc}')
        return False
```

### Pattern 8: Resumo diário 18h BRT (n8n Schedule Trigger)

**What:** Workflow n8n dedicado com `scheduleTrigger` em cron `0 18 * * *` (com timezone do workflow = `America/Sao_Paulo`). Faz query `SELECT COUNT(*) FROM generated_clips WHERE status='pending'`, envia mensagem se count > 0.

**When to use:** Cron 18h diário, conforme decisão.

**Example:**
```json
{
  "parameters": {
    "rule": {
      "interval": [
        { "field": "cronExpression", "expression": "0 18 * * *" }
      ]
    }
  },
  "id": "cron-18h",
  "name": "Cron 18h BRT",
  "type": "n8n-nodes-base.scheduleTrigger",
  "typeVersion": 1.2
}
```
E definir `settings.timezone = "America/Sao_Paulo"` no workflow. Source: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/

### Anti-Patterns to Avoid

- **Parsing manual de chat_id no Code node ignorando o filtro nativo do Trigger** — duplica lógica, escapa de filtros do n8n, mais propenso a bugs. Use `restrictToChatIds` do TelegramTrigger.
- **Hardcoded `5760918317` em workflow JSON commitado** — bagunça allowlist multi-ambiente; leia de `$env.TELEGRAM_CHAT_ID_ALLOWED` em todos os nodes. n8n suporta `={{ $env.VAR }}` em campos de string.
- **Mudar `publisher.py` para suportar `status IN ('pending', 'approved')` durante migração** — viola a decisão "publisher publica apenas approved"; introduz race conditions com o bot. Faça swap atômico: migration + restart do clip-processor.
- **Bypass de quota em `/aprovar`** — viola decisão explícita ("o bot é alavanca, não bypass"). `/aprovar` apenas muda status; o publisher continua respeitando `QuotaManager`.
- **Cleanup imediato do raw video em `/rejeitar`** — decisão explícita: manter raw video para recorte futuro; apagar **apenas** o MP4 do clip.
- **Escrever em `clip_path` arquivo NULL em vez de manter o registro** — preserve o registro com `status='rejected'` (auditoria); apenas remover o arquivo do disco.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Validar webhook do Telegram (autenticidade) | Validador HMAC custom no Code node | Telegram Trigger node nativo + `secret_token` no `setWebhook` (header `X-Telegram-Bot-Api-Secret-Token`) | Bug-prone; o Trigger node valida `bot_id` e o `secret_token` cobre spoof |
| Tunnel HTTPS para expor n8n | nginx + Let's Encrypt + dynamic DNS | Cloudflare Tunnel (`cloudflared`) | Sem porta inbound, TLS termina no CF, gratuito, zero config de renovação |
| Parser de URL do YouTube | Regex próprio "quase certo" | Regex documentado abaixo + fallback yt-dlp | yt-dlp já normaliza várias formas de URL; regex serve como pré-validação rápida |
| Metadata de vídeo arbitrário (`/processar`) | YouTube Data API `videos.list` com OAuth | yt-dlp `extract_info(download=False)` | Gratuito, sem quota; tira pressão das 10.000 units/dia |
| Allowlist por `chat_id` | Code node lendo lista de env var | `restrictToChatIds` no TelegramTrigger node | Implementação nativa do n8n (PR #27643, mar/2026); dropa silenciosamente |
| Cron diário com timezone | crontab no host ou `time.sleep` | `scheduleTrigger` do n8n (workflow timezone) ou APScheduler (`CronTrigger(timezone=...)`) | Ambos honram DST corretamente |
| Constant-time comparison de secret_token | `a == b` (vulnerável a timing) | `hmac.compare_digest` (stdlib) | Padrão de segurança; Trigger node usa internamente |
| Idempotência de "avisei sobre TTL 24h" | Tabela `clip_warnings` MySQL | Redis SET com chave `clip_warned:<id>` e TTL = 24h | Evita ALTER TABLE adicional na fase; coerente com `youtube_uploads:<date>` |

**Key insight:** A maior parte do que parece "código novo" desta fase é **glue code n8n** — quase tudo já existe em forma de node nativo. O Python novo é finito: 3 módulos pequenos (`ttl_worker.py`, `telegram_notifier.py`, `processar.py`) + 1 swap de literal em `publisher.py`.

## Common Pitfalls

### Pitfall 1: Swap de `'pending'` → `'approved'` em `publisher.py` quebra clips legados

**What goes wrong:** Após a migration, há clips em `pending` criados antes do swap. Se o publisher passa direto a buscar só `approved`, eles ficam "presos" — só saem com aprovação manual ou rejeição pelo TTL.

**Why it happens:** Mudança atômica da semântica de `pending` (era "pronto para upload"; vira "aguardando aprovação").

**How to avoid:** Aceitar essa transição como esperada. Após deploy, **enviar `/clipes` no bot** e aprovar/rejeitar manualmente o backlog. Documentar isso no checkpoint operacional. Como confirmação adicional: **Wave 0 da fase deve incluir um script `migrate-pending-clips.sql`** opcional que marca clips legados como `approved` em massa, se o operador quiser pular essa fila inicial.

**Warning signs:** Após deploy, contador "clips publicados hoje" cai para 0; `SELECT COUNT(*) FROM generated_clips WHERE status='pending'` cresce sem que `approved` cresça.

### Pitfall 2: Race condition `/aprovar X` seguido rapidamente de `/rejeitar X`

**What goes wrong:** Dois comandos quase simultâneos: o primeiro muda para `approved`, o segundo tenta mudar para `rejected`. Se o publisher já tiver pego o clip entre os dois, o `rejeitar` ocorre depois do upload.

**Why it happens:** Sem lock de linha; statements separados.

**How to avoid:**
1. Toda mudança de status via bot deve incluir guard na cláusula WHERE:
   - `/aprovar`: `UPDATE generated_clips SET status='approved' WHERE id=%s AND status='pending'`
   - `/rejeitar`: `UPDATE generated_clips SET status='rejected' WHERE id=%s AND status IN ('pending', 'approved')` (rejeita até durante a fila)
2. Após o UPDATE, verificar `rowcount`. Se 0 → mensagem "id X não está em estado válido para esta ação".
3. Publisher já faz `UPDATE ... SET status='publishing' WHERE id=%s` (Phase 5), mas **não** tem guard de status. Para fechar 100% do gap, mudar para `UPDATE ... SET status='publishing' WHERE id=%s AND status='approved'` — se 0 rows, pular o clip silenciosamente.

**Warning signs:** Logs `[PUB] Clip N publicado` seguidos de `/rejeitar N` no histórico do bot.

### Pitfall 3: Regex de YouTube URL deixa Shorts/embed escapar

**What goes wrong:** Regex naive tipo `/v=([^&]+)/` falha para `youtu.be/ID`, `/shorts/ID`, `/embed/ID`, `/v/ID`.

**Why it happens:** YouTube tem ~6 formas oficiais de URL.

**How to avoid:** Use o regex testado (Pattern 4) ou tente parse com `urllib.parse` antes do regex. Sempre validar que o resultado tem exatamente 11 caracteres em `[A-Za-z0-9_-]`. Em caso de dúvida, fazer `yt-dlp` resolver — ele normaliza tudo.

**Warning signs:** `/processar` retorna "URL inválida" em URLs visivelmente válidas.

### Pitfall 4: ALTER TABLE bloqueia se o ENUM atinge limites de storage

**What goes wrong:** MySQL ENUM com até 255 valores cabe em 1 byte; entre 256 e 65535, 2 bytes. Adicionar valores que **mudam o tamanho** força table rebuild com lock.

**Why it happens:** Mudança de armazenamento físico.

**How to avoid:** Estamos passando de 6 para 8 valores no ENUM — bem longe do limite de 255. Operação é metadata-only no MySQL 8.4. **Mas** o padrão do projeto (Phase 3/5) é usar `INFORMATION_SCHEMA` + prepared statements para ADD COLUMN — para ALTER ENUM esse padrão não se aplica; `ALTER TABLE ... MODIFY COLUMN` é a operação direta correta.

**Warning signs:** Migration leva mais de 1 segundo; `SHOW PROCESSLIST` mostra "copy to tmp table".

### Pitfall 5: Cloudflare Tunnel sem `WEBHOOK_URL` no n8n gera URL errada

**What goes wrong:** n8n gera URL de webhook como `http://localhost:5678/webhook/...` que vai pro `setWebhook` do Telegram — Telegram bate em localhost, falha em silêncio.

**Why it happens:** n8n usa `WEBHOOK_URL` env var como prefixo absoluto. Sem ela, usa hostname do container.

**How to avoid:** **Sempre setar `WEBHOOK_URL=https://<seudominio-tunnel>.com.br` no env do n8n**. Reiniciar o container após mudar.

**Warning signs:** `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo` mostra `"url": "http://localhost:5678/..."`.

### Pitfall 6: `cloudflared` no compose mas n8n não exposto no Tunnel

**What goes wrong:** Container `cloudflared` sobe, token autentica no CF Zero Trust, mas o tunnel não tem **Public Hostname** apontando para `http://n8n:5678` (configuração fica no dashboard CF, não no compose).

**How to avoid:** Plan deve incluir um checkpoint manual: "Acessar dashboard CF Zero Trust → Tunnel → Public Hostnames → adicionar route". Após isso, validar com `curl https://<dominio>/webhook-test/ping` que dá HTTP 200.

**Warning signs:** Container `cloudflared` logs "registered tunnel connection" mas Telegram retorna 502/timeout.

### Pitfall 7: TTL worker disparando warn repetidamente

**What goes wrong:** Sem track de "já avisei sobre clip X", o worker rodando a cada hora envia warn 24 vezes durante a janela 24h-48h.

**How to avoid:** Redis SET key `clip_warned:<id>` com TTL = 24h (a partir do warn). Pattern 5 menciona; planner deve detalhar.

### Pitfall 8: TelegramTrigger `restrictToChatIds` aceita string CSV mas exige número inteiro

**What goes wrong:** Configurar `restrictToChatIds: "5760918317, 123"` (com espaços) ou apenas como string pode causar conferência falsa (comparação string vs int do payload).

**How to avoid:** Usar valor único sem espaços. Para múltiplos, separar por vírgula sem espaços. Trigger node faz cast interno para number. Testar enviando `/ajuda` de outro chat — não deve receber resposta.

## Code Examples

Verified patterns from official sources:

### Example 1: Telegram Trigger node com allowlist embutida

```json
{
  "parameters": {
    "updates": ["message"],
    "additionalFields": {
      "restrictToChatIds": "5760918317"
    }
  },
  "id": "tg-trigger",
  "name": "Telegram Trigger",
  "type": "n8n-nodes-base.telegramTrigger",
  "typeVersion": 1.2,
  "credentials": {
    "telegramApi": { "id": "telegram-canal-decortes", "name": "Telegram Canal de Cortes" }
  }
}
```
Source: https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.telegramtrigger/ + PR #27643

### Example 2: setWebhook com secret_token via curl

```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"${N8N_WEBHOOK_URL}/webhook/telegram-canaldecortes\",
    \"secret_token\": \"${TELEGRAM_WEBHOOK_SECRET}\",
    \"allowed_updates\": [\"message\"]
  }"
```
Source: https://core.telegram.org/bots/api#setwebhook

### Example 3: n8n MySQL node — `/aprovar` com guard de status

```json
{
  "parameters": {
    "operation": "executeQuery",
    "query": "UPDATE generated_clips SET status='approved' WHERE id={{ $('Parse Comando').first().json.arg }} AND status='pending'; SELECT ROW_COUNT() AS affected;",
    "additionalFields": {}
  },
  "name": "Aprovar Clip",
  "type": "n8n-nodes-base.mySql",
  "typeVersion": 2,
  "credentials": {
    "mySql": { "id": "mysql-canal-decortes", "name": "MySQL Canal de Cortes" }
  }
}
```

Resposta do bot via IF: se `affected = 1` → "✓ Clip X aprovado"; senão "Clip X não está pendente (id inválido ou já decidido)".

### Example 4: `/rejeitar` chama clip-processor para apagar MP4

n8n usa `executeCommand` node:
```json
{
  "parameters": {
    "command": "docker exec clip-processor python -m src.rejeitar {{ $('Parse Comando').first().json.arg }}"
  },
  "name": "Rejeitar Clip",
  "type": "n8n-nodes-base.executeCommand",
  "typeVersion": 1
}
```

Onde `src.rejeitar` é um pequeno módulo:
```python
# clip-processor/src/rejeitar.py
import os, sys
from src.db import get_db_connection

def rejeitar(clip_id: int) -> int:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT clip_path, status FROM generated_clips WHERE id=%s",
                (clip_id,)
            )
            row = cur.fetchone()
            if not row:
                print(f'ERRO: clip {clip_id} não existe')
                return 1
            if row['status'] not in ('pending', 'approved'):
                print(f'ERRO: clip {clip_id} está em status {row["status"]}')
                return 2

            cur.execute(
                "UPDATE generated_clips SET status='rejected' "
                "WHERE id=%s AND status IN ('pending', 'approved')",
                (clip_id,)
            )
            affected = cur.rowcount
        conn.commit()

        if affected and row['clip_path'] and os.path.exists(row['clip_path']):
            os.remove(row['clip_path'])
            print(f'OK: clip {clip_id} rejeitado, MP4 removido')
        else:
            print(f'OK: clip {clip_id} rejeitado (MP4 não encontrado)')
        return 0
    finally:
        conn.close()

if __name__ == '__main__':
    sys.exit(rejeitar(int(sys.argv[1])))
```

### Example 5: yt-dlp metadata-only

```python
import yt_dlp

opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)

print(info['id'])           # ex.: 'dQw4w9WgXcQ'
print(info['title'])        # ex.: 'Never Gonna Give You Up'
print(info['channel_id'])   # ex.: 'UCuAXFkgsw1L7xaCfnd5JJOw'
print(info['upload_date'])  # ex.: '20091025'
```
Source: https://github.com/yt-dlp/yt-dlp/issues/5412

### Example 6: Switch node para roteamento de comandos

```json
{
  "parameters": {
    "rules": {
      "values": [
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/status" }] }, "outputKey": "status" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/clipes" }] }, "outputKey": "clipes" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/aprovar" }] }, "outputKey": "aprovar" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/rejeitar" }] }, "outputKey": "rejeitar" },
        { "conditions": { "string": [{ "value1": "={{ $json.command }}", "operation": "equals", "value2": "/processar" }] }, "outputKey": "processar" }
      ]
    },
    "fallbackOutput": "0"
  },
  "name": "Roteador",
  "type": "n8n-nodes-base.switch",
  "typeVersion": 2
}
```

### Example 7: TTL worker com warn idempotente

```python
# clip-processor/src/ttl_worker.py
import os, requests, redis
from src.db import get_db_connection

TTL_HOURS = int(os.environ.get('CLIP_PENDING_TTL_HOURS', 48))
WARN_HOURS = int(os.environ.get('CLIP_PENDING_WARN_HOURS', 24))
N8N_NOTIFY_URL = os.environ.get('N8N_NOTIFY_URL', 'http://n8n:5678/webhook/notify')

def run_ttl_once(conn=None, redis_client=None):
    own_db = conn is None
    own_redis = redis_client is None
    if own_db:
        conn = get_db_connection()
    if own_redis:
        redis_client = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'redis'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            decode_responses=True,
        )

    try:
        # 1) Expirar
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE generated_clips SET status='rejected' "
                "WHERE status='pending' AND created_at < NOW() - INTERVAL %s HOUR",
                (TTL_HOURS,)
            )
            expired_count = cur.rowcount
        conn.commit()

        # 2) Listar a punto de expirar
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title FROM generated_clips "
                "WHERE status='pending' "
                "AND created_at < NOW() - INTERVAL %s HOUR "
                "AND created_at > NOW() - INTERVAL %s HOUR",
                (WARN_HOURS, TTL_HOURS)
            )
            soon_to_expire = cur.fetchall()

        warned = 0
        for clip in soon_to_expire:
            key = f'clip_warned:{clip["id"]}'
            if redis_client.set(key, '1', nx=True, ex=24 * 3600):
                # NX = só envia uma vez por janela
                try:
                    requests.post(N8N_NOTIFY_URL, json={
                        'event': 'clip_ttl_warning',
                        'payload': {'clip_id': clip['id'], 'title': clip['title']}
                    }, timeout=5)
                    warned += 1
                except requests.RequestException:
                    pass

        return {'expired': expired_count, 'warned': warned}
    finally:
        if own_db:
            conn.close()
```

### Example 8: cloudflared no docker-compose

```yaml
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    restart: unless-stopped
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
    networks:
      - internal
    depends_on:
      - n8n
```

### Example 9: n8n env vars no docker-compose para Cloudflare Tunnel

```yaml
  n8n:
    image: n8nio/n8n:1.100.0
    environment:
      - GENERIC_TIMEZONE=America/Sao_Paulo
      - TZ=America/Sao_Paulo
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - WEBHOOK_URL=${N8N_WEBHOOK_URL}
      - N8N_HOST=${N8N_HOST}
      - N8N_PROTOCOL=https
      - N8N_PORT=5678
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Webhook node + Code node parser para chat_id allowlist | Telegram Trigger node + `restrictToChatIds` | n8n PR #27643 (mar/2026) | Simplifica 1 node a menos; drop nativo robusto |
| ngrok para expor n8n | Cloudflare Tunnel via `cloudflared` container | Mainstream em 2025-2026 | Sem porta inbound, sem expiração de URL de tunnel, gratuito |
| YouTube Data API search.list para metadata | yt-dlp `extract_info(download=False)` | Sempre disponível | Sem consumir quota; mesma qualidade de dados |
| IF nodes encadeados como roteador | Switch node (typeVersion 2) | n8n 1.0+ | Performance + legibilidade |
| Cron via crontab + script bash | n8n Schedule Trigger ou APScheduler | n8n 1.x / APScheduler 3.x | Honra DST; integra com workflow |

**Deprecated/outdated:**
- ngrok como solução de produção: aceitável apenas para dev local; em produção (mesmo Mac local rodando 24/7), Cloudflare Tunnel é a escolha
- `n8n-nodes-base.webhook` para receber Telegram: ainda funciona, mas perde 2 benefícios do TelegramTrigger (validação `secret_token` automática, allowlist embutida)

## Open Questions

1. **Domínio para o Cloudflare Tunnel**
   - What we know: o tunnel precisa de um hostname público (subdomain de algum domínio gerenciado pelo CF do operador)
   - What's unclear: o operador tem domínio na CF? O plan precisa de um checkpoint manual: "Configurar DNS no dashboard CF"
   - Recommendation: planner deve incluir tarefa de checkpoint manual antes do setWebhook; valor de `N8N_WEBHOOK_URL` é placeholder até esse passo

2. **Reaproveitamento de `01-telegram-handler.json`**
   - What we know: skeleton tem ~360 linhas, com `/buscar`, `/trending`, `/fila`, `/status` roteados via IF
   - What's unclear: vale a pena editar in-place ou começar um novo workflow JSON (`06-router.json`) preservando o histórico?
   - Recommendation: criar `06-router.json` novo (reusa o JS de parse + estrutura geral); arquivar `01-04` em `telegram-n8n/workflows/archive/` para clareza. Esta evolução fica registrada no STATE.md como "Decisão de Fase 6".

3. **Logging de ações do bot**
   - What we know: decisão marcou logging em MySQL (tabela `clip_approvals`) como deferred
   - What's unclear: faz sentido logar via stdout do clip-processor (visível em `docker logs`) ou via Telegram (mensagem de eco)?
   - Recommendation: stdout do clip-processor + eco no Telegram (a própria resposta "Clip X aprovado" serve de log natural). Plan deve adotar essa abordagem mínima.

4. **CLI vs subcomando módulo**
   - What we know: padrão atual usa `docker exec clip-processor python -m src.pipeline_runner`
   - What's unclear: criar 1 entrypoint CLI unificado (`src/cli.py`) com subcomandos `processar`, `rejeitar`, ou módulos separados `src/processar.py`, `src/rejeitar.py`
   - Recommendation: módulos separados (consistente com `pipeline_runner`); planner pode unificar em `src/cli.py` se preferir, mas não é necessário

5. **Migração do backlog de clips em `pending` no momento do swap**
   - What we know: imediatamente após deploy, todos os clips antigos em `pending` ficam aguardando aprovação humana
   - What's unclear: quanto backlog existirá no momento do deploy? Operador quer aprovar manualmente o backlog ou pular?
   - Recommendation: incluir SQL helper opcional `mysql/manual-workflow/approve-backlog.sql` (não-rodado por padrão) com `UPDATE generated_clips SET status='approved' WHERE status='pending' AND created_at < '2026-06-19 00:00:00'`. Operador decide rodar ou não.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (já configurado em `clip-processor/pytest.ini`) |
| Config file | `clip-processor/pytest.ini` (`addopts = -v --tb=short`) |
| Quick run command | `docker exec clip-processor pytest tests/test_<file>.py -x` |
| Full suite command | `docker exec clip-processor pytest tests/ -v` |
| Conftest fixtures | `mock_db_conn`, `mock_redis`, `sample_video_id` (já disponíveis) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| CTRL-01 | TelegramTrigger node configura `restrictToChatIds` e dropa updates fora da allowlist | smoke (workflow JSON validation) | `python -c "import json; w=json.load(open('telegram-n8n/workflows/06-router.json')); assert any(n['type']=='n8n-nodes-base.telegramTrigger' and 'restrictToChatIds' in n['parameters'].get('additionalFields',{}) for n in w['nodes'])"` | Wave 0 (criar `06-router.json`) |
| CTRL-01 | Bot ignora silenciosamente chats fora da allowlist | manual checkpoint | Enviar `/ajuda` de chat secundário → nenhuma resposta em 30s | Manual |
| CTRL-02 | Migration adiciona `approved`/`rejected` ao ENUM sem perder dados | integration (DB) | `docker exec mysql mysql -uclips_user -p$CLIPS_DB_PASSWORD clips_automation -e "SHOW COLUMNS FROM generated_clips LIKE 'status'" | grep -E 'approved.*rejected'` | Wave 0 (criar `05-controle-manual-migration.sql`) |
| CTRL-02 | publisher.py seleciona apenas `approved` | unit | `pytest tests/test_publisher.py::TestPublishApprovedClips -x` | Modificar `tests/test_publisher.py` |
| CTRL-02 | publisher.py respeita quota + janela mesmo para clips approved | unit | `pytest tests/test_publisher.py::TestPublishApprovedClips::test_quota_blocked_leaves_clip_as_approved -x` | Modificar `tests/test_publisher.py` |
| CTRL-03 | `/aprovar` muda `pending` → `approved` apenas em status correto (guard) | unit + integration (n8n MySQL query) | `pytest tests/test_aprovar.py -x` (testa a query SQL via mock) + manual: `mysql -e "UPDATE ... WHERE id=X AND status='pending'"` retorna ROW_COUNT=1 | Wave 0 (criar `tests/test_aprovar.py` — ou apenas validar via SQL no checkpoint) |
| CTRL-03 | `/rejeitar` muda status → `rejected` e remove MP4, preserva raw video | unit | `pytest tests/test_rejeitar.py -x` | Wave 0 (criar `tests/test_rejeitar.py` para `src/rejeitar.py`) |
| CTRL-03 | `/rejeitar` em clip inexistente retorna erro sem efeito | unit | `pytest tests/test_rejeitar.py::test_clip_nao_existe -x` | Wave 0 |
| CTRL-04 | `/processar` extrai video_id de URLs canônicas (watch?v=, youtu.be, shorts/) | unit | `pytest tests/test_processar.py::TestParseVideoId -x` | Wave 0 (criar `tests/test_processar.py`) |
| CTRL-04 | `/processar` é idempotente: vídeo já existente retorna status atual | unit | `pytest tests/test_processar.py::TestUpsertSourceVideo::test_idempotente -x` | Wave 0 |
| CTRL-04 | `/processar` insere com `status='pending'` (não bypassa fluxo) | unit | `pytest tests/test_processar.py::TestUpsertSourceVideo::test_status_pending -x` | Wave 0 |
| CTRL-05 | TTL worker converte `pending` → `rejected` após 48h | unit | `pytest tests/test_ttl_worker.py::TestExpire -x` | Wave 0 (criar `tests/test_ttl_worker.py`) |
| CTRL-05 | TTL worker emite warn 24h antes (uma vez por clip via Redis SET NX) | unit | `pytest tests/test_ttl_worker.py::TestWarn -x` | Wave 0 |
| CTRL-05 | TTL worker idempotente: 2 runs sequenciais não duplicam warns | unit | `pytest tests/test_ttl_worker.py::TestWarn::test_no_warn_duplicado -x` | Wave 0 |
| CTRL-06 | cloudflared service definido no docker-compose com token env | smoke | `grep -A2 cloudflared docker-compose.yml | grep CLOUDFLARE_TUNNEL_TOKEN` | Wave 0 (modificar `docker-compose.yml`) |
| CTRL-06 | n8n WEBHOOK_URL/N8N_PROTOCOL definidos | smoke | `grep -E "WEBHOOK_URL|N8N_PROTOCOL" docker-compose.yml` | Wave 0 |
| CTRL-06 | webhook do Telegram aponta para n8n via tunnel (smoke test) | manual checkpoint | `curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo | jq .result.url` confirma URL do Cloudflare Tunnel | Manual |
| CTRL-06 | Notificação de upload publicado dispara via n8n | unit (telegram_notifier) + manual smoke | `pytest tests/test_telegram_notifier.py -x` (mock requests) + manual: aprovar 1 clip e verificar mensagem chega | Wave 0 (criar `tests/test_telegram_notifier.py`) |
| CTRL-06 | Falha crítica no pipeline dispara notificação | unit | `pytest tests/test_telegram_notifier.py::test_failure_event -x` | Wave 0 |
| CTRL-06 | Resumo diário 18h BRT roda apenas se há clips pending | smoke (workflow JSON) + integration | Validar JSON tem cron `0 18 * * *` + workflow timezone `America/Sao_Paulo` + IF skip-if-zero | Wave 0 (criar `06-cron-resumo-diario.json`) |

### Sampling Rate
- **Per task commit:** `docker exec clip-processor pytest tests/test_<arquivo>.py -x`
- **Per wave merge:** `docker exec clip-processor pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green + manual checkpoints (Telegram + Tunnel + getWebhookInfo) executados e documentados antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `mysql/init/05-controle-manual-migration.sql` — migration ENUM (CTRL-02)
- [ ] `clip-processor/src/processar.py` — skeleton + RED test (CTRL-04)
- [ ] `clip-processor/src/rejeitar.py` — skeleton + RED test (CTRL-03)
- [ ] `clip-processor/src/ttl_worker.py` — skeleton + RED test (CTRL-05)
- [ ] `clip-processor/src/telegram_notifier.py` — skeleton + RED test (CTRL-06)
- [ ] `clip-processor/tests/test_processar.py` — RED imports
- [ ] `clip-processor/tests/test_rejeitar.py` — RED imports
- [ ] `clip-processor/tests/test_ttl_worker.py` — RED imports
- [ ] `clip-processor/tests/test_telegram_notifier.py` — RED imports
- [ ] `clip-processor/tests/test_publisher.py` — adicionar classe `TestPublishApprovedClips` (RED swap)
- [ ] `telegram-n8n/workflows/06-router.json` — esqueleto com TelegramTrigger + Switch (sem implementação completa, só estrutura)
- [ ] `telegram-n8n/workflows/06-cron-resumo-diario.json` — esqueleto com scheduleTrigger 18h
- [ ] `docker-compose.yml` — adicionar serviço `cloudflared` + env vars n8n
- [ ] `.env.example` — adicionar `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID_ALLOWED`, `TELEGRAM_WEBHOOK_SECRET`, `CLOUDFLARE_TUNNEL_TOKEN`, `N8N_WEBHOOK_URL`, `N8N_HOST`, `CLIP_PENDING_TTL_HOURS`, `CLIP_PENDING_WARN_HOURS`, `N8N_NOTIFY_URL`

*Estrutura de teste segue padrão Phase 2/3/5: imports no topo dos `test_*.py` produzem `ModuleNotFoundError` como RED válido até os módulos serem criados.*

## Sources

### Primary (HIGH confidence)

- https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.telegramtrigger/ — Telegram Trigger events list, webhook config, credentials
- https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.telegram/ — Telegram sendMessage operations + parse_mode
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/ — Schedule Trigger timezone (`GENERIC_TIMEZONE` + workflow timezone)
- https://core.telegram.org/bots/api#setwebhook — setWebhook spec, `secret_token`, `X-Telegram-Bot-Api-Secret-Token` header, `allowed_updates`
- https://dev.mysql.com/doc/refman/8.0/en/alter-table.html — ALTER TABLE rules, ENUM add-value-at-end is metadata-only
- https://github.com/n8n-io/n8n/pull/27643 — Telegram Trigger chatId filter fix (mar/2026) — confirms `restrictToChatIds` drops events without resolvable id
- Repo local — `/Users/alessandrobm1/develop/server/wordpress/canaldecortes/clip-processor/src/publisher.py`, `db.py`, `quota_manager.py`, `pipeline_runner.py`, `main.py`, `mysql/init/01-clips-schema.sql`, `03-schema-migration.sql`, `04-publishing-migration.sql`, `tests/conftest.py`, `tests/test_publisher.py`, `tests/test_pipeline_runner.py`, `telegram-n8n/workflows/01-telegram-handler.json`, `n8n/workflows/canaldecortes-pipeline.json`, `telegram-n8n/SETUP.md`

### Secondary (MEDIUM confidence)

- https://dev.to/kfuras/self-host-n8n-with-cloudflare-zero-trust-and-docker-3e0f — docker-compose com cloudflared + env vars n8n (WEBHOOK_URL, N8N_HOST, N8N_PROTOCOL)
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if/ — IF node behavior; comparison para decisão IF vs Switch
- https://apscheduler.readthedocs.io/en/3.x/userguide.html — BlockingScheduler com múltiplos jobs (interval + cron)
- https://github.com/yt-dlp/yt-dlp/issues/5412 — confirmed yt-dlp metadata via `skip_download` + `extract_info(download=False)`

### Tertiary (LOW confidence — flagged for validation)

- https://chriskyfung.github.io/blog/devtools/secure-self-host-n8n-stack/ — pattern alternativo Traefik+Cloudflare (não recomendado aqui; usamos só Tunnel direto)
- https://blog.bothero.ai/telegram-setwebhook-the-90-second-configuration-that-breaks-60-of-small-business-bots-and-how-to-get-it-right-the-first-time — secret_token pattern (cross-checks Telegram docs)
- https://regex101.com/library/fwFZqu — biblioteca de regex de URL YouTube (verificada manualmente contra padrões oficiais)

## Metadata

**Confidence breakdown:**
- Standard stack (n8n, Telegram nodes, MySQL ENUM): HIGH — todas as fontes primárias são docs oficiais; padrões já testados em outras fases do projeto
- Cloudflare Tunnel + n8n compose: MEDIUM — guia community confiável + práticas atuais; planner deve confirmar com checkpoint manual de DNS na CF
- Architecture patterns (TTL worker, notifier): HIGH — código consistente com APScheduler/requests já usados; mocks viáveis
- Pitfalls: HIGH — derivados diretamente de comportamento conhecido do MySQL + lifecycle do publisher.py existente
- Validation architecture: HIGH — segue padrão Phase 2/3/5 (RED imports, mock_db_conn, fixtures conftest)

**Research date:** 2026-06-19
**Valid until:** 2026-07-19 (30 dias — estável, exceto eventuais mudanças no n8n Telegram Trigger node que merecem re-verificação se ocorrerem após esta data)
