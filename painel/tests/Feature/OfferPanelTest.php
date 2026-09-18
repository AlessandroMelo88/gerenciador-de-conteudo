<?php

use App\Models\Offer;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;
use Inertia\Testing\AssertableInertia as Assert;

uses(DatabaseTransactions::class);

beforeEach(function () {
    DB::table('niches')->insertOrIgnore([
        'slug' => 'futebol', 'label' => 'Futebol', 'created_at' => now(), 'updated_at' => now(),
    ]);
});

it('exige login no painel de ofertas', function () {
    $offer = Offer::factory()->create();

    $this->get('/painel/ofertas')->assertRedirect('/login');
    $this->post('/painel/ofertas', [])->assertRedirect('/login');
    $this->put("/painel/ofertas/{$offer->id}", ['status' => 'approved'])->assertRedirect('/login');
    $this->delete("/painel/ofertas/{$offer->id}")->assertRedirect('/login');
});

it('renderiza Offers com as props do contrato', function () {
    $user = User::factory()->create();
    $offer = Offer::factory()->create(['commission_percent' => 35.5]);

    $this->actingAs($user)
        ->get('/painel/ofertas')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('Offers', false)
            ->where('activeStatus', 'draft')
            ->has('counts', fn (Assert $c) => $c
                ->whereType('todos', 'integer')
                ->whereType('draft', 'integer')
                ->whereType('approved', 'integer')
                ->whereType('rejected', 'integer')
                ->whereType('archived', 'integer'))
            ->has('niches.0', fn (Assert $n) => $n->hasAll(['slug', 'label']))
            ->has('offers.0', fn (Assert $o) => $o
                ->where('id', $offer->id)
                ->where('commissionPercent', 35.5)
                ->where('trackingUrl', url('/o/'.$offer->slug))
                ->where('status', 'draft')
                ->where('approvedAt', null)
                ->where('telegramPostedAt', null)
                ->hasAll([
                    'network', 'externalId', 'niche', 'title', 'description', 'productUrl',
                    'affiliateUrl', 'imageUrl', 'priceCents', 'currency', 'ctaText', 'copyShort',
                    'copyLong', 'aiProvider', 'clicksCount', 'createdAt',
                ])));

    $this->actingAs($user)
        ->get('/painel/ofertas?status=todos')
        ->assertInertia(fn (Assert $page) => $page->component('Offers', false)->where('activeStatus', 'todos'));
});

it('cria oferta manual como draft', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/painel/ofertas', [
            'title' => 'Camisa oficial',
            'affiliate_url' => 'https://mercadolivre.com/sec/abc',
            'niche' => 'futebol',
            'cta_text' => 'Garanta a sua',
        ])
        ->assertRedirect()
        ->assertSessionHas('success');

    $offer = Offer::where('title', 'Camisa oficial')->sole();
    expect($offer->network)->toBe('manual')
        ->and($offer->ai_provider)->toBe('manual')
        ->and($offer->status)->toBe('draft');

    $this->actingAs($user)
        ->post('/painel/ofertas', ['title' => 'X', 'affiliate_url' => 'javascript:alert(1)', 'niche' => 'futebol'])
        ->assertSessionHasErrors('affiliate_url');
});

it('aprovar seta approved_at e sair de approved zera', function () {
    $user = User::factory()->create();
    $offer = Offer::factory()->create();

    $this->actingAs($user)->put("/painel/ofertas/{$offer->id}", ['status' => 'approved'])->assertRedirect();
    expect($offer->refresh()->status)->toBe('approved')
        ->and($offer->approved_at)->not->toBeNull();

    $this->actingAs($user)->put("/painel/ofertas/{$offer->id}", ['status' => 'archived'])->assertRedirect();
    expect($offer->refresh()->approved_at)->toBeNull();

    $this->actingAs($user)->put("/painel/ofertas/{$offer->id}", ['status' => 'publicado'])->assertSessionHasErrors('status');
});

it('apaga oferta', function () {
    $user = User::factory()->create();
    $offer = Offer::factory()->create();

    $this->actingAs($user)
        ->delete("/painel/ofertas/{$offer->id}")
        ->assertRedirect()
        ->assertSessionHas('success', 'Oferta apagada');

    expect(Offer::find($offer->id))->toBeNull();
});
