# Phase 7: Schema Multi-Canal + Python Pipeline - Research

**Researched:** 2026-06-22
**Domain:** Python pipeline extensions — MySQL migrations, Redis quota, FFmpeg watermark, OAuth multi-channel, blacklist guard
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Schema `destination_channels`:** Tabela MySQL (não ENV vars) com slug, name, niche, youtube_channel_id, credit_template, active. Path do token e watermark derivados do slug por convenção — não ficam no banco.
- **OAuth por canal:** `youtube/token-{slug}.json` por convenção; `YouTubeUploader` recebe `channel_slug` e lê `f'/app/youtube/token-{channel_slug}.json'`. `DEFAULT_TOKEN_FILE = '/app/token.json'` permanece como fallback.
- **Ferramenta OAuth:** `python -m src.youtube_oauth --channel <slug>` — gera `token-{slug}.json`.
- **Watermark:** PNG com alpha, path `/app/branding/watermark-{slug}.png`, volume `./branding:/app/branding:ro`, posição canto superior direito (`overlay=W-w-20:20`), edge case ausente → log warning + continua sem watermark.
- **Blacklist:** Coluna `blacklisted BOOLEAN DEFAULT FALSE` em `source_channels` + INDEX; guard em `rss_poller.py` antes do download; sem purga retroativa.
- **Redis quota por canal:** Key `youtube_uploads:{channel_id}:{date}` (substitui `youtube_uploads:{date}`); `QuotaManager` recebe `channel_id` no construtor.
- **Créditos:** `destination_channels.credit_template`; adicionados programaticamente após geração do Claude; `source_channels` ganha `channel_handle VARCHAR(100)`.
- **Roteamento:** `source_channels.target_niche` → `destination_channels WHERE niche = target_niche`; join simples no publisher.
- **Scope:** Apenas `mysql/init/`, `clip-processor/src/`. Painel Laravel fica na Fase 8.

### Claude's Discretion

- Ordem exata dos filtros FFmpeg (watermark antes ou depois do burn_subtitles)
- Mensagem de log exata quando canal blacklistado é bloqueado
- Estrutura interna do `youtube_oauth` helper (wizard interativo vs flags diretas)
- Estratégia de retry quando token OAuth expira durante upload (1 tentativa de refresh antes de notificar)

### Deferred Ideas (OUT OF SCOPE)

- Dashboard de status de OAuth pelo painel (Fase 8)
- Toggle de `blacklisted` pelo painel sem SQL (Fase 8)
- Múltiplos nichos por canal-fonte
- Rate limiting por canal-fonte
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MCAN-01 | Sistema suporta múltiplos canais YouTube de destino, cada um com token OAuth próprio e GCP Project separado | OAuth por canal via `token-{slug}.json`; `YouTubeUploader` parametrizado por slug; migration cria `destination_channels` |
| MCAN-02 | Canais-fonte têm campo `niche` que determina qual canal-destino recebe o clip | Coluna `target_niche` em `source_channels`; JOIN com `destination_channels.niche` no publisher |
| MCAN-03 | Cota de uploads é independente por canal-destino (3/dia por canal) | Redis key `youtube_uploads:{channel_id}:{date}`; `QuotaManager` estendido com `channel_id` |
| MCAN-04 | Pipeline publica automaticamente 3 vídeos/dia por canal no horário 19h-22h BRT | `MAX_UPLOADS_PER_DAY` padrão mudado de 2 → 3 por canal; janela 19h-22h já implementada |
| COPY-01 | Watermark/logo queimado no clip via FFmpeg após geração das legendas | Filtro FFmpeg `overlay=W-w-20:20` com PNG alpha; passo adicional em `video_processor.py` |
| COPY-02 | Descrição gerada pelo Claude inclui créditos do canal original | `credit_template` de `destination_channels` + `channel_handle` de `source_channels`; append pós-Claude em `metadata_generator.py` |
| COPY-03 | Canais blacklistados bloqueados no RSS poller antes do download | Coluna `blacklisted` em `source_channels`; filtro `WHERE active=TRUE AND blacklisted=FALSE` no SELECT do poller |
</phase_requirements>

