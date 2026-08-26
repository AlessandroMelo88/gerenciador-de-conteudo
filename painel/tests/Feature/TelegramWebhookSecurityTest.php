<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

final class TelegramWebhookSecurityTest extends TestCase
{
    use DatabaseTransactions;

    protected function setUp(): void
    {
        parent::setUp();

        config(['telegram.bots.mybot.webhook_secret' => 'test-telegram-secret']);
        Http::fake([
            '*api.telegram.org*' => Http::response(['ok' => true, 'result' => ['message_id' => 1]], 200),
        ]);
    }

    public function test_webhook_without_secret_is_rejected(): void
    {
        $this->postJson('/telegramcanal', $this->telegramUpdate())
            ->assertUnauthorized();

        Http::assertNothingSent();
    }

    public function test_update_without_chat_id_is_ignored(): void
    {
        $payload = $this->telegramUpdate();
        unset($payload['message']['chat']);

        $this->postJson('/telegramcanal', $payload, [
            'X-Telegram-Bot-Api-Secret-Token' => 'test-telegram-secret',
        ])->assertOk();

        Http::assertNothingSent();
    }

    /** @return array<string, mixed> */
    private function telegramUpdate(): array
    {
        return [
            'update_id' => 900001,
            'message' => [
                'message_id' => 100,
                'from' => ['id' => 5760918317, 'first_name' => 'Test'],
                'chat' => ['id' => 5760918317, 'type' => 'private'],
                'text' => '/ajuda',
                'entities' => [[
                    'offset' => 0,
                    'length' => 6,
                    'type' => 'bot_command',
                ]],
                'date' => time(),
            ],
        ];
    }
}
