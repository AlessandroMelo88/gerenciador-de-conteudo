# Arquitetura — Canal de Cortes

> **Escopo:** este documento descreve o sistema **como ele é hoje** (as-built). Verificado lendo o código em 15/07/2026 no commit `dca6e44`; correções pontuais de formato, fallback de metadata, scheduler e limpeza de disco aplicadas em 13/08/2026.
>
> **Detalhe por subsistema vive em [`Docs/`](Docs/README.md)** — este arquivo é a visão geral; pipeline, download, transcrição, seleção por IA, corte, publicação, banco, estados e runbook têm documento próprio lá. Comece pelo [`Docs/README.md`](Docs/README.md).
> Não confundir com `.planning/research/ARCHITECTURE.md`, que é um documento de **pesquisa de junho/2026**: ele planeja um futuro que em parte não aconteceu (migração do bot para o n8n, painel em Filament) e não deve ser usado como referência do estado atual.
>
> **Para quem vai ler isso primeiro (inclusive IA):** comece pelas seções 1 a 3. A seção 10 lista as divergências conhecidas entre a documentação antiga e o código — leia antes de confiar no `README.md`.

---

## 1. O que o sistema faz

Pipeline automatizado que monitora canais de futebol no YouTube, corta os melhores momentos com IA e publica os clips em canais próprios. O fluxo padrão é 100% automático: da descoberta via RSS até o upload, sem intervenção humana. O painel web existe para o operador **observar e corrigir**, não para operar o fluxo normal.

Dois formatos de saída, decididos automaticamente pela duração do vídeo original:

- **`curto`** — vídeo fonte < 7 min. Vira até 3 shorts verticais (1080x1920), de 30 s a 3 min cada.
- **`longo`** — vídeo fonte ≥ 7 min. Vira **um único** corte horizontal contínuo de 7 a 20 min.

