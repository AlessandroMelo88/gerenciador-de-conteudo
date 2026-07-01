<?php

use App\Models\DestinationChannel;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;

uses(DatabaseTransactions::class);

it('creates a destination_channel with niche via Select field', function () {
    $user = User::factory()->create();
    $countBefore = DestinationChannel::query()->count();
    $this->actingAs($user)
        ->post('/admin/destination-channels', [
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

it('renders OAuth status badge in the resource table', function () {
    $user = User::factory()->create();
    DestinationChannel::factory()->create(['slug' => 'badge-test', 'oauth_expired_flag' => true]);
    $this->actingAs($user)
        ->get('/admin/destination-channels')
        ->assertOk()
        ->assertSee('expired');
});
