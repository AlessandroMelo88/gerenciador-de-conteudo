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

/** Props da página. O banco de teste é compartilhado: comparar deltas, não totais absolutos. */
function performanceProps(User $user, string $query = ''): array
{
    return test()->actingAs($user)
        ->get('/painel/ofertas/performance'.$query)
        ->assertOk()
        ->viewData('page')['props'];
}

function insertClick(Offer $offer, ?string $channel, string $ipHash, $createdAt = null): void
{
    DB::table('offer_clicks')->insert([
        'offer_id' => $offer->id,
        'channel' => $channel,
        'ip_hash' => $ipHash,
        'created_at' => $createdAt ?? now(),
    ]);
}

it('exige login na tela de performance', function () {
    $this->get('/painel/ofertas/performance')->assertRedirect('/login');
});

it('renderiza OfferPerformance com as props do contrato', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->get('/painel/ofertas/performance')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('OfferPerformance', false)
            ->where('days', 30)
            ->where('periods', [7, 30, 90])
            ->has('totals', fn (Assert $t) => $t
                ->whereType('clicks', 'integer')
                ->whereType('uniqueVisitors', 'integer')
                ->whereType('offersWithClicks', 'integer')
                ->whereType('approvedOffers', 'integer'))
            ->has('byDay', 30)
            ->where('byDay.29.date', now()->toDateString())
            ->has('byChannel')
            ->has('byOffer')
            ->has('niches'));
});

it('período inválido volta para 30 dias', function () {
    $user = User::factory()->create();

    expect(performanceProps($user, '?days=365')['days'])->toBe(30)
        ->and(performanceProps($user, '?days=7')['byDay'])->toHaveCount(7);
});

it('agrega cliques por oferta, canal e dia, respeitando o período', function () {
    $user = User::factory()->create();
    $before = performanceProps($user);

    $offer = Offer::factory()->approved()->create();
    insertClick($offer, 'telegram', str_repeat('a', 64));
    insertClick($offer, 'telegram', str_repeat('a', 64));
    insertClick($offer, null, str_repeat('b', 64));
    insertClick($offer, 'youtube', str_repeat('c', 64), now()->subDays(40)); // fora dos 30 dias

    $after = performanceProps($user);

    expect($after['totals']['clicks'] - $before['totals']['clicks'])->toBe(3)
        ->and(end($after['byDay'])['clicks'] - end($before['byDay'])['clicks'])->toBe(3);

    $row = collect($after['byOffer'])->firstWhere('id', $offer->id);
    expect($row['clicks'])->toBe(3)
        ->and($row['uniqueVisitors'])->toBe(2)
        ->and($row['trackingUrl'])->toBe(url('/o/'.$offer->slug))
        ->and(collect($row['channels'])->pluck('clicks', 'channel')->all())->toBe(['telegram' => 2, 'direto' => 1]);

    $telegram = fn (array $props) => collect($props['byChannel'])->firstWhere('channel', 'telegram')['clicks'] ?? 0;
    expect($telegram($after) - $telegram($before))->toBe(2);

    $row90 = collect(performanceProps($user, '?days=90')['byOffer'])->firstWhere('id', $offer->id);
    expect($row90['clicks'])->toBe(4);
});

it('nunca expõe ip_hash nas props', function () {
    $user = User::factory()->create();
    $offer = Offer::factory()->approved()->create();
    $hash = hash('sha256', '203.0.113.7'.config('app.key'));
    insertClick($offer, 'blog', $hash);

    $json = json_encode(performanceProps($user));

    expect($json)->not->toContain($hash)
        ->and($json)->not->toContain('ip_hash');
});