---

## Summary

A Fase 7 é uma fase de extensão do pipeline Python existente — nenhum novo serviço ou framework é introduzido. Todo o trabalho é dentro dos arquivos `clip-processor/src/` já estabelecidos e de uma nova migration SQL. O padrão arquitetural já está validado nas Fases 2-6: injeção de dependência nos construtores para testabilidade, `INFORMATION_SCHEMA` + prepared statements para migrations idempotentes no MySQL 8.4, e `_key(now, channel_id)` no Redis para namespacing.

O maior risco técnico é a propagação do `destination_channel` object por todas as camadas do pipeline: o `publisher.py` precisa fazer o JOIN para descobrir o canal-destino de cada clip, instanciar `QuotaManager` e `YouTubeUploader` parametrizados por canal, e passar o `credit_template` para o `metadata_generator`. A cadeia de dados é longa mas cada elo já tem seu padrão de injeção estabelecido.

O segundo risco é a ordem dos filtros FFmpeg para watermark + legendas. A approach correta é encadear os dois filtros num único passo usando `filter_complex` ou `vf` com vírgula, ou aplicar em dois passes separados. Dois passes separados (já é o padrão do `burn_subtitles`) são mais simples de testar e manter — o watermark entra como um segundo passo após `burn_subtitles`, seguindo o padrão já usado para legendas.

**Recomendação primária:** Extender cada módulo na ordem de dependência: migration SQL → `quota_manager.py` → `uploader.py` → `rss_poller.py` → `video_processor.py` → `metadata_generator.py` → `publisher.py` → `youtube_oauth` helper.

---

## Standard Stack

### Core (tudo já no projeto — sem novas dependências)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pymysql | current | MySQL 8.4 migrations e queries | Já em requirements.txt; padrão do projeto |
| redis-py | current | Redis key `youtube_uploads:{channel_id}:{date}` | Já em requirements.txt; padrão Fases 2-6 |
| google-api-python-client | current | YouTube Data API v3 upload por canal | Já em requirements.txt; padrão Phase 5 |
| google-auth-oauthlib | current | OAuth flow para `youtube_oauth` helper | Já em requirements.txt; usado em `youtube/generate_token.py` existente |
| subprocess (stdlib) | N/A | FFmpeg via `subprocess.run(check=True)` | Padrão de `video_processor.py` Fases 4-6 |

### Sem novas dependências necessárias

Todos os pacotes necessários já estão em `requirements.txt`. A Fase 7 não requer `pip install` de nada novo.

---

## Architecture Patterns

### Recommended Structure (adições Fase 7)

```
clip-processor/src/
├── quota_manager.py        # EXTEND: channel_id no construtor e na _key()
├── uploader.py             # EXTEND: channel_slug → token-{slug}.json
├── rss_poller.py           # EXTEND: blacklist guard + target_niche no SELECT
├── video_processor.py      # EXTEND: overlay_watermark() antes/depois burn_subtitles
├── metadata_generator.py   # EXTEND: append_credits() após generate_metadata()
├── publisher.py            # EXTEND: JOIN destination_channels + loop por canal
└── youtube_oauth.py        # NEW: python -m src.youtube_oauth --channel <slug>

mysql/init/
└── 06-multi-canal-migration.sql   # NEW: destination_channels + ALTER source_channels

branding/                   # NEW: volume bind mount (criado pelo operador)
├── watermark-futebol-em-cortes.png
└── watermark-podcast-cortes.png

youtube/
├── token.json              # existente (fallback Phase 5)
├── token-futebol-em-cortes.json   # gerado pelo youtube_oauth helper
└── token-podcast-cortes.json      # gerado pelo youtube_oauth helper
```

### Pattern 1: Migration idempotente no MySQL 8.4

**What:** INFORMATION_SCHEMA check + prepared statement — padrão estabelecido nas Fases 3, 4, 5.
**When to use:** Sempre que ADD COLUMN; para CREATE TABLE usar IF NOT EXISTS.

