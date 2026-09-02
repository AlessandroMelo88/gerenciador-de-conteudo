# Sistema — `painel/`

Referência de rotas, controllers e páginas. Visão conceitual em [`../ARCHITECTURE.md`](../ARCHITECTURE.md) seções 3 e 7.
O lado Python da fronteira está em [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md).

Última atualização: **13/08/2026**

---

## O que é

**Laravel 13 + Inertia 3 + React 19 + shadcn/ui + Tailwind 4 + Vite 8 + TypeScript.** Dark mode fixo via `class="dark"` no `<html>`.

O Filament foi removido por completo no commit `dca6e44` — qualquer menção a ele em README ou nome de arquivo é resíduo. Sobrou um órfão: `app/Filament/Pages/Dashboard.php`, que estende uma classe que não existe mais no autoloader. Só não quebra porque nada o referencia; **deve ser deletado**.

**O painel é para observar e corrigir, não para operar.** O fluxo normal é 100% automático, da descoberta via RSS até o upload.

---

## A regra da fronteira

Esta é a decisão que mais confunde quem chega agora:

- Para **ler** → o painel vai direto na fonte (MySQL, Redis, disco)
- Para **agir sobre disco ou processo** → o painel **nunca** toca no filesystem do pipeline; chama o sidecar HTTP em `clip-processor:8090` via `ClipProcessorClient`
- **Exceção:** transição de status simples o painel escreve direto no MySQL (ex.: `approve()` faz `UPDATE generated_clips SET status='approved'`)

Isso substituiu o padrão anterior de `docker exec` / socket do Docker.

**Consequência:** com o `clip-processor` parado, tudo que passa pelo sidecar falha — apagar arquivo, purgar antigos, resolver canal, processar URL.

---

## Rotas

Todas em `routes/web.php`. Grupo `['web','auth']` salvo indicação.

### Dashboard — `DashboardController`

| Método | Rota | Faz |
|---|---|---|
| GET | `/painel` | Página principal |
| POST | `/painel/clips/{clip}/approve` · `/reject` · `/reprocess` | Ações por clip |
| POST | `/painel/clips/bulk-approve` · `bulk-reject` | Ações em massa |
| POST | `/painel/videos/reorder` | Reordena a fila ociosa (drag) |
| POST | `/painel/videos/{video}/pause` · `/resume` · `/prioritize` | Controle de fila |
| POST | `/painel/videos/{video}/delete` · `/bulk-delete` | Apaga **arquivo**, não a linha |

### Vídeos — `SourceVideoController`

| Método | Rota | Faz |
|---|---|---|
| GET | `/painel/videos` | Listagem filtrável (tabs ativos/falharam/todos, filtro "seguro apagar", busca, data) + cards de métrica |
| POST | `/painel/videos/{video}/delete-file` · `/bulk-delete-files` | Apaga arquivo via sidecar |
| POST | `/painel/videos/purge-old` | **Única ação que apaga linha do banco**, por data |

Desde 12/08/2026 (commit `2af0657`) a página recebe dois blocos de métrica montados no controller
(`storageMetrics` e `downloadWindowMetrics` em `SourceVideoController`), renderizados por
`video-summary-cards.tsx`: espaço livre/usado/total em GB e % de uso do volume de vídeos, mais a
ocupação da janela de download. A limpeza por data ganhou atalhos de período.

O espaço vem de `disk_free_space` sobre o disco `clips-videos` — é o **disco do host**, o mesmo que o
disk guard de 2 GB do downloader mede. Número alto ali é o sintoma que precede o pipeline parar de
baixar.

### Canais

`DestinationChannelController` (`/painel/canais-destino`): CRUD, `POST .../watermark` para upload de marca d'água, badge de OAuth expirado.
`SourceChannelController` (`/painel/canais-fonte`): CRUD por URL — resolve o canal via sidecar (yt-dlp), tabs por nicho, toggles de ativo/blacklist.
`NicheController`: só `POST /painel/niches`.

### Outros

