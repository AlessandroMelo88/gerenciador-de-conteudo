<?php

use App\Models\SourceChannel;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

it('creates a source_channel via internal API resolve', function () {
    $user = User::factory()->create();
    Http::fake([
        '*/internal/resolve-channel' => Http::response([
            'channel_id' => 'UC_TEST_123',
            'channel_name' => 'Canal Teste',
            'channel_handle' => '@teste',
        ], 200),
    ]);

    $countBefore = SourceChannel::query()->count();
    $this->actingAs($user)
        ->post('/painel/canais-fonte', [
            'url' => 'https://youtube.com/@teste',
            'target_niche' => 'futebol',
        ])
        ->assertRedirect();

    expect(SourceChannel::query()->where('youtube_channel_id', 'UC_TEST_123')->exists())->toBeTrue();
    expect(SourceChannel::query()->count())->toBe($countBefore + 1);
});

it('shows an error when yt-dlp resolution fails and does not insert a row', function () {
    $user = User::factory()->create();
    Http::fake([
        '*/internal/resolve-channel' => Http::response(['error' => 'yt-dlp failed'], 422),
    ]);

    $countBefore = SourceChannel::query()->count();
    $this->actingAs($user)
        ->post('/painel/canais-fonte', [
            'url' => 'https://not-a-channel',
            'target_niche' => 'futebol',
        ])
        ->assertSessionHasErrors();

    expect(SourceChannel::query()->count())->toBe($countBefore);
});

it('toggles blacklisted without editing the queue', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create(['blacklisted' => false]);
    $this->actingAs($user)
        ->put("/painel/canais-fonte/{$channel->id}", ['blacklisted' => true])
        ->assertRedirect();
    expect($channel->refresh()->blacklisted)->toBeTrue();
});
