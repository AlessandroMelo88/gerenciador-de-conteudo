# Phase 9: Bot Telegram no Laravel - Research

**Researched:** 2026-07-02
**Domain:** Telegram Bot SDK (PHP) + Laravel 13 webhook + Redis deduplication + Python sidecar HTTP
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BOT-01 | Bot Telegram migrado para Laravel; webhook em `alessandromelo.com.br/telegramcanal` via nginx → Laravel | irazasyed/telegram-bot-sdk v3.16 (Laravel 13 support confirmed); CSRF exclusion via bootstrap/app.php; nginx location block + setWebhook API call |
| BOT-02 | Todos os 6 comandos do v1 funcionam no novo bot Laravel com deduplicação de update_id via Redis | Command classes via SDK; Redis::set NX pattern; allowlist check via TELEGRAM_CHAT_ID_ALLOWED |
| BOT-03 | Notificações do pipeline Python (upload publicado, falha crítica, resumo diário) enviadas via Laravel | Novo endpoint POST /internal/pipeline-event em Laravel; telegram_notifier.py aponta para LARAVEL_NOTIFY_URL; ttl_worker.py idem; Artisan schedule para resumo diário |
</phase_requirements>

---

## Summary

Phase 9 migra o bot Telegram do n8n (Cloudflare Tunnel + n8n Trigger) para o Laravel já existente na Phase 8. O bot recebe updates via webhook HTTP POST em `/telegramcanal`, processa os 6 comandos do v1 com guard de allowlist e deduplicação Redis, e o pipeline Python passa a notificar o Laravel em vez do n8n.

A migração tem três pilares: (1) instalar `irazasyed/telegram-bot-sdk ^3.16` no projeto Laravel e criar 6 Command classes; (2) mudar `telegram_notifier.py` e `ttl_worker.py` para POST no novo endpoint Laravel `/internal/pipeline-event`; (3) registrar o novo webhook no Telegram (`setWebhook` apontando para `https://alessandromelo.com.br/telegramcanal`) e desativar o workflow do n8n.

O nginx para `canaldecortes.local` já rota tudo via `try_files → index.php` — nenhuma mudança de nginx é necessária localmente. Para produção (`alessandromelo.com.br`), o bloco nginx daquele domínio precisa de um `location /telegramcanal` apontando para o mesmo PHP-FPM. A deduplicação usa Redis DB 1 (mesmo Redis já conectado, conexão `default` do Laravel) com chave `tg:dedup:{update_id}` e TTL 300s.

**Primary recommendation:** Use `irazasyed/telegram-bot-sdk ^3.16` com o pattern `commandsHandler(true)`, não construa roteamento de comandos manualmente.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| irazasyed/telegram-bot-sdk | ^3.16 | Webhook handler, Command classes, sendMessage | Já decidido em STATE.md; v3.16.0 = suporte Laravel 13 (confirmado packagist) |
| Laravel Redis (phpredis) | já instalado | Deduplicação update_id via SET NX | Já configurado na Phase 8; conexão `default` (DB 1) isolada do Python (DB 0) |
| Laravel Eloquent | já instalado | Queries para /status e /clipes | Models GeneratedClip, SourceVideo já existem (Phase 8) |
| ClipProcessorClient | já existe | Delegar /rejeitar e /processar ao Python sidecar | Padrão Phase 8; mantém lógica de negócio no Python |
| Artisan Scheduling | já no Laravel | Cron do resumo diário (18h BRT) | Substitui o `06-cron-resumo-diario.json` do n8n |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pest 4 + pest-plugin-laravel | já instalado | Testes Feature do webhook e comandos | Mesmo padrão das Phases 8 |
| DatabaseTransactions | trait Pest | Rollback automático após cada teste | Não usar RefreshDatabase (apagaria tabelas do pipeline Python) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| irazasyed/telegram-bot-sdk | Guzzle HTTP puro para Telegram API | SDK abstrai parsing de Update, roteamento de comandos e replyWith helpers — mão-na-roda para os 6 comandos |
| Redis SET NX | Cache::remember ou DB lock | SET NX é atômico e mais rápido; evita race condition que Cache::remember não garante |
| Artisan schedule | n8n cron persistir | O objetivo de BOT-03 é eliminar dependência do n8n; schedule Laravel não requer infraestrutura adicional |

