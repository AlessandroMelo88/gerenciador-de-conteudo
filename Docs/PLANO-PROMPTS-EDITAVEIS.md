# Plano — Prompts de IA editáveis pelo painel

**Data:** 13/08/2026
**Status:** plano, nada implementado
**Objetivo:** o dono do projeto ver e editar, pelo painel, as instruções que a IA usa para escolher
os cortes — sem editar Python e sem `docker compose build` — e acompanhar métricas para saber se
um prompt novo é melhor que o anterior.

---

## 1. Situação atual (verificada em 13/08/2026)

A seleção de momentos roda em `clip-processor/src/selector.py`. Provider real em produção é o
**Groq LLaMA 3.3-70b** (`llama-3.3-70b-versatile`, `clip-processor/src/selector.py:104`), porque
`ANTHROPIC_API_KEY` está vazia na operação normal — o caminho Anthropic
(`clip-processor/src/selector.py:93`) existe mas cai no fallback.

O que está hardcoded:

| Constante | Local | Valor |
|---|---|---|
| `SYSTEM_PROMPT` | `clip-processor/src/selector.py:15` | prompt do formato **curto** (≤3 momentos, 30–180s) |
| `LONG_SYSTEM_PROMPT` | `clip-processor/src/selector.py:38` | prompt do formato **longo** (1 segmento, 420–1200s) |
| `MIN_SHORTFORM_SECONDS` | `clip-processor/src/selector.py:58` | 30 |
| `MAX_SHORTFORM_SECONDS` | `clip-processor/src/selector.py:59` | 180 |
| `MIN_LONGFORM_SECONDS` | `clip-processor/src/selector.py:61` | 420 |
| `MAX_LONGFORM_SECONDS` | `clip-processor/src/selector.py:62` | 1200 |
| `MAX_CHARS` (truncagem da transcrição) | `clip-processor/src/selector.py:223` | 8000 curto / 20000 longo |
| corte por score | `clip-processor/src/selector.py:315` | `score < 7` descarta |

O container **não tem bind mount para `src/`** — os volumes do serviço são só `youtube/`, `videos/`
e `branding/` (`../docker-compose.yml`, serviço `clip-processor`). A imagem embute o código no
build, então qualquer palavra alterada exige `docker compose build clip-processor && docker compose
up -d clip-processor`.

**Esse atrito já custou caro:** o ajuste de duração foi commitado em 12/08/2026 mas o container
seguia rodando a imagem de 01/08/2026 — 11 dias em que o código "correto" no repositório não tinha
efeito nenhum, e dezenas de clips de 2–4 segundos foram cortados e publicados no YouTube. O ganho
central deste plano não é conforto de UI: é **eliminar a possibilidade de divergência entre o que
está no repositório e o que está rodando**.

`MIN_LONGFORM_SECONDS` também é importado fora do módulo (`clip-processor/src/rss_poller.py:41`) —
qualquer mudança de origem desse valor precisa cobrir esse import.

---

## 2. Versões confirmadas (regra `docs-first`)

Leitura do lockfile/manifest, não de memória:

| Componente | Versão | Onde confirmei |
|---|---|---|
| Laravel Framework | **13.18.0** (`php artisan --version`), requisito `^13.8` | `painel/composer.json` |
| PHP | `^8.3` | `painel/composer.json` |
| Inertia (server) | `inertiajs/inertia-laravel ^3.1` | `painel/composer.json` |
| Inertia (client) | `@inertiajs/react ^3.6.1` | `painel/package.json` |
| React | `^19.2.7` | `painel/package.json` |
| Tailwind | `^4.0.0` (config em CSS, sem `tailwind.config.js`) | `painel/package.json` |
| Vite | `^8.0.0` | `painel/package.json` |
| Testes | Pest `^4.7` + PHPUnit `^12.5` | `painel/composer.json` |
| Recharts (gráficos) | `^3.8.0`, embrulhado em `painel/resources/js/components/ui/chart.tsx` | `painel/package.json` |
| Python | pymysql + Flask (sidecar) | `clip-processor/src/db.py`, `clip-processor/src/internal_api.py` |

Recursos nativos que o plano usa em vez de lógica própria:

- **Migrations Laravel** para criar as tabelas. O painel já migra dentro do banco do pipeline:
  `painel/config/database.php:20` usa `DB_CONNECTION` e `painel/.env.example:26` aponta
  `DB_DATABASE=clips_automation`. Precedente: `painel/database/migrations/2026_07_14_010214_create_niches_table.php`
  criou `niches` nesse mesmo banco. Não inventar `.sql` novo em `mysql/init/` para isto.
- **Form Request** (`php artisan make:request`) com `rules()` + `prepareForValidation()` para
  validar o corpo do prompt e os limites de duração — não `if` espalhado no controller.
- **Eloquent + `casts`** para os modelos; `DB::transaction()` na troca de versão ativa.
- **`config/services.php`** para qualquer nova chave (o cliente do sidecar já lê de lá:
  `painel/config/services.php` → `clip_processor.url` / `clip_processor.token`).