```sql
-- Source: mysql/init/03-schema-migration.sql (padrão estabelecido)
SET @has_col = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'source_channels'
    AND COLUMN_NAME = 'target_niche'
);
SET @sql = IF(
  @has_col = 0,
  'ALTER TABLE source_channels ADD COLUMN target_niche VARCHAR(50) NULL AFTER channel_name',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
```

Para o ENUM de `generated_clips`, o padrão é MODIFY COLUMN com o ENUM completo (idempotente — MySQL não muda se já está no estado final):

```sql
-- Adicionar coluna destination_channel_id ao generated_clips
ALTER TABLE generated_clips
  MODIFY COLUMN status ENUM(...) DEFAULT 'pending_cut';  -- sem mudança necessária Phase 7
```

### Pattern 2: QuotaManager estendido com channel_id

**What:** Adicionar `channel_id` como parâmetro do construtor; `_key()` retorna `youtube_uploads:{channel_id}:{date}`.
**When to use:** Cada instância de `QuotaManager` representa a quota de um canal-destino específico.

```python
# Extensão de clip-processor/src/quota_manager.py
class QuotaManager:
    def __init__(self, redis_client, max_uploads_per_day: int | None = None, channel_id: str | None = None):
        self.redis_client = redis_client
        self.channel_id = channel_id  # None = modo legado (fallback Phase 5)
        self.max_uploads_per_day = self._resolve_limit(max_uploads_per_day)
        self._max = self.max_uploads_per_day

    def _key(self, now: datetime) -> str:
        date_str = now.strftime('%Y-%m-%d')
        if self.channel_id:
            return f'youtube_uploads:{self.channel_id}:{date_str}'
        return f'youtube_uploads:{date_str}'  # fallback retrocompat
```

### Pattern 3: YouTubeUploader parametrizado por channel_slug

**What:** `channel_slug` resolve o path do token via convenção; retrocompatibilidade mantida via `DEFAULT_TOKEN_FILE`.
**When to use:** Toda instanciação de `YouTubeUploader` para um canal-destino específico.

```python
# Extensão de clip-processor/src/uploader.py
DEFAULT_TOKEN_FILE = '/app/token.json'

class YouTubeUploader:
    def __init__(self, token_file=None, channel_slug=None, ...):
        if channel_slug:
            self.token_file = f'/app/youtube/token-{channel_slug}.json'
        else:
            self.token_file = token_file or os.environ.get('YOUTUBE_TOKEN_FILE', DEFAULT_TOKEN_FILE)
```

### Pattern 4: Watermark FFmpeg com overlay=W-w-20:20

**What:** Passo adicional em `video_processor.py` após `burn_subtitles`. PNG com alpha no canto superior direito.
**When to use:** Sempre que `watermark_path` existir em disco para o canal-destino.

```python
# Novo método em clip-processor/src/video_processor.py
def overlay_watermark(input_path: str, watermark_path: str, output_path: str) -> str:
    """Queima watermark PNG (com alpha) no canto superior direito do clip."""
    if not os.path.exists(watermark_path):
        _log(f'AVISO: watermark não encontrado em {watermark_path} — pulo overlay')
        return input_path  # retorna input sem modificar

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    subprocess.run(
        [
            'ffmpeg',
            '-i', input_path,
            '-i', watermark_path,
            '-filter_complex', 'overlay=W-w-20:20',
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-c:a', 'copy',
            output_path,
            '-y',
        ],
        check=True,
        capture_output=True,
    )
    return output_path
```

**Ordem no `process_clip()`:** `burn_subtitles` → `overlay_watermark` → arquivo final. Isso garante que o watermark fica sobre as legendas, não embaixo. A variável intermediária `watermarked_path` é gerada como `{clip_id}_watermarked.mp4` e removida ao final.

**Nota sobre `-filter_complex` vs `-vf`:** Para inputs múltiplos (clip + watermark PNG como streams separados), `-filter_complex` é obrigatório. `-vf` funciona apenas com um input.

