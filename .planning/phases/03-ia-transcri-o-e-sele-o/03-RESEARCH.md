# Phase 3: IA — Transcrição e Seleção - Research

**Researched:** 2026-06-18
**Domain:** Groq Whisper API (transcrição) + Anthropic Claude Haiku 4.5 (seleção de momentos)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Trigger:** Transcrição e seleção disparadas no mesmo poll (rss_poller), fluxo linear download → transcribing → selecting → (fila de corte). Sem job separado no scheduler.
- **Armazenamento:** JSON de transcrição salvo em disco: `videos/{youtube_video_id}_transcript.json`. Banco MySQL armazena caminho na coluna `transcript_path` da tabela `source_videos`.
- **Duração dos momentos:** 5-10 minutos por clip. Claude Haiku instrução: "identifique segmentos de 5-10 minutos com alto engajamento".
- **Schema por momento:** `start_time` (segundos), `end_time` (segundos), `score` (1-10), `reason` (string). Armazenado em `generated_clips` com status `pending_cut`.
- **Limite por vídeo:** Máximo 3 momentos não-sobrepostos. Se overlap: mantém maior score, descarta outro.
- **Filtro:** Score ≥ 7 → insere em `generated_clips` com `pending_cut`. Score < 7 → log apenas, não persiste.
- **Formato resposta Haiku:** JSON estruturado via `output_config` (structured outputs API). Schema: `[{"start_time": N, "end_time": N, "score": N, "reason": "..."}]`. Fallback: se parse falhar, marcar vídeo como `failed` e logar resposta bruta.
- **Conteúdo-alvo:** Futebol (análise, gol + reação, debate) e podcasts de tópicos variados.

### Claude's Discretion

- Prompt exato para o Haiku (linguagem, exemplos, instruções de formatação)
- Implementação do merge de overlaps (algoritmo interno)
- Tratamento de transcrições muito longas (chunking se necessário)
- Estrutura interna dos módulos transcriber.py e selector.py

### Deferred Ideas (OUT OF SCOPE)

- Reposting de cortes prontos (pipeline diferente sem transcrição) — candidato a Phase 5.1 ou v2
- Estratégia de conteúdo por horário — escopo da Phase 5 (PUB-03)
- Detecção de momentos por pico de volume de áudio — alinhado com OPT-03 (v2)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AI-01 | Áudio do vídeo transcrito pelo Groq Whisper API com idioma PT-BR, gerando texto com timestamps por segmento | Groq `whisper-large-v3-turbo`, `response_format="verbose_json"`, `language="pt"`, segmentos com `start`/`end` em segundos |
| AI-02 | Claude Haiku API analisa a transcrição completa e retorna lista de momentos com score 1-10, start/end e motivo | Anthropic `claude-haiku-4-5`, structured outputs com `output_config`, schema de array de objetos validado |
| AI-03 | Apenas momentos com score ≥ 7 são enviados para corte (filtro de qualidade) | Filtro Python pós-parse + insert em `generated_clips` com status `pending_cut` |
</phase_requirements>

---

## Summary

A Phase 3 implementa dois módulos Python independentes — `transcriber.py` e `selector.py` — integrados ao fluxo existente do `rss_poller.py`. O `transcriber.py` usa a Groq Whisper API para transcrever o áudio de vídeos com status `downloaded`, gerando um JSON em disco com segmentos e timestamps. O `selector.py` usa Claude Haiku 4.5 com structured outputs para analisar a transcrição e identificar os melhores momentos de 5-10 minutos, inserindo apenas aqueles com score ≥ 7 em `generated_clips`.

A decisão mais crítica de implementação é a **migração do schema MySQL**: `source_videos` precisa da coluna `transcript_path VARCHAR(500)`, e `generated_clips` precisa de duas alterações — a coluna `reason TEXT` e o estado `pending_cut` no ENUM de status. Estas alterações são pré-requisito de Wave 0. O schema atual define `generated_clips.status ENUM('pending', 'published', 'failed')` que não contém `pending_cut` — é necessário `ALTER TABLE`.

