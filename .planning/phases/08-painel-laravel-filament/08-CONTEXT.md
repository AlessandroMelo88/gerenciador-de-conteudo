# Phase 8: Painel Laravel/Filament - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Painel web em Laravel 13 + Filament 5 para o único operador (single-user) gerenciar canais-fonte (CRUD com URL do YouTube), canais-destino (CRUD com badge de status OAuth), monitorar o pipeline em tempo real e aprovar/rejeitar clips da fila — sem SQL manual, sem depender do Telegram.

O painel vive em `canaldecortes/painel/`, reusa o container `php` compartilhado do `wordpress/docker-compose.yml`, é acessado em `canaldecortes.local` e lê/escreve direto na base `clips_automation` do MySQL 8.4 existente. Todo o pipeline Python (Phases 2–7) permanece intocado — o painel só orquestra dados e chama comandos existentes via `docker exec`.

**Fora do escopo desta fase:**
- Bot Telegram no Laravel (Phase 9)
- Deploy em servidor de produção (implantação futura, vide PROJECT.md)
- Multi-user, roles, permissões
- Fluxo OAuth 100% no Laravel (mantém `src.youtube_oauth` Python)

</domain>

<decisions>
## Implementation Decisions

### Instalação e integração Docker

- **Localização:** app Laravel em `canaldecortes/painel/` (isolado, versionado dentro do projeto).
- **Container:** reusa o container `php` (php-fpm) compartilhado em `wordpress/docker-compose.yml`. Novo bind mount: `./canaldecortes/painel:/var/www/html/painel:cached`. Zero container novo.
- **Nginx:** novo arquivo de conf **próprio** dentro de `canaldecortes/` (ex: `canaldecortes/docker/nginx/canaldecortes.conf`) e adicionado ao volume `nginx_conf` do container `nginx` no `wordpress/docker-compose.yml`. Padrão de virtual host segue o mesmo modelo dos outros Laravel do repositório, mas **sem tocar/editar/ler arquivos de outros projetos** (kelnab, feeb, riodelux, etc.).
- **URL:** `http://canaldecortes.local` (raiz, sem subdomínio "painel"). Configuração via `/etc/hosts` local.
- **Acesso ao banco:** conexão única direta ao container `mysql`. Laravel `.env`: `DB_HOST=mysql`, `DB_DATABASE=clips_automation`, credenciais do próprio `CLIPS_DB_*`. Eloquent Models apontam para tabelas existentes (`source_channels`, `destination_channels`, `source_videos`, `generated_clips`) — sem migrations Laravel para elas.
- **Migrations Laravel novas:** só as tabelas Laravel próprias (`users`, `sessions`, `cache`, `jobs`, `migrations`) — vivem no MESMO banco `clips_automation`. Prefixo `laravel_` opcional para evitar colisão futura (a definir no plan).
- **Redis:** mesma instância `redis` compartilhada; Laravel usa DB index diferente do pipeline Python (ex: `REDIS_DB=1`) para não colidir chaves.
- **Composer/assets:** rodam via `docker exec php composer install` e `docker exec php php artisan ...` — igual ao workflow dos outros Laravel do stack.

### Autenticação e usuários

- **Modo:** single-user. Um único operador (o dono do projeto) usa o painel.
- **Criação do usuário inicial:** comando artisan interativo — `php artisan painel:create-user` — pergunta email e senha, cria linha em `users` com senha hasheada (bcrypt). Roda uma vez no setup.
- **Email registrado no setup:** `alessandrobm1988@gmail.com`.
- **Senha:** digitada interativamente no comando artisan. **Nunca gravada em arquivo, env var, seeder ou memória.**
- **Login:** session-based padrão Filament 5 (cookie de sessão Laravel). Tentativa de acesso sem auth redireciona pra `/admin/login`. Nenhuma rota do painel é pública exceto login.
- **Reset de senha:** página de perfil dentro do painel ("Alterar senha": atual + nova + confirmação). Sem email, sem magic link.
- **Emergência (recomendado no plan):** disponibilizar também `php artisan painel:reset-password {email}` para resetar via CLI se o operador perder acesso.
- **Rota `/register`:** desabilitada.