- **Autorização:** as rotas do painel já estão sob `middleware(['web','auth'])`
  (`painel/routes/web.php`). É um painel de um único operador; não há papéis. Não criar Policy
  agora — **mas** se um dia entrar segundo usuário, a checagem vai numa Policy
  (`AiPromptPolicy@update`), não em `if` no controller.
- **`useForm` do `@inertiajs/react`** + `sonner` para o formulário e o feedback, igual
  `painel/resources/js/pages/Settings.tsx`.

---

## 3. Por onde o prompt deve trafegar — decisão

Os dois canais existentes entre painel e pipeline:

1. **MySQL compartilhado** (`clips_automation`) — Laravel e Python escrevem/leem as mesmas tabelas.
2. **Sidecar HTTP na porta 8090** (`clip-processor/src/internal_api.py`), consumido por
   `painel/app/Services/ClipProcessorClient.php`. Sempre no sentido **Laravel → Python**, para
   ações que exigem o processo Python (yt-dlp, ffmpeg, arquivo em disco). Existe também o sentido
   inverso, só para eventos: `LARAVEL_NOTIFY_URL` → `POST /internal/pipeline-event`.

Comparação honesta das quatro opções de armazenamento/leitura:

| Opção | Prós | Contras | Custo por seleção |
|---|---|---|---|
| **Tabela MySQL lida na hora da seleção** (recomendada) | fonte única de verdade; Laravel escreve com migration/Eloquent nativos; versionamento e FK de métricas de graça; Python já tem conexão aberta (`clip-processor/src/db.py:26`); zero mudança no `docker-compose.yml` | se o MySQL cair, precisa de fallback (já é requisito de qualquer jeito — e se o MySQL cai o pipeline inteiro para, ver incidente 27/07/2026) | 1 `SELECT` indexado (~1 ms) por vídeo transcrito; frequência real é de poucas seleções por hora |
| Cache em Redis | leitura sub-ms | segunda fonte de verdade + invalidação para manter em sincronia; o Redis aqui hoje é volátil por design (dedup + quota) e o CLAUDE.md registra que mexer nele tem efeito colateral; ganho de latência irrelevante numa chamada que já espera segundos pela LLM | ~0,2 ms, e um bug novo de coerência |
| Arquivo em volume compartilhado | Python lê sem banco | exige **novo volume no `docker-compose.yml` compartilhado com outros projetos** (contra a regra de isolamento); Laravel escrevendo arquivo → sem transação, sem histórico, sem FK; escrita parcial lida no meio | ~0,1 ms + risco operacional |
| Endpoint no sidecar | usa o canal que já existe | o sentido está errado: **o Python** é quem precisa ler, então o Python passaria a depender do HTTP do Laravel (nova dependência de runtime e novo modo de falha num daemon que hoje só precisa de MySQL + Redis); e o dado ainda teria de morar em algum lugar — provavelmente no MySQL | 1 hop HTTP + o `SELECT` que o Laravel faria de todo modo |

### Recomendação

> **O prompt mora em tabela no MySQL `clips_automation`, criada por migration do Laravel, e o
> `selector.py` lê essa tabela no início de cada seleção, com fallback para as constantes
> hardcoded.** O sidecar 8090 entra **apenas** para duas coisas que exigem o processo Python:
> (a) o endpoint read-only da Fase 1, que mostra o que a **imagem em execução** realmente tem
> (é isso que denuncia a divergência de 11 dias), e (b) o smoke test antes de ativar uma versão.

Redis fica de fora inteiramente: o ganho é ruído diante da latência da própria LLM e o custo é uma
segunda fonte de verdade para manter coerente.

### Fluxo

```mermaid
flowchart TD
    subgraph Painel["Painel — Laravel 13.18 + Inertia + React 19"]
        UI["Página 'Cortes com IA'<br/>ver / editar / ativar / reverter"]
        FR["Form Request<br/>valida corpo e limites"]
        CTRL["AiPromptController"]
        UI --> FR --> CTRL
    end

    subgraph DB["MySQL clips_automation"]
        P["ai_prompts<br/>(slot: formato + nicho)"]
        V["ai_prompt_versions<br/>(histórico imutável)"]
        R["ai_selection_runs<br/>(métricas por execução)"]
        G["generated_clips<br/>+ ai_prompt_version_id"]
    end

    CTRL -->|"INSERT versão + UPDATE active_version_id<br/>(DB::transaction)"| P
    CTRL --> V

    subgraph Py["clip-processor (container separado)"]
        PS["prompt_store.get_prompt(conn, fmt, nicho)"]
        SEL["selector.select_moments()"]
        DEF["DEFAULT_* hardcoded<br/>(fallback)"]
        API["internal_api.py :8090<br/>GET /internal/ai-config<br/>POST /internal/ai-prompt/smoke-test"]
    end

    P -.->|"SELECT na hora da seleção"| PS
    V -.-> PS
    PS -->|ok| SEL
    PS -->|"vazio / inválido / MySQL fora"| DEF
    DEF --> SEL
    SEL -->|"system prompt = corpo editável + contrato JSON fixo"| LLM["Groq LLaMA 3.3-70b<br/>(fallback: Anthropic Haiku se houver key)"]
    LLM -->|'{"moments": [...]}'| SEL
    SEL -->|"grava funil + versão usada"| R
    SEL -->|"insert_selected_moments com ai_prompt_version_id"| G

    CTRL -.->|"ClipProcessorClient (HTTP 8090)"| API
    API -.-> PS
    G -.->|"aprovado / rejeitado / duração / score"| UI
    R -.->|"funil por versão"| UI
```

