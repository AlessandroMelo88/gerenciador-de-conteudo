# Arquitetura — Canal de Cortes

> **Escopo:** este documento descreve o sistema **como ele é hoje** (as-built). Revisado em 26/08/2026 após a adoção do PostgreSQL, das migrations Laravel e do contrato de qualidade bloqueante.
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

O `docker-compose.yml` fica na **raiz deste repositório** e foi configurado como um projeto Compose isolado. Ele usa a rede e os volumes próprios do projeto, não define `container_name`, não publica PostgreSQL/Redis no host e não reutiliza mounts de outros Compose. O `.env` lido pelo Compose é o `.env` da raiz deste repositório.

| Serviço | Dono | Portas no host | Papel para o Canal de Cortes |
|---|---|---|---|
| `clip-processor` | **exclusivo** | **nenhuma** | Daemon Python: todo o pipeline + sidecar HTTP interno na 8090 |
| `nginx` | exclusivo | `8088 → 80` | Serve o painel Laravel |
| `php` | exclusivo | — (9000 interno) | PHP-FPM que roda o painel Laravel |
| `postgres:16-alpine` | exclusivo | — (5432 interno) | Hospeda o database `clips_automation` em volume nomeado |
| `postgres-backup` | exclusivo, perfil `backup` | — | Gera dump diário compactado e checksum |
| `redis:7-alpine` | exclusivo | — (6379 interno) | Dedup + cota diária (db 0 = pipeline, db 1 = painel) |

Este projeto não depende de MySQL, MinIO ou serviços de outros Compose.

**Serviço opcional:** `postgres-backup` só é ativado pelo perfil `backup`. Os artefatos antigos de n8n/cloudflared não fazem parte deste checkout; a decisão de usar APScheduler no `clip-processor` e o scheduler do Laravel está registrada nos ADRs e nesta documentação.

### Acesso HTTP

Não existe rota `/painel` no nginx — `/painel` é apenas o caminho no filesystem dos containers. O acesso local é por `http://localhost:8088` → `docker/nginx/canaldecortes.conf` → root `/var/www/html/painel/public` → `fastcgi_pass php:9000`.

---

## 3. A fronteira entre os dois serviços

Esta é a decisão arquitetural mais importante do sistema, e a que mais confunde quem chega agora.

```
                 ┌──────────────────────────────────┐
   navegador ──► │  painel (Laravel 13 + Inertia)   │
                 └───────┬──────────────────┬───────┘
                         │                  │
        HTTP interno     │                  │  leitura direta
     X-Internal-Token    │                  │  (PostgreSQL, Redis, disco)
                         ▼                  ▼
                 ┌───────────────┐   ┌──────────────────┐
                 │ clip-processor│──►│ PostgreSQL / Redis│
                 │  sidecar 8090 │   │ volumes de vídeo │
                 └───────────────┘   └──────────────────┘
                         ▲
                         │  POST /internal/pipeline-event
                         └──── (eventos → Telegram)
```

**A regra:** para **ler**, o painel vai direto na fonte (PostgreSQL, Redis, disco). Para **agir sobre disco ou processos** (apagar arquivo, resolver canal via yt-dlp, enfileirar URL), o painel **nunca** toca no filesystem do pipeline — chama o sidecar HTTP. Isso substituiu o padrão anterior de `docker exec` / socket do Docker (decisão registrada em `painel/config/services.php:38-39`).

Exceção importante à regra: **transições de status simples o painel escreve direto no PostgreSQL** (ex.: `approve()` faz `UPDATE generated_clips SET status='approved' WHERE status='pending'`). Só o que mexe em disco/processo passa pelo sidecar.

### O sidecar (`clip-processor/src/internal_api.py`)

Flask em `0.0.0.0:8090`, thread daemon, **sem porta publicada** — só alcançável pela rede docker `internal`. Autenticação por token compartilhado no header `X-Internal-Token`, comparado com `CLIP_PROCESSOR_INTERNAL_TOKEN`. É **fail-closed**: se a env var estiver vazia, toda rota responde 401.

| Rota (POST) | Body | Retorno |
|---|---|---|
| `/internal/resolve-channel` | `{url}` | `{channel_id, channel_name, channel_handle}`; 422 se yt-dlp falhar |
| `/internal/process-url` | `{url, format}` | `{exit_code}` — 0 ok, 2 URL inválida, 3 metadata falhou |
| `/internal/reject-clip` | `{clip_id}` | `{exit_code}` — 0 ok, 1 inexistente, 2 status inválido |
| `/internal/delete-source-video` | `{source_video_id}` | `{deleted, freed_bytes}` |
| `/internal/purge-old-videos` | `{before_date}` | `{deleted_rows, freed_bytes}` |

`GET /health` no sidecar responde `{"status":"ok"}` e é usado pelo healthcheck do container. As rotas operacionais continuam sem porta publicada e protegidas pelo token interno.

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