**Installation:**
```bash
docker exec -it php bash -c "cd /var/www/html/painel && composer require irazasyed/telegram-bot-sdk"
docker exec -it php bash -c "cd /var/www/html/painel && php artisan vendor:publish --tag='telegram-config'"
```

---

## Architecture Patterns

### Recommended Project Structure

```
painel/
├── app/
│   ├── Http/Controllers/
│   │   └── TelegramWebhookController.php   # recebe POST /telegramcanal
│   └── Telegram/Commands/
│       ├── StatusCommand.php
│       ├── ClipesCommand.php
│       ├── AprovarCommand.php
│       ├── RejeitarCommand.php
│       ├── ProcessarCommand.php
│       └── AjudaCommand.php
├── config/
│   └── telegram.php                        # gerado por vendor:publish
└── routes/
    └── web.php                             # + POST /telegramcanal e /internal/pipeline-event

clip-processor/src/
├── telegram_notifier.py                    # mudar N8N_NOTIFY_URL → LARAVEL_NOTIFY_URL
├── ttl_worker.py                           # mudar N8N_NOTIFY_URL → LARAVEL_NOTIFY_URL
└── internal_api.py                         # + POST /internal/process-url (novo endpoint)
```

### Pattern 1: Webhook Controller com Allowlist + Deduplicação

**What:** Controller recebe POST do Telegram, verifica allowlist (chat_id), faz deduplicação Redis e despacha para comandos SDK.
**When to use:** Toda entrada de update do Telegram — sem exceção.

```php
// Source: irazasyed.github.io/telegram-bot-sdk docs + Laravel 13 Redis facade
namespace App\Http\Controllers;

use Illuminate\Support\Facades\Redis;
use Telegram\Bot\Laravel\Facades\Telegram;

class TelegramWebhookController extends Controller
{
    public function handle(): \Illuminate\Http\Response
    {
        $update = Telegram::getWebhookUpdate();

        // 1) Allowlist: silencioso se chat_id não autorizado
        $chatId = optional($update->getMessage())->getChat()?->getId();
        $allowed = (string) config('telegram.bots.mybot.chat_id_allowed');
        if ($chatId && (string) $chatId !== $allowed) {
            return response('ok');
        }

        // 2) Deduplicação: SET NX — silencioso se update_id já visto
        $updateId = $update->updateId;
        $key = "tg:dedup:{$updateId}";
        $isNew = Redis::connection('default')->set($key, '1', 'NX', 'EX', 300);
        if (! $isNew) {
            return response('ok');
        }

        // 3) Despacha para Command classes
        Telegram::commandsHandler(true);

        return response('ok');
    }
}
```

### Pattern 2: Command Class (exemplo /aprovar)

**What:** Cada comando estende `Telegram\Bot\Commands\Command`, usa `$pattern` para argumento opcional e `$this->replyWithMessage()` para responder.

```php
// Source: telegram-bot-sdk.com/docs/guides/commands-system
namespace App\Telegram\Commands;

use App\Models\GeneratedClip;
use Telegram\Bot\Commands\Command;

class AprovarCommand extends Command
{
    protected string $name = 'aprovar';
    protected string $description = 'Aprova um clip para publicação';
    protected string $pattern = '{clip_id}';

    public function handle(): void
    {
        $clipId = (int) $this->argument('clip_id');

        if (! $clipId) {
            $this->replyWithMessage(['text' => 'Uso: /aprovar <id>']);
            return;
        }

        $affected = GeneratedClip::query()
            ->where('id', $clipId)
            ->where('status', 'pending')
            ->update(['status' => 'approved']);

        $text = $affected
            ? "Clip #{$clipId} aprovado."
            : "Clip #{$clipId} não encontrado ou status inválido.";

        $this->replyWithMessage(['text' => $text]);
    }
}
```