### Pattern 5: Append de créditos em metadata_generator.py

**What:** Créditos adicionados programaticamente após `generate_metadata()` — separação entre conteúdo IA e compliance.
**When to use:** Sempre, independente do que Claude retornar.

```python
# Extensão de clip-processor/src/metadata_generator.py
def append_credits(description: str, credit_template: str, channel_handle: str) -> str:
    """Adiciona linha de créditos ao final da descrição. Nunca sobrescreve conteúdo existente."""
    if not credit_template or not channel_handle:
        return description
    credits_line = credit_template.format(channel_handle=channel_handle)
    return f'{description}\n\n{credits_line}'
```

### Pattern 6: Blacklist guard no rss_poller.py

**What:** Filtro `WHERE active = TRUE AND blacklisted = FALSE` no SELECT de canais. Log antes de bloquear individual entries.
**When to use:** Substituição direta do SELECT existente em `poll_all_channels`.

```python
# Extensão de clip-processor/src/rss_poller.py
# SELECT atual:
cur.execute('SELECT id, channel_name, rss_url FROM source_channels WHERE active = TRUE')

# SELECT Phase 7 (adiciona blacklisted filter):
cur.execute(
    'SELECT id, channel_name, rss_url, target_niche '
    'FROM source_channels '
    'WHERE active = TRUE AND blacklisted = FALSE'
)
```

**Nota:** O guard está no SELECT de canais ativos, não por entrada individual do feed. Isso é correto: um canal blacklisted não é processado de forma alguma, não apenas seus vídeos individuais são bloqueados.

### Pattern 7: publisher.py com loop por canal-destino

**What:** `publisher.py` passa a iterar por canais-destino ativos, instanciar `QuotaManager` e `YouTubeUploader` por canal, e buscar clips roteados para esse canal.

```python
# publisher.py — novo fluxo multi-canal
def publish_pending_clips(conn, redis_client, uploader=None, quota_manager=None, now=None) -> int:
    """Itera por canais-destino ativos e publica clips roteados para cada um."""
    destination_channels = _fetch_destination_channels(conn)
    total_published = 0

    for dest_channel in destination_channels:
        channel_uploader = uploader or YouTubeUploader(channel_slug=dest_channel['slug'])
        channel_quota = quota_manager or QuotaManager(redis_client, channel_id=dest_channel['youtube_channel_id'])

        clips = _fetch_pending_clips_for_channel(conn, dest_channel['id'])
        for clip in clips:
            # ... lógica existente, usando channel_uploader e channel_quota
            total_published += _publish_one(conn, clip, channel_uploader, channel_quota, dest_channel, now)

    return total_published


def _fetch_destination_channels(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute('SELECT id, slug, name, niche, youtube_channel_id, credit_template FROM destination_channels WHERE active = TRUE')
        return cur.fetchall()


def _fetch_pending_clips_for_channel(conn, destination_channel_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.source_video_id, gc.clip_path, gc.thumbnail_path, '
            'gc.title, gc.description, gc.tags, sv.local_path AS source_local_path, '
            'sc.channel_handle '
            'FROM generated_clips gc '
            'JOIN source_videos sv ON sv.id = gc.source_video_id '
            'JOIN source_channels sc ON sc.id = sv.channel_id '
            'WHERE gc.status = %s '
            'AND gc.destination_channel_id = %s '
            'AND gc.clip_path IS NOT NULL '
            'AND gc.title IS NOT NULL '
            'ORDER BY gc.created_at ASC',
            (_publishable_status(), destination_channel_id),
        )
        return cur.fetchall()
```

**Nota sobre `destination_channel_id` em `generated_clips`:** O clip precisa saber para qual canal-destino foi roteado. Isso ocorre em `process_clip()` (via `video_processor.py`) que já faz o JOIN com `source_channels` para obter `target_niche`. O roteamento (`INSERT` do `destination_channel_id` em `generated_clips`) acontece no momento em que os clips são inseridos por `insert_selected_moments()` em `selector.py` — que precisa ser estendido para fazer o JOIN com `destination_channels` e salvar o `destination_channel_id`.

