# Phase 8: Painel Laravel/Filament - Research

**Researched:** 2026-07-01
**Domain:** Laravel 13 + Filament 5 admin panel over an existing MySQL schema owned by a Python pipeline; cross-container command execution from PHP to Python
**Confidence:** MEDIUM-HIGH (stack/API findings HIGH via official docs + sibling-project evidence in this exact repo; cross-container execution architecture is a new pattern for this stack — MEDIUM, flagged for validation)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Instalação e integração Docker**
- Localização: app Laravel em `canaldecortes/painel/` (isolado, versionado dentro do projeto).
- Container: reusa o container `php` (php-fpm) compartilhado em `wordpress/docker-compose.yml`. Novo bind mount: `./canaldecortes/painel:/var/www/html/painel:cached`. Zero container novo.
- Nginx: novo arquivo de conf próprio dentro de `canaldecortes/` (ex: `canaldecortes/docker/nginx/canaldecortes.conf`) e adicionado ao volume `nginx_conf` do container `nginx`. Sem tocar/editar/ler arquivos de outros projetos (kelnab, feeb, riodelux, etc.).
- URL: `http://canaldecortes.local` (raiz, sem subdomínio "painel"). Via `/etc/hosts` local.
- Acesso ao banco: conexão única direta ao container `mysql`. Laravel `.env`: `DB_HOST=mysql`, `DB_DATABASE=clips_automation`, credenciais do próprio `CLIPS_DB_*`. Eloquent Models apontam para tabelas existentes (`source_channels`, `destination_channels`, `source_videos`, `generated_clips`) — sem migrations Laravel para elas.
- Migrations Laravel novas: só as tabelas Laravel próprias (`users`, `sessions`, `cache`, `jobs`, `migrations`) — vivem no MESMO banco `clips_automation`. Prefixo `laravel_` opcional (a definir no plan).
- Redis: mesma instância `redis` compartilhada; Laravel usa DB index diferente do pipeline Python (ex: `REDIS_DB=1`) para não colidir chaves.
- Composer/assets: rodam via `docker exec php composer install` e `docker exec php php artisan ...`.

**Autenticação e usuários**
- Modo single-user. Comando artisan interativo `php artisan painel:create-user` (email + senha, bcrypt). Roda uma vez no setup.
- Email registrado no setup: `alessandrobm1988@gmail.com`. Senha nunca gravada em arquivo/env/seeder/memória.
- Login session-based padrão Filament 5. Redireciona para `/admin/login`. Nenhuma rota pública exceto login.
- Reset de senha: página de perfil ("Alterar senha": atual + nova + confirmação). Sem email/magic link.
- Emergência: `php artisan painel:reset-password {email}` via CLI.
- Rota `/register` desabilitada.

**CRUD de canais-fonte**
- Entrada: campo único com URL do canal YouTube.
- Resolução: `docker exec clip-processor yt-dlp --flat-playlist --skip-download --dump-single-json {url}` via `Symfony\Component\Process` (ou equivalente) — extrai `channel_id`, `channel_name`, `channel_handle`. Zero cota YouTube Data API.
- Persistência: INSERT em `source_channels` com `youtube_channel_id`, `name`, `channel_handle`, `target_niche` (Select::make explícito), `blacklisted=FALSE` default.
- Toggle blacklist: Filament Toggle inline (UPDATE puro em `blacklisted`). Vídeos já enfileirados NÃO são purgados. Tooltip: "Afeta apenas novos vídeos. Para purgar a fila use SQL manual".
- Erros do yt-dlp: notificação de erro Filament ("Não consegui resolver esse canal. Verifique a URL").

**CRUD de canais-destino e OAuth**
- CRUD: `slug`, `name`, `niche` (Select::make explícito), `youtube_channel_id`, `credit_template`, `active`.
- NUNCA usar `--generate` do Filament em tabelas com ENUM.
- Fluxo OAuth do canal: painel exibe instrução copy-paste `docker exec -it clip-processor python -m src.youtube_oauth --channel {slug}`. Operador roda no host. Nenhuma lógica OAuth no Laravel.
- Badge de status OAuth calculado sob demanda na listagem:
  - Arquivo `youtube/token-{slug}.json` não existe → missing (cinza).
  - Arquivo existe → authorized (verde).
  - Estado expired (vermelho) setado quando o pipeline Python reporta `oauth_expired`; painel lê de campo simples (nome exato a definir no plan).
- Verificação de arquivo: Laravel lê o mesmo volume `./youtube:/app/youtube:ro` que o clip-processor usa.

**Dashboard e widgets**
- Auto-refresh: widgets Filament nativos com `->pollingInterval('5s')`. Zero SSE/WebSockets/Reverb.
- 4 widgets iniciais: (1) cota YouTube por canal-destino hoje (Redis `youtube_uploads:{channel_id}:{YYYY-MM-DD}`); (2) fila de aprovação (`generated_clips.status='pending'`) com actions inline Aprovar/Rejeitar; (3) últimos 10 uploads publicados; (4) últimas falhas do pipeline (`source_videos.status='failed'` OU `generated_clips.status='failed'`).

**Aprovar / Rejeitar clip**
- Aprovar: UPDATE puro `generated_clips SET status='approved' WHERE id=? AND status='pending'`. Espelha `/aprovar` do Telegram — sem módulo Python.
- Rejeitar: `docker exec clip-processor python -m src.rejeitar {clip_id}` via `Symfony\Component\Process`. Preserva side-effect de apagar o MP4. Reusa exit codes 0/1/2.
- Consistência com bot: comportamento IDÊNTICO ao Telegram — publisher só consome clips `approved`.