---

## 4. Modelo de dados

Três tabelas novas + uma coluna nova. Tudo via migration Laravel (`painel/database/migrations/`),
banco `clips_automation`.

### 4.1 `ai_prompts` — o *slot*

Um registro por combinação de formato e nicho. É o ponteiro estável para a versão ativa.

| Coluna | Tipo | Notas |
|---|---|---|
| `id` | `id()` | |
| `format` | `enum('curto','longo')` | mesmo domínio de `source_videos.format` |
| `niche_id` | `foreignId nullable` → `niches.id`, `nullOnDelete()` | `NULL` = padrão global usado quando o nicho não tem prompt próprio |
| `active_version_id` | `unsignedBigInteger nullable` | FK para `ai_prompt_versions` adicionada em **segunda migration** (dependência circular) com `nullOnDelete()` |
| `timestamps` | | |

Único: `unique(['format','niche_id'])`.

Nicho vem de `source_channels.target_niche` → `niches.slug`
(`painel/database/migrations/2026_07_14_010214_create_niches_table.php`; resolução análoga à de
`clip-processor/src/selector.py:269`). O prompt atual já é escrito para futebol/podcast, então o
recorte por nicho é a evolução natural — **mas na Fase 2 basta semear os dois slots globais
(`niche_id = NULL`, `curto` e `longo`)**; o `SELECT` do Python já nasce com o `COALESCE` de nicho
para não precisar de migration nova depois.

### 4.2 `ai_prompt_versions` — histórico imutável

Nunca sofre `UPDATE` de conteúdo: editar = criar versão nova. É o que permite voltar atrás e
comparar métricas.

| Coluna | Tipo | Notas |
|---|---|---|
| `id` | `id()` | |
| `ai_prompt_id` | `foreignId` → `ai_prompts.id`, `cascadeOnDelete()` | tabela nova e própria; cascade aqui é seguro |
| `version` | `unsignedInteger` | sequencial por slot; `unique(['ai_prompt_id','version'])` |
| `body` | `text` | **parte editável** do system prompt (persona + critérios). Sem o contrato JSON |
| `min_seconds` | `unsignedSmallInteger` | substitui `MIN_SHORTFORM_SECONDS` / `MIN_LONGFORM_SECONDS` |
| `max_seconds` | `unsignedSmallInteger` | substitui `MAX_SHORTFORM_SECONDS` / `MAX_LONGFORM_SECONDS` |
| `max_moments` | `unsignedTinyInteger` | 3 no curto, 1 no longo (`clip-processor/src/selector.py:215`) |
| `min_score` | `unsignedTinyInteger` | hoje fixo em 7 (`clip-processor/src/selector.py:315`) |
| `notes` | `text nullable` | "por que mudei" — escrito pelo dono, aparece no histórico |
| `created_by` | `foreignId nullable` → `users.id`, `nullOnDelete()` | quem escreveu |
| `smoke_tested_at` | `timestamp nullable` | preenchido pelo smoke test; **pré-requisito para ativar** (Fase 4) |
| `activated_at` / `deactivated_at` | `timestamp nullable` | quando entrou e saiu do ar — é o que amarra clips antigos à versão certa se o `ai_prompt_version_id` faltar |
| `timestamps` | | |

Sem `DELETE` na UI: versão sai do ar por `deactivated_at`, nunca é apagada. Isso protege as
métricas históricas e evita qualquer discussão de FK.

### 4.3 `generated_clips.ai_prompt_version_id`

Coluna nova, `INT NULL`, com índice, FK para `ai_prompt_versions(id)` **`ON DELETE SET NULL`**.

Nota deliberada: as duas FKs atuais de `generated_clips` (`fk_generated_clips_video`,
`fk_generated_clips_destination_channel`) são `RESTRICT` implícito, sem `ON DELETE CASCADE` — é o
que faz `DELETE` em `source_videos` com clips vinculados falhar, comportamento documentado no
CLAUDE.md e *desejável*. Aqui o requisito é o oposto: apagar uma versão de prompt **nunca** pode
travar nem apagar um clip. Daí `SET NULL`. Combinado com "não apagamos versões", o caminho crítico
nunca é exercido.

Clips criados antes da Fase 3 ficam com `NULL` — são a linha de base "pré-instrumentação" e devem
ser excluídos das comparações por versão.

### 4.4 `ai_selection_runs` — o que hoje só existe em log

Uma linha por chamada de `select_moments()`. O funil de descarte hoje só aparece em `stdout`
(`clip-processor/src/selector.py:168`), e log de container é volátil — foi exatamente o que se
perdeu quando o `clip-processor` foi podado. Sem esta tabela não há como responder "esse prompt novo
é melhor?".