### Pattern 3: Endpoint Laravel para notificações Python

**What:** `POST /internal/pipeline-event` recebe evento do Python e envia mensagem Telegram ao operador.
**Auth:** Mesmo `X-Internal-Token` já usado pelo clip-processor ↔ painel (padrão Phase 8).

```php
// Em routes/web.php — SEM middleware auth (chamado pelo Python, não pelo browser)
Route::post('/internal/pipeline-event', function (\Illuminate\Http\Request $request) {
    $token = config('services.clip_processor.token');
    if ($request->header('X-Internal-Token') !== $token) {
        return response()->json(['error' => 'unauthorized'], 401);
    }

    $event   = $request->input('event');
    $payload = $request->input('payload', []);

    $text = match ($event) {
        'upload_published'  => "Upload publicado: {$payload['title']} — {$payload['youtube_url']}",
        'pipeline_failure'  => "Falha crítica [{$payload['stage']}]: {$payload['error_msg']}",
        'clip_ttl_warning'  => "Clip #{$payload['clip_id']} expira em {$payload['expires_in_hours']}h: {$payload['title']}",
        'daily_summary'     => $payload['text'] ?? 'Resumo diário: sem clips pendentes.',
        default             => "Evento desconhecido: {$event}",
    };

    \Telegram\Bot\Laravel\Facades\Telegram::sendMessage([
        'chat_id' => config('telegram.bots.mybot.chat_id_allowed'),
        'text'    => $text,
    ]);

    return response()->json(['ok' => true]);
});
```

### Pattern 4: Python → Laravel (telegram_notifier.py)

**What:** Trocar `N8N_NOTIFY_URL` por `LARAVEL_NOTIFY_URL` com Host header explícito para roteamento via nginx interno.

```python
# Source: baseado em clip-processor/src/telegram_notifier.py existente
import os
import requests

LARAVEL_NOTIFY_URL = os.getenv(
    'LARAVEL_NOTIFY_URL',
    'http://nginx/internal/pipeline-event'
)
LARAVEL_HOST_HEADER = os.getenv('LARAVEL_HOST_HEADER', 'canaldecortes.local')
INTERNAL_TOKEN = os.getenv('CLIP_PROCESSOR_INTERNAL_TOKEN', '')

def notify(event_type: str, payload: dict, timeout: float = 5.0) -> bool:
    try:
        resp = requests.post(
            LARAVEL_NOTIFY_URL,
            json={'event': event_type, 'payload': payload},
            headers={
                'Host': LARAVEL_HOST_HEADER,
                'X-Internal-Token': INTERNAL_TOKEN,
            },
            timeout=timeout,
        )
        if resp.status_code >= 400:
            print(f'[NOTIFY] warn: Laravel retornou HTTP {resp.status_code} para {event_type}')
            return False
        return True
    except requests.RequestException as exc:
        print(f'[NOTIFY] warn: falha ao notificar {event_type}: {exc}')
        return False
```

### Pattern 5: Novo endpoint Python /internal/process-url

**What:** Adicionar `POST /internal/process-url` ao `internal_api.py` para que o Laravel delegue `/processar <url>` ao Python.

```python
# Em clip-processor/src/internal_api.py — adicionar ao app Flask existente
from src.processar import main as processar_main

@app.post('/internal/process-url')
def _route_process_url():
    if not _check_auth():
        return jsonify(error='unauthorized'), 401
    payload = request.get_json(silent=True) or {}
    url = payload.get('url')
    if not url:
        return jsonify(error='missing url'), 400
    exit_code = processar_main(url)
    return jsonify(exit_code=exit_code), 200
```

### Pattern 6: Artisan Schedule — Resumo Diário 18h BRT