**Preview do clip**
- Thumbnail + título + descrição + tags + status + link YouTube. Sem player HTML5.
- Se quiser assistir: abrir MP4 direto no Finder/VLC (volume local). Documentar no README.

### Claude's Discretion (planner decide)
- Estrutura exata das Filament Resources (campos exibidos, ordem, tabs).
- Estratégia de cache/queries do widget de cota (ler Redis toda hora ou memoizar 5s).
- Nome exato da coluna que registra `oauth_expired` reportado pelo pipeline (coluna nova em `destination_channels` vs Redis vs cache Laravel).
- Uso de prefixo `laravel_` nas tabelas Laravel nativas em `clips_automation`.
- Layout visual de cada widget (cards, grids, cores dos badges).
- Copy exato das mensagens de erro e sucesso.
- Estratégia para expor `docker exec` do container `php` para o container `clip-processor` (docker socket mounted vs sidecar helper vs ssh interno) — decisão técnica do planner e do gsd-phase-researcher.

### Deferred Ideas (OUT OF SCOPE)
- 2FA (TOTP) no login — só se painel virar público em produção.
- Basic Auth extra no nginx — mesma razão.
- Fluxo OAuth 100% no Laravel — copy-paste basta.
- Player HTML5 embutido — abrir MP4 no Finder é suficiente.
- Modal "purgar vídeos na fila" ao blacklistar — contradiz decisão da Phase 7.
- Bulk actions (blacklistar N canais de uma vez) — volume não justifica ainda.
- Notificações push do painel para o Telegram — Phase 9 (bot Laravel).
- Rate limiting por canal-fonte — deferred (nota da Phase 7).
- Dashboard de custos (Groq + Claude usage) — medir escala primeiro.
- Comando artisan `painel:health-check` — nice-to-have, planner decide.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-------------------|
| PANEL-01 | Operador adiciona/remove/desativa canais-fonte via formulário web sem SQL | Filament Resource pattern (Select::make explícito, ToggleColumn), Process facade com array-command para invocar `yt-dlp` — ver Architecture Patterns e Code Examples |
| PANEL-02 | Operador adiciona canais-destino com niche e status OAuth (authorized/expired/missing) pelo painel | Schema real de `destination_channels` confirmado (mysql/init/06-multi-canal-migration.sql); gap real encontrado — pipeline Python NÃO emite `oauth_expired` hoje (uploader.py não trata `RefreshError`) — ver Common Pitfalls #3 e Open Questions #1 |
| PANEL-03 | Dashboard mostra status em tempo real com atualização automática | `->poll('5s')` em Table, `$pollingInterval` default 5s em widgets stats — confirmado via docs oficiais Filament 5.x |
| PANEL-04 | Operador aprova/rejeita clips pelo painel (alternativa ao Telegram) | `recordActions()` (renomeado de `actions()` no Filament 5), `rejeitar.py` exit codes 0/1/2 já documentados e reutilizáveis, UPDATE guard idêntico ao usado por `/aprovar` — ver Code Examples |
| PANEL-05 | Painel protegido por autenticação básica de usuário/senha | Filament `->login()` + `authGuard`, `painel:create-user` via Laravel Prompts (`password()` mascarado), confirmado disponível (laravel/prompts é dependência do laravel/framework 13) |
</phase_requirements>

## Summary

Este é o primeiro app Laravel/Filament do projeto Canal de Cortes, mas NÃO é o primeiro do stack Docker: o mesmo `docker-compose.yml` e o mesmo container `php` já hospedam o Kelnab, rodando exatamente **Laravel ^13 + Filament ^5.4 + Pest ^4** — essa combinação está validada em produção neste ambiente, reduzindo o risco de incompatibilidade de versões a quase zero. O padrão de vhost Nginx (`kelnab.conf`) e o padrão de bind-mount no `php`/`nginx` do docker-compose raiz são diretamente reaproveitáveis.

O ponto genuinamente novo e de maior risco desta fase é a comunicação PHP→Python: duas ações do painel (resolver canal-fonte via `yt-dlp` e rejeitar um clip) precisam executar um comando dentro do container `clip-processor` a partir do container `php`. A imagem `php` compartilhada NÃO tem `docker` CLI instalado e NÃO monta `/var/run/docker.sock`, e ela é compartilhada por ~8 projetos Laravel independentes (kelnab, feeb, riodelux, gringo, placebeats, etc.) — montar o socket Docker nela daria a QUALQUER um desses projetos controle total sobre todos os containers do host, uma escalada de privilégio inaceitável e incompatível com a regra de isolamento entre projetos já registrada no histórico do projeto. A pesquisa recomenda **não usar `docker exec`/Docker socket** e, em vez disso, expor um pequeno servidor HTTP interno dentro do próprio container `clip-processor` (que já está na mesma rede Docker `internal` que o `php`), com 2 endpoints mínimos (`/internal/resolve-channel`, `/internal/reject-clip`) chamados via `Illuminate\Support\Facades\Http`. Isso preserva 100% dos exit codes e side-effects já implementados em `rejeitar.py`, sem tocar em Docker no host e sem aumentar a superfície de ataque dos outros projetos do stack.