| Coluna | Tipo | Notas |
|---|---|---|
| `id` | `id()` | |
| `source_video_id` | `int nullable`, **indexado, sem FK** | ver justificativa abaixo |
| `ai_prompt_version_id` | `foreignId nullable` → `ai_prompt_versions.id`, `nullOnDelete()` | |
| `format` | `enum('curto','longo')` | |
| `provider` / `model` | `varchar(32)` / `varchar(64)` | `groq` / `llama-3.3-70b-versatile`, ou `anthropic` / `claude-haiku-4-5` |
| `fallback_used` | `boolean` | Anthropic falhou e caiu no Groq |
| `prompt_source` | `enum('db','hardcoded')` | denuncia fallback silencioso de prompt |
| `transcript_chars` / `transcript_truncated` | `unsignedInteger` / `boolean` | truncagem de `clip-processor/src/selector.py:223` distorce a comparação; precisa ser visível |
| `transcript_duration` | `float nullable` | |
| `moments_returned` | `unsignedSmallInteger` | quantos a IA devolveu |
| `moments_after_overlap` | `unsignedSmallInteger` | após `_remove_overlaps` (`clip-processor/src/selector.py:122`) |
| `moments_after_duration` | `unsignedSmallInteger` | após filtro/esticamento de duração |
| `moments_inserted` | `unsignedSmallInteger` | após corte por score, o que virou clip |
| `returned_durations` | `json` | array de durações cruas devolvidas pela IA — é o número que mostraria os 2–4s na hora |
| `parse_error` | `text nullable` | JSON inválido (prompt quebrado) |
| `latency_ms` | `unsignedInteger nullable` | |
| `created_at` | `timestamp` | |

**Por que `source_video_id` sem FK:** `purge_old_videos` (`clip-processor/src/internal_api.py:171`)
apaga linhas de `source_videos`. Uma FK `RESTRICT` aqui quebraria a limpeza de disco; uma FK
`CASCADE` apagaria justamente o histórico de métricas que queremos guardar. Coluna solta e indexada
resolve os dois: a métrica sobrevive à limpeza e a limpeza não trava.

---

## 5. Como o clip-processor consome

### 5.1 Novo módulo `clip-processor/src/prompt_store.py`

```
PromptConfig = dataclass(body, min_seconds, max_seconds, max_moments, min_score,
                         version_id, source)   # source: 'db' | 'hardcoded'

DEFAULTS = {'curto': PromptConfig(<constantes atuais>, version_id=None, source='hardcoded'),
            'longo': PromptConfig(...)}

get_prompt(conn, fmt, niche_slug=None) -> PromptConfig
    try:
        SELECT v.* FROM ai_prompts p
          JOIN ai_prompt_versions v ON v.id = p.active_version_id
         WHERE p.format = %s
           AND (p.niche_id = (SELECT id FROM niches WHERE slug=%s) OR p.niche_id IS NULL)
         ORDER BY p.niche_id IS NULL      -- nicho específico ganha do global
         LIMIT 1
        valida (ver 5.3); se passar -> PromptConfig(source='db')
    except Exception as e:
        log('[PROMPT] falha ao ler prompt do banco (%s) — usando hardcoded', e)
    return DEFAULTS[fmt]

compose_system_prompt(cfg) -> str
    return cfg.body + DURATION_RULE.format(min=cfg.min_seconds, max=cfg.max_seconds) \
                    + JSON_CONTRACT   # constante NÃO editável
```

`JSON_CONTRACT` é a cauda que hoje fecha os dois prompts
(`Responda APENAS com JSON válido, sem texto adicional:\n{"moments": [...]}`) — sai do texto
editável e vira constante Python. O usuário **não pode** apagá-la.

### 5.2 Mudanças em `selector.py`

| Ponto | Mudança |
|---|---|
| `clip-processor/src/selector.py:15` e `:38` | renomear para `DEFAULT_SHORT_BODY` / `DEFAULT_LONG_BODY`, **sem** a cauda JSON (que migra para `prompt_store.JSON_CONTRACT`). O texto continua no código como fallback |
| `clip-processor/src/selector.py:58-62` | ficam como `DEFAULT_*`; reexportar `MIN_LONGFORM_SECONDS` para não quebrar `clip-processor/src/rss_poller.py:41` (ou, melhor, ajustar o import lá) |
| `clip-processor/src/selector.py:168` `_filter_shortform_duration` | receber `min_s`/`max_s` como parâmetro em vez de ler a constante global |
| `clip-processor/src/selector.py:139` `_enforce_longform_duration` | idem para `min_s`/`max_s` |
| `clip-processor/src/selector.py:188` `select_moments` | nova assinatura `select_moments(transcript, anthropic_client=None, fmt='curto', conn=None, niche_slug=None) -> tuple[list[dict], SelectionRun]`; chama `get_prompt` no início e devolve, junto com os momentos, o registro do funil |
| `clip-processor/src/selector.py:298` `insert_selected_moments` | novo parâmetro `ai_prompt_version_id` gravado no `INSERT`; `min_score` vem do `PromptConfig` em vez do literal `7` (`:315`) |
| `clip-processor/src/rss_poller.py:142-143` | passar `conn` e o nicho; persistir o `SelectionRun` em `ai_selection_runs` |