**What:** Substitui o `06-cron-resumo-diario.json` do n8n. Usa `routes/console.php` no padrão Laravel 13.

```php
// Em routes/console.php
use Illuminate\Support\Facades\Schedule;
use App\Models\GeneratedClip;
use Telegram\Bot\Laravel\Facades\Telegram;

Schedule::call(function () {
    $pending = GeneratedClip::where('status', 'pending')->count();
    if ($pending === 0) return;  // skip se 0 pendentes (replicando regra Phase 6)

    Telegram::sendMessage([
        'chat_id' => config('telegram.bots.mybot.chat_id_allowed'),
        'text'    => "Resumo diário: {$pending} clipes aguardando aprovação.",
    ]);
})->dailyAt('18:00')->timezone('America/Sao_Paulo');
```

### Anti-Patterns to Avoid

- **Não usar `getUpdates()` polling:** Se webhook estiver ativo, `getUpdates()` retorna vazio. Escolha um dos dois.
- **Não verificar `Sec-Fetch-Site` para o webhook:** O Telegram não envia esse header; a rota PRECISA estar no `preventRequestForgery(except:)`.
- **Não compartilhar Redis DB 0 para dedup Telegram:** DB 0 é do Python pipeline (quota, dedup de vídeos). Usar conexão `default` (DB 1) evita colisão de chaves.
- **Não chamar Telegram API direto do Python após Phase 9:** BOT-03 proíbe; todo envio passa pelo endpoint Laravel.
- **Não usar `RefreshDatabase`:** Apaga tabelas do pipeline Python. Usar `DatabaseTransactions` como nas Phases 7-8.
- **Não esquecer de deduplicar no edge:** A deduplicação DEVE ocorrer antes de `commandsHandler()`, senão um /aprovar duplicado corrompe status.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parsing de comandos do Telegram | Parser de `message.text` com regex | `commandsHandler(true)` do SDK | O SDK resolve aliases, `$pattern`, argumentos, dispatch de classe automaticamente |
| Envio de mensagem Telegram | `Guzzle::post()` direto para api.telegram.org | `Telegram::sendMessage()` / `$this->replyWithMessage()` | Helper já preenche `chat_id` automaticamente em contexto de comando |
| Verificação de assinatura do webhook | HMAC manual | `setWebhook` com `secret_token` + validação automática do SDK | O SDK verifica o header `X-Telegram-Bot-Api-Secret-Token` automaticamente |
| Agendamento do resumo diário | Script Python cron ou n8n workflow | Artisan Schedule (`routes/console.php`) | Já faz parte do Laravel; zero infraestrutura adicional |

**Key insight:** O SDK cuida de todo o protocolo Telegram (parsing, dispatch, reply helpers). O código da aplicação fica apenas em lógica de negócio (queries Eloquent, chamadas ao ClipProcessorClient).

---

## Common Pitfalls

### Pitfall 1: CSRF bloqueando o webhook

**What goes wrong:** Laravel retorna 419 para o POST do Telegram em `/telegramcanal`.
**Why it happens:** O Telegram não envia `_token` CSRF nem `Sec-Fetch-Site`. A middleware `PreventRequestForgery` bloqueia por padrão.
**How to avoid:** Em `bootstrap/app.php`:
```php
->withMiddleware(function (Middleware $middleware): void {
    $middleware->preventRequestForgery(except: [
        'telegramcanal',
        'internal/pipeline-event',
    ]);
})
```
**Warning signs:** O setWebhookInfo mostra `last_error_message: "Wrong response from the webhook: 419"`.

### Pitfall 2: Deduplicação ineficaz com race condition

**What goes wrong:** Dois requests paralelos do mesmo update_id passam pela verificação antes que o primeiro salve no Redis.
**Why it happens:** Check-then-set (two operations) não é atômico.
**How to avoid:** Usar `Redis::set($key, '1', 'NX', 'EX', 300)` — SET NX é atômico na camada Redis; só um dos paralelos recebe `true`.
**Warning signs:** Comando `/aprovar 42` aplicado duas vezes ao mesmo clip, mudando status de `approved` para... `approved` (idempotente neste caso, mas `/rejeitar` duplicado apaga MP4 duas vezes com erro no segundo).