Um segundo achado relevante: o estado `expired` do badge OAuth (exigido literalmente por PANEL-02) não tem hoje nenhum produtor no pipeline Python — `uploader.py` só tenta `creds.refresh()` e não captura `google.auth.exceptions.RefreshError`. Ler apenas o arquivo `token-{slug}.json` não é suficiente para distinguir "autorizado" de "expirado" (o arquivo continua existindo mesmo com refresh_token revogado). É necessário um toque cirúrgico em `uploader.py` (captura de exceção + persistência de 1 coluna) para que o requisito seja de fato satisfazível — está documentado em detalhe nos Pitfalls e Open Questions.

**Primary recommendation:** Use Laravel 13 + Filament 5.4 (idêntico ao Kelnab), monte o painel em `canaldecortes/painel/` no container `php` já existente, resolva CRUDs e widgets com os componentes nativos do Filament 5 (`Select::make` explícito, `ToggleColumn`, `TableWidget` com `->poll('5s')`, `recordActions()`), e substitua toda comunicação PHP→Python planejada via `docker exec` por chamadas HTTP internas a um endpoint leve dentro do `clip-processor` — mantendo os exit codes/side-effects do `rejeitar.py` intactos.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|---------------|
| laravel/framework | ^13.0 | Framework base | Já validado neste stack pelo Kelnab; STATE.md já registrou "Laravel 13 (não 11, EOL)" como decisão de Roadmap v2.0 |
| filament/filament | ^5.4 | Admin panel (Resources, Widgets, Actions, Notifications) | Idêntico ao Kelnab (`composer.json` confirmado); v5 já roda em produção neste ambiente |
| laravel/prompts | ^0.3 (dependência transitiva do framework) | `text()`/`password()` mascarado em comandos artisan interativos | Necessário para `painel:create-user` sem nunca ecoar a senha no terminal |
| predis/predis OU extensão `redis` (phpredis) | ^3.4 / nativa | Cliente Redis para ler `youtube_uploads:*` e opcionalmente cache/session | `php` Dockerfile já compila `pecl install redis` (phpredis nativo) — usar `REDIS_CLIENT=phpredis` evita dependência composer extra |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pestphp/pest + pestphp/pest-plugin-laravel | ^4.x / ^4.x | Test runner | Padrão do Kelnab (`composer.json require-dev`); manter consistência com o resto do stack |
| laravel/pint | ^1.27 | Code style | Já usado pelo Kelnab; opcional mas consistente |
| Flask (Python, no lado clip-processor) | leve, sem versão fixa (ou `http.server`/`wsgiref` puro) | Servidor HTTP interno mínimo para expor `resolve-channel` e `reject-clip` ao painel | Ver Architecture Patterns — substitui `docker exec` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| HTTP sidecar interno no clip-processor | Montar `/var/run/docker.sock` no container `php` + instalar Docker CLI | Mais simples de escrever, mas dá controle total de Docker do host a TODOS os ~8 projetos Laravel que compartilham o container `php` — risco de segurança inaceitável neste ambiente multi-tenant. Rejeitado. |
| HTTP sidecar interno no clip-processor | SSH do `php` para `clip-processor` | Exige instalar/gerenciar `sshd`, chaves de host e usuário dentro do `clip-processor` — mais partes móveis que um endpoint HTTP simples, sem ganho de segurança real (mesma rede interna `internal`). Rejeitado. |
| Flask/`http.server` como thread em `main.py` | Endpoint dedicado com FastAPI + uvicorn | FastAPI/uvicorn adiciona um novo runtime ASGI e mais dependências; para 2 endpoints internos de baixíssimo tráfego, Flask (ou até `http.server`/`BaseHTTPRequestHandler` puro) é suficiente e mais leve. Recomendado: Flask por legibilidade, mas `http.server` puro é aceitável se quiser zero dependência nova. |
| Prefixo `laravel_` nas tabelas nativas do Laravel | Sem prefixo | Não há colisão de nomes hoje (`source_channels`, `source_videos`, `generated_clips`, `destination_channels` vs `users`, `sessions`, `cache`, `jobs`) — prefixo é defesa contra colisão futura, não uma necessidade atual. Recomendação: sem prefixo, mais simples; revisitar se um dia disputar nomes. |

**Installation (dentro do container `php`, projeto criado em `canaldecortes/painel/`):**
```bash
docker exec -it php bash -c "cd /var/www/html/painel && composer create-project laravel/laravel . '^13.0'"
docker exec -it php bash -c "cd /var/www/html/painel && composer require filament/filament:'^5.4'"
docker exec -it php bash -c "cd /var/www/html/painel && php artisan filament:install --panels"
docker exec -it php bash -c "cd /var/www/html/painel && composer require pestphp/pest pestphp/pest-plugin-laravel --dev"
docker exec -it php bash -c "cd /var/www/html/painel && php artisan pest:install"
```

## Architecture Patterns