### Anti-Patterns to Avoid

- **Não colocar `channel_slug` ou `watermark_path` no banco:** Path derivado de convenção é determinístico e não requer migração quando muda. O padrão do projeto (ver CONTEXT.md) define isso explicitamente.
- **Não fazer retry automático de OAuth expirado sem notificação:** Token expirado silencioso fará o canal parar de publicar sem log visível. Notificar via `telegram_notifier.notify('oauth_expired', ...)` antes de desistir.
- **Não instanciar um único `QuotaManager` para todos os canais:** A quota é por canal-destino; instanciar um QM global reintroduz o bug que MCAN-03 resolve.
- **Não usar `-vf` com dois inputs no FFmpeg:** `-filter_complex` é obrigatório para overlay de imagem sobre vídeo (dois inputs distintos).
- **Não fazer purga retroativa de vídeos de canal blacklistado:** Decision explícita no CONTEXT.md — vídeos já enfileirados continuam.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth flow para novo canal | Novo fluxo OAuth custom | Reusar `InstalledAppFlow` do `google-auth-oauthlib` (já em requirements.txt; padrão de `youtube/generate_token.py`) | Edge cases de redirect URI, PKCE, refresh — já tratados |
| Watermark PNG com transparência | Manipulação manual de pixels | FFmpeg `-filter_complex overlay=W-w-20:20` com PNG alpha | FFmpeg já instalado no container; PNG alpha funciona sem flags extras |
| Namespace Redis por canal | Custom serialização da key | Convenção `youtube_uploads:{channel_id}:{date}` no `_key()` | Simples, testável, sem novas dependências |
| Template de créditos | Motor de templates | `str.format(channel_handle=...)` nativo do Python | Único campo de interpolação; motor de templates seria over-engineering |

---

## Common Pitfalls

### Pitfall 1: `destination_channel_id` precisa ser salvo em `generated_clips` no momento da seleção

**What goes wrong:** Se o roteamento for feito apenas no `publisher.py` na hora do upload, um clip publicado no canal errado causa perda de quota e possível ban de conta.
**Why it happens:** O roteamento parece ser responsabilidade do publisher, mas o clip já nasce com destino definido (nicho do canal-fonte é imutável).
**How to avoid:** Estender `insert_selected_moments()` em `selector.py` para fazer o JOIN `source_channels → destination_channels` e persistir `destination_channel_id` em cada clip inserido. `generated_clips` ganha coluna `destination_channel_id INT` com FK para `destination_channels`.
**Warning signs:** `_fetch_pending_clips_for_channel()` retorna clips de nichos misturados.

### Pitfall 2: `overlay=W-w-20:20` referencia dimensões do **primeiro** input

**What goes wrong:** Em `-filter_complex`, `W` e `w` se referem ao input stream que precede o overlay. Se a ordem dos inputs for `ffmpeg -i watermark.png -i clip.mp4`, então `W` é a largura do PNG, não do vídeo.
**Why it happens:** A documentação do FFmpeg usa `W`/`H` para o overlay target e `w`/`h` para o overlay source, mas a ordem dos streams importa.
**How to avoid:** Sempre usar `ffmpeg -i clip.mp4 -i watermark.png -filter_complex 'overlay=W-w-20:20'` — clip primeiro, watermark segundo. `W` = largura do clip (1080px), `w` = largura do watermark PNG.
**Warning signs:** Watermark aparece cortado ou em posição errada no vídeo final.

### Pitfall 3: Retrocompatibilidade do `QuotaManager` — testes existentes quebram

