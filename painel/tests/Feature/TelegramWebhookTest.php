<?php

use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Redis;

uses(DatabaseTransactions::class);

/**
 * Cria um payload de Update do Telegram com o chat_id autorizado por padrão.
 */
function fakeTgUpdate(int $updateId = 1, int|string $chatId = 5760918317, string $text = '/ajuda'): array
{
    return [
        'update_id' => $updateId,
        'message'   => [
            'message_id' => 100,
            'from'       => ['id' => (int) $chatId, 'first_name' => 'Test'],
            'chat'       => ['id' => (int) $chatId, 'type' => 'private'],
            'text'       => $text,
            'date'       => time(),
        ],
    ];
}

beforeEach(function () {
    // Fake a API do Telegram para não fazer chamadas HTTP reais durante testes.
    Http::fake([
        '*api.telegram.org*' => Http::response(['ok' => true, 'result' => ['message_id' => 1]], 200),
    ]);
});

it('returns 200 ok for valid update from authorized chat_id', function () {
    $uid = random_int(10000, 99999);
    Redis::connection('default')->del("tg:dedup:{$uid}");

    $this->postJson('/telegramcanal', fakeTgUpdate(updateId: $uid))
        ->assertStatus(200);
});

it('returns 200 silently for update from unauthorized chat_id', function () {
    $response = $this->postJson('/telegramcanal', fakeTgUpdate(chatId: 9999999));
    $response->assertStatus(200);
    // Não deve ter chamado a API do Telegram (nenhum replyWithMessage)
    Http::assertNothingSent();
});

it('deduplicates same update_id — second request returns 200 without re-executing command', function () {
    $uid = random_int(100000, 999999);
    Redis::connection('default')->del("tg:dedup:{$uid}");

    // Primeira request — deve processar e salvar Redis key
    $this->postJson('/telegramcanal', fakeTgUpdate(updateId: $uid))->assertStatus(200);

    // Segunda request com mesmo update_id — deve ser bloqueada silenciosamente
    $this->postJson('/telegramcanal', fakeTgUpdate(updateId: $uid))->assertStatus(200);

    // Redis key deve existir com TTL > 0 (SET NX EX 300)
    expect(Redis::connection('default')->exists("tg:dedup:{$uid}"))->toBe(1);
    expect(Redis::connection('default')->ttl("tg:dedup:{$uid}"))->toBeGreaterThan(0);

    // Telegram API deve ter sido chamada apenas UMA vez (não duas)
    Http::assertSentCount(1);
});