### Recommended Project Structure
```
canaldecortes/painel/
├── app/
│   ├── Console/Commands/
│   │   ├── CreatePainelUser.php        # painel:create-user (Laravel Prompts)
│   │   └── ResetPainelPassword.php     # painel:reset-password {email}
│   ├── Filament/
│   │   ├── Resources/
│   │   │   ├── SourceChannelResource.php
│   │   │   └── DestinationChannelResource.php
│   │   └── Widgets/
│   │       ├── QuotaTodayWidget.php        # stats widget, pollingInterval 5s
│   │       ├── PendingApprovalWidget.php    # TableWidget com recordActions Aprovar/Rejeitar
│   │       ├── RecentUploadsWidget.php      # TableWidget últimos 10 publicados
│   │       └── RecentFailuresWidget.php     # TableWidget failed
│   ├── Models/
│   │   ├── SourceChannel.php           # aponta para source_channels (sem timestamps custom além dos já existentes)
│   │   ├── DestinationChannel.php      # aponta para destination_channels + accessor oauth_status
│   │   ├── SourceVideo.php
│   │   └── GeneratedClip.php
│   ├── Providers/Filament/AdminPanelProvider.php
│   └── Services/
│       └── ClipProcessorClient.php     # wrapper Http::baseUrl(config('services.clip_processor.url'))
├── database/migrations/                # só users/sessions/cache/jobs (padrão Laravel), NENHUMA migration para tabelas do pipeline
├── config/services.php                 # 'clip_processor' => ['url' => env('CLIP_PROCESSOR_INTERNAL_URL'), 'token' => env('CLIP_PROCESSOR_INTERNAL_TOKEN')]
└── tests/
    ├── Feature/
    └── Unit/
```

### Pattern 1: Eloquent Models sobre tabelas existentes do pipeline (sem migration)
**What:** Models Eloquent com `$table` explícito, `$fillable`, e SEM `Schema::create` correspondente — o schema já existe via `mysql/init/*.sql`.
**When to use:** Toda vez que o CRUD do painel opera em `source_channels`, `destination_channels`, `source_videos`, `generated_clips`.
**Example:**
```php
// app/Models/DestinationChannel.php
class DestinationChannel extends Model
{
    protected $table = 'destination_channels';
    protected $fillable = ['slug', 'name', 'niche', 'youtube_channel_id', 'credit_template', 'active'];
    public $timestamps = true; // created_at/updated_at já existem na tabela (ver 06-multi-canal-migration.sql)

    public function getOauthStatusAttribute(): string
    {
        if ($this->oauth_expired_flag) {
            return 'expired';
        }
        return file_exists(storage_path("app/youtube/token-{$this->slug}.json")) ? 'authorized' : 'missing';
    }
}
```

### Pattern 2: Table widget com polling nativo (PANEL-03)
**What:** `Filament\Widgets\TableWidget` com `->poll('5s')` na `table()`.
**When to use:** Fila de aprovação, últimos uploads, últimas falhas.
**Example:**
```php
// Source: https://filamentphp.com/docs/5.x/tables/overview (confirmado via WebFetch)
use Filament\Widgets\TableWidget as BaseWidget;
use Filament\Tables\Table;
use Filament\Actions\Action;

class PendingApprovalWidget extends BaseWidget
{
    public function table(Table $table): Table
    {
        return $table
            ->query(GeneratedClip::query()->where('status', 'pending'))
            ->poll('5s')
            ->recordActions([
                Action::make('aprovar')
                    ->requiresConfirmation()
                    ->action(fn (GeneratedClip $record) =>
                        GeneratedClip::where('id', $record->id)
                            ->where('status', 'pending')
                            ->update(['status' => 'approved'])
                    ),
                Action::make('rejeitar')
                    ->requiresConfirmation()
                    ->action(fn (GeneratedClip $record, ClipProcessorClient $client) =>
                        $client->rejectClip($record->id)
                    ),
            ]);
    }
}
```

### Pattern 3: Ponte HTTP interna em vez de `docker exec` (decisão de arquitetura desta fase)
**What:** Em vez de `Symfony\Component\Process`/`Illuminate\Support\Facades\Process` rodando `docker exec clip-processor ...` a partir do `php`, o `clip-processor` expõe uma pequena API HTTP interna (mesma rede Docker `internal`, sem porta publicada no host) com 2 rotas:
- `POST /internal/resolve-channel` `{url}` → roda `yt-dlp --flat-playlist --skip-download --dump-single-json {url}` internamente e devolve JSON `{channel_id, channel_name, channel_handle}` ou erro.
- `POST /internal/reject-clip` `{clip_id}` → chama a função `rejeitar(clip_id)` já existente em `src/rejeitar.py` diretamente (sem subprocess) e devolve `{exit_code, message}`.

**When to use:** Toda vez que o painel precisar de uma ação que hoje só existe como script Python (`yt-dlp`, `rejeitar.py`). NÃO se aplica ao fluxo OAuth (`youtube_oauth.py`), que continua 100% copy-paste manual no terminal do operador — não há chamada programática do Laravel ali, então não há problema de Docker/exec a resolver nesse caso.
**Why not `docker exec`:** o container `php` é compartilhado por outros projetos Laravel do mesmo host (`kelnab`, `feeb`, `riodelux`, `gringo`, `placebeats` — todos montados no mesmo `docker-compose.yml` raiz). Instalar `docker` CLI + montar `/var/run/docker.sock` nesse container concede a QUALQUER um desses projetos (mesmo os que nada têm a ver com Canal de Cortes) controle root sobre todos os containers do host. Isso viola a separação entre projetos já estabelecida para este ambiente.
**Example (lado Python — adição mínima, não um novo módulo grande):**
```python
# clip-processor/src/internal_api.py (novo arquivo pequeno)
from flask import Flask, request, jsonify
import subprocess, os
from src.rejeitar import rejeitar

app = Flask(__name__)
INTERNAL_TOKEN = os.environ.get('CLIP_PROCESSOR_INTERNAL_TOKEN')

def _check_auth():
    return request.headers.get('X-Internal-Token') == INTERNAL_TOKEN

@app.post('/internal/reject-clip')
def reject_clip():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    clip_id = request.json.get('clip_id')
    exit_code = rejeitar(int(clip_id))
    return jsonify(exit_code=exit_code)

@app.post('/internal/resolve-channel')
def resolve_channel():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    url = request.json.get('url')
    result = subprocess.run(
        ['yt-dlp', '--flat-playlist', '--skip-download', '--dump-single-json', url],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return jsonify(error='yt-dlp failed', stderr=result.stderr), 422
    return jsonify(raw=result.stdout)
```
```python
# clip-processor/src/main.py (trecho a acrescentar antes de scheduler.start())
import threading
from src.internal_api import app as internal_app
threading.Thread(
    target=lambda: internal_app.run(host='0.0.0.0', port=8090, use_reloader=False),
    daemon=True,
).start()
```
**Example (lado Laravel):**
```php
// Source: https://laravel.com/docs/13.x/http-client (padrão Illuminate\Support\Facades\Http)
use Illuminate\Support\Facades\Http;

class ClipProcessorClient
{
    public function rejectClip(int $clipId): int
    {
        $response = Http::timeout(10)
            ->withHeader('X-Internal-Token', config('services.clip_processor.token'))
            ->post(config('services.clip_processor.url') . '/internal/reject-clip', ['clip_id' => $clipId]);

        return $response->json('exit_code', 1);
    }
}
```