### Pitfall 3: Python → Laravel via host errado

**What goes wrong:** `telegram_notifier.py` faz `requests.post('http://nginx/...')` e o nginx serve outro vhost (o `default_server` retorna 404 ou HTML estático).
**Why it happens:** A URL `http://nginx` sem `Host` header envia `Host: nginx`, que não bate com `server_name canaldecortes.local`.
**How to avoid:** Sempre incluir `headers={'Host': 'canaldecortes.local'}` na chamada Python. Ou adicionar `server_name canaldecortes.local nginx;` no canaldecortes.conf (mais frágil).
**Warning signs:** `[NOTIFY] warn: Laravel retornou HTTP 404` nos logs do clip-processor.

### Pitfall 4: Webhook URL sem HTTPS

**What goes wrong:** Telegram rejeita `setWebhook` com URL `http://`.
**Why it happens:** Telegram só aceita HTTPS (exceto portas 8443, 88, 80 em modo especial que requer certificado próprio).
**How to avoid:** O webhook de produção DEVE usar `https://alessandromelo.com.br/telegramcanal`. Para desenvolvimento local, testar o controller diretamente via `$this->postJson('/telegramcanal', ...)` sem registrar no Telegram.
**Warning signs:** `curl setWebhook` retorna `{"ok":false,"description":"Bad Request: bad webhook: HTTPS url must be provided for webhook"}`.

### Pitfall 5: config/telegram.php não publicado

**What goes wrong:** `Telegram::commandsHandler()` lança `RuntimeException: No bot token set`.
**Why it happens:** O arquivo `config/telegram.php` precisa ser criado via `vendor:publish` antes de definir o bot token.
**How to avoid:** Rodar `php artisan vendor:publish --tag="telegram-config"` imediatamente após `composer require`. Adicionar `TELEGRAM_BOT_TOKEN` ao `.env`.
**Warning signs:** Erro em qualquer chamada ao facade Telegram.

### Pitfall 6: commandsHandler retorna Update, não bool

**What goes wrong:** Código espera `true`/`false` de `commandsHandler(true)`.
**Why it happens:** O método retorna o objeto `Update`, não um booleano.
**How to avoid:** Ignorar o retorno ou guardar para logging; nunca usar como condição.

### Pitfall 7: n8n workflow de notificações não desativado

**What goes wrong:** Tanto n8n quanto Laravel enviam a mesma notificação duplicada.
**Why it happens:** `telegram_notifier.py` já aponta para Laravel, mas o workflow n8n `06-router.json` ainda tem o Webhook `/webhook/notify` ativo.
**How to avoid:** Desativar o workflow `06-router.json` no n8n APÓS confirmar que Laravel está recebendo as notificações. O Telegram Trigger do n8n também deve ser desativado.

---

## Code Examples

### Registrar comandos em config/telegram.php

```php
// Source: telegram-bot-sdk.com/docs/getting-started/configuration
return [
    'bots' => [
        'mybot' => [
            'token'            => env('TELEGRAM_BOT_TOKEN'),
            'webhook_url'      => env('TELEGRAM_WEBHOOK_URL', 'https://alessandromelo.com.br/telegramcanal'),
            'chat_id_allowed'  => env('TELEGRAM_CHAT_ID_ALLOWED', '5760918317'),
            'commands'         => [
                App\Telegram\Commands\StatusCommand::class,
                App\Telegram\Commands\ClipesCommand::class,
                App\Telegram\Commands\AprovarCommand::class,
                App\Telegram\Commands\RejeitarCommand::class,
                App\Telegram\Commands\ProcessarCommand::class,
                App\Telegram\Commands\AjudaCommand::class,
            ],
        ],
    ],
    'default' => 'mybot',
];
```