**What goes wrong:** `test_quota_manager.py` e `test_publisher.py` instanciam `QuotaManager(redis)` sem `channel_id`. Se o construtor exigir `channel_id`, todos os 15+ testes existentes quebram imediatamente.
**Why it happens:** O `channel_id` é um novo parâmetro opcional, mas o `_key()` precisa do comportamento legado quando ele é `None`.
**How to avoid:** `channel_id=None` é default; `_key()` usa fallback `youtube_uploads:{date}` quando `channel_id` é None (conforme código de exemplo no Pattern 2 acima). Todos os testes existentes continuam passando sem modificação.
**Warning signs:** `pytest tests/test_quota_manager.py` falha com `TypeError: __init__() got unexpected keyword argument`.

### Pitfall 4: `burn_subtitles` e `overlay_watermark` criam arquivos intermediários

**What goes wrong:** `process_clip()` atual usa `raw_clip_path` → `burn_subtitles` → `final_clip_path`. Com watermark, a cadeia é `raw_clip_path` → `burn_subtitles` → `subtitled_clip_path` → `overlay_watermark` → `final_clip_path`. Se `overlay_watermark` falhar ou não existir watermark, o arquivo intermediário `subtitled_clip_path` fica em disco.
**How to avoid:** Tratar o retorno de `overlay_watermark` — se retornar o `input_path` (watermark ausente), simplesmente renomear/mover para `final_clip_path`. Limpar arquivo intermediário `subtitled_clip_path` em ambos os casos.
**Warning signs:** Acúmulo de arquivos `_subtitled.mp4` em `/app/videos/clips/`.

### Pitfall 5: Token OAuth em modo Testing expira em 7 dias

**What goes wrong:** OAuth app em modo Testing do Google Cloud Console expira o refresh_token após 7 dias, causando falha silenciosa de upload.
**Why it happens:** Google limita tokens de apps não verificadas. Já documentado como blocker em STATE.md.
**How to avoid:** Ao configurar o segundo canal, iniciar processo de verificação Production imediatamente (leva 2-4 semanas). Para desenvolvimento, reautenticar o token semanalmente com `python -m src.youtube_oauth --channel <slug>`.
**Warning signs:** Upload falha com `invalid_grant` ou `Token has been expired or revoked` no log.

### Pitfall 6: `generated_clips` JOIN para `source_channels` precisa de `channel_handle`

**What goes wrong:** `metadata_generator.append_credits()` precisa do `channel_handle` do canal-fonte. Se o SELECT em `_fetch_pending_clips_for_channel()` não incluir o JOIN com `source_channels`, o campo não estará disponível.
**Why it happens:** O `SAMPLE_CLIP` em `test_publisher.py` não tem `channel_handle` — os testes existentes passarão mesmo sem o campo, mas produção terá créditos vazios.
**How to avoid:** SELECT explícito de `sc.channel_handle` no JOIN de `_fetch_pending_clips_for_channel()`. Testes novos devem incluir `channel_handle` no `SAMPLE_CLIP`.

---

## Code Examples

Verified patterns from existing codebase:

### Migration idempotente ADD COLUMN (padrão Fase 3)
```sql
-- Source: mysql/init/03-schema-migration.sql
SET @has_col = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'source_channels'
    AND COLUMN_NAME = 'blacklisted'
);
SET @sql = IF(
  @has_col = 0,
  'ALTER TABLE source_channels ADD COLUMN blacklisted BOOLEAN DEFAULT FALSE',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
```

### QuotaManager _key() com channel_id (extensão do existente)
```python
# Source: clip-processor/src/quota_manager.py (extensão)
def _key(self, now: datetime) -> str:
    date_str = now.strftime('%Y-%m-%d')
    if self.channel_id:
        return f'youtube_uploads:{self.channel_id}:{date_str}'
    return f'youtube_uploads:{date_str}'  # retrocompat fallback
```

### burn_subtitles — padrão FFmpeg via subprocess (existente)
```python
# Source: clip-processor/src/video_processor.py
subprocess.run(
    ['ffmpeg', '-i', input_clip_path, '-vf', subtitle_filter, '-c:v', 'libx264',
     '-preset', 'veryfast', '-crf', '23', '-c:a', 'copy', output_path, '-y'],
    check=True,
    capture_output=True,
)
```