### Pattern 4: Select explícito em ENUM/niche (regra já registrada no Roadmap v2.0)
**What:** SEMPRE `Select::make('niche')->options(['futebol' => 'Futebol', 'podcast' => 'Podcast'])`, NUNCA `php artisan make:filament-resource --generate` em `destination_channels`/`generated_clips` (ambas têm ENUM/valores fixos que o gerador automático poderia corromper).
**When to use:** Todo formulário que toca `niche`, `target_niche` ou (indiretamente, leitura apenas) `generated_clips.status`.

### Anti-Patterns to Avoid
- **Migration Laravel para tabelas do pipeline:** NUNCA rodar `php artisan make:migration create_source_channels_table` — a tabela já existe e tem FKs geridas pelo SQL em `mysql/init/`. Usar apenas Models apontando para o schema existente.
- **`--generate` em Resources com ENUM:** já documentado como anti-pattern no Roadmap v2.0 — reforçado aqui porque `destination_channels.niche` e `generated_clips.status` são exatamente esse caso.
- **Montar `docker.sock` num container compartilhado por múltiplos projetos:** ver Pattern 3.
- **Ler apenas a existência do arquivo de token para decidir "expired":** o arquivo continua existindo mesmo com refresh_token revogado — ver Common Pitfalls #3.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Auto-refresh do dashboard a cada 5s | Livewire polling customizado, JS `setInterval` + fetch | `->poll('5s')` (Table) / `$pollingInterval` (Stats/Chart widgets) nativos do Filament | Já é o comportamento default de `StatsOverviewWidget` (5s) e suportado nativamente em qualquer `Table` — zero JS customizado necessário |
| Confirmação antes de aprovar/rejeitar | Modal customizado Livewire | `Action::make(...)->requiresConfirmation()` | Nativo do Filament Actions, já cobre acessibilidade e UX padrão |
| Autenticação e redirecionamento para login | Middleware customizado de auth | `->login()` do `Panel` + `Authenticate::class` em `authMiddleware()` | Filament já implementa isso; reinventar introduz bugs de sessão/CSRF |
| Rodar comando externo e capturar exit code/stdout/stderr | `shell_exec`/`exec()` cru do PHP | `Illuminate\Support\Facades\Process` (array-command, `->timeout()`, `->run()->exitCode()`) | API testável (`Process::fake()`), evita escaping manual de shell, timeout embutido |
| Badge colorido por status | CSS customizado | `TextColumn::make(...)->badge()->color(fn ($state) => match(...))` | Padrão nativo Filament, mapeamento direto estado→cor |

**Key insight:** Praticamente todo requisito desta fase (CRUD, polling, actions, auth) tem um componente nativo do Filament 5 — a única peça genuinamente "não resolvida por biblioteca" é a ponte de execução PHP→Python, que é um problema de arquitetura de infraestrutura, não de UI, e está tratada no Pattern 3.

## Common Pitfalls

### Pitfall 1: Montar Docker socket num container compartilhado por múltiplos projetos
**What goes wrong:** Qualquer aplicação Laravel hospedada no mesmo container `php` (kelnab, feeb, riodelux, gringo, placebeats) passaria a ter, transitivamente, controle root sobre todos os containers do host assim que o socket for montado.
**Why it happens:** É a solução "óbvia" e mais rápida de implementar para rodar comandos em outro container, e é exatamente o que o CONTEXT.md descreveu como uma das opções em aberto.
**How to avoid:** Usar a ponte HTTP interna (Pattern 3) — nenhuma alteração no `Dockerfile`/`docker-compose.yml` compartilhado além do bind mount do painel já decidido.
**Warning signs:** Qualquer PLAN.md que mencione `apt-get install docker.io` no Dockerfile compartilhado (`wordpress/Dockerfile`) ou `/var/run/docker.sock` no `docker-compose.yml` raiz deve ser reavaliado.