Groq Whisper API suporta MP4 diretamente (sem extração de áudio prévia), com limite de 25MB por arquivo no tier gratuito. Para vídeos de 720p com 1-2 horas de duração (podcasts), o arquivo pode exceder 25MB — o tratamento de chunking via ffmpeg é responsabilidade do `transcriber.py` com lógica de 10 minutos de overlap entre chunks.

**Primary recommendation:** Usar Groq `whisper-large-v3-turbo` + `response_format="verbose_json"` + `language="pt"` para transcrição; usar `anthropic.Anthropic().messages.create()` com `output_config` e json_schema para seleção. O prefill (`assistant` role) está depreciado nos modelos 4.x — usar structured outputs em vez disso.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| groq | já instalado | Cliente Python para Groq API (Whisper) | Já em requirements.txt, GROQ_API_KEY configurada |
| anthropic | já instalado | Cliente Python para Claude Haiku | Já em requirements.txt, suporta structured outputs |
| pymysql | já instalado | Inserção em `generated_clips`, update de status | Padrão do projeto em db.py |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| subprocess + ffmpeg | sistema | Chunking de áudio para arquivos >25MB | Quando `os.path.getsize(mp4_path) > 24_000_000` |
| json | stdlib | Serialização/deserialização do JSON de transcrição | Sempre — para salvar e ler `_transcript.json` |
| pydantic | opcional | Validação tipada do schema de momentos | Alternativa ao json_schema raw — não instalar se não estiver no requirements.txt |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `whisper-large-v3-turbo` | `whisper-large-v3` | Turbo é 3x mais barato ($0.04/h vs $0.111/h) com WER aceitável (12% vs 10.3%) para PT-BR |
| Structured outputs `output_config` | Prefill com `[` no assistant | Prefill retorna 400 error em modelos 4.x — usar structured outputs |
| Groq Whisper | faster-whisper local | Groq = gratuito, sem GPU, sem 2.5GB de disco (decisão Phase 1) |

**Installation:** Nenhuma nova dependência — `groq` e `anthropic` já estão em `clip-processor/requirements.txt`.

---

## Architecture Patterns

### Recommended Project Structure

```
clip-processor/src/
├── transcriber.py       # AI-01: Groq Whisper → JSON em disco
├── selector.py          # AI-02+AI-03: Claude Haiku → generated_clips
├── db.py                # Reutilizar update_status(), + novas funções de DB
├── rss_poller.py        # Integrar chamadas de transcriber e selector no fluxo
└── main.py              # Daemon (sem alteração nesta fase)

clip-processor/tests/
├── test_transcriber.py  # Cobre AI-01
├── test_selector.py     # Cobre AI-02 e AI-03
└── conftest.py          # Reutilizar mock_db_conn, sample_video_id

mysql/init/
└── 03-schema-migration.sql  # ADD COLUMN transcript_path + ALTER ENUM + ADD COLUMN reason
```

### Pattern 1: Injeção de Dependência para Testes (padrão estabelecido)

**What:** Funções aceitam clientes de API como parâmetro opcional — `None` = produção, injetado = teste.
**When to use:** Sempre, para manter testabilidade sem chamadas reais às APIs.

```python
# Fonte: padrão estabelecido em rss_poller.py / downloader.py
def transcribe_video(video_id: str, video_path: str, groq_client=None) -> dict | None:
    """
    Args:
        video_id: youtube_video_id
        video_path: caminho do .mp4 em /app/videos/
        groq_client: cliente Groq (None = produção, injetado = testes)
    Returns:
        dict com segmentos e metadata, ou None em caso de falha
    """
    if groq_client is None:
        from groq import Groq
        groq_client = Groq()
    # ...
```

### Pattern 2: Groq Whisper — Transcrição com Timestamps por Segmento

**What:** Chamada à Groq Audio API com `verbose_json` para obter timestamps por segmento.
**When to use:** Para qualquer vídeo com status `downloaded`.

```python
# Fonte: https://console.groq.com/docs/speech-to-text
from groq import Groq

def _transcribe_file(groq_client, file_path: str) -> object:
    """Transcreve um arquivo de áudio/vídeo via Groq Whisper."""
    with open(file_path, 'rb') as f:
        transcription = groq_client.audio.transcriptions.create(
            file=f,
            model='whisper-large-v3-turbo',
            response_format='verbose_json',
            timestamp_granularities=['segment'],
            language='pt',
            temperature=0.0,
        )
    return transcription
```