O limiar é `MIN_LONGFORM_SECONDS = 420` ([`selector.py:61`](clip-processor/src/selector.py#L61)), usado
tanto na detecção de formato quanto na validação da duração do corte longo. `MIN_SHORTFORM_SECONDS`
subiu de 15 s para **30 s** em 13/08/2026 ([`selector.py:58`](clip-processor/src/selector.py#L58)): em
15 s não se fecha um raciocínio, e o prompt do modo curto foi reescrito junto — mudar a constante
sozinha faz o modelo entregar 30 s picados só para bater a régua.

---

## 2. Topologia

O `docker-compose.yml` fica **um nível acima** deste projeto, em `/server/wordpress/`, e é **compartilhado com outros projetos** (kelnab, feeb, placebeads, riodelux, gringo). O `.env` que o compose lê é o da raiz `wordpress/` — **não** o `canaldecortes/.env`.

| Serviço | Dono | Portas no host | Papel para o Canal de Cortes |
|---|---|---|---|
| `clip-processor` | **exclusivo** | **nenhuma** | Daemon Python: todo o pipeline + sidecar HTTP interno na 8090 |
| `nginx` | compartilhado | 80 | Serve o vhost `canaldecortes.local` |
| `php` | compartilhado | — (9000 interno) | PHP-FPM que roda o painel Laravel |
| `mysql:8.4` | compartilhado | 3306 | Hospeda o database `clips_automation` |
| `redis:alpine` | compartilhado | 6379 | Dedup + cota diária (db 0 = pipeline, db 1 = painel) |

`postgres`, `minio` e `minio-init` pertencem a outros projetos e não têm relação com este.

**Serviços mortos, mantidos comentados no compose apenas por histórico:** `n8n` e `cloudflared`. O n8n foi substituído pelo APScheduler dentro do `clip-processor` (ciclo do pipeline) e pelo `Schedule::call()` do Laravel (`painel/routes/console.php:17-27`, resumo diário 18h BRT). O workflow em `n8n/workflows/` está com `"active": false` e o SQLite dele não é escrito desde 17/jun.

### Acesso HTTP

Não existe rota `/painel` no nginx — `/painel` é apenas o caminho no filesystem dos containers. O acesso é por **vhost**: `canaldecortes.local` → `docker/nginx/canaldecortes.conf` → root `/var/www/html/painel/public` → `fastcgi_pass php:9000`.

---

## 3. A fronteira entre os dois serviços

Esta é a decisão arquitetural mais importante do sistema, e a que mais confunde quem chega agora.

```
                 ┌──────────────────────────────────┐
   navegador ──► │  painel (Laravel 13 + Inertia)   │
                 └───────┬──────────────────┬───────┘
                         │                  │
        HTTP interno     │                  │  leitura direta
     X-Internal-Token    │                  │  (MySQL, Redis, disco)
                         ▼                  ▼
                 ┌───────────────┐   ┌──────────────────┐
                 │ clip-processor│──►│ MySQL / Redis /  │
                 │  sidecar 8090 │   │ volumes de vídeo │
                 └───────────────┘   └──────────────────┘
                         ▲
                         │  POST /internal/pipeline-event
                         └──── (eventos → Telegram)
```

**A regra:** para **ler**, o painel vai direto na fonte (MySQL, Redis, disco). Para **agir sobre disco ou processos** (apagar arquivo, resolver canal via yt-dlp, enfileirar URL), o painel **nunca** toca no filesystem do pipeline — chama o sidecar HTTP. Isso substituiu o padrão anterior de `docker exec` / socket do Docker (decisão registrada em `painel/config/services.php:38-39`).

Exceção importante à regra: **transições de status simples o painel escreve direto no MySQL** (ex.: `approve()` faz `UPDATE generated_clips SET status='approved' WHERE status='pending'`). Só o que mexe em disco/processo passa pelo sidecar.

### O sidecar (`clip-processor/src/internal_api.py`)

Flask em `0.0.0.0:8090`, thread daemon, **sem porta publicada** — só alcançável pela rede docker `internal`. Autenticação por token compartilhado no header `X-Internal-Token`, comparado com `CLIP_PROCESSOR_INTERNAL_TOKEN`. É **fail-closed**: se a env var estiver vazia, toda rota responde 401.

| Rota (POST) | Body | Retorno |
|---|---|---|
| `/internal/resolve-channel` | `{url}` | `{channel_id, channel_name, channel_handle}`; 422 se yt-dlp falhar |
| `/internal/process-url` | `{url, format}` | `{exit_code}` — 0 ok, 2 URL inválida, 3 metadata falhou |
| `/internal/reject-clip` | `{clip_id}` | `{exit_code}` — 0 ok, 1 inexistente, 2 status inválido |
| `/internal/delete-source-video` | `{source_video_id}` | `{deleted, freed_bytes}` |
| `/internal/purge-old-videos` | `{before_date}` | `{deleted_rows, freed_bytes}` |

Não há rota de health check.

O caminho inverso é `telegram_notifier.py` → `POST /internal/pipeline-event` no painel, com o **mesmo token**. Eventos: `upload_published`, `pipeline_failure`, `clip_ttl_warning`, `daily_summary`. É best-effort: falha ali nunca propaga para o pipeline.

---

## 4. O pipeline (`clip-processor`)

### Agendamento

APScheduler (`BlockingScheduler`, timezone `America/Sao_Paulo`), configurado em `src/main.py`. No boot: recupera downloads travados (`downloading` → `pending`), sobe o sidecar em thread e roda **um** ciclo completo síncrono. Depois entrega ao scheduler:

| Job | Função | Intervalo |
|---|---|---|
| `ingest_cycle` | `run_ingest_cycle` | **20 min** |
| `publish_cycle` | `run_publish_only` | **20 min** |
| `clip_pending_ttl` | `run_ttl_once` | 1 h |
| `state_recovery` | `run_recovery_once` | **30 min** |

Todos com `coalesce=True, max_instances=1, misfire_grace_time=900`.

> O `state_recovery` foi adicionado em 13/08/2026. Antes, o recovery de estado preso rodava **só no
> boot** — o que travasse depois do container subir ficava preso até o próximo restart. Detalhe em
> [`Docs/ESTADOS-E-TRANSICOES.md`](Docs/ESTADOS-E-TRANSICOES.md).

> **Ingestão e publicação são jobs separados.** O ciclo completo (`run_pipeline_once`) só roda no boot; não está mais agendado. O `ingest_cycle` (commit `dca6e44`) existe para que uma vaga aberta na janela de download — porque um vídeo foi excluído no painel ou uma publicação concluiu — seja reposta em ~20 min em vez de esperar o ciclo antigo de 6 h.

### Etapas

1. **Descoberta** — `poll_all_channels` varre o RSS de cada `source_channel` ativo e não-blacklistado. Por entrada: dedup (Redis `SET NX`, TTL 30 dias, com fallback para MySQL) → filtro de título (bloqueia keywords de aposta/cassino) → detecção de formato (yt-dlp metadata; falha ⇒ assume `curto`) → `INSERT status='pending'`.
2. **Download** — janela fixa **por formato**, que não se canibaliza: até 6 `curto` e 4 `longo` **ocupando disco simultaneamente**. Baixa só o déficit. Só considera vídeos publicados nas últimas 24 h (`FRESHNESS_DAYS = 1`), ordenados por `published_at DESC` — a notícia mais recente ganha, não a descoberta mais antiga. yt-dlp 720p, 3 tentativas, aborta se restarem < 2 GB de disco.
3. **Transcrição** — Groq Whisper (`whisper-large-v3-turbo`, pt). Arquivo > 24 MB é convertido para MP3 antes.
4. **Seleção de momentos** — Claude Haiku escolhe os trechos com score 0–10. Prompt e truncagem variam por formato (`longo`: 1 segmento, 420–1200 s; `curto`: até 3 momentos, 30–180 s). Ver [`Docs/SISTEMA-IA-SELECAO.md`](Docs/SISTEMA-IA-SELECAO.md).
5. **Corte e pós-produção** — FFmpeg: corta → gera SRT → queima legenda → marca d'água → thumbnail. `curto` recebe crop 1080x1920; `longo` preserva o horizontal (`scale=-2:1080`).
6. **Metadata** — Claude Haiku gera título, descrição e tags a partir da transcrição do trecho.
7. **Publicação** — respeitando cota, janela horária e round-robin (ver 4.2).

Cada etapa roda em `try/except` isolado que loga e dispara `notify('pipeline_failure', ...)` — uma falha não derruba o scheduler.

> ⚠️ **Nomenclatura enganosa:** apesar do nome, `rss_poller.py` não faz só polling. `poll_all_channels` também executa o estágio de IA (transcrição + seleção) e o de corte. O `pipeline_runner` só cuida de descoberta e download.

### 4.1 Fallbacks de IA

| Chamada | Fallback |
|---|---|
| Seleção de momentos (Claude) | **Groq LLaMA `llama-3.3-70b-versatile`.** Sem `ANTHROPIC_API_KEY`, vai direto no Groq. Groq falhando também ⇒ nenhum momento. |
| Metadata (Claude) | **Groq LLaMA `llama-3.3-70b-versatile`** (adicionado em 27/07/2026). Só se as duas IAs falharem cai no determinístico: título = título do vídeo original, descrição = `reason` da seleção, tags fixas. |
| Transcrição (Groq Whisper) | **Nenhum.** Falhou ⇒ vídeo marcado `failed`. |
| Dedup (Redis) | `SELECT` no MySQL. |
| Cota (Redis) | **Nenhum.** Redis fora ⇒ publicação para. |

### 4.2 Cota, janela e round-robin

- Chave Redis `youtube_uploads:{channel_id}:{data}`, mais um contador `:longo`. Data em `America/Sao_Paulo`, TTL até a meia-noite local.
- `MAX_UPLOADS_PER_DAY` é **clampado em [0, 6]** — existe um teto rígido de 6 uploads/dia por canal no código, independente da env var.
- `MAX_LONGO_UPLOADS_PER_DAY` é teto de uploads `longo` e, enquanto houver longo publishable na fila, reserva esses slots na cota total (curto só usa `total − slots_longo_ainda_não_usados`). Sem longo na fila, a reserva some.
- **Janela horária: 19h–22h (SP)**, com bypass total via `UPLOAD_WINDOW_BYPASS=true`.
- **Round-robin por canal FONTE** (`_round_robin_by_source_channel`): os clips saem em `created_at ASC`, mas são intercalados por canal de origem. Sem isso, uma leva represada de um único canal monopolizaria a cota por dias.
- Roteamento fonte → destino é por **nicho**: `source_channels.target_niche` casa com `destination_channels.niche`.
- Guard de corrida com a rejeição: `_transition_to_publishing` só avança se o `UPDATE ... WHERE status=?` afetar alguma linha.
- Quando um vídeo fonte não tem mais nenhum clip em estado não-terminal e ao menos um publicou, `_maybe_finalize_source_video` apaga do disco o `.mp4` bruto **e**, de cada clip, o MP4 final, o `_raw.mp4`, o `_subtitled.mp4` e a thumbnail; zera `clip_path`/`thumbnail_path` e marca o vídeo `published` com `local_path=NULL`. A cascata de clips é de 12/08/2026 (commit `5009112`).

### 4.3 OAuth do YouTube

Um token por canal-destino, em `/app/youtube/token-{slug}.json`, gerado pelo CLI interativo `youtube_oauth.py`. Se o refresh falhar, o uploader grava `destination_channels.oauth_expired_flag=TRUE` (o painel mostra o badge) e re-lança. Um upload bem-sucedido limpa a flag sozinho.

---

## 5. Máquina de estados

> Versão completa, com quem escreve cada transição, diagramas Mermaid e a tabela do que **tem e não tem
> recuperação automática**, em [`Docs/ESTADOS-E-TRANSICOES.md`](Docs/ESTADOS-E-TRANSICOES.md). O resumo
> abaixo é suficiente para orientação, não para operar.

### `source_videos.status`

```
pending → downloading → downloaded → transcribing → selecting → published
                 │                        │
                 └────────► failed ◄──────┘
```

`selecting` é o **estado final de sucesso do ramo de IA** — nada o move adiante. O vídeo só vira `published` mais tarde, pelo publisher, quando seus clips terminam.

> `cutting` existe no ENUM e é lido como guard em `internal_api.py`, mas **nenhum código escreve esse valor em `source_videos`**. O guard de "arquivo em uso" nunca dispara por ele.

### `generated_clips.status`

```
pending_cut → cutting → pending ──► publishing → published
                          │  ▲            └────► failed
                          │  └── approved (só o painel escreve)
                          └────► rejected (painel, /rejeitar ou TTL)
```

- **`approved` nunca é escrito pelo Python** — vem exclusivamente do painel.
- **O que o publisher considera publicável depende de `MANUAL_APPROVAL_REQUIRED`**: `true` ⇒ só `approved`; `false` (default) ⇒ publica `pending` direto, sem revisão humana.
- `ttl_worker` auto-rejeita clips `pending` com mais de `CLIP_PENDING_TTL_HOURS` (48h), avisando uma vez no Telegram em 24h (idempotente via chave Redis `clip_warned:{id}`).

---

## 6. Schema (`clips_automation`)

**As tabelas do pipeline não são geridas por migrations do Laravel.** Elas nascem de SQL bruto em `mysql/init/01..07`, aplicado **manualmente** via `docker exec`. O painel apenas as mapeia com Eloquent e `$table` explícito.

Consequências práticas:
- `php artisan migrate:fresh` **não** reconstrói o schema do pipeline.
- Por isso `RefreshDatabase` está desligado em `tests/Pest.php` e os testes usam `DatabaseTransactions` sobre tabelas pré-existentes.

| Tabela | Origem | Notas |
|---|---|---|
| `source_channels` | `mysql/init` | `target_niche`, `channel_handle`, `blacklisted`, `rss_url`, `active` |
| `source_videos` | `mysql/init` | FK → `source_channels`; `format` ENUM(`curto`,`longo`); `local_path`, `transcript_path` |
| `generated_clips` | `mysql/init` | FK → `source_videos` e → `destination_channels`; `score`, `reason`, `start_time`/`end_time`, `upload_error` |
| `destination_channels` | `mysql/init` | `slug`, `niche`, `credit_template`, `oauth_expired_flag` |
| `niches` | **migration Laravel** | Única tabela de domínio do painel; seeda `futebol` e `podcast` |
| `users`, `sessions`, `cache`, `jobs` | migration Laravel | Mesmo database |

> `niches` é a fonte de verdade dos selects, mas **não há FK** ligando `source_channels.target_niche` / `destination_channels.niche` a ela — seguem VARCHAR livre.

---

## 7. O painel (`painel/`)

**Stack real: Laravel 13 + Inertia 3 + React 19 + shadcn/ui + Tailwind 4 + Vite 8 + TypeScript.**

> **O Filament foi removido por completo** no commit `dca6e44`. Não está no `composer.json`, no `composer.lock` nem no `vendor/`. Não há `PanelProvider` nem rota Filament, e as 8 rotas GET do painel retornam `Inertia::render(...)`. Qualquer menção a Filament no `README.md` ou em nome de arquivo é resíduo — ver seção 10.

Dark mode é fixo via `class="dark"` no `<html>`. Não há layout compartilhado do Inertia: cada página compõe `AppSidebar` + `SiteHeader`, e o reuso de cabeçalho é feito pelo componente `page-header.tsx` (descrição + slot de ações por rota).

### Páginas

| Rota | Página | Função |
|---|---|---|
| `/` | — | Redirect: logado → `/painel`, senão → `/login` |
| `/login` | `Login` | Split-screen; form em `login-form.tsx` |
| `/painel` | `Dashboard` | Fila de aprovação, fila aguardando cota, falhas, consumo de cota do dia |
| `/painel/canais-destino` | `DestinationChannels` | CRUD + upload de marca d'água + badge OAuth |
| `/painel/canais-fonte` | `SourceChannels` | CRUD por URL (resolve via sidecar), tabs por nicho, toggles |
| `/painel/videos` | `SourceVideos` | Listagem filtrável + gestão de disco (delete, bulk, purge) |
| `/painel/processar-video` | `ProcessVideo` | Enfileiramento manual de URLs |
| `/painel/configuracoes` | `Settings` | Tabs; reset de senha funcional |
| `/painel/documentacao` | `Documentation` | Ajuda estática dentro do painel |

Rotas públicas sem CSRF (`bootstrap/app.php`): `POST /telegramcanal` (webhook do bot) e `POST /internal/pipeline-event`.

### Autenticação

Guard `web` (session, driver `database`), único guard — não há Sanctum/API. Logout é **`POST /logout`** (nunca GET), disparado por `router.post('/logout')` no dropdown do avatar. **Não existe registro público** — o operador é criado interativamente por `php artisan painel:create-user` (senha ≥ 10 chars, nunca ecoada); reset por `painel:reset-password {email}`.

### Testes

35 testes, 13 arquivos (Pest 4). Cobrem comandos do Telegram, aprovação/rejeição de clips, eventos de pipeline, guards de auth, CRUD de canais, accessor de OAuth e os comandos Artisan.

**Sem cobertura:** `SettingsController`, `ProcessVideoController`, `SourceVideoController` (o mais complexo depois do Dashboard), `NicheController` e a rota `clips.preview`. Nenhum teste de frontend.

---

## 8. Configuração

O compose lê o `.env` da **raiz `wordpress/`**. O `canaldecortes/.env.example` está defasado dele.

| Var | Serve para |
|---|---|
| `ANTHROPIC_API_KEY` | Claude: seleção de momentos + metadata |
| `GROQ_API_KEY` | Whisper (transcrição) + fallback de seleção |
| `CLIPS_DB_PASSWORD` | Senha do `clips_user` |
| `CLIP_PROCESSOR_INTERNAL_TOKEN` | Token compartilhado painel ↔ sidecar (mesmo valor nos dois lados) |
| `MANUAL_APPROVAL_REQUIRED` | `false` (default) publica sem revisão; `true` exige `approved` |
| `MAX_UPLOADS_PER_DAY` / `MAX_LONGO_UPLOADS_PER_DAY` | Cota diária por canal (teto rígido de 6 no código) |
| `UPLOAD_WINDOW_BYPASS` | Ignora a janela 19h–22h |
| `YOUTUBE_PRIVACY_STATUS` | `privacyStatus` do upload (default `private`) |
| `CLIP_PENDING_TTL_HOURS` / `CLIP_PENDING_WARN_HOURS` | TTL de auto-rejeição (48h/24h) |
| `LARAVEL_NOTIFY_URL` / `LARAVEL_HOST_HEADER` | Endpoint de eventos e Host para o roteamento nginx |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID_ALLOWED` | Bot; vivem no `painel/.env`, não no compose |

---

## 9. Onde mexer para cada tipo de mudança

| Quero... | Vou em |
|---|---|
| Mudar como a IA escolhe momentos | `clip-processor/src/selector.py` (prompts por formato) |
| Mudar título/descrição/tags | `clip-processor/src/metadata_generator.py` |
| Mudar corte/legenda/watermark | `clip-processor/src/video_processor.py` |
| Mudar cota, janela ou round-robin | `quota_manager.py` e `publisher.py` |
| Mudar cadência dos jobs | `clip-processor/src/main.py` |
| Mudar quantos vídeos ficam em disco | `DOWNLOAD_WINDOW_*` em `pipeline_runner.py` |
| Adicionar ação do painel que toca disco | Rota nova no `internal_api.py` **+** método no `ClipProcessorClient.php` |
| Adicionar página ao painel | `routes/web.php` + controller + `resources/js/pages/*.tsx` |
| Alterar schema do pipeline | SQL novo em `mysql/init/`, aplicado à mão (**não** é migration) |

---

## 10. Divergências conhecidas e dívida técnica

Registrado aqui porque documentação errada custa mais caro que documentação ausente.

### Documentação desatualizada

1. **Stack do painel atualizada para Inertia.js + React + shadcn UI** — referências legadas a Filament nos READMEs foram corrigidas em favor da stack real (Laravel 12 + Inertia.js + React 19 + Tailwind CSS + shadcn UI).
2. **`.planning/research/ARCHITECTURE.md`** é pesquisa de junho, não estado atual: descreve migração do bot para o n8n e painel Filament, nenhum dos dois válido hoje.
3. **`n8n/workflows/README.md`** manda importar workflows num container que não existe mais.

### Código morto

4. **`painel/app/Filament/Pages/Dashboard.php`** — órfão que sobreviveu por acidente à limpeza dos outros 18 arquivos Filament. `extends Filament\Pages\Dashboard`, classe que **não existe mais no autoloader**. Só não quebra porque nada o referencia; um `composer dump-autoload -o` com classmap authoritative daria fatal error. **Deve ser deletado.**
5. **`app-sidebar.tsx`** — flag `external` e o branch `<a>` existiam só para linkar rotas Filament. Nenhum item usa; dead code.
6. **`scripts/validate-infra.sh`** — checa n8n na 5678; como termina com `exit 1` se houver falha, **nunca passa**.
7. **`scripts/validate-phase6-n8n.py`** — aponta para `telegram-n8n/`, diretório que não existe. Explode ao rodar.
8. **`dedup.mark_failed_redis`** está definida mas nunca é chamada: download que falha deixa a chave `video:{id}` no Redis por 30 dias, então o RSS não re-ingere o vídeo.
9. Nomes de teste ainda dizem "Resource" (`SourceChannelResourceTest`), mas o conteúdo já é Inertia.

### Armadilhas de configuração

10. **`env()` fora de config** em `DashboardController` (`MAX_UPLOADS_PER_DAY`, `MANUAL_APPROVAL_REQUIRED`). Com `config:cache` ativo, `env()` retorna `null` e cai nos defaults **silenciosamente** — o painel passa a mostrar número diferente do que o publisher usa.
11. **Drift de default do `MAX_UPLOADS_PER_DAY`:** `:-2` no serviço `php`, `:-1` no `clip-processor`. Só não morde porque a var está setada no `.env` da raiz.
12. **`ANTHROPIC_API_KEY` vazia é um modo de falha silencioso:** o `selector` degrada limpo para o Groq, mas o `metadata_generator` instancia `anthropic.Anthropic()` sem key ⇒ exceção ⇒ **sempre** o fallback determinístico. O clip é publicado com o título bruto do vídeo original, sem erro visível.
13. **Senha inconsistente:** `painel:create-user` exige ≥ 10 chars; o reset pela UI (`SettingsController`) exige apenas 8.
14. **`destination_channels` seedados têm `youtube_channel_id` placeholder** (`UC_PLACEHOLDER_FUTEBOL` / `UC_PLACEHOLDER_PODCAST`). Se ninguém trocou no banco, seguem inválidos.
15. **`docker/nginx_conf/canaldecortes.conf` na raiz `wordpress/` tem 0 bytes** e é sobrescrito pelo bind-mount. Vestigial e confuso.
