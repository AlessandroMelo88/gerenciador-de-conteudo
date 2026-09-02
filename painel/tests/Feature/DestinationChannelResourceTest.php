<?php

use App\Models\DestinationChannel;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Inertia\Testing\AssertableInertia as Assert;

uses(DatabaseTransactions::class);

it('creates a destination_channel with niche via Select field', function () {
    $user = User::factory()->create();
    $countBefore = DestinationChannel::query()->count();
    $this->actingAs($user)
        ->post('/painel/canais-destino', [
            'slug' => 'novo-canal-teste',
            'name' => 'Novo Canal',
            'niche' => 'podcast',
            'youtube_channel_id' => 'UC_NEW_ONE',
            'credit_template' => 'Créditos: @{channel_handle}',
            'active' => true,
        ])
        ->assertRedirect();
    expect(DestinationChannel::query()->count())->toBe($countBefore + 1);
    $channel = DestinationChannel::query()->where('slug', 'novo-canal-teste')->first();
    expect($channel->niche)->toBe('podcast');
});

it('exposes OAuth status in the destination channels page props', function () {
    $user = User::factory()->create();
    DestinationChannel::factory()->create(['slug' => 'badge-test', 'oauth_expired_flag' => true]);

    $this->actingAs($user)
        ->get('/painel/canais-destino')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('DestinationChannels')
            ->where('channels', fn ($channels) => collect($channels)
                ->firstWhere('slug', 'badge-test')['oauthStatus'] === 'expired'));
});

it('updates template_config for a destination channel', function () {
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create(['slug' => 'template-test']);

    $config = [
        'headerTitle' => 'POLÍTICA EM CORTES',
        'headerBadge' => '🔴 DEBATE AO VIVO',
        'accentColor' => '#E50914',
        'bgStyle' => 'blur_dark',
        'subtitleColor' => '#facc15',
        'ctaText' => 'INSCREVA-SE NO CANAL',
    ];

    $this->actingAs($user)
        ->put("/painel/canais-destino/{$channel->id}", [
            'template_config' => $config,
        ])
        ->assertRedirect();

    $channel->refresh();
    expect($channel->template_config)->toBe($config);
});
