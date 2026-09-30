<?php

use App\Models\SourceChannel;
use App\Models\SourceVideo;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Inertia\Testing\AssertableInertia as Assert;

uses(DatabaseTransactions::class);

it('defaults source input priority to neutral', function () {
    $channel = SourceChannel::factory()->create();

    expect($channel->fresh()->input_priority)->toBe(0);
});

it('defaults source freshness to the current one-day policy', function () {
    $channel = SourceChannel::factory()->create();

    expect($channel->fresh()->freshness_days)->toBe(1);
});

it('updates source input priority in the configured range', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    $this->actingAs($user)
        ->put("/painel/canais-fonte/{$channel->id}", ['input_priority' => 8])
        ->assertRedirect();

    expect($channel->refresh()->input_priority)->toBe(8);
});

it('accepts the lower source input priority boundary', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    $this->actingAs($user)
        ->put("/painel/canais-fonte/{$channel->id}", ['input_priority' => -10])
        ->assertRedirect();

    expect($channel->refresh()->input_priority)->toBe(-10);
});

it('rejects source input priorities outside the configured range', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    foreach ([11, -11] as $invalidPriority) {
        $this->actingAs($user)
            ->put("/painel/canais-fonte/{$channel->id}", ['input_priority' => $invalidPriority])
            ->assertSessionHasErrors('input_priority');
    }

    expect($channel->refresh()->input_priority)->toBe(0);
});

it('lets each source channel pick the 3-day freshness window', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    $this->actingAs($user)
        ->put("/painel/canais-fonte/{$channel->id}", ['freshness_days' => 3])
        ->assertRedirect();

    expect($channel->refresh()->freshness_days)->toBe(3);
});

it('rejects freshness windows that would reopen the old backlog', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    foreach ([0, 2, 30, 1500] as $invalidDays) {
        $this->actingAs($user)
            ->put("/painel/canais-fonte/{$channel->id}", ['freshness_days' => $invalidDays])
            ->assertSessionHasErrors('freshness_days');
    }

    expect($channel->refresh()->freshness_days)->toBe(1);
});

it('exposes freshness and priority to the source channels page', function () {
    $this->withoutVite();
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create(['freshness_days' => 3, 'input_priority' => 4]);

    $this->actingAs($user)
        ->get('/painel/canais-fonte')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('SourceChannels')
            ->where('channels', fn ($channels) => collect($channels)->contains(
                fn ($c) => data_get($c, 'id') === $channel->id
                    && data_get($c, 'freshnessDays') === 3
                    && data_get($c, 'inputPriority') === 4
            )));
});

it('keeps published source videos out of the active tab but in the all tab', function () {
    $this->withoutVite();
    $user = User::factory()->create();
    $active = SourceVideo::factory()->create(['status' => 'pending', 'title' => 'aba ativos filtro unico']);
    $published = SourceVideo::factory()->create(['status' => 'published', 'title' => 'aba ativos filtro unico']);
    SourceVideo::factory()->create(['status' => 'failed', 'title' => 'aba ativos filtro unico']);

    $this->actingAs($user)
        ->get('/painel/videos?search='.urlencode('aba ativos filtro unico'))
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('SourceVideos')
            ->has('videos.data', 1)
            ->where('videos.data.0.id', $active->getKey()));

    $this->actingAs($user)
        ->get('/painel/videos?tab=todos&search='.urlencode('aba ativos filtro unico'))
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->where('videos.data', fn ($videos) => collect($videos)
                ->contains(fn ($video) => data_get($video, 'id') === $published->getKey())));
});