1. **Descoberta** — `poll_all_channels` varre o RSS de cada `source_channel` ativo e não-blacklistado. Por entrada: dedup (Redis `SET NX`, TTL 30 dias, com fallback para PostgreSQL) → filtro de título (bloqueia keywords de aposta/cassino) → detecção de formato (yt-dlp metadata; falha ⇒ assume `curto`) → `INSERT status='pending'`.
2. **Download** — janela fixa **por formato**, que não se canibaliza: até 6 `curto` e 4 `longo` **ocupando disco simultaneamente**. Baixa só o déficit. Considera vídeos publicados nos últimos `FRESHNESS_DAYS` dias (default 365), ordenados por `published_at DESC` — a notícia mais recente ganha, não a descoberta mais antiga. yt-dlp 720p, 3 tentativas, aborta se restarem < 2 GB de disco.
3. **Transcrição** — Groq Whisper (`whisper-large-v3-turbo`, pt). Arquivo > 24 MB é convertido para MP3 antes.
4. **Seleção de momentos** — Claude Haiku escolhe os trechos com score 0–10. Prompt e truncagem variam por formato (`longo`: 1 segmento, 420–1200 s; `curto`: até 3 momentos, 30–180 s). Ver [`Docs/SISTEMA-IA-SELECAO.md`](Docs/SISTEMA-IA-SELECAO.md).
5. **Corte e pós-produção** — FFmpeg: corta → gera SRT → queima legenda → marca d'água → thumbnail com chamada textual literal. `curto` recebe crop 1080x1920; `longo` preserva o horizontal (`scale=-2:1080`).
6. **Metadata e thumbnail** — Claude Haiku/Groq gera título, descrição e tags para SEO; um prompt dedicado escolhe a chamada literal da thumbnail a partir da transcrição.
7. **Publicação** — respeitando cota, janela horária e round-robin (ver 4.2).

Cada etapa roda em `try/except` isolado que loga e dispara `notify('pipeline_failure', ...)` — uma falha não derruba o scheduler.

> ⚠️ **Nomenclatura enganosa:** apesar do nome, `rss_poller.py` não faz só polling. `poll_all_channels` também executa o estágio de IA (transcrição + seleção) e o de corte. O `pipeline_runner` só cuida de descoberta e download.

### 4.1 Fallbacks de IA

| Chamada | Fallback |
|---|---|
| Seleção de momentos (Claude) | **Groq LLaMA `llama-3.3-70b-versatile`.** Sem `ANTHROPIC_API_KEY`, vai direto no Groq. Groq falhando também ⇒ nenhum momento. |
| Metadata (Claude) | **Groq LLaMA `llama-3.3-70b-versatile`** (adicionado em 27/07/2026). Só se as duas IAs falharem cai no determinístico: título = título do vídeo original, descrição = `reason` da seleção, tags fixas. |
| Transcrição (Groq Whisper) | **Nenhum.** Falhou ⇒ vídeo marcado `failed`. |
| Dedup (Redis) | `SELECT` no PostgreSQL. |
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

**Todas as tabelas são geridas por migrations do Laravel** em `painel/database/migrations`, inclusive as tabelas do pipeline. O serviço `panel-init` aplica o schema antes de liberar os demais serviços. O painel e o clip-processor compartilham o PostgreSQL, cada um com suas responsabilidades de leitura e escrita. Backups são gerados pelo serviço opcional `postgres-backup` em `backups/postgres/`; a restauração exige confirmação explícita pelo script de operação.

Consequências práticas:
- `php artisan migrate:fresh` reconstrói o schema do pipeline e do painel; use-o apenas em banco descartável.
- A suíte usa `DatabaseTransactions` para isolar cada teste sem recriar as tabelas a cada caso.

| Tabela | Origem | Notas |
|---|---|---|
| `source_channels` | migration Laravel `2026_08_26_000000` | `target_niche`, `channel_handle`, `blacklisted`, `rss_url`, `active` |
| `source_videos` | migration Laravel `2026_08_26_000001` | FK → `source_channels`; `format` (`curto`/`longo`); `local_path`, `transcript_path` |
| `generated_clips` | migration Laravel `2026_08_26_000003` | FK → `source_videos` e → `destination_channels`; `score`, `reason`, `start_time`/`end_time`, `upload_error` |
| `destination_channels` | migration Laravel `2026_08_26_000002` | `slug`, `niche`, `credit_template`, `oauth_expired_flag` |
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

O Compose lê o `.env` da raiz deste repositório. Os defaults públicos estão em `.env.example` e `painel/.env.example`.

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
| Alterar schema do pipeline | nova migration em `painel/database/migrations/` + `php artisan migrate` |

---

## 10. Divergências conhecidas e dívida técnica

Registrado aqui porque documentação errada custa mais caro que documentação ausente.

### Legado documentado

1. **`.planning/research/ARCHITECTURE.md`** é pesquisa de junho/2026, não estado atual:
   descreve uma migração do bot para n8n e um painel Filament que não foram adotados.
2. **`dedup.mark_failed_redis`** permanece como helper de compatibilidade para fluxos que
   removem um registro falho antes de um novo polling; o fluxo normal mantém falhas no PostgreSQL
   como estado terminal.
3. Nomes de teste ainda dizem "Resource" (`SourceChannelResourceTest`), mas o conteúdo já
   é Inertia.

### Armadilhas de configuração

4. O painel lê `MAX_UPLOADS_PER_DAY` e `MANUAL_APPROVAL_REQUIRED` por
   `config/pipeline.php`, mantendo os valores corretos mesmo com `config:cache`.
5. O teto de `MAX_UPLOADS_PER_DAY` é centralizado em 6 no painel e no worker; alterações
   devem atualizar ambos os contratos.
6. **`destination_channels` seedados têm `youtube_channel_id` placeholder**
   (`UC_PLACEHOLDER_FUTEBOL` / `UC_PLACEHOLDER_PODCAST`). Se ninguém trocou no
   banco, seguem inválidos.
7. O endpoint do webhook do Telegram exige `TELEGRAM_WEBHOOK_SECRET` e o endpoint de
   eventos exige `CLIP_PROCESSOR_INTERNAL_TOKEN`; ambos falham fechado quando a
   configuração ou o header está ausente.