Estrutura de cada segmento retornado:
```json
{
  "id": 8,
  "seek": 3000,
  "start": 43.92,
  "end": 50.16,
  "text": "texto transcrito aqui",
  "avg_logprob": -0.097,
  "no_speech_prob": 0.012
}
```

### Pattern 3: Claude Haiku — Structured Outputs sem Prefill

**What:** Usar `output_config` com `json_schema` para garantir JSON válido. Prefill depreciado em modelos 4.x.
**When to use:** Para analisar a transcrição e retornar momentos estruturados.

```python
# Fonte: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
import anthropic

MOMENT_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'start_time': {'type': 'number'},
            'end_time': {'type': 'number'},
            'score': {'type': 'number'},
            'reason': {'type': 'string'},
        },
        'required': ['start_time', 'end_time', 'score', 'reason'],
        'additionalProperties': False,
    },
}

def select_moments(transcript_text: str, anthropic_client=None) -> list[dict]:
    if anthropic_client is None:
        anthropic_client = anthropic.Anthropic()

    response = anthropic_client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': transcript_text}],
        output_config={
            'format': {
                'type': 'json_schema',
                'schema': {
                    'type': 'object',
                    'properties': {'moments': MOMENT_SCHEMA},
                    'required': ['moments'],
                    'additionalProperties': False,
                },
            }
        },
    )
    import json
    data = json.loads(response.content[0].text)
    return data['moments']
```

**IMPORTANTE:** O schema precisa de wrapper `{"moments": [...]}` porque `output_config` exige `type: object` no nível raiz. O array de momentos fica em `data['moments']`.

### Pattern 4: Status Flow na Integração com rss_poller

**What:** O fluxo de transcrição+seleção é chamado dentro de `poll_all_channels` após o download.
**When to use:** Para cada vídeo que passa de `downloaded` para `transcribing`.

```python
# Integração em rss_poller.py — padrão do projeto
from src.transcriber import transcribe_video
from src.selector import select_and_insert_moments
from src.db import update_status

def _process_ai_pipeline(conn, video_id, video_path):
    """Executa transcrição + seleção para um vídeo downloaded."""
    update_status(conn, video_id, 'transcribing')
    transcript = transcribe_video(video_id, video_path)
    if transcript is None:
        update_status(conn, video_id, 'failed')
        return

    # Salva JSON em disco e atualiza transcript_path no banco
    _save_transcript(conn, video_id, transcript)

    update_status(conn, video_id, 'selecting')
    select_and_insert_moments(conn, video_id, transcript)
    # Status final definido pelo selector (selecting → próxima fase)
```

### Anti-Patterns to Avoid

- **Prefill do assistant com `[`:** Retorna HTTP 400 nos modelos Anthropic 4.x. Usar `output_config` com `json_schema`.
- **Passar texto da transcrição crua sem join:** Groq retorna lista de segmentos — fazer `" ".join(seg.text for seg in transcription.segments)` antes de enviar ao Haiku.
- **Assumir que MP4 de 720p cabe em 25MB:** Um vídeo de 1h em 720p pode ter 600MB+. Verificar tamanho do arquivo e chunkar se necessário antes de chamar a API.
- **Inserir `pending_cut` sem migrar o ENUM:** O schema atual tem `ENUM('pending', 'published', 'failed')`. INSERT falhará silenciosamente ou com erro se o estado não existir.
- **Fechar a conexão de banco dentro dos módulos:** Padrão do projeto — quem chama é responsável por fechar. `transcriber.py` e `selector.py` recebem `conn` e não fecham.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON schema validation | Parser regex / validação manual | `output_config` com structured outputs | Anthropic garante JSON válido via constrained decoding |
| Timestamp de segmentos | Calculação manual de offsets | `verbose_json` + `timestamp_granularities=['segment']` | API retorna `start`/`end` em segundos prontos |
| Retry em falhas de API | Loop customizado com sleep | Groq SDK e Anthropic SDK têm retry automático com backoff | SDKs já gerenciam timeouts e retry |
| Chunking de transcrição para prompt longo | Lógica de janela deslizante complexa | Passar transcrição completa — Haiku 4.5 tem 200k token context window | Um vídeo de 2h de podcast tem ~30k tokens de transcrição — cabe na janela |