### overlay_watermark — padrão novo (dois inputs = filter_complex)
```python
# clip-processor/src/video_processor.py (novo método)
subprocess.run(
    ['ffmpeg', '-i', input_path, '-i', watermark_path,
     '-filter_complex', 'overlay=W-w-20:20',
     '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-c:a', 'copy',
     output_path, '-y'],
    check=True,
    capture_output=True,
)
```

### Injeção de dependência nos testes (padrão do projeto)
```python
# Source: clip-processor/tests/test_publisher.py
with patch('src.publisher.QuotaManager') as MockQuota:
    MockQuota.return_value.can_upload.return_value = True
    result = publish_pending_clips(conn, redis, uploader=uploader, now=dt_sp(20))
```

### Notify OAuth expirado (reusar telegram_notifier existente)
```python
# Source: clip-processor/src/telegram_notifier.py (padrão Phase 6)
from src.telegram_notifier import notify
notify('oauth_expired', {'channel_slug': slug, 'token_path': token_path})
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `youtube_uploads:{date}` Redis key | `youtube_uploads:{channel_id}:{date}` | Fase 7 | Quota independente por canal; fallback None mantém retrocompat |
| Single `token.json` | `token-{slug}.json` por canal | Fase 7 | Múltiplos canais sem conflito de credenciais |
| `burn_subtitles` como etapa final de vídeo | `burn_subtitles` → `overlay_watermark` → final | Fase 7 | Compliance COPY-01; arquivo intermediário necessário |
| `generated_clips` sem `destination_channel_id` | `generated_clips` com `destination_channel_id FK` | Fase 7 | Roteamento correto no publisher; verificável via campo |
| `source_channels` sem `target_niche`, `channel_handle`, `blacklisted` | 3 novas colunas | Fase 7 | Roteamento MCAN-02, créditos COPY-02, blacklist COPY-03 |

---

## Open Questions

1. **`selector.py` precisa de acesso à tabela `destination_channels` para resolver o roteamento?**
   - What we know: `insert_selected_moments()` em `selector.py` insere em `generated_clips`; se precisar persistir `destination_channel_id`, precisa de JOIN com `destination_channels` via `source_channels.target_niche`.
   - What's unclear: `selector.py` recebe `source_video_id` mas não `channel_id` do canal-fonte — precisa de um SELECT adicional para obter o `target_niche` e depois o `destination_channel_id`.
   - Recommendation: Adicionar `source_channel_id` como parâmetro opcional de `insert_selected_moments()`, ou fazer o JOIN internamente. Alternativa: mover o roteamento para `rss_poller._process_ai_pipeline()` que já tem acesso à linha completa do canal-fonte.

2. **`process_clip()` em `video_processor.py` precisa de `channel_slug` para saber qual watermark usar?**
   - What we know: `process_clip()` recebe `conn` e `clip_id`; atualmente faz JOIN com `source_videos` mas não com `destination_channels`.
   - What's unclear: O watermark path é derivado do slug do canal-destino. `process_clip()` precisaria de um JOIN adicional: `generated_clips → destination_channel_id → destination_channels.slug`.
   - Recommendation: Adicionar o campo `destination_channel_slug` no SELECT de `_fetch_clip()` via JOIN com `destination_channels`. Isso requer que `destination_channel_id` já esteja em `generated_clips` (ver open question 1).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (com pytest-mock) |
| Config file | `clip-processor/pytest.ini` |
| Quick run command | `docker exec clip-processor python -m pytest tests/test_quota_manager.py tests/test_publisher.py tests/test_rss_poller.py tests/test_video_processor.py -x -q` |
| Full suite command | `docker exec clip-processor python -m pytest -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MCAN-01 | `YouTubeUploader(channel_slug='futebol-em-cortes')` lê `token-futebol-em-cortes.json` | unit | `pytest tests/test_uploader.py -x -k channel_slug` | ❌ Wave 0 |
| MCAN-02 | `_fetch_pending_clips_for_channel(conn, dest_id)` filtra por `destination_channel_id` | unit | `pytest tests/test_publisher.py -x -k destination_channel` | ❌ Wave 0 |
| MCAN-03 | `QuotaManager(redis, channel_id='UCxxx')._key(now)` retorna `youtube_uploads:UCxxx:2026-06-22` | unit | `pytest tests/test_quota_manager.py -x -k channel_id` | ❌ Wave 0 |
| MCAN-04 | Dois canais ativos com quota 3/dia; atingir 3 no canal A não bloqueia canal B | unit | `pytest tests/test_publisher.py -x -k multi_canal` | ❌ Wave 0 |
| COPY-01 | `overlay_watermark(input, wm, out)` chama FFmpeg com `filter_complex overlay=W-w-20:20` | unit | `pytest tests/test_video_processor.py -x -k watermark` | ❌ Wave 0 |
| COPY-01 | `overlay_watermark` com watermark ausente retorna `input_path` sem chamar FFmpeg | unit | `pytest tests/test_video_processor.py -x -k watermark_missing` | ❌ Wave 0 |
| COPY-02 | `append_credits(desc, template, handle)` adiciona linha de créditos ao final da descrição | unit | `pytest tests/test_metadata_generator.py -x -k credits` | ❌ Wave 0 |
| COPY-03 | `poll_all_channels` com canal `blacklisted=TRUE` → `insert_video` não chamado | unit | `pytest tests/test_rss_poller.py -x -k blacklist` | ❌ Wave 0 — EXTEND test_rss_poller.py |