### CRUD de canais-fonte

- **Entrada:** campo único que aceita URL do canal YouTube (ex: `https://youtube.com/@nome` ou `https://youtube.com/channel/UCxxx`).
- **Resolução:** ao salvar, Laravel chama `docker exec clip-processor yt-dlp --flat-playlist --skip-download --dump-single-json {url}` via `Symfony\Component\Process`; extrai `channel_id`, `channel_name`, `channel_handle`. Zero consumo de cota YouTube Data API (mesma tática do `/processar` do bot Telegram — Phase 6 Plan 06-04).
- **Persistência:** INSERT em `source_channels` com `youtube_channel_id`, `name`, `channel_handle`, `target_niche` (Select::make explícito), `blacklisted=FALSE` default.
- **Toggle blacklist:** Filament Toggle inline na tabela. UPDATE puro em `source_channels.blacklisted`. Vídeos já enfileirados NÃO são purgados (mantém decisão da Phase 7). Tooltip do toggle: "Afeta apenas novos vídeos. Para purgar a fila use SQL manual".
- **Erros do yt-dlp:** URL inválida ou canal inexistente → notificação de erro Filament ("Não consegui resolver esse canal. Verifique a URL"). Exit codes documentados na Phase 6 Plan 06-04 são reutilizados.

### CRUD de canais-destino e OAuth

- **CRUD:** formulário com `slug` (VARCHAR único), `name`, `niche` (Select::make explícito — sem ENUM auto-gerado), `youtube_channel_id`, `credit_template`, `active`.
- **Nunca usar `--generate` do Filament em tabelas com ENUM** (regra do Roadmap v2.0 — evita corrupção de state machine).
- **Fluxo OAuth do canal:** ao criar destination channel, o painel exibe um bloco de instrução "copy-paste": `docker exec -it clip-processor python -m src.youtube_oauth --channel {slug}`. Operador roda no host, faz o OAuth pelo browser (a ferramenta já existe desde Phase 7). Nenhuma lógica OAuth no Laravel.
- **Badge de status OAuth:** calculado sob demanda quando a listagem é renderizada. Regra:
  - Arquivo `youtube/token-{slug}.json` não existe → **missing** (badge cinza).
  - Arquivo existe → **authorized** (badge verde).
  - Estado `expired` (badge vermelho) é setado quando o pipeline Python reporta `oauth_expired` via `telegram_notifier`; painel lê essa sinalização de um campo simples (a definir no plan — provavelmente `destination_channels.oauth_status` ou Redis key). Detalhe fica para o planner.
- **Verificação de arquivo:** Laravel lê `storage_path()` ou path relativo mapeado ao mesmo volume `./youtube:/app/youtube:ro` que o clip-processor usa. Bind mount somente-leitura já existe no docker-compose do canaldecortes.

### Dashboard e widgets

- **Auto-refresh:** widgets Filament nativos com `->pollingInterval('5s')`. Zero SSE, zero WebSockets, zero Reverb.
- **Widgets iniciais (todos os 4):**
  1. **Cota YouTube por canal-destino hoje** — ex: "Futebol em Cortes: 2/3 · Podcast Cortes: 0/3". Lê `youtube_uploads:{channel_id}:{YYYY-MM-DD}` do Redis (chave definida pela Phase 7).
  2. **Fila de aprovação (`generated_clips.status='pending'`) em destaque** — table widget no topo com actions inline "Aprovar" / "Rejeitar".
  3. **Últimos 10 uploads publicados** — table widget com título, canal-destino, hora, link YouTube.
  4. **Últimas falhas do pipeline** — `source_videos.status='failed'` OU `generated_clips.status='failed'`, com mensagem de erro se houver.