### setWebhook — produção

```bash
# Executar após deploy; substituir variáveis do .env
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://alessandromelo.com.br/telegramcanal\",
    \"secret_token\": \"${TELEGRAM_WEBHOOK_SECRET}\",
    \"allowed_updates\": [\"message\"]
  }"

# Verificar
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool
```

### /status command — query Eloquent

```php
// Source: Eloquent patterns estabelecidos nas Phases 8 (GeneratedClip model)
namespace App\Telegram\Commands;

use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use Telegram\Bot\Commands\Command;

class StatusCommand extends Command
{
    protected string $name = 'status';
    protected string $description = 'Mostra status do pipeline';

    public function handle(): void
    {
        $videos  = SourceVideo::query()->selectRaw('status, count(*) as n')->groupBy('status')->pluck('n', 'status');
        $clips   = GeneratedClip::query()->selectRaw('status, count(*) as n')->groupBy('status')->pluck('n', 'status');

        $lines = ["Pipeline status:"];
        foreach ($videos as $s => $n) $lines[] = "  vídeos {$s}: {$n}";
        foreach ($clips  as $s => $n) $lines[] = "  clips {$s}: {$n}";

        $this->replyWithMessage(['text' => implode("\n", $lines)]);
    }
}
```

### Rota webhook + rota internal/pipeline-event em routes/web.php

```php
// Source: telegram-bot-sdk.com/docs/guides/webhook-updates + padrão Phase 8
use App\Http\Controllers\TelegramWebhookController;

// Telegram webhook — SEM autenticação, SEM CSRF (excluído em bootstrap/app.php)
Route::post('/telegramcanal', [TelegramWebhookController::class, 'handle']);

// Pipeline Python → Telegram — protegido por X-Internal-Token (padrão Phase 8)
Route::post('/internal/pipeline-event', [TelegramWebhookController::class, 'pipelineEvent']);
```

### ClipProcessorClient — novo método processUrl