Compatibilidade de testes: `clip-processor/tests/test_selector.py` chama `select_moments` sem
`conn`. Com `conn=None`, `get_prompt` devolve o `DEFAULTS` direto sem tocar no banco — os testes
existentes continuam válidos e ganham dois casos novos (prompt do banco usado; prompt inválido cai
no default).

### 5.3 Cache e invalidação

**Recomendação: sem cache.** A seleção acontece uma vez por vídeo transcrito — poucas por hora.
Um `SELECT` indexado nesse intervalo é irrelevante perto dos segundos que a chamada à LLM leva, e
"sem cache" significa **invalidação zero**: salvou no painel, o próximo vídeo já usa. Isso é
exatamente o oposto do problema de hoje (mudança que fica 11 dias sem efeito) e não vale a pena
reintroduzi-lo em versão menor por 1 ms.

Se algum dia a frequência subir, o incremento é um cache de módulo com TTL de 60 s e chave
`(fmt, niche_slug)`, com log de "prompt recarregado (versão N)". Não antes de haver número que
justifique.

### 5.4 Comportamento em falha (requisito, não detalhe)

Cadeia de degradação, cada passo logado com prefixo `[PROMPT]`:

1. `SELECT` levanta exceção (MySQL fora, tabela ausente, credencial) → `DEFAULTS[fmt]`,
   `prompt_source='hardcoded'`.
2. Nenhuma linha ativa (`active_version_id IS NULL`) → `DEFAULTS[fmt]`.
3. `body` vazio, só espaço, ou fora dos limites de tamanho → `DEFAULTS[fmt]`.
4. `min_seconds >= max_seconds`, ou zero/negativo, ou `max_moments = 0` → `DEFAULTS[fmt]`
   (validação também acontece na gravação, mas o Python não confia no banco).
5. Se a IA responder JSON inválido, `_parse_moments` (`clip-processor/src/selector.py:87`) já
   levanta e `select_moments` já devolve `[]`; a diferença é que agora isso é **gravado** em
   `ai_selection_runs.parse_error` — e a UI pode alertar "a versão N está devolvendo JSON inválido".

`get_prompt` **nunca** propaga exceção. O pipeline nunca para por causa do prompt. É a mesma lição
do buraco do `metadata_generator.py` corrigido em 27/07/2026: caminho de IA nasce com fallback.

---

## 6. Proteção contra prompt ruim

Quatro camadas, do mais barato ao mais caro:

### 6.1 Partes fixas × parte editável

| Parte | Editável? | Onde vive |
|---|---|---|
| Persona + critérios de escolha (o que o dono quer mexer) | **sim** | `ai_prompt_versions.body` |
| Frase de duração ("entre X e Y segundos") | **não** — gerada de `min_seconds`/`max_seconds` | `prompt_store.DURATION_RULE` |
| Quantidade de momentos | **não** — gerada de `max_moments` | idem |
| Contrato JSON (`Responda APENAS com JSON válido... {"moments": [...]}`) | **não** | `prompt_store.JSON_CONTRACT` |

Assim o usuário não consegue apagar a instrução de JSON: ela é concatenada depois do texto dele.
Duração e quantidade saem de campos numéricos com `min`/`max` — nada de o número no texto divergir
do número do filtro, que é precisamente o descasamento que gerou os clips de 2–4 s.

### 6.2 Validação na gravação (Form Request nativo)

`StoreAiPromptVersionRequest`, regras:

- `body`: `required|string|min:200|max:4000`;
- `body` não pode conter `{"moments"` nem `Responda APENAS com JSON` (a cauda é do sistema — erro
  explicando isso);
- `min_seconds`: `required|integer|min:10|max:3600`;
- `max_seconds`: `required|integer|gt:min_seconds|max:3600`;
- teto por formato via `Rule::in` / `after()`: `curto` ≤ 300 s, `longo` ≥ 300 s — impede trocar os
  formatos por engano;
- `max_moments`: `required|integer|min:1|max:5`;
- `min_score`: `required|integer|min:1|max:10`;
- `notes`: `nullable|string|max:500`.

### 6.3 Smoke test antes de ativar

Nova rota no sidecar: `POST /internal/ai-prompt/smoke-test {version_id}`
(`clip-processor/src/internal_api.py`, mesmo padrão de auth `X-Internal-Token`,
`clip-processor/src/internal_api.py:34`) + método em
`painel/app/Services/ClipProcessorClient.php`.

O endpoint monta o prompt daquela versão, roda a seleção contra uma **transcrição fixture** guardada
no repositório do clip-processor (um `.json` de um vídeo real de cada formato — o
`transcription_jobs` do painel já produz material para isso) e devolve:

```json
{"ok": true, "parse_ok": true, "moments": 3,
 "durations": [92.4, 145.0, 61.7], "within_bounds": true,
 "provider": "groq", "latency_ms": 4120, "raw_error": null}
```

