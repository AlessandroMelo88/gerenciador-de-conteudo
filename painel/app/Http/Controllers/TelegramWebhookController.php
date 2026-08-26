<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Redis;
use Illuminate\Validation\Rule;
use LogicException;
use Telegram\Bot\Laravel\Facades\Telegram;
use Telegram\Bot\Objects\Update;

class TelegramWebhookController extends Controller
{
    public function handle(Request $request): Response
    {
        if (! $this->hasValidWebhookSecret($request)) {
            return response('unauthorized', 401);
        }

        $update = new Update($request->json()->all());

        // 1) Allowlist — silencioso se chat_id não autorizado
        $chatId = $update->message?->chat?->id;
        $allowed = (string) config('telegram.bots.mybot.chat_id_allowed');
        if ($chatId === null || $allowed === '' || ! hash_equals($allowed, (string) $chatId)) {
            return response('ok');
        }

        // 2) Deduplicação — SET NX atômico; silencioso se update_id já visto
        // PhpRedisConnection::set($key, $value, $expireResolution, $expireTTL, $flag)
        // Internamente constrói [$flag, $expireResolution => $expireTTL] para phpredis.
        $updateId = $request->input('update_id');
        if (is_int($updateId) || (is_string($updateId) && ctype_digit($updateId))) {
            $key = "tg:dedup:{$updateId}";
            $isNew = Redis::connection('default')->set($key, '1', 'EX', 300, 'NX');
            if (! $isNew) {
                return response('ok');
            }
        }

        // 3) Despacha para Command classes registradas em config/telegram.php
        Telegram::processCommand($update);

        return response('ok');
    }

    public function pipelineEvent(Request $request): JsonResponse
    {
        // Auth: mesmo X-Internal-Token do ClipProcessorClient (Phase 8)
        $token = (string) config('services.clip_processor.token', '');
        $providedToken = (string) $request->header('X-Internal-Token', '');
        if ($token === '' || $providedToken === '' || ! hash_equals($token, $providedToken)) {
            return response()->json(['error' => 'unauthorized'], 401);
        }

        $data = $request->validate([
            'event' => ['required', 'string', Rule::in([
                'upload_published',
                'pipeline_failure',
                'clip_ttl_warning',
                'daily_summary',
            ])],
            'payload' => ['nullable', 'array'],
        ]);

        $event = (string) $data['event'];
        $payload = $data['payload'] ?? [];
        $text = match ($event) {
            'upload_published' => sprintf(
                'Upload publicado: %s — %s',
                $this->payloadString($payload, 'title', 'sem título'),
                $this->payloadString($payload, 'youtube_url', 'URL indisponível'),
            ),
            'pipeline_failure' => sprintf(
                'Falha crítica [%s]: %s',
                $this->payloadString($payload, 'stage', 'etapa desconhecida'),
                $this->payloadString($payload, 'error_msg', 'erro não informado'),
            ),
            'clip_ttl_warning' => sprintf(
                'Clip #%s expira em %sh: %s',
                $this->payloadString($payload, 'clip_id', '?'),
                $this->payloadString($payload, 'expires_in_hours', '?'),
                $this->payloadString($payload, 'title', 'sem título'),
            ),
            'daily_summary' => $this->payloadString(
                $payload,
                'text',
                'Resumo diário: sem clips pendentes.',
            ),
            default => throw new LogicException('Evento de pipeline não suportado.'),
        };

        Telegram::sendMessage([
            'chat_id' => config('telegram.bots.mybot.chat_id_allowed'),
            'text' => $text,
        ]);

        return response()->json(['ok' => true]);
    }

    private function hasValidWebhookSecret(Request $request): bool
    {
        $expected = (string) config('telegram.bots.mybot.webhook_secret', '');
        $provided = (string) $request->header('X-Telegram-Bot-Api-Secret-Token', '');

        return $expected !== ''
            && $provided !== ''
            && hash_equals($expected, $provided);
    }

    private function payloadString(array $payload, string $key, string $fallback): string
    {
        $value = $payload[$key] ?? null;

        return is_scalar($value) && (string) $value !== '' ? (string) $value : $fallback;
    }
}