### Aprovar / Rejeitar clip

- **Aprovar (Filament Action):** UPDATE puro em `generated_clips SET status='approved' WHERE id=? AND status='pending'`. Espelha o `/aprovar` do bot Telegram (Phase 6 Plan 06-07 — sem módulo Python).
- **Rejeitar (Filament Action):** chama `docker exec clip-processor python -m src.rejeitar {clip_id}` via `Symfony\Component\Process`. Isso preserva o side-effect crítico de apagar o MP4 do disco (Phase 6 Plan 06-03) e reusa exit codes documentados (0/1/2) para mostrar mensagem correta ao operador.
- **Consistência com bot:** o comportamento é IDÊNTICO ao Telegram — não há segundo caminho de aprovação. Publisher continua consumindo só clips `approved`.

### Preview do clip

- **Painel:** thumbnail (já gerada em `/app/videos/thumbnails/` pelo pipeline) + título + descrição gerada pelo Claude + tags + status + link YouTube (se publicado). **Sem player HTML5.** Rápido, sem expor MP4 via HTTP.
- **Se o operador quiser assistir antes de aprovar:** volume `videos/` fica no filesystem local — pode abrir o MP4 direto no Finder/VLC. Documentar isso no README do painel.

### Claude's Discretion (planner decide)

- Estrutura exata das Filament Resources (nomes de campos exibidos, ordem, agrupamento em tabs se necessário).
- Estratégia de cache/queries do widget de cota (ler Redis toda hora ou memoizar 5s).
- Nome exato da coluna que registra `oauth_expired` reportado pelo pipeline (coluna nova em `destination_channels` vs Redis vs cache Laravel).
- Uso de prefixo `laravel_` nas tabelas Laravel nativas em `clips_automation` (evitar colisão futura vs mais limpo sem prefixo).
- Layout visual de cada widget (cards, grids, cores dos badges).
- Copy exato das mensagens de erro e sucesso.
- Estratégia para expor `docker exec` do container `php` para o container `clip-processor` (docker socket mounted vs sidecar helper vs ssh interno) — decisão técnica do planner e do gsd-phase-researcher.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- **Schema MySQL:** Phase 7 já criou `destination_channels` com `slug`, `niche`, `credit_template`, `active`. `source_channels` já tem `target_niche`, `channel_handle`, `blacklisted`. `generated_clips.status` ENUM já tem `pending/approved/rejected/publishing/published/failed`. **Zero mudança de schema Python** — Filament só monta CRUD por cima.
- **`clip-processor/src/youtube_oauth.py`:** ferramenta CLI que gera `token-{slug}.json`. Reusada 100% via instrução copy-paste no painel.
- **`clip-processor/src/rejeitar.py`:** Phase 6 Plan 06-03 — exit codes documentados (0=ok, 1=clip não existe, 2=status inválido). Reusada via `docker exec`.
- **Volume `./youtube:/app/youtube`:** já montado no clip-processor. Painel monta o mesmo volume `ro` para checar existência de `token-{slug}.json`.
- **Volume `./videos:/app/videos`:** já existe. Painel monta `ro` para expor thumbnails ao Filament.
- **QuotaManager Redis keys:** Phase 7 estabeleceu `youtube_uploads:{channel_id}:{YYYY-MM-DD}` — painel lê direto.
- **Container `mysql` e `redis`:** já rodando no `wordpress/docker-compose.yml`. Só adicionar env vars no `.env` do painel.

### Established Patterns

