<?php

use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

/**
 * Cria update com update_id único para evitar conflito de dedup entre testes.
 */
function tgCmd(string $text): array
{
    return [
        'update_id' => random_int(200000, 299999),
        'message'   => [
            'message_id' => 1,
            'from'       => ['id' => 5760918317, 'first_name' => 'Test'],
            'chat'       => ['id' => 5760918317, 'type' => 'private'],
            'text'       => $text,
            'date'       => time(),
        ],
    ];
}

beforeEach(function () {
    Http::fake([
        '*api.telegram.org*'       => Http::response(['ok' => true, 'result' => ['message_id' => 1]], 200),
        '*/internal/reject-clip*'  => Http::response(['exit_code' => 0], 200),
        '*/internal/process-url*'  => Http::response(['exit_code' => 0], 200),
    ]);
});

it('/status returns 200 and sends Telegram message with status data', function () {
    SourceVideo::factory()->create(['status' => 'published']);
    GeneratedClip::factory()->create(['status' => 'pending']);

    $this->postJson('/telegramcanal', tgCmd('/status'))->assertStatus(200);

    Http::assertSent(fn ($req) =>
        str_contains($req->url(), 'api.telegram.org') &&
        str_contains($req['text'] ?? '', 'status')
    );
});

it('/clipes returns 200 and sends Telegram message listing pending clips', function () {
    GeneratedClip::factory()->create(['status' => 'pending', 'title' => 'Clip Teste ABC']);

    $this->postJson('/telegramcanal', tgCmd('/clipes'))->assertStatus(200);

    Http::assertSent(fn ($req) => str_contains($req->url(), 'api.telegram.org'));
});

it('/aprovar <id> changes clip status pending → approved', function () {
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);

    $this->postJson('/telegramcanal', tgCmd("/aprovar {$clip->id}"))->assertStatus(200);

    expect($clip->refresh()->status)->toBe('approved');
});

it('/aprovar <id> non-pending clip leaves status unchanged', function () {
    $clip = GeneratedClip::factory()->create(['status' => 'published']);

    $this->postJson('/telegramcanal', tgCmd("/aprovar {$clip->id}"))->assertStatus(200);

    expect($clip->refresh()->status)->toBe('published');
});

it('/rejeitar <id> calls ClipProcessorClient reject-clip endpoint', function () {
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);

    $this->postJson('/telegramcanal', tgCmd("/rejeitar {$clip->id}"))->assertStatus(200);

    Http::assertSent(fn ($req) =>
        str_contains($req->url(), '/internal/reject-clip') &&
        $req['clip_id'] === $clip->id
    );
});

it('/processar <url> calls ClipProcessorClient process-url endpoint', function () {
    $this->postJson('/telegramcanal', tgCmd('/processar https://youtube.com/watch?v=abc123'))
        ->assertStatus(200);

    Http::assertSent(fn ($req) =>
        str_contains($req->url(), '/internal/process-url') &&
        str_contains($req['url'] ?? '', 'youtube.com')
    );
});

it('/ajuda returns 200 and sends help text via Telegram', function () {
    $this->postJson('/telegramcanal', tgCmd('/ajuda'))->assertStatus(200);

    Http::assertSent(fn ($req) => str_contains($req->url(), 'api.telegram.org'));
});