| Rota | Controller | Faz |
|---|---|---|
| `/painel/processar-video` | `ProcessVideoController` | Enfileira URL manual |
| `/painel/transcricoes` | `TranscriptionController` | Transcrição local (whisper.cpp); `/download` baixa o resultado |
| `/painel/configuracoes` | `SettingsController` | Reset de senha (exige 8 chars — o comando Artisan exige 10) |
| `/painel/documentacao` | `DocumentationController` | Ajuda estática |
| `/painel/clips/{clip}/preview` | closure | Serve o MP4 do clip para o `<video>` da fila |

### Públicas, sem CSRF

Registradas em `bootstrap/app.php`:
- `POST /telegramcanal` — webhook do bot
- `POST /internal/pipeline-event` — eventos vindos do `telegram_notifier.py`, mesmo `X-Internal-Token`

---

## Páginas

`resources/js/pages/`: `Dashboard`, `SourceVideos`, `SourceChannels`, `DestinationChannels`, `ProcessVideo`, `TranscricaoLocal`, `Settings`, `Documentation`, `Login`.

Não há layout compartilhado do Inertia — cada página compõe `AppSidebar` + `SiteHeader`, e o reuso de cabeçalho é via `page-header.tsx`.

### Como ler o Dashboard

Os quatro cards e as três listas confundem com frequência. O que cada um é:

| Elemento | O que realmente é |
|---|---|
| **Janela de download ativa** | Vídeos que **já baixaram e têm .mp4 em disco agora**. Não é fila de download. Teto: 6 `curto` + 4 `longo` |
| **Backlog download** | Vídeos `pending`, **sem arquivo**. Não aparecem na lista acima, e nenhum botão do painel apaga essas linhas (bug 6) |
| **Fila de aprovação** | Clips já cortados esperando aprovação. Só tem conteúdo se `MANUAL_APPROVAL_REQUIRED=true` |
| **Na fila (aguardando cota)** | Clips aprovados esperando vaga de upload |
| **Publicados (7d)** | Histórico do que foi ao ar |

O botão "Apagar" da janela de download apaga **o arquivo**, não o registro — vídeo sem `local_path` é ignorado como *skipped*.

---

## Autenticação

Guard `web` (session, driver `database`), único guard — não há Sanctum nem API. Logout é **`POST /logout`**, nunca GET.

**Não existe registro público.** O operador é criado por `php artisan painel:create-user` (senha ≥ 10 chars, nunca ecoada); reset por `painel:reset-password {email}`.

---

## Banco

O painel mapeia com Eloquent e `$table` explícito as tabelas do pipeline, que **não são migrations do Laravel** — nascem de SQL bruto em `mysql/init/01..07`, aplicado à mão.

Consequências:
- `php artisan migrate:fresh` **não** reconstrói o schema do pipeline
- por isso `RefreshDatabase` está desligado em `tests/Pest.php`; os testes usam `DatabaseTransactions` sobre tabelas pré-existentes

Única tabela de domínio do painel: `niches` (migration Laravel, seeda `futebol` e `podcast`). Não há FK ligando `source_channels.target_niche` a ela — segue VARCHAR livre.

---

## Armadilhas conhecidas

1. **`env()` fora de config** em `DashboardController` (`MAX_UPLOADS_PER_DAY`, `MANUAL_APPROVAL_REQUIRED`). Com `config:cache` ativo, `env()` retorna `null` e cai nos defaults **em silêncio** — o painel passa a mostrar número diferente do que o publisher usa.
2. **Drift de default:** `MAX_UPLOADS_PER_DAY` é `:-2` no serviço `php` e `:-1` no `clip-processor`. Só não morde porque a var está setada no `.env` da raiz.
3. O `.env` que o compose lê é o da **raiz `wordpress/`**, não o `canaldecortes/.env`.

---

## Testes

35 testes, 13 arquivos (Pest 4). Cobrem comandos do Telegram, aprovação/rejeição, eventos de pipeline, guards de auth, CRUD de canais e comandos Artisan.

**Sem cobertura:** `SettingsController`, `ProcessVideoController`, `SourceVideoController` (o mais complexo depois do Dashboard), `NicheController` e a rota `clips.preview`. Nenhum teste de frontend.
