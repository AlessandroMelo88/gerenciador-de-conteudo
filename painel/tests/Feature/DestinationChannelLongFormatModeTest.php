<?php

use App\Enums\LongFormatMode;
use App\Models\DestinationChannel;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;
use Inertia\Testing\AssertableInertia as Assert;

uses(DatabaseTransactions::class);

it('defaults long_format_mode to auto', function () {
    $channel = DestinationChannel::factory()->create(['slug' => 'longo-default']);

    expect($channel->fresh()->long_format_mode)->toBe(LongFormatMode::Auto)
        ->and(DB::table('destination_channels')->where('id', $channel->id)->value('long_format_mode'))->toBe('auto');
});

it('creates a channel with each long_format_mode', function (string $mode) {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/painel/canais-destino', [
            'slug' => "longo-{$mode}",
            'name' => 'Canal Longo',
            'niche' => 'podcast',
            'youtube_channel_id' => "UC_LONGO_{$mode}",
            'long_format_mode' => $mode,
        ])
        ->assertRedirect()
        ->assertSessionHasNoErrors();

    expect(DestinationChannel::query()->where('slug', "longo-{$mode}")->first()->long_format_mode->value)->toBe($mode);
})->with(['auto', 'short_only', 'both']);

it('updates long_format_mode to each mode', function (string $mode) {
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create(['slug' => "upd-{$mode}"]);

    $this->actingAs($user)
        ->put("/painel/canais-destino/{$channel->id}", ['long_format_mode' => $mode])
        ->assertRedirect()
        ->assertSessionHasNoErrors();

    expect($channel->fresh()->long_format_mode->value)->toBe($mode);
})->with(['auto', 'short_only', 'both']);

it('rejects an invalid long_format_mode on create and update', function () {
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create(['slug' => 'longo-invalido']);

    $this->actingAs($user)
        ->post('/painel/canais-destino', [
            'slug' => 'longo-invalido-novo',
            'name' => 'X',
            'niche' => 'podcast',
            'youtube_channel_id' => 'UC_INVALIDO',
            'long_format_mode' => 'longo_sempre',
        ])
        ->assertSessionHasErrors('long_format_mode');

    $this->actingAs($user)
        ->put("/painel/canais-destino/{$channel->id}", ['long_format_mode' => 'qualquer'])
        ->assertSessionHasErrors('long_format_mode');

    expect($channel->fresh()->long_format_mode)->toBe(LongFormatMode::Auto);
});

it('exposes longFormatMode in the destination channels page props', function () {
    $user = User::factory()->create();
    DestinationChannel::factory()->create(['slug' => 'longo-prop', 'long_format_mode' => 'both']);

    $this->actingAs($user)
        ->get('/painel/canais-destino')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('DestinationChannels')
            ->where('channels', fn ($channels) => collect($channels)
                ->firstWhere('slug', 'longo-prop')['longFormatMode'] === 'both'));
});