```php
// Em App\Services\ClipProcessorClient (adicionar ao existente)
/** @return int exit_code (0=ok, 2=URL inválida, 3=yt-dlp falhou). */
public function processUrl(string $url): int
{
    $response = Http::timeout(30)
        ->withHeader('X-Internal-Token', (string) $this->token)
        ->post($this->baseUrl.'/internal/process-url', ['url' => $url]);

    if (! $response->successful()) {
        throw new RuntimeException('Erro ao processar URL: HTTP '.$response->status());
    }

    return (int) $response->json('exit_code', 3);
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| n8n Telegram Trigger + Cloudflare Tunnel | Laravel webhook em `/telegramcanal` | Phase 9 | Elimina dependência de n8n e tunnel para o bot |
| n8n `/webhook/notify` como receptor de notificações | Laravel `POST /internal/pipeline-event` | Phase 9 | Python notifica Laravel; Laravel chama Telegram |
| n8n cron `06-cron-resumo-diario.json` às 18h | Artisan Schedule em `routes/console.php` | Phase 9 | Sem n8n necessário para o resumo |
| `telegram_notifier.N8N_NOTIFY_URL` | `telegram_notifier.LARAVEL_NOTIFY_URL` | Phase 9 | Python → Laravel; n8n não está mais no fluxo |

**Deprecated/outdated:**
- `N8N_NOTIFY_URL` env var: substituída por `LARAVEL_NOTIFY_URL` (manter retrocompat com default para evitar quebra antes do deploy)
- Workflow n8n `06-router.json`: desativar Telegram Trigger e Webhook `/webhook/notify` após Phase 9 green

---

## Open Questions

1. **Nginx em `alessandromelo.com.br` para produção**
   - What we know: O domínio tem nginx com SSL Let's Encrypt (confirmado em feeb/Docs/servidor-aquivos/). Não existe arquivo `docker/nginx_conf/alessandromelo.conf`.
   - What's unclear: Se o nginx de `alessandromelo.com.br` roda no mesmo Docker (php:9000) ou num servidor separado.
   - Recommendation: O planner deve criar um plano de "ops" para adicionar `location /telegramcanal` ao server block de `alessandromelo.com.br`. Se for o mesmo Docker, adicionar server block em `docker/nginx_conf/` (fora do repo, como fase 6). Checkpoint final deve verificar `getWebhookInfo` com `last_error_message` ausente.

2. **Artisan cron runner ativo no container php**
   - What we know: O `docker-compose.yml` tem `command: bash -c "cron && php-fpm"` no serviço php — o cron do sistema está ativo.
   - What's unclear: Se existe um `crontab` que chama `php artisan schedule:run` a cada minuto no container php.
   - Recommendation: O planner deve verificar e, se ausente, adicionar `* * * * * cd /var/www/html/painel && php artisan schedule:run >> /dev/null 2>&1` via Docker exec ou Dockerfile.

3. **Formato do `chat_id` em callbacks vs mensagens**
   - What we know: `TELEGRAM_CHAT_ID_ALLOWED=5760918317` (um único chat_id). O allowlist guard verifica `getMessage()->getChat()->getId()`.
   - What's unclear: Se o bot também receberá callback queries (botões inline) — por agora Phase 9 só tem comandos de texto.
   - Recommendation: Por ora, guard só em `getMessage()`. Callback queries fora de escopo de Phase 9.

---

## Validation Architecture

> `nyquist_validation: true` em `.planning/config.json` — seção incluída.

### Test Framework

| Property | Value |
|----------|-------|
| Framework (Laravel) | Pest 4.7 + pest-plugin-laravel 4.1 |
| Config file | `painel/phpunit.xml` + `painel/tests/Pest.php` |
| Quick run command | `docker exec php bash -c "cd /var/www/html/painel && ./vendor/bin/pest tests/Feature/TelegramWebhookTest.php -x"` |
| Full suite command | `docker exec php bash -c "cd /var/www/html/painel && ./vendor/bin/pest"` |
| Framework (Python) | pytest com `pytest.ini` em `clip-processor/` |
| Quick run Python | `docker exec clip-processor python -m pytest tests/test_telegram_notifier.py tests/test_internal_api.py -x -v` |
| Full suite Python | `docker exec clip-processor python -m pytest -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BOT-01 | POST /telegramcanal retorna 200 'ok' com update válido | Feature | `pest tests/Feature/TelegramWebhookTest.php` | ❌ Wave 0 |
| BOT-01 | POST /telegramcanal retorna 200 (silencioso) com chat_id não autorizado | Feature | `pest tests/Feature/TelegramWebhookTest.php` | ❌ Wave 0 |
| BOT-01 | POST /telegramcanal sem X-Telegram-Bot-Api-Secret-Token — bot ignora (não 403) | Feature | `pest tests/Feature/TelegramWebhookTest.php` | ❌ Wave 0 |
| BOT-02 | Mesmo update_id enviado 2x — segundo request retorna 'ok' sem executar comando | Feature | `pest tests/Feature/TelegramWebhookTest.php::deduplication` | ❌ Wave 0 |
| BOT-02 | /aprovar {id} — GeneratedClip.status muda pending→approved | Feature | `pest tests/Feature/TelegramCommandsTest.php` | ❌ Wave 0 |
| BOT-02 | /rejeitar {id} — chama ClipProcessorClient::rejectClip() | Feature | `pest tests/Feature/TelegramCommandsTest.php` | ❌ Wave 0 |
| BOT-02 | /processar {url} — chama ClipProcessorClient::processUrl() | Feature | `pest tests/Feature/TelegramCommandsTest.php` | ❌ Wave 0 |
| BOT-02 | /status — retorna texto com contagem de status | Feature | `pest tests/Feature/TelegramCommandsTest.php` | ❌ Wave 0 |
| BOT-02 | /clipes — retorna lista de clips pending | Feature | `pest tests/Feature/TelegramCommandsTest.php` | ❌ Wave 0 |
| BOT-03 | POST /internal/pipeline-event com upload_published — chama Telegram::sendMessage | Feature | `pest tests/Feature/PipelineEventTest.php` | ❌ Wave 0 |
| BOT-03 | POST /internal/pipeline-event sem token — retorna 401 | Feature | `pest tests/Feature/PipelineEventTest.php` | ❌ Wave 0 |
| BOT-03 | telegram_notifier.notify() POST para LARAVEL_NOTIFY_URL com Host header | Unit | `pytest tests/test_telegram_notifier.py` | ✅ (precisa update) |
| BOT-03 | internal_api /internal/process-url retorna exit_code | Unit | `pytest tests/test_internal_api.py` | ✅ (precisa update) |