- **Filament em ENUM:** SEMPRE `Select::make()->options([...])` explícito. NUNCA `--generate`. Regra registrada no Roadmap v2.0.
- **Injeção de dependência para testes:** modelo Python usa `client=None` opcional. Laravel/Filament: Feature tests com `RefreshDatabase` + factories; Unit tests para Actions com mock do `Symfony\Component\Process`.
- **Docker exec no pipeline:** Phase 6 já estabeleceu `n8n → docker exec clip-processor python -m src.rejeitar`. Painel Laravel segue mesmo padrão a partir do container `php`.
- **Comandos artisan versionados:** padrão de outros Laravel do stack — comandos custom em `app/Console/Commands/`.
- **Logger `[TIMESTAMP] [PREFIX] mensagem`:** pipeline Python usa; painel Laravel usa `Log::channel('painel')` com formato compatível para grep unificado (nice-to-have).

### Integration Points

- **`wordpress/docker-compose.yml`:** adicionar bind mount `./canaldecortes/painel:/var/www/html/painel:cached` no service `php` e mount do nginx conf novo do canaldecortes no service `nginx`. **Não editar volumes/config de outros projetos.**
- **Nginx conf novo:** vive em `canaldecortes/docker/nginx/canaldecortes.conf` (ou path equivalente definido pelo plan). server_name `canaldecortes.local`, root `/var/www/html/painel/public`, PHP-FPM em `php:9000`.
- **`canaldecortes/.env`:** adiciona `PAINEL_*` env vars se necessário (ou o painel usa `painel/.env` próprio — decidir no plan).
- **`canaldecortes/painel/.env` (Laravel):** conecta em `DB_HOST=mysql`, `REDIS_HOST=redis`, `REDIS_DB=1`. Usa credenciais já existentes.
- **Docker socket para `docker exec`:** container `php` precisa acesso a `/var/run/docker.sock` OU um mecanismo alternativo (a definir pelo planner — pode ser um endpoint HTTP interno no clip-processor que substitua o exec).
- **`/etc/hosts`:** operador adiciona `127.0.0.1 canaldecortes.local` no host — documentar no README.

</code_context>

<specifics>
## Specific Ideas

- **URL raiz `canaldecortes.local` sem subdomínio "painel"** — o painel É o Canal de Cortes para o operador.
- **Copy-paste OAuth vale ouro** — mais simples que qualquer botão que tente executar OAuth interativo por docker exec assíncrono. E é o mesmo comando que o operador já rodou uma vez para o primeiro canal (Phase 7).
- **Widgets padrão Filament resolvem 100% do dashboard** — não escrever Livewire component custom. `->pollingInterval('5s')` nativo.
- **Aprovar = UPDATE, rejeitar = docker exec** — assimetria intencional. Espelha o bot Telegram exatamente. Consistência é mais importante que uniformidade.
- **Sem player MP4 no painel** — reduz superfície de ataque, elimina configuração de nginx `location` protegido e reduz complexidade. Se precisar assistir, abre no Finder.
- **Email `alessandrobm1988@gmail.com` documentado; senha jamais.** Setup roda `php artisan painel:create-user` interativo.

</specifics>

<deferred>
## Deferred Ideas

- **2FA (TOTP) no login** — deferred; só se o painel virar público em produção.
- **Basic Auth extra no nginx** — deferred; mesma razão.
- **Fluxo OAuth 100% no Laravel** — deferred; copy-paste basta enquanto o operador tem acesso ao terminal.
- **Player HTML5 embutido** — deferred; abrir MP4 no Finder é suficiente.
- **Modal "purgar vídeos na fila" ao blacklistar** — deferred; contradiz decisão da Phase 7.
- **Bulk actions** (blacklistar N canais de uma vez) — deferred; volume não justifica ainda.
- **Notificações push do painel para o Telegram** — Phase 9 (bot Laravel).
- **Rate limiting por canal-fonte** — deferred (nota vinda da Phase 7).
- **Dashboard de custos (Groq + Claude usage)** — deferred; medir escala primeiro.
- **Comando artisan `painel:health-check`** — nice-to-have; planner decide.

</deferred>

---

*Phase: 08-painel-laravel-filament*
*Context gathered: 2026-07-01*
