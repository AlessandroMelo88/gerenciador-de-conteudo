<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Redis;
use Telegram\Bot\Laravel\Facades\Telegram;

class TelegramWebhookController extends Controller
{
    public function handle(Request $request): Response
    {
        // Parse update do body Laravel (não php://input, que fica vazio em testes Feature).
        $updateData = $request->json()->all();

        // Telegram Bot API sempre envia entities para comandos. Testes que simplificam o
        // payload e omitem entities precisam do fallback abaixo para que o CommandBus
        // consiga detectar e despachar o comando pelo campo text.
        if (isset($updateData['message']['text'])) {
            $text = $updateData['message']['text'];
            if (str_starts_with($text, '/') && empty($updateData['message']['entities'])) {
                $end = (int) (strpos($text, ' ') ?: strlen($text));
                $updateData['message']['entities'] = [[
                    'offset' => 0,
                    'length' => $end,
                    'type'   => 'bot_command',
                ]];
            }
        }

        // SDK v3.x usa magic __get com snake_case para acessar propriedades.
        $update = new \Telegram\Bot\Objects\Update($updateData);

        // 1) Allowlist — silencioso se chat_id não autorizado
        $chatId  = $update->message?->chat?->id;
        $allowed = (string) config('telegram.bots.mybot.chat_id_allowed');
        if ($chatId && (string) $chatId !== $allowed) {
            return response('ok');
        }

        // 2) Deduplicação — SET NX atômico; silencioso se update_id já visto
        // PhpRedisConnection::set($key, $value, $expireResolution, $expireTTL, $flag)
        // Internamente constrói [$flag, $expireResolution => $expireTTL] para phpredis.
        $updateId = $update->updateId;
        if ($updateId) {
            $key   = "tg:dedup:{$updateId}";
            $isNew = Redis::connection('default')->set($key, '1', 'EX', 300, 'NX');
            if (! $isNew) {
                return response('ok');
            }
        }

        // 3) Despacha para Command classes registradas em config/telegram.php
        Telegram::processCommand($update);

        return response('ok');
    }

    public function pipelineEvent(Request $request): \Illuminate\Http\JsonResponse
    {
        // Auth: mesmo X-Internal-Token do ClipProcessorClient (Phase 8)
        $token = config('services.clip_processor.token');
        if ($request->header('X-Internal-Token') !== $token) {
            return response()->json(['error' => 'unauthorized'], 401);
        }

        $event   = $request->input('event');
        $payload = $request->input('payload', []);
        $panelUrl = rtrim((string) config('app.url', 'https://toolscut.alessandromelo.com.br'), '/');

        $text = match ($event) {
            'upload_published' => "✅ Upload publicado: {$payload['title']} — {$payload['youtube_url']}",
            'pipeline_failure' => "🚨 Falha crítica [{$payload['stage']}]: {$payload['error_msg']}\n🔗 Painel: {$panelUrl}/painel",
            'clip_ttl_warning' => "⚠️ Clip #{$payload['clip_id']} expira em {$payload['expires_in_hours']}h: {$payload['title']}\n🔗 Painel: {$panelUrl}/painel",
            'daily_summary'    => $payload['text'] ?? 'Resumo diário: sem clips pendentes.',
            'watchdog_alert'   => "🐕 [WATCHDOG] " . ($payload['message'] ?? 'Alerta de integridade do pipeline') . "\n🔗 Painel: {$panelUrl}/painel",
            'oauth_warning'    => "🔑 [ALERTA OAUTH] " . ($payload['message'] ?? 'Credenciais OAuth ausentes') . "\n" . (isset($payload['warnings']) ? implode("\n", (array) $payload['warnings']) : '') . "\n🔗 Canais: {$panelUrl}/painel/canais",
            'disk_warning'     => "💾 [ALERTA DISCO] {$payload['free_gb']} GB livres ({$payload['used_percent']}% em uso).\n🔗 Painel: {$panelUrl}/painel",
            default            => "Evento: {$event}",
        };

        Telegram::sendMessage([
            'chat_id' => config('telegram.bots.mybot.chat_id_allowed'),
            'text'    => $text,
        ]);

        $alertEmail = env('ADMIN_ALERT_EMAIL');
        if ($alertEmail && in_array($event, ['pipeline_failure', 'watchdog_alert', 'oauth_warning'])) {
            try {
                \Illuminate\Support\Facades\Mail::raw($text, function ($message) use ($alertEmail, $event) {
                    $message->to($alertEmail)
                        ->subject("[Alerta Canal de Cortes] {$event}");
                });
            } catch (\Throwable $e) {
                \Illuminate\Support\Facades\Log::warning("Falha ao enviar e-mail de alerta: " . $e->getMessage());
            }
        }

        return response()->json(['ok' => true]);
    }
}