Regras: `parse_ok = false` → **não ativa**, mostra o erro. `within_bounds = false` (momentos fora
de `min_seconds`/`max_seconds`) → ativa mas com aviso na UI ("essa versão devolveu 2 de 3 momentos
fora da faixa"). Sucesso preenche `smoke_tested_at`, que a rota de ativação exige.

Custo: 1 chamada Groq por teste, no free tier já em uso. Barato o suficiente para ser obrigatório.

### 6.4 Rollback em um clique

A versão anterior continua na tabela. Reverter = `UPDATE ai_prompts SET active_version_id = <antiga>`
dentro de `DB::transaction()`. Nada de reeditar texto sob pressão.

---

## 7. UI no painel

### 7.1 Onde vive

**Página própria: `Cortes com IA`, rota `GET /painel/cortes-ia`**, no grupo
`middleware(['web','auth'])` de `painel/routes/web.php`, com item novo em
`painel/resources/js/components/app-sidebar.tsx`.

Não é aba de Configurações. `painel/resources/js/pages/Settings.tsx` hoje é escopo de conta (só
troca de senha) e a tela nova precisa de tabelas, histórico, diff e gráficos — cabe mal numa aba de
conta e cresce. Controller novo `AiPromptController` (`index`, `store`, `activate`, `smokeTest`),
página `painel/resources/js/pages/CortesIA.tsx`.

### 7.2 O que a tela mostra

`Tabs` no topo por formato: **Curto** | **Longo** (`painel/resources/js/components/ui/tabs.tsx`,
padrão já usado em `clip-queue-tabs.tsx`). Dentro de cada aba, quatro blocos:

**A. Em uso agora** (o pedido explícito, read-only)
- `Card` com `Badge` "versão N • ativa desde 12/08/2026".
- **Palavras-chave e frases-chave em uso**: as expressões que o prompt enfatiza — extraídas
  server-side do `body` pelos termos em CAIXA ALTA e pelas frases entre delimitadores
  (hoje: `ASSUNTO COMPLETO`, `NUNCA selecione`, `análise tática`, `debate acalorado`,
  `revelação de bastidores`, `COMENTÁRIO sobre um gol`, `discussão intensa`, `momento de conflito`,
  `humor`; no longo: `segmento CONTÍNUO`, `análise tática do início ao fim`, `resposta longa e
  coesa`, `debate que se desenvolve`). Render como lista de `Badge` — é a leitura de 5 segundos
  que ele quer, sem ler o prompt inteiro.
- Régua de duração e quantidade em `Badge`: `30–180 s`, `até 3 momentos`, `score mínimo 7`.
- Prompt efetivo completo em `ScrollArea` com fonte monoespaçada, marcando visualmente o
  **trecho fixo** (contrato JSON e regra de duração) em cinza, para ficar claro o que não se edita.
- **Selo de sincronia:** ao lado, o que o sidecar respondeu em `GET /internal/ai-config` — a
  configuração da **imagem em execução**. Se divergir do banco, `Badge` destructive
  "container desatualizado". É o alarme que faltava em 01–12/08/2026.

**B. Editar** (Fase 4)
- `Textarea` grande para `body` (`painel/resources/js/components/ui/textarea.tsx`), `Input`
  numérico para `min_seconds`/`max_seconds`/`max_moments`/`min_score`, `Input` para `notes`.
- `useForm` do `@inertiajs/react`; erros do Form Request aparecem por campo (mesmo padrão de
  `painel/resources/js/pages/Settings.tsx`).
- Botões: **Salvar como nova versão** (não ativa) → **Rodar smoke test** (`Button` com
  `Progress`/spinner, resultado em `Card`) → **Ativar** (`AlertDialog` de confirmação,
  desabilitado até o smoke passar). `toast` do `sonner` em cada etapa.

**C. Histórico** (Fase 5)
- `Table` com versão, autor, `notes`, ativada em, desativada em, e ações **Ver** / **Reverter**
  (`ConfirmButton`, já existe em `painel/resources/js/components/confirm-button.tsx`).
- Diff simples versão↔versão em `Dialog` (destaque por linha; sem lib nova).

**D. Métricas por versão** (Fase 6) — seção 8.

### 7.3 `impeccable`

Vale invocar a skill `impeccable` em dois momentos da execução, não antes:

1. **Fase 1**, no bloco "Em uso agora": é uma tela densa de texto (prompt longo + badges +
   números) e a hierarquia é o que decide se ela é útil ou ilegível — hierarquia visual,
   tipografia monoespaçada, distinção fixo/editável, estado vazio.
2. **Fase 6**, na tela de métricas: escolha de gráfico, paleta consistente, comparação lado a lado
   de duas versões, e como mostrar "amostra pequena, não conclua nada ainda" sem poluir.

Fases 2–5 são backend e formulário sobre padrão já existente no painel; não precisam.

---

## 8. Métricas para avaliar prompt

Todas amarradas por `generated_clips.ai_prompt_version_id` e `ai_selection_runs.ai_prompt_version_id`
(seção 4). O painel calcula com Eloquent/query builder; nada de lógica de estatística própria.

| Métrica | Como se calcula | Fonte |
|---|---|---|
| **Taxa de aprovação** | `approved + published` ÷ (`approved + published + rejected`) | `generated_clips.status` (enum já tem `approved`/`rejected`; a rejeição vem do painel via `clip-processor/src/rejeitar.py`) |
| **Distribuição de duração dos clips gerados** | histograma de `end_time - start_time`, com as bordas `min_seconds`/`max_seconds` desenhadas | `generated_clips.start_time`, `generated_clips.end_time` |
| **Funil de momentos** | soma de `moments_returned` → `moments_after_overlap` → `moments_after_duration` → `moments_inserted` | `ai_selection_runs` |
| **Descarte por duração** | `moments_after_overlap - moments_after_duration`, absoluto e em % | `ai_selection_runs` |
| **Descarte por score** | `moments_after_duration - moments_inserted` | `ai_selection_runs` |
| **Score médio** | `AVG(score)` dos clips da versão | `generated_clips.score` |
| **Vídeos que geraram 0 clips** | `COUNT(*) WHERE moments_inserted = 0` ÷ total de runs da versão | `ai_selection_runs` (hoje isso vira `source_videos.status='failed'` em `clip-processor/src/rss_poller.py:145`, indistinguível de falha de download) |
| **Duração crua devolvida pela IA** | percentis de `returned_durations` | `ai_selection_runs.returned_durations` |
| **Saúde do prompt** | % de runs com `parse_error` não nulo; % com `prompt_source='hardcoded'` | `ai_selection_runs` |
| **Custo/latência** | mediana de `latency_ms`, contagem por `provider` | `ai_selection_runs` |
| **Tempo até decisão** | mediana de `updated_at - created_at` nos clips resolvidos | `generated_clips` |

**Duas métricas de leitura direta que respondem "melhorou?":**
`% de momentos devolvidos que sobrevivem ao filtro de duração` (mede se o prompt entendeu a régua)
e `taxa de aprovação` (mede se o dono gosta do resultado). O resto é diagnóstico.

**Honestidade estatística — obrigatório na tela:**

- Não é A/B teste. Versões rodam em janelas de tempo diferentes, sobre canais e assuntos
  diferentes: é observacional, com confundimento. Mostrar sempre o `n` e a janela de datas.
- Abaixo de ~30 runs, exibir "amostra pequena" em vez de percentual grande na tela.
- Clips com `ai_prompt_version_id IS NULL` (pré-Fase 3) ficam **fora** de qualquer comparação —
  filtrar explicitamente, senão o baseline contamina tudo.
- Clip publicado sem passar por aprovação manual (`MANUAL_APPROVAL_REQUIRED=false`) não é sinal de
  aprovação. Segmentar por esse regime ou a taxa mente.
- `transcript_truncated = true` distorce a comparação (a IA viu material diferente); oferecer o
  filtro "só runs não truncados".

---

## 9. Fases de execução

Cada fase é entregável sozinha e tem critério verificável. **Só a Fase 2 exige rebuild — e é o
último rebuild obrigatório para mexer em prompt.**

### Fase 1 — Ver o que está rodando (read-only)
Sem banco novo, sem edição.
- `GET /internal/ai-config` no sidecar devolve, da **imagem em execução**: os dois prompts, as
  quatro constantes de duração, `MAX_CHARS`, `min_score`, provider/modelo efetivos e o
  `git_sha`/data de build (variável de build no `Dockerfile`).
- `ClipProcessorClient::aiConfig()`, `AiPromptController@index`, página `CortesIA.tsx` com o bloco
  A da seção 7.2 (badges de palavras-chave por formato + prompt completo em `ScrollArea`).
- **Pronto quando:** abrir `/painel/cortes-ia` mostra as palavras-chave dos dois formatos e a data
  de build do container; alterar `SYSTEM_PROMPT` no repositório **sem** rebuildar mantém a tela
  igual (prova que ela reflete o que roda, não o repositório).
- Valor: resolve o pedido "ver o que está em uso", custa pouco, e detecta divergência
  imagem↔repositório — o bug de 11 dias apareceria no primeiro acesso.

### Fase 2 — Prompt no banco, lido em runtime
- Migrations: `ai_prompts`, `ai_prompt_versions`, FK `active_version_id`; seeder cria versão 1 de
  cada formato **com o texto exato de hoje** (`clip-processor/src/selector.py:15` e `:38`, menos a
  cauda JSON) e as constantes atuais.
- `clip-processor/src/prompt_store.py` + refatoração de `selector.py` (seção 5.2) + testes Pest/
  pytest do fallback.
- **Pronto quando:** `UPDATE ai_prompt_versions SET body = ... ` na mão faz o **próximo** vídeo usar
  o texto novo, com `[PROMPT] versão N carregada` no log e **sem rebuild**; e `docker compose stop
  mysql` no ambiente de teste não impede a seleção de rodar com o prompt hardcoded (log
  `usando hardcoded`). Testes atuais de `test_selector.py` continuam verdes.
- Após esta fase a Fase 1 passa a comparar banco × imagem e acende o selo de divergência.

### Fase 3 — Instrumentação de métricas
- Migration de `ai_selection_runs` + coluna `generated_clips.ai_prompt_version_id`.
- `select_moments` devolve o funil; `rss_poller` persiste; `insert_selected_moments` grava a versão.
- **Pronto quando:** processar um vídeo gera 1 linha em `ai_selection_runs` com o funil coerente
  (`moments_returned >= moments_inserted`) e todo clip novo sai com `ai_prompt_version_id`
  preenchido. Nenhuma tela ainda — dado começa a acumular antes de existir edição, para haver
  baseline.

### Fase 4 — Edição pelo painel, com validação e smoke test
- `StoreAiPromptVersionRequest` (seção 6.2), `store`/`activate` em transação,
  `POST /internal/ai-prompt/smoke-test` + fixtures de transcrição, bloco B da UI.
- **Pronto quando:** editar no painel → salvar → smoke test verde → ativar faz o próximo vídeo usar
  o texto novo; tentar salvar `body` sem 200 caracteres, com `max_seconds <= min_seconds`, ou
  colando a cauda JSON é recusado com erro por campo; ativar sem smoke test é impossível.

### Fase 5 — Histórico, diff e reverter
- `Table` de versões, `Dialog` de diff, `ConfirmButton` de reverter.
- **Pronto quando:** reverter para a versão 1 leva menos de 10 s de clique a efeito e o próximo
  vídeo já usa a versão 1, com `activated_at`/`deactivated_at` coerentes.

### Fase 6 — Métricas por versão
- Consultas da seção 8, gráficos com `painel/resources/js/components/ui/chart.tsx` (Recharts
  3.8), avisos de amostra pequena e filtros (`transcript_truncated`, regime de aprovação).
- **Pronto quando:** a tela mostra, por versão, taxa de aprovação, histograma de duração, funil e
  score médio, com `n` e janela de datas visíveis; e recusa comparação com `n < 30` exibindo
  "amostra pequena".

### Fase 7 (opcional) — Prompt por nicho
- UI para criar slot com `niche_id`; o `SELECT` da Fase 2 já suporta.
- **Pronto quando:** um canal fonte com `target_niche = 'podcast'` usa o prompt de podcast e os
  demais seguem no global, comprovado em `ai_selection_runs.ai_prompt_version_id`.

---

## 10. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| **Dono degrada a qualidade sem perceber** | clips piores publicados por semanas antes de alguém notar | métricas da Fase 6 comparando versão nova × anterior; smoke test antes de ativar; reverter em 1 clique; a versão anterior nunca é apagada. Sugestão operacional: manter a versão nova no ar por um número mínimo de vídeos antes de julgar, e olhar o funil antes da taxa de aprovação (chega mais rápido) |
| **Divergência imagem × repositório volta** (o bug de 01–12/08/2026) | mudança sem efeito por dias | Fase 1 expõe build date + config em execução com `Badge` destructive na divergência; Fase 2 tira o prompt da imagem, então o caso deixa de existir para prompt (segue valendo para mudança de código) |
| **Prompt quebra o contrato JSON** | `_parse_moments` (`clip-processor/src/selector.py:87`) levanta, pipeline gera 0 clips | contrato JSON é constante não editável (6.1); validação recusa o texto (6.2); smoke test barra a ativação (6.3); `ai_selection_runs.parse_error` alerta depois |
| **Duração no texto divergindo do filtro numérico** | causa raiz dos clips de 2–4 s | duração é campo numérico único, usado ao mesmo tempo na frase do prompt e no filtro — impossível divergir |
| **MySQL fora** | seleção pararia se dependesse do banco para o prompt | `get_prompt` nunca levanta; cai em `DEFAULTS` e registra `prompt_source='hardcoded'` (5.4). Nota: no incidente de 27/07/2026 o MySQL fora já parava o pipeline inteiro — o prompt não agrava isso |
| **Refatoração de `selector.py` quebra o pipeline** | pior que o problema original | assinaturas retrocompatíveis (`conn=None` → default); `clip-processor/tests/test_selector.py` roda antes; atenção ao import de `MIN_LONGFORM_SECONDS` em `clip-processor/src/rss_poller.py:41` |
| **`ai_selection_runs` cresce sem parar** | tabela infla | ~3 linhas por vídeo; irrelevante por anos. Se incomodar, agregar por versão e podar runs > 1 ano — **nunca** as versões |
| **FK nova travando limpeza de disco** | `purge_old_videos` falha e o SSD lota de novo (causa raiz do incidente) | `ai_selection_runs.source_video_id` sem FK; `ai_prompt_version_id` em `generated_clips` com `ON DELETE SET NULL` (4.3) |
| **Alguém tenta apagar versão de prompt** | perda de histórico e de métrica | UI não oferece delete; só `deactivated_at` |
| **Comparação estatística ingênua** | decisão errada com base em 5 clips | avisos e filtros obrigatórios na tela (seção 8) |

---

## 11. Fora de escopo neste plano

- Prompt do `metadata_generator.py` (título/descrição/tags). Mesmo padrão se aplica e a tabela
  `ai_prompts` acomoda com um `purpose` novo, mas fica para depois — a seleção é onde dói.
- `MAX_CHARS` / estratégia de truncagem (`clip-processor/src/selector.py:223`): exposta como
  leitura na Fase 1, mas não editável — mexer nela interage com o limite de TPM do Groq e merece
  decisão própria.
- A/B test real (duas versões ativas em paralelo por sorteio). Possível sobre este modelo
  (`ai_selection_runs` já registra a versão por run), mas com o volume atual de vídeos por dia não
  há amostra para concluir nada.
- Escolha de provider/modelo pelo painel.