### Pitfall 2: Badge OAuth "expired" sem produtor no pipeline Python
**What goes wrong:** O painel exibe sempre "authorized" (arquivo existe) mesmo quando o refresh_token foi revogado (comum em apps OAuth em modo Testing, que expiram em 7 dias — já documentado como Blocker/Concern em STATE.md) — quebrando literalmente o requisito PANEL-02.
**Why it happens:** `uploader.py._load_credentials()` só chama `creds.refresh(Request())` quando `creds.expired` é True e possui `refresh_token`; não há `try/except` em volta dessa chamada, então uma falha de refresh (`google.auth.exceptions.RefreshError`, ex: `invalid_grant: Token has been expired or revoked`) atualmente propaga como exceção genérica e não persiste nenhum estado consultável pelo painel.
**How to avoid:** Adicionar um `try/except google.auth.exceptions.RefreshError` em `_load_credentials()` que, ao falhar, persiste um estado `expired` (recomendado: coluna `oauth_expired_flag BOOLEAN DEFAULT FALSE` em `destination_channels`, resetada para `FALSE` no próximo upload bem-sucedido do mesmo canal — self-healing). Isso é um toque cirúrgico e justificado em `uploader.py`, não uma reescrita do pipeline.
**Warning signs:** PLAN.md que assume "ler o arquivo `token-{slug}.json` é suficiente para status OAuth" sem mencionar captura de `RefreshError` — vai deixar PANEL-02 sem cobertura real para o estado `expired`.

### Pitfall 3: Ler a chave errada de Redis para o widget de cota
**What goes wrong:** Widget de cota sempre mostra 0/N mesmo com uploads recentes.
**Why it happens:** O pipeline Python conecta ao Redis SEM especificar `db=` (confirmado em `rss_poller.py`/`ttl_worker.py` → `redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)`), ou seja, usa o DB 0 padrão. A decisão do CONTEXT.md é o Laravel usar `REDIS_DB=1` para sessão/cache — se o widget usar a MESMA conexão Redis padrão do Laravel (DB 1) para ler `youtube_uploads:{channel_id}:{date}`, ele estará lendo o banco errado (vazio).
**How to avoid:** Configurar uma SEGUNDA conexão Redis nomeada em `config/database.php` (ex: `'pipeline' => [...'database' => 0]`) usada exclusivamente pelo widget de cota, distinta da conexão `default` (DB 1) usada por sessão/cache do Laravel.
**Warning signs:** Código do widget usando `Redis::get(...)` (conexão default) em vez de `Redis::connection('pipeline')->get(...)`.

### Pitfall 4: Chave de cota usa `youtube_channel_id`, não o ID interno da tabela
**What goes wrong:** Widget monta a chave Redis com `destination_channels.id` (INT autoincrement) e nunca bate com a chave real.
**Why it happens:** `publisher.py` instancia `QuotaManager(redis_client, channel_id=dest['youtube_channel_id'])` — confirmado em código — ou seja, a chave usa o ID do canal no YouTube (ex: `UC_PLACEHOLDER_FUTEBOL`), não o `id` interno do MySQL.
**How to avoid:** Widget deve montar a chave como `youtube_uploads:{destination_channel->youtube_channel_id}:{data_atual_America/Sao_Paulo}`.

### Pitfall 5: `Filament\Tables\Actions` (namespace do Filament 3/4) em vez de `Filament\Actions` (Filament 5)
**What goes wrong:** Código copiado de tutoriais/exemplos antigos (Filament 3.x, muito comum em buscas) usando `Filament\Tables\Actions\Action` falha silenciosamente ou gera erro de classe não encontrada.
**Why it happens:** A partir do Filament 4/5, as Actions foram extraídas para o pacote `filament/actions` com namespace unificado `Filament\Actions\*`, e o método de tabela mudou de `->actions([...])` para `->recordActions([...])` — confirmado via documentação oficial 5.x.
**How to avoid:** Sempre `use Filament\Actions\Action;` e `->recordActions([...])` neste projeto.

## Code Examples

### Comando artisan interativo de criação de usuário (PANEL-05)
```php
// Source: padrão Laravel Prompts, confirmado como dependência disponível (laravel/prompts ^0.3 via composer.lock do Kelnab)
use function Laravel\Prompts\text;
use function Laravel\Prompts\password;
use Illuminate\Support\Facades\Hash;
use App\Models\User;

class CreatePainelUser extends Command
{
    protected $signature = 'painel:create-user';

    public function handle(): int
    {
        $email = text('Email do operador', required: true);
        $pass = password('Senha (não será exibida)', required: true);

        User::create([
            'name' => 'Operador',
            'email' => $email,
            'password' => Hash::make($pass),
        ]);

        $this->info("Usuário {$email} criado.");
        return self::SUCCESS;
    }
}
```

### Select explícito de niche (não gerar via `--generate`)
```php
// Source: https://filamentphp.com/docs/5.x/forms/select (confirmado via WebFetch)
use Filament\Forms\Components\Select;

Select::make('niche')
    ->label('Nicho')
    ->options([
        'futebol' => 'Futebol',
        'podcast' => 'Podcast',
    ])
    ->required()
```

### Toggle inline de blacklist (PANEL-01)
```php
// Source: https://filamentphp.com/docs/5.x/tables/columns/toggle (confirmado via WebFetch)
use Filament\Tables\Columns\ToggleColumn;

ToggleColumn::make('blacklisted')
    ->label('Blacklisted')
    ->tooltip('Afeta apenas novos vídeos. Para purgar a fila use SQL manual.')
```