### Sampling Rate

- **Per task commit:** `docker exec clip-processor python -m pytest tests/ -x -q --tb=short`
- **Per wave merge:** `docker exec clip-processor python -m pytest -v`
- **Phase gate:** Full suite green antes do `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_quota_manager.py` — adicionar testes com `channel_id` parameter (MCAN-03)
- [ ] `tests/test_uploader.py` — adicionar testes com `channel_slug` parameter (MCAN-01)
- [ ] `tests/test_publisher.py` — adicionar `destination_channel_id` ao `SAMPLE_CLIP` e testes multi-canal (MCAN-02, MCAN-04)
- [ ] `tests/test_video_processor.py` — adicionar testes de `overlay_watermark` com mocker de subprocess (COPY-01)
- [ ] `tests/test_metadata_generator.py` — adicionar testes de `append_credits()` (COPY-02)
- [ ] `tests/test_rss_poller.py` — adicionar testes de blacklist guard no SELECT (COPY-03)

Todos são extensões de arquivos existentes — nenhum arquivo de teste novo necessário.

---

## Sources

### Primary (HIGH confidence)

- Código-fonte do projeto em `clip-processor/src/` — lido diretamente nesta sessão
- `mysql/init/03-schema-migration.sql`, `04-publishing-migration.sql`, `05-controle-manual-migration.sql` — padrão de migration idempotente verificado
- `clip-processor/tests/` — padrões de teste verificados (injeção de dependência, mocks, fixtures)
- `.planning/phases/07-schema-multi-canal-python-pipeline/07-CONTEXT.md` — decisões locked verificadas
- `.planning/STATE.md` — histórico de decisões e blockers documentados

### Secondary (MEDIUM confidence)

- FFmpeg documentation — `overlay` filter com dois inputs requer `-filter_complex` (não `-vf`); `W`/`H` referencia dimensões do video input quando clip é o primeiro stream. Verificado via conhecimento técnico de FFmpeg consolidado.

### Tertiary (LOW confidence)

- Nenhum item nesta categoria.

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — todos os pacotes já estão em `requirements.txt`; zero novas dependências
- Architecture: HIGH — padrões verificados diretamente no código-fonte das Fases 3-6
- Pitfalls: HIGH (técnicos) / MEDIUM (OAuth Testing expiry) — baseados em código real e STATE.md
- Migration SQL: HIGH — padrão INFORMATION_SCHEMA + prepared statements verificado em 3 arquivos

**Research date:** 2026-06-22
**Valid until:** 2026-09-22 (stack estável; sem dependências externas novas)