### Sampling Rate

- **Per task commit:** Quick run do arquivo de teste específico ao task
- **Per wave merge:** `./vendor/bin/pest` (full Laravel) + `pytest -v` (full Python) — ambos devem estar GREEN
- **Phase gate:** Full suite green antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `painel/tests/Feature/TelegramWebhookTest.php` — cobre BOT-01 e BOT-02 (deduplicação)
- [ ] `painel/tests/Feature/TelegramCommandsTest.php` — cobre BOT-02 (6 comandos)
- [ ] `painel/tests/Feature/PipelineEventTest.php` — cobre BOT-03 (endpoint notificações)
- [ ] `clip-processor/tests/test_telegram_notifier.py` — atualizar testes existentes: mudar `N8N_NOTIFY_URL` para `LARAVEL_NOTIFY_URL`, adicionar verificação do `Host` header
- [ ] `clip-processor/tests/test_internal_api.py` — adicionar testes para novo `/internal/process-url`

---

## Sources

### Primary (HIGH confidence)

- Packagist `irazasyed/telegram-bot-sdk` — versões confirmadas: v3.16.0 existe, suporte Laravel 13 confirmado no changelog
- `telegram-bot-sdk.com/docs/guides/commands-system` — estrutura de Command classes, `$pattern`, `argument()`, `replyWithMessage()`
- `telegram-bot-sdk.com/docs/guides/webhook-updates` — `commandsHandler(true)`, `getWebhookUpdate()`
- `laravel.com/docs/13.x/csrf` — `$middleware->preventRequestForgery(except: [...])` em bootstrap/app.php
- Codebase Phase 8 — `ClipProcessorClient`, `GeneratedClip`, `SourceVideo`, `DatabaseTransactions` pattern, conexões Redis, `tests/Pest.php`

### Secondary (MEDIUM confidence)

- WebSearch: deduplicação Redis SET NX para webhooks — padrão amplamente confirmado na literatura; implementação específica inferida de `ttl_worker.py` existente (já usa `redis_client.set(key, '1', nx=True, ex=...)`)
- WebSearch: CSRF exclusion Laravel 13 + Telegram webhook — confirmado via docs oficiais Laravel 13

### Tertiary (LOW confidence)

- Situação do nginx para `alessandromelo.com.br`: inferida de `feeb/Docs/servidor-aquivos/` (documentação de referência, não config ativa no Docker). O planner deve confirmar a localização real do server block.
- Artisan cron runner no container php: o docker-compose tem `cron && php-fpm` mas não confirmei se existe crontab configurado para `schedule:run`.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — irazasyed/telegram-bot-sdk v3.16 confirmado no packagist com suporte Laravel 13; todos os outros componentes já estão instalados (Laravel 13, Pest 4, Redis, Eloquent)
- Architecture: HIGH — padrão de Command classes confirmado na doc oficial; padrão ClipProcessorClient já estabelecido na Phase 8; único LOW é a configuração nginx de produção
- Pitfalls: HIGH — CSRF e Redis NX verificados; Host header nginx inferido mas muito provável

**Research date:** 2026-07-02
**Valid until:** 2026-08-02 (SDK estável, 30 dias)