### Badge de status OAuth (PANEL-02)
```php
// Source: https://filamentphp.com/docs/5.x/tables/columns/text (confirmado via WebFetch)
use Filament\Tables\Columns\TextColumn;

TextColumn::make('oauth_status') // accessor no Model, ver Pattern 1
    ->badge()
    ->color(fn (string $state): string => match ($state) {
        'authorized' => 'success',
        'expired' => 'danger',
        'missing' => 'gray',
        default => 'primary',
    })
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-------------------|---------------|--------|
| `Filament\Tables\Actions\Action`, `->actions([...])` | `Filament\Actions\Action`, `->recordActions([...])` | Filament 4 (pacote `filament/actions` extraído) | Todo código de exemplo Filament 3.x encontrado em buscas precisa de tradução de namespace/método antes de ser usado neste projeto |
| `BadgeColumn::make(...)` | `TextColumn::make(...)->badge()->color(...)` | Filament 3+ (BadgeColumn foi deprecada/absorvida) | Usar `TextColumn` com `->badge()`, não procurar por `BadgeColumn` |

**Deprecated/outdated:** Nenhum achado específico de deprecação dentro do escopo desta fase além dos dois itens acima — este domínio (Filament 5, lançado recentemente) ainda não tem histórico longo de mudanças dentro da própria major version.

## Open Questions

1. **Qual é exatamente o mecanismo de persistência do estado `oauth_expired`?**
   - What we know: não existe hoje nenhum produtor desse sinal no pipeline Python (`uploader.py` não captura `RefreshError`); o Redis/telegram_notifier também não tem esse evento (`clip_expired` é algo diferente — refere-se a TTL de aprovação de clip, não a OAuth).
   - What's unclear: se o planner vai optar por tocar `uploader.py` (recomendado, ver Pitfall 2) ou se vai aceitar uma versão reduzida do requisito (ex: badge só authorized/missing, expired sempre cinza até o próximo upload falhar visivelmente e o operador notar via Telegram).
   - Recommendation: tocar `uploader.py` com uma coluna `oauth_expired_flag` (nome final a definir no plan) — é uma mudança pequena, isolada, e é a única forma de o painel realmente detectar token revogado sem esperar o operador perceber por outro canal.

2. **Onde exatamente roda o servidor HTTP interno do `clip-processor` (Pattern 3)?**
   - What we know: `main.py` hoje é um único processo em foreground rodando `BlockingScheduler.start()` (bloqueante); não há framework web nas dependências atuais (`requirements.txt`).
   - What's unclear: se o planner prefere Flask (mais legível, 1 dependência nova) ou um `http.server`/`BaseHTTPRequestHandler` sem dependências novas, e se prefere rodar o servidor numa thread dentro de `main.py` (mais simples) ou como processo separado no mesmo container via `supervisord` (mais isolado, mais complexo).
   - Recommendation: thread daemon dentro de `main.py` + Flask — menor esforço de implementação, tráfego baixíssimo (2 endpoints, uso de um único operador), consistente com o restante do pipeline que também roda tudo num único processo Python.

3. **Nome do panel/guard Filament — seguir o padrão multi-panel do Kelnab (`App\Gestao\...`, guard `gestao`) ou o padrão default de instalação (`App\Filament\...`, guard `web`)?**
   - What we know: Kelnab usa uma estrutura customizada de múltiplos panels/clusters porque atende múltiplos tipos de usuário; Canal de Cortes é single-user, single-panel.
   - What's unclear: nenhuma real ambiguidade técnica — é só uma escolha de escopo.
   - Recommendation: usar o padrão default gerado por `php artisan filament:install --panels` (`App\Filament\...`, panel id `admin`, guard `web`) — menos código, adequado a um único operador; a estrutura do Kelnab existe para resolver um problema (múltiplos tipos de usuário) que este projeto não tem.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Pest 4 (`pestphp/pest` + `pestphp/pest-plugin-laravel`) — a ser instalado no Wave 0, nenhum app Laravel existe ainda em `canaldecortes/painel/` |
| Config file | `canaldecortes/painel/tests/Pest.php` (gerado por `php artisan pest:install`) — não existe ainda |
| Quick run command | `docker exec php bash -c "cd /var/www/html/painel && php artisan test --filter=<Test>"` |
| Full suite command | `docker exec php bash -c "cd /var/www/html/painel && php artisan test"` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|--------------|
| PANEL-05 | Rota do painel sem login redireciona para `/admin/login` | Feature | `php artisan test --filter=AuthenticationTest` | ❌ Wave 0 |
| PANEL-01 | Form de canal-fonte insere linha em `source_channels` (com `Http::fake()`/`Process::fake()` mockando resolução) | Feature | `php artisan test --filter=SourceChannelResourceTest` | ❌ Wave 0 |
| PANEL-01 | yt-dlp retorna erro → notificação Filament de erro exibida, nenhuma linha inserida | Feature | `php artisan test --filter=SourceChannelResourceTest::it_shows_error_on_invalid_url` | ❌ Wave 0 |
| PANEL-02 | Form de canal-destino insere linha em `destination_channels` com `niche` via Select | Feature | `php artisan test --filter=DestinationChannelResourceTest` | ❌ Wave 0 |
| PANEL-02 | Accessor `oauth_status` retorna authorized/expired/missing corretamente conforme arquivo + flag | Unit | `php artisan test --filter=DestinationChannelOauthStatusTest` | ❌ Wave 0 |
| PANEL-03 | Widgets de dashboard configuram `->poll('5s')` / `$pollingInterval` | Unit/Feature (assert na config do componente, não no tempo real) | `php artisan test --filter=DashboardWidgetsTest` | ❌ Wave 0 |
| PANEL-04 | Action "Aprovar" muda `pending`→`approved` só quando status atual é `pending` | Feature | `php artisan test --filter=ClipApprovalTest::it_approves_pending_clip` | ❌ Wave 0 |
| PANEL-04 | Action "Rejeitar" chama o cliente HTTP interno e reflete o exit code retornado | Feature (`Http::fake()`) | `php artisan test --filter=ClipApprovalTest::it_rejects_clip_via_internal_api` | ❌ Wave 0 |

*(Nyquist adicional recomendado, fora do PANEL-XX formal mas cobrindo o Pitfall 2/3/4: teste unitário Python em `clip-processor/tests/test_uploader.py` cobrindo `RefreshError` capturado e flag persistida — ver Wave 0 Gaps.)*

### Sampling Rate
- **Per task commit:** `php artisan test --filter=<TesteRelevante>`
- **Per wave merge:** `php artisan test` (suite completa Pest)
- **Phase gate:** Full suite verde antes de `/gsd:verify-work`

### Wave 0 Gaps
- [ ] App Laravel inteiro (`composer create-project`, `filament:install --panels`, `pest:install`) — nada existe em `canaldecortes/painel/` hoje.
- [ ] `tests/Feature/AuthenticationTest.php`
- [ ] `tests/Feature/SourceChannelResourceTest.php`
- [ ] `tests/Feature/DestinationChannelResourceTest.php`
- [ ] `tests/Unit/DestinationChannelOauthStatusTest.php`
- [ ] `tests/Feature/DashboardWidgetsTest.php`
- [ ] `tests/Feature/ClipApprovalTest.php`
- [ ] `database/factories/SourceChannelFactory.php`, `DestinationChannelFactory.php`, `SourceVideoFactory.php`, `GeneratedClipFactory.php` (apontando para tabelas existentes, sem migrations correspondentes — factories precisam funcionar com `RefreshDatabase` só nas tabelas Laravel nativas + seeds manuais para as tabelas do pipeline em ambiente de teste)
- [ ] `clip-processor/src/internal_api.py` + `clip-processor/tests/test_internal_api.py` (novo, cobre os 2 endpoints da Pattern 3)
- [ ] Ajuste em `clip-processor/src/uploader.py` para capturar `RefreshError` + teste correspondente em `clip-processor/tests/test_uploader.py`
- [ ] Framework install: `composer require pestphp/pest pestphp/pest-plugin-laravel --dev && php artisan pest:install`

## Sources

### Primary (HIGH confidence)
- Filament 5.x docs — `https://filamentphp.com/docs/5.x/tables/overview` — confirmado `->poll('5s')`, `recordActions()`
- Filament 5.x docs — `https://filamentphp.com/docs/5.x/tables/columns/toggle` — `ToggleColumn`
- Filament 5.x docs — `https://filamentphp.com/docs/5.x/tables/columns/text` — `->badge()->color()`
- Filament 5.x docs — `https://filamentphp.com/docs/5.x/forms/select` — `Select::make(...)->options([...])`
- Filament 5.x docs — `https://filamentphp.com/docs/5.x/widgets/stats-overview` — `$pollingInterval` default 5s
- Laravel 13.x docs — `https://laravel.com/docs/13.x/processes` — `Illuminate\Support\Facades\Process`, timeout, exit code, `Process::fake()`
- Código-fonte do próprio repositório: `clip-processor/src/rejeitar.py`, `uploader.py`, `quota_manager.py`, `telegram_notifier.py`, `mysql/init/01-clips-schema.sql`, `mysql/init/06-multi-canal-migration.sql`, `wordpress/docker-compose.yml`, `wordpress/Dockerfile`, `kelnab/composer.json`, `kelnab/composer.lock`, `wordpress/docker/nginx_conf/kelnab.conf`, `kelnab/app/Providers/Filament/GestaoPanelProvider.php`

