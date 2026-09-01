<?php

use App\Models\DestinationChannel;
use App\Models\MediaAsset;
use App\Models\User;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Inertia\Testing\AssertableInertia as Assert;

use function Pest\Laravel\actingAs;

it('uploads a global intro to the media library', function () {
    Storage::fake('branding');
    $user = User::factory()->create();

    actingAs($user)
        ->post('/painel/configuracoes/midia', [
            'kind' => 'intro',
            'name' => 'Intro principal',
            'file' => UploadedFile::fake()->create('intro.mp4', 512, 'video/mp4'),
            'format' => 'curto',
            'duration_seconds' => 4,
        ])
        ->assertRedirect();

    $asset = MediaAsset::query()->where('name', 'Intro principal')->firstOrFail();
    expect($asset->kind)->toBe('intro')
        ->and($asset->format)->toBe('curto')
        ->and($asset->duration_seconds)->toBe(4)
        ->and($asset->destination_channel_id)->toBeNull();
    Storage::disk('branding')->assertExists($asset->path);
});

it('exposes media readiness and destination scopes in settings', function () {
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create(['name' => 'Canal Futebol']);
    MediaAsset::create(['kind' => 'intro', 'name' => 'Intro', 'path' => 'media/intro/a.mp4']);
    MediaAsset::create(['kind' => 'outro', 'name' => 'Outro', 'path' => 'media/outro/a.mp4']);
    MediaAsset::create([
        'kind' => 'music',
        'name' => 'Trilha',
        'path' => 'media/music/a.mp3',
        'destination_channel_id' => $channel->getKey(),
    ]);

    actingAs($user)
        ->get('/painel/configuracoes')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('Settings')
            ->where('mediaConfiguration.ready', true)
            ->where('mediaConfiguration.introCount', 1)
            ->where('mediaConfiguration.outroCount', 1)
            ->where('mediaConfiguration.musicCount', 1)
            ->where('destinationChannels', fn ($channels) => collect($channels)
                ->contains(fn ($item) => $item['id'] === $channel->getKey())));
});

it('deletes the file and database record together', function () {
    Storage::fake('branding');
    $user = User::factory()->create();
    Storage::disk('branding')->put('media/music/trilha.mp3', 'audio');
    $asset = MediaAsset::create([
        'kind' => 'music',
        'name' => 'Trilha',
        'path' => 'media/music/trilha.mp3',
    ]);

    actingAs($user)
        ->delete("/painel/configuracoes/midia/{$asset->getKey()}")
        ->assertRedirect();

    expect(MediaAsset::query()->find($asset->getKey()))->toBeNull();
    Storage::disk('branding')->assertMissing('media/music/trilha.mp3');
});
