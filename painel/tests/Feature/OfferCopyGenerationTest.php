<?php

use App\Models\Offer;
use App\Models\User;
use App\Services\OfferCopywriter;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

const PRODUCT_HTML = <<<'HTML'
<html><head><title>Chuteira X</title>
<meta property="og:description" content="Chuteira leve para society">
<meta property="product:price:amount" content="199.90">
</head><body><nav>menu</nav><h1>Chuteira X</h1><p>Solado de borracha, cabedal sintético.</p><script>track()</script></body></html>
HTML;

beforeEach(function () {
    // DNS falso: o teste não depende de rede e exercita a trava de SSRF.
    app()->bind(OfferCopywriter::class, fn () => new class extends OfferCopywriter
    {
        protected function resolveHost(string $host): array
        {
            return $host === 'interno.test' ? ['10.0.0.5'] : ['93.184.216.34'];
        }
    });
    config(['services.anthropic.key' => 'sk-test', 'services.groq.key' => 'gsk-test', 'services.groq.model' => 'm']);
});

function copyJson(): string
{
    return json_encode([
        'cta_text' => 'Garanta a sua',
        'copy_short' => 'Leveza pra jogar melhor no society. Veja em https://x.com',
        'copy_long' => "Parágrafo um.\n\nLink de afiliado.",
    ]);
}

it('exige login para gerar copy', function () {
    $this->post('/painel/ofertas/gerar-copy', ['affiliate_url' => 'https://loja.test/p'])->assertRedirect('/login');
});

it('gera copy pela Anthropic lendo a página do produto', function () {
    Http::fake([
        'loja.test/*' => Http::response(PRODUCT_HTML, 200, ['Content-Type' => 'text/html; charset=utf-8']),
        'api.anthropic.com/*' => Http::response(['content' => [['type' => 'text', 'text' => copyJson()]]]),
    ]);

    $this->actingAs(User::factory()->create())
        ->postJson('/painel/ofertas/gerar-copy', ['affiliate_url' => 'https://loja.test/p', 'niche' => 'futebol'])
        ->assertOk()
        ->assertJson(['provider' => 'anthropic', 'cta_text' => 'Garanta a sua'])
        ->assertJsonPath('copy_short', 'Leveza pra jogar melhor no society. Veja em');

    Http::assertSent(fn ($req) => str_contains($req->url(), 'anthropic')
        && str_contains($req['messages'][0]['content'], 'Solado de borracha')
        && str_contains($req['messages'][0]['content'], 'Preço na página: 199.90')
        && ! str_contains($req['messages'][0]['content'], 'track()'));
});

it('cai para a Groq quando a Anthropic falha', function () {
    Http::fake([
        'loja.test/*' => Http::response(PRODUCT_HTML, 200, ['Content-Type' => 'text/html']),
        'api.anthropic.com/*' => Http::response(['error' => 'x'], 500),
        'api.groq.com/*' => Http::response(['choices' => [['message' => ['content' => '<think>..</think>'.copyJson()]]]]),
    ]);

    $this->actingAs(User::factory()->create())
        ->postJson('/painel/ofertas/gerar-copy', ['affiliate_url' => 'https://loja.test/p'])
        ->assertOk()
        ->assertJsonPath('provider', 'groq');
});

it('não busca endereço interno e pede título quando não há página', function () {
    Http::fake();

    $this->actingAs(User::factory()->create())
        ->postJson('/painel/ofertas/gerar-copy', ['affiliate_url' => 'http://interno.test/admin'])
        ->assertStatus(422)
        ->assertJsonPath('message', 'Não consegui ler a página. Preencha o título e tente de novo.');

    Http::assertNothingSent();
});

it('responde 422 quando as duas IAs falham', function () {
    Http::fake([
        'loja.test/*' => Http::response(PRODUCT_HTML, 200, ['Content-Type' => 'text/html']),
        'api.anthropic.com/*' => Http::response([], 500),
        'api.groq.com/*' => Http::response(['choices' => [['message' => ['content' => 'sem json']]]]),
    ]);

    $this->actingAs(User::factory()->create())
        ->postJson('/painel/ofertas/gerar-copy', ['product_url' => 'https://loja.test/p'])
        ->assertStatus(422);
});

it('grava o provedor da IA ao salvar oferta com texto gerado', function () {
    DB::table('niches')->insertOrIgnore(['slug' => 'futebol', 'label' => 'Futebol', 'created_at' => now(), 'updated_at' => now()]);

    $this->actingAs(User::factory()->create())->post('/painel/ofertas', [
        'title' => 'Chuteira X',
        'affiliate_url' => 'https://loja.test/p?aff=1',
        'niche' => 'futebol',
        'copy_short' => 'Texto',
        'ai_provider' => 'groq',
    ])->assertRedirect();

    expect(Offer::where('title', 'Chuteira X')->value('ai_provider'))->toBe('groq');
});