### Secondary (MEDIUM confidence)
- WebSearch — Tecnativa docker-socket-proxy `EXEC` flag (confirma que exec via socket é uma capacidade de alto risco desabilitada por padrão) — reforça a recomendação do Pattern 3
- WebSearch — `google.auth.exceptions.RefreshError` / `invalid_grant: Token has been expired or revoked` — confirma nome da exceção e comportamento
- WebSearch — `Filament\Widgets\TableWidget` como classe base para widgets de tabela — confirmado em múltiplas fontes de versões diferentes do Filament (não obtive a página exata da doc 5.x, que retornou 404)

### Tertiary (LOW confidence)
- Nenhum achado crítico dependeu exclusivamente de fonte não verificada.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Laravel 13 + Filament 5.4 já roda em produção neste exato ambiente Docker (Kelnab), zero incerteza de compatibilidade
- Architecture (ponte PHP→Python): MEDIUM — recomendação bem fundamentada em princípios de segurança e no código real do repo, mas é um padrão NOVO para este projeto (nenhum precedente de "sidecar HTTP" existe ainda no clip-processor) — validar no primeiro plan/checkpoint
- Pitfalls (oauth_expired, chave Redis): HIGH — confirmados lendo o código-fonte real (`uploader.py`, `publisher.py`, `rss_poller.py`), não inferência

**Research date:** 2026-07-01
**Valid until:** 30 dias (stack estável; Filament 5 é recente mas a API central usada aqui — tables, actions, widgets — tem baixa probabilidade de breaking change em patch releases)
