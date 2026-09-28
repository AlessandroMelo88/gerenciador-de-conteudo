<?php

use App\Models\Offer;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

// Nichos exclusivos do teste: o banco de teste é compartilhado e pode ter ofertas reais aprovadas.
beforeEach(function () {
    config([
        'telegram.bots.mybot.token' => 'test-token',
        'affiliates.telegram.channels' => ['tg-teste-a' => '@canal_a', 'tg-teste-b' => '-100200'],
        'affiliates.telegram.per_run' => 10,
    ]);

    // Cada teste registra o próprio fake: o primeiro fake que casa com a URL vence,
    // então um fake genérico aqui esconderia o de erro.
    Http::preventStrayRequests();
});

function fakeTelegramOk(): void
{
    Http::fake([
        '*api.telegram.org*' => Http::response(['ok' => true, 'result' => ['message_id' => 1]], 200),
    ]);
}

it('envia oferta aprovada para o canal do nicho e marca telegram_posted_at', function () {
    fakeTelegramOk();
    $offer = Offer::factory()->approved()->create(['niche' => 'tg-teste-a', 'copy_short' => 'Camisa com 30% off']);

    $this->artisan('offers:publish-telegram')->assertExitCode(0);

    Http::assertSent(fn ($req) => str_contains($req->url(), 'api.telegram.org')
        && $req['chat_id'] === '@canal_a'
        && str_contains($req['text'], 'Camisa com 30% off')
        && str_contains($req['text'], url('/o/'.$offer->slug).'?c=telegram'));

    expect($offer->refresh()->telegram_posted_at)->not->toBeNull();
});

it('é idempotente: segunda execução não reenvia', function () {
    fakeTelegramOk();
    Offer::factory()->approved()->create(['niche' => 'tg-teste-a']);

    $this->artisan('offers:publish-telegram')->assertExitCode(0);
    $this->artisan('offers:publish-telegram')->assertExitCode(0);

    Http::assertSentCount(1);
});

it('ignora oferta não aprovada, já enviada ou de nicho sem canal', function () {
    fakeTelegramOk();
    Offer::factory()->create(['niche' => 'tg-teste-a']); // draft
    Offer::factory()->create(['niche' => 'tg-teste-a', 'status' => 'rejected']);
    Offer::factory()->approved()->create(['niche' => 'tg-teste-a', 'telegram_posted_at' => now()->subDay()]);
    $semCanal = Offer::factory()->approved()->create(['niche' => 'tg-sem-canal']);

    $this->artisan('offers:publish-telegram')->assertExitCode(0);

    Http::assertNothingSent();
    expect($semCanal->refresh()->telegram_posted_at)->toBeNull();
});

it('não marca a oferta quando o Telegram recusa, e tenta de novo depois', function () {
    Http::fake([
        '*api.telegram.org*' => Http::sequence()
            ->push(['ok' => false, 'error_code' => 400, 'description' => 'Bad Request: chat not found'], 400)
            ->push(['ok' => true, 'result' => ['message_id' => 2]], 200),
    ]);
    $offer = Offer::factory()->approved()->create(['niche' => 'tg-teste-b']);

    $this->artisan('offers:publish-telegram')->assertExitCode(1);
    expect($offer->refresh()->telegram_posted_at)->toBeNull();

    $this->artisan('offers:publish-telegram')->assertExitCode(0);
    expect($offer->refresh()->telegram_posted_at)->not->toBeNull();
});

it('respeita o limite por execução, mais antigas primeiro', function () {
    fakeTelegramOk();
    $antiga = Offer::factory()->approved()->create(['niche' => 'tg-teste-a', 'approved_at' => now()->subDays(2)]);
    $nova = Offer::factory()->approved()->create(['niche' => 'tg-teste-a', 'approved_at' => now()]);

    $this->artisan('offers:publish-telegram', ['--limit' => 1])->assertExitCode(0);

    Http::assertSentCount(1);
    expect($antiga->refresh()->telegram_posted_at)->not->toBeNull()
        ->and($nova->refresh()->telegram_posted_at)->toBeNull();
});

it('dry-run não envia nem marca', function () {
    fakeTelegramOk();
    $offer = Offer::factory()->approved()->create(['niche' => 'tg-teste-a']);

    $this->artisan('offers:publish-telegram', ['--dry-run' => true])->assertExitCode(0);

    Http::assertNothingSent();
    expect($offer->refresh()->telegram_posted_at)->toBeNull();
});

it('falha fechado sem token ou sem canais configurados', function () {
    fakeTelegramOk();
    Offer::factory()->approved()->create(['niche' => 'tg-teste-a']);

    config(['telegram.bots.mybot.token' => null]);
    $this->artisan('offers:publish-telegram')->assertExitCode(1);

    config(['telegram.bots.mybot.token' => 'test-token', 'affiliates.telegram.channels' => []]);
    $this->artisan('offers:publish-telegram')->assertExitCode(1);

    Http::assertNothingSent();
});