**Key insight:** A transcrição de um vídeo de 2 horas gera aproximadamente 20-30k tokens de texto. O contexto de 200k tokens do Claude Haiku 4.5 comporta isso com margem ampla — não é necessário chunking no envio ao Haiku. Chunking é necessário apenas na chamada à Groq Whisper API (limite de 25MB no tier gratuito).

---

## Common Pitfalls

### Pitfall 1: Schema MySQL Incompleto — `pending_cut` e `reason`

**What goes wrong:** `INSERT INTO generated_clips (status) VALUES ('pending_cut')` falha com `Data truncated for column 'status'` porque o ENUM atual é `('pending', 'published', 'failed')`.

**Why it happens:** O CONTEXT.md define `pending_cut` como status, mas o `01-clips-schema.sql` foi criado na Phase 1 com apenas 3 estados. A coluna `reason` também não existe.

**How to avoid:** Wave 0 DEVE incluir migration SQL:
```sql
ALTER TABLE generated_clips
  MODIFY COLUMN status ENUM('pending_cut', 'pending', 'cutting', 'published', 'failed') DEFAULT 'pending_cut';

ALTER TABLE generated_clips
  ADD COLUMN reason TEXT AFTER score;

ALTER TABLE source_videos
  ADD COLUMN transcript_path VARCHAR(500) AFTER local_path;
```

**Warning signs:** Testes de integração passam mas inserção em produção falha com erro de enum.

### Pitfall 2: Prefill Depreciado em Modelos Anthropic 4.x

**What goes wrong:** `messages=[{"role": "assistant", "content": "["}]` retorna HTTP 400 error nos modelos claude-haiku-4-5 e posteriores.

**Why it happens:** O CONTEXT.md menciona "prefill com `[`" como técnica, mas essa funcionalidade foi removida dos modelos 4.x (desde abril 2026). A substituição é o `output_config` com structured outputs.

**How to avoid:** Usar SOMENTE `output_config` com `json_schema`. A resposta virá em `response.content[0].text` como JSON string válido.

**Warning signs:** HTTP 400 com mensagem "prefill not supported".

### Pitfall 3: Arquivo MP4 > 25MB na Groq API

**What goes wrong:** `groq.BadRequestError: File size exceeds maximum allowed size` para vídeos longos.

**Why it happens:** Vídeos de podcasts de 1-2 horas em 720p ficam entre 300MB e 1GB. Limite gratuito é 25MB.

**How to avoid:** Antes de chamar a API, verificar o tamanho do arquivo. Se exceder 24MB, extrair áudio em MP3 mono 16kHz via ffmpeg (reduz 10-20x o tamanho), ou chunkar em segmentos de 10 minutos com overlap de 10 segundos.

```python
import subprocess, os

def _prepare_audio(video_path: str) -> tuple[str, bool]:
    """Extrai áudio comprimido se arquivo for muito grande.
    Returns: (path_to_use, should_delete_after)
    """
    size = os.path.getsize(video_path)
    if size <= 24_000_000:  # 24MB — margem de segurança
        return video_path, False

    audio_path = video_path.replace('.mp4', '_audio.mp3')
    subprocess.run([
        'ffmpeg', '-i', video_path, '-vn',
        '-ar', '16000', '-ac', '1',
        '-b:a', '32k', audio_path, '-y'
    ], check=True, capture_output=True)
    return audio_path, True
```

**Warning signs:** `groq.BadRequestError` com menção a file size.

### Pitfall 4: Output `content[0].text` vs `parsed_output`

**What goes wrong:** Usar `response.parsed_output` quando chamou `messages.create()` (não `messages.parse()`).

**Why it happens:** O SDK Anthropic tem dois métodos: `messages.create()` retorna texto em `content[0].text`; `messages.parse()` (método beta) retorna `parsed_output` tipado. Usar `output_config` com `messages.create()` é o caminho estável.

**How to avoid:** Com `output_config` via `messages.create()`: `json.loads(response.content[0].text)`.

