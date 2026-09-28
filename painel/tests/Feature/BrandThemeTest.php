<?php

use App\Support\Brand;
use Illuminate\Http\Request;
use Inertia\Testing\AssertableInertia as Assert;

it('usa Canal de Cortes por padrão', function () {
    $this->get('/login')
        ->assertOk()
        ->assertSee('data-brand="canaldecortes"', false)
        ->assertInertia(fn (Assert $page) => $page
            ->where('brand.key', 'canaldecortes')
            ->where('brand.name', 'Canal de Cortes')
            ->where('brand.icon', 'clapperboard')
            ->where('brand.logo', null)
            ->etc());
});

it('seleciona a marca pelo host mapeado em branding.domains', function () {
    config(['branding.domains' => ['painel.umbrella.test' => 'umbrella']]);

    $this->get('http://painel.umbrella.test/login')
        ->assertOk()
        ->assertSee('data-brand="umbrella"', false)
        ->assertSee('<title inertia>Umbrella Solutions</title>', false)
        ->assertInertia(fn (Assert $page) => $page
            ->where('brand.key', 'umbrella')
            ->where('brand.name', 'Umbrella Solutions')
            ->etc());

    // Host fora do mapa segue o padrão.
    $this->get('http://outro.test/login')->assertSee('data-brand="canaldecortes"', false);
});

it('APP_BRAND define a marca padrão e marca desconhecida cai no fallback', function () {
    config(['branding.default' => 'umbrella']);
    expect(Brand::resolve(Request::create('http://qualquer.test/'))['key'])->toBe('umbrella');

    config(['branding.default' => 'naoexiste']);
    expect(Brand::resolve(Request::create('http://qualquer.test/'))['key'])->toBe('canaldecortes');
});

it('usa o logo configurado quando existe', function () {
    config(['branding.brands.umbrella.logo' => '/images/umbrella.svg', 'branding.default' => 'umbrella']);

    expect(Brand::resolve()['logo'])->toBe('/images/umbrella.svg');
});
