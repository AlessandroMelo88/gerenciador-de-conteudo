<?php

use App\Models\Offer;
use App\Models\OfferClick;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;

uses(DatabaseTransactions::class);

beforeEach(function () {
    DB::table('niches')->insertOrIgnore([
        'slug' => 'futebol', 'label' => 'Futebol', 'created_at' => now(), 'updated_at' => now(),
    ]);
});

it('redireciona 302, grava clique com ip_hash e incrementa clicks_count', function () {
    $offer = Offer::factory()->approved()->create(['affiliate_url' => 'https://go.hotmart.com/XYZ']);

    $this->withServerVariables(['REMOTE_ADDR' => '203.0.113.7'])
        ->withHeaders(['User-Agent' => str_repeat('a', 400), 'Referer' => 'https://t.me/canal'])
        ->get('/o/'.$offer->slug.'?c=telegram')
        ->assertStatus(302)
        ->assertRedirect('https://go.hotmart.com/XYZ');

    $click = OfferClick::where('offer_id', $offer->id)->sole();
    expect($click->channel)->toBe('telegram')
        ->and($click->ip_hash)->toBe(hash('sha256', '203.0.113.7'.config('app.key')))
        ->and(strlen($click->user_agent))->toBe(255)
        ->and($click->referer)->toBe('https://t.me/canal')
        ->and($offer->refresh()->clicks_count)->toBe(1);

    // Nenhuma coluna guarda o IP cru.
    expect(json_encode(DB::table('offer_clicks')->where('id', $click->id)->first()))->not->toContain('203.0.113.7');
});

it('responde 404 para oferta não aprovada', function () {
    $offer = Offer::factory()->create(); // draft

    $this->get('/o/'.$offer->slug)->assertNotFound();
    expect(OfferClick::where('offer_id', $offer->id)->count())->toBe(0);
});

it('responde 404 para slug inexistente', function () {
    $this->get('/o/naoexiste9')->assertNotFound();
});

it('grava channel inválido como null', function () {
    $offer = Offer::factory()->approved()->create();

    $this->get('/o/'.$offer->slug.'?c=hackeado')->assertStatus(302);

    expect(OfferClick::where('offer_id', $offer->id)->sole()->channel)->toBeNull();
});

it('não redireciona para esquema inseguro gravado no banco', function () {
    $offer = Offer::factory()->approved()->create();
    DB::table('offers')->where('id', $offer->id)->update(['affiliate_url' => 'javascript:alert(1)']);

    $this->get('/o/'.$offer->slug)->assertNotFound();
});