### Pitfall 5: Overlap entre Momentos Ignorado

**What goes wrong:** Dois momentos selecionados pelo Haiku com timestamps sobrepostos geram dois clips que cortam o mesmo trecho do vídeo.

**Why it happens:** O Haiku pode selecionar momentos próximos com `start`/`end` sobrepostos mesmo sendo instruído a não fazê-lo.

**How to avoid:** Implementar verificação de overlap em Python após o parse:

```python
def _remove_overlaps(moments: list[dict]) -> list[dict]:
    """Remove momentos sobrepostos, mantendo o de maior score."""
    # Ordenar por score decrescente
    sorted_moments = sorted(moments, key=lambda m: m['score'], reverse=True)
    selected = []
    for candidate in sorted_moments:
        overlaps = any(
            not (candidate['end_time'] <= kept['start_time'] or
                 candidate['start_time'] >= kept['end_time'])
            for kept in selected
        )
        if not overlaps:
            selected.append(candidate)
        if len(selected) >= 3:
            break
    return selected
```

---

## Code Examples

### Transcrição completa com verbose_json

```python
# Fonte: https://console.groq.com/docs/speech-to-text
from groq import Groq
import json

def transcribe_video(video_id: str, video_path: str, groq_client=None) -> dict | None:
    if groq_client is None:
        groq_client = Groq()

    try:
        with open(video_path, 'rb') as f:
            result = groq_client.audio.transcriptions.create(
                file=f,
                model='whisper-large-v3-turbo',
                response_format='verbose_json',
                timestamp_granularities=['segment'],
                language='pt',
                temperature=0.0,
            )

        segments = [
            {'start': seg.start, 'end': seg.end, 'text': seg.text}
            for seg in result.segments
        ]
        return {'video_id': video_id, 'text': result.text, 'segments': segments}

    except Exception as exc:
        _log(f'[AI] Erro na transcrição de {video_id}: {exc}')
        return None
```

### Salvar JSON em disco e atualizar transcript_path

```python
import json, os

VIDEOS_DIR = '/app/videos'

def _save_transcript(conn, video_id: str, transcript: dict) -> str:
    """Salva JSON de transcrição em disco e atualiza transcript_path no banco."""
    json_path = os.path.join(VIDEOS_DIR, f'{video_id}_transcript.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)

    # Atualiza transcript_path na tabela source_videos
    sql = 'UPDATE source_videos SET transcript_path=%s WHERE youtube_video_id=%s'
    with conn.cursor() as cur:
        cur.execute(sql, (json_path, video_id))
    conn.commit()
    return json_path
```

### Seleção com Claude Haiku e structured outputs

```python
# Fonte: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
import anthropic, json

SYSTEM_PROMPT = """Você é um especialista em identificar momentos virais de vídeos de futebol e podcasts.
Analise a transcrição fornecida e identifique os melhores segmentos para criar clips de 5 a 10 minutos.

Para futebol: priorize análise tática, debate acalorado, reação a gol, revelação de bastidores.
Para podcasts: priorize discussão intensa, revelação importante, momento de conflito ou humor.

Retorne no máximo 3 momentos não-sobrepostos, ordenados por score decrescente (10 = viral garantido, 1 = sem valor).
Considere apenas momentos onde o conteúdo é coeso e completo dentro do intervalo de 5-10 minutos."""

MOMENT_OUTPUT_SCHEMA = {
    'format': {
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'moments': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'start_time': {'type': 'number'},
                            'end_time': {'type': 'number'},
                            'score': {'type': 'number'},
                            'reason': {'type': 'string'},
                        },
                        'required': ['start_time', 'end_time', 'score', 'reason'],
                        'additionalProperties': False,
                    },
                }
            },
            'required': ['moments'],
            'additionalProperties': False,
        },
    }
}


def select_moments(transcript: dict, anthropic_client=None) -> list[dict]:
    """Analisa transcrição e retorna momentos selecionados pelo Haiku."""
    if anthropic_client is None:
        anthropic_client = anthropic.Anthropic()

    # Montar texto da transcrição com timestamps para contexto do modelo
    lines = []
    for seg in transcript.get('segments', []):
        start = int(seg['start'])
        end = int(seg['end'])
        lines.append(f'[{start}s-{end}s] {seg["text"]}')
    transcript_text = '\n'.join(lines)

    try:
        response = anthropic_client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': transcript_text}],
            output_config=MOMENT_OUTPUT_SCHEMA,
        )
        data = json.loads(response.content[0].text)
        return data.get('moments', [])

    except Exception as exc:
        _log(f'[AI] Erro na seleção de momentos: {exc}')
        return []
```

