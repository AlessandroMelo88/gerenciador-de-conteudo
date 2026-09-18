<?php

use App\Models\Offer;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;

uses(DatabaseTransactions::class);

const OFFER_TEST_TOKEN = 'token-de-teste-afiliados';

beforeEach(function () {
    config()->set('services.affiliate.token', OFFER_TEST_TOKEN);
    DB::table('niches')->insertOrIgnore([
        'slug' => 'futebol', 'label' => 'Futebol', 'created_at' => now(), 'updated_at' => now(),
    ]);
});

function offerItem(array $overrides = []): array
{
    return array_merge([
        'network' => 'hotmart',
        'external_id' => 'HT-'.uniqid(),
        'niche' => 'futebol',
        'title' => 'Curso de tática',
        'affiliate_url' => 'https://go.hotmart.com/ABC123',
        'price_cents' => 19700,
        'commission_percent' => 50,
        'copy_short' => 'Aprenda tática',
        'ai_provider' => 'groq',
    ], $overrides);
}

function postOffers($test, array $items, ?string $token = OFFER_TEST_TOKEN)
{
    $headers = $token === null ? [] : ['Authorization' => 'Bearer '.$token];

    return $test->postJson('/api/offers', ['offers' => $items], $headers);
}

it('responde 503 quando o token não está configurado no servidor', function () {
    config()->set('services.affiliate.token', null);

    postOffers($this, [offerItem()], 'qualquer')
        ->assertStatus(503)
        ->assertExactJson(['error' => 'affiliate_api_not_configured']);
});

it('responde 401 com token errado ou ausente', function () {
    postOffers($this, [offerItem()], 'errado')->assertStatus(401)->assertExactJson(['error' => 'unauthorized']);
    postOffers($this, [offerItem()], null)->assertStatus(401);
    $this->getJson('/api/offers')->assertStatus(401);
});

it('cria ofertas em lote como draft', function () {
    $response = postOffers($this, [offerItem(), offerItem(['external_id' => null]), offerItem(['network' => 'shopee'])])
        ->assertOk()
        ->assertJson(['created' => 3, 'updated' => 0, 'skipped' => 0])
        ->assertJsonCount(3, 'offers')
        ->assertJsonStructure(['offers' => [['id', 'slug', 'status', 'result', 'tracking_url']]]);

    foreach ($response->json('offers') as $row) {
        expect($row['status'])->toBe('draft')
            ->and($row['result'])->toBe('created')
            ->and($row['tracking_url'])->toBe(url('/o/'.$row['slug']))
            ->and(strlen($row['slug']))->toBe(8);
    }
});

it('atualiza oferta existente em draft (updated)', function () {
    $item = offerItem();
    postOffers($this, [$item])->assertOk();

    postOffers($this, [array_merge($item, ['title' => 'Título novo'])])
        ->assertOk()
        ->assertJson(['created' => 0, 'updated' => 1, 'skipped' => 0]);

    $offer = Offer::where('network', 'hotmart')->where('external_id', $item['external_id'])->sole();
    expect($offer->title)->toBe('Título novo');
});

it('não sobrescreve oferta já aprovada (skipped)', function () {
    $offer = Offer::factory()->approved()->create(['title' => 'Aprovado pelo operador']);

    postOffers($this, [offerItem(['network' => $offer->network, 'external_id' => $offer->external_id, 'title' => 'Tentativa'])])
        ->assertOk()
        ->assertJson(['created' => 0, 'updated' => 0, 'skipped' => 1])
        ->assertJsonPath('offers.0.status', 'approved')
        ->assertJsonPath('offers.0.result', 'skipped');

    expect($offer->refresh()->title)->toBe('Aprovado pelo operador');
});

it('ignora status enviado pelo cliente', function () {
    $item = offerItem(['status' => 'approved']);
    postOffers($this, [$item])->assertOk()->assertJsonPath('offers.0.status', 'draft');

    expect(Offer::where('external_id', $item['external_id'])->value('status'))->toBe('draft');
});

it('rejeita affiliate_url com esquema javascript com 422', function () {
    postOffers($this, [offerItem(['affiliate_url' => 'javascript:alert(1)'])])
        ->assertStatus(422)
        ->assertJsonValidationErrors(['offers.0.affiliate_url']);
});

it('rejeita lote vazio e nicho inexistente', function () {
    postOffers($this, [])->assertStatus(422)->assertJsonValidationErrors(['offers']);
    postOffers($this, [offerItem(['niche' => 'nicho-que-nao-existe-xyz'])])
        ->assertStatus(422)
        ->assertJsonValidationErrors(['offers.0.niche']);
});

it('lista ofertas aprovadas por padrão com tracking_url', function () {
    $approved = Offer::factory()->approved()->create();
    Offer::factory()->create(); // draft, não deve aparecer

    $response = $this->getJson('/api/offers?niche=futebol&per_page=100', ['Authorization' => 'Bearer '.OFFER_TEST_TOKEN])
        ->assertOk()
        ->assertJsonStructure(['data', 'current_page', 'per_page', 'total']);

    $rows = collect($response->json('data'));
    expect($rows->pluck('status')->unique()->all())->toBe(['approved'])
        ->and($rows->firstWhere('id', $approved->id)['tracking_url'])->toBe(url('/o/'.$approved->slug));

    $this->getJson('/api/offers?per_page=101', ['Authorization' => 'Bearer '.OFFER_TEST_TOKEN])->assertStatus(422);
});