### Inserção em generated_clips com filtro de score

```python
def insert_selected_moments(conn, source_video_id: int, video_id: str, moments: list[dict]) -> int:
    """Insere momentos com score >= 7 em generated_clips. Retorna quantidade inserida."""
    inserted = 0
    for moment in moments:
        score = moment.get('score', 0)
        if score < 7:
            _log(f'[AI] Momento descartado (score {score}): {moment.get("reason", "")}')
            continue

        sql = (
            'INSERT INTO generated_clips '
            '(source_video_id, start_time, end_time, score, reason, status) '
            'VALUES (%s, %s, %s, %s, %s, %s)'
        )
        with conn.cursor() as cur:
            cur.execute(sql, (
                source_video_id,
                moment['start_time'],
                moment['end_time'],
                score,
                moment.get('reason', ''),
                'pending_cut',
            ))
        conn.commit()
        inserted += 1
        _log(f'[AI] Momento inserido: score={score}, {moment["start_time"]}s-{moment["end_time"]}s')

    return inserted
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Prefill com `[` para JSON | `output_config` com `json_schema` | Abril 2026 (modelos 4.x) | Prefill retorna 400 error — obrigatório usar structured outputs |
| `output_format` (beta) | `output_config.format` (GA) | Late 2025 | Beta header não é mais necessário; `output_format` continua funcionando em transição |
| faster-whisper local | Groq Whisper API | Phase 1 desta fase | Sem GPU, sem 2.5GB de disco — gratuito até 2.000 transcrições/dia |
| `whisper-large-v3` | `whisper-large-v3-turbo` | Disponível desde 2024 | 3x mais barato ($0.04/h), velocidade maior, WER 12% vs 10.3% |

**Deprecated/outdated:**
- Prefill do assistant: removido nos modelos 4.x (Sonnet 4.5+, Haiku 4.5+, Opus 4.5+)
- `anthropic-beta: structured-outputs-2025-11-13` header: não é mais necessário (GA)
- faster-whisper local: substituído pelo Groq API neste projeto (decisão Phase 1)

---

## Open Questions

1. **Tamanho dos MP4 de podcasts de 2h em 720p**
   - What we know: Vídeos de 720p variam entre 1-3 GB por hora de conteúdo
   - What's unclear: Tamanho real dos arquivos após download pelo yt-dlp com o formato `bestvideo[height<=720]+bestaudio/best`
   - Recommendation: Implementar verificação de tamanho + extração de áudio MP3 comprimido como fallback no Wave 0 do transcriber. Testar com um vídeo real de 1h antes de marcar AI-01 como completo.

2. **`source_video_id` vs `youtube_video_id` no insert de generated_clips**
   - What we know: `generated_clips` tem FK `source_video_id` referenciando `source_videos.id` (INT), não o `youtube_video_id` (string)
   - What's unclear: O fluxo em rss_poller passa o `youtube_video_id` (string) — é necessário fazer SELECT para obter o `id` INT antes de inserir em `generated_clips`
   - Recommendation: `select_and_insert_moments` deve receber `source_video_id` (INT) ou fazer lookup: `SELECT id FROM source_videos WHERE youtube_video_id = %s`

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-mock (já instalados) |
| Config file | `clip-processor/pytest.ini` (existe) |
| Quick run command | `cd clip-processor && pytest tests/test_transcriber.py tests/test_selector.py -v --tb=short` |
| Full suite command | `cd clip-processor && pytest tests/ -v --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AI-01 | Groq Whisper retorna segmentos com start/end/text | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_transcription_returns_segments -x` | Wave 0 |
| AI-01 | Arquivo `_transcript.json` salvo em disco | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_transcript_saved_to_disk -x` | Wave 0 |
| AI-01 | `transcript_path` atualizado no banco | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_transcript_path_updated_in_db -x` | Wave 0 |
| AI-01 | Arquivo >25MB usa extração de áudio antes de chamar API | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_large_file_audio_extraction -x` | Wave 0 |
| AI-01 | Falha na API → vídeo marcado como `failed` | unit | `pytest tests/test_transcriber.py::TestTranscribeVideo::test_api_failure_marks_video_failed -x` | Wave 0 |
| AI-02 | Claude Haiku retorna lista de momentos válidos | unit | `pytest tests/test_selector.py::TestSelectMoments::test_returns_moments_list -x` | Wave 0 |
| AI-02 | Transcript com timestamps no formato `[Ns-Ns]` é enviado ao Haiku | unit | `pytest tests/test_selector.py::TestSelectMoments::test_transcript_formatted_with_timestamps -x` | Wave 0 |
| AI-03 | Momento com score >= 7 é inserido em generated_clips | unit | `pytest tests/test_selector.py::TestInsertMoments::test_score_7_inserted -x` | Wave 0 |
| AI-03 | Momento com score < 7 é descartado (não inserido) | unit | `pytest tests/test_selector.py::TestInsertMoments::test_score_6_discarded -x` | Wave 0 |
| AI-03 | Momentos sobrepostos: mantém maior score | unit | `pytest tests/test_selector.py::TestInsertMoments::test_overlap_keeps_higher_score -x` | Wave 0 |
| AI-03 | Máximo 3 momentos inseridos por vídeo | unit | `pytest tests/test_selector.py::TestInsertMoments::test_max_3_moments -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `cd clip-processor && pytest tests/test_transcriber.py tests/test_selector.py -v --tb=short`
- **Per wave merge:** `cd clip-processor && pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green antes do `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `clip-processor/tests/test_transcriber.py` — cobre AI-01 (arquivo não existe)
- [ ] `clip-processor/tests/test_selector.py` — cobre AI-02 e AI-03 (arquivo não existe)
- [ ] `mysql/init/03-schema-migration.sql` — ADD COLUMN `transcript_path`, ALTER ENUM para incluir `pending_cut`, ADD COLUMN `reason`
- [ ] `clip-processor/src/transcriber.py` — módulo principal AI-01 (arquivo não existe)
- [ ] `clip-processor/src/selector.py` — módulo principal AI-02+AI-03 (arquivo não existe)

---

## Sources

### Primary (HIGH confidence)

- [Groq Speech-to-Text Docs](https://console.groq.com/docs/speech-to-text) — modelos disponíveis, parâmetros, limites de arquivo, estrutura verbose_json
- [Anthropic Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — output_config, json_schema, compatibilidade Haiku 4.5, sem necessidade de beta header
- [Anthropic Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview) — model IDs confirmados: `claude-haiku-4-5`, `claude-haiku-4-5-20251001`

### Secondary (MEDIUM confidence)

- [Groq Rate Limits](https://console.groq.com/docs/rate-limits) — 2.000 req/dia, 7.200 segundos de áudio/hora no tier gratuito
- [Groq Pricing](https://console.groq.com/docs/model/whisper-large-v3) — `whisper-large-v3-turbo`: $0.04/h; `whisper-large-v3`: $0.111/h
- Código existente do projeto (db.py, rss_poller.py, downloader.py, conftest.py) — padrões estabelecidos confirmados por leitura direta

### Tertiary (LOW confidence)

- WebSearch sobre prefill depreciação em modelos 4.x (Abril 2026) — verificar se `claude-haiku-4-5` especificamente rejeita prefill antes de assumir

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — bibliotecas já instaladas, APIs verificadas nas docs oficiais
- Architecture: HIGH — padrões estabelecidos do projeto, schema SQL lido diretamente
- Pitfalls: HIGH (schema MySQL, prefill) / MEDIUM (tamanho de arquivo em produção)
- Validation: HIGH — pytest.ini existe, padrões de mock estabelecidos em conftest.py

**Research date:** 2026-06-18
**Valid until:** 2026-07-18 (APIs estáveis; verificar se Anthropic lança Haiku 4.6 antes da implementação)
