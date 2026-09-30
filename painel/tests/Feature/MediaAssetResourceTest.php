<?php

use App\Models\DestinationChannel;
use App\Models\MediaAsset;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Inertia\Testing\AssertableInertia as Assert;

use function Pest\Laravel\actingAs;

uses(DatabaseTransactions::class);

it('uploads an intro to a destination channel media library', function () {
    Storage::fake('branding');
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create();

    actingAs($user)
        ->post('/painel/configuracoes/midia', [
            'kind' => 'intro',
            'name' => 'Intro principal',
            'file' => UploadedFile::fake()->create('intro.mp4', 512, 'video/mp4'),
            'destination_channel_id' => $channel->getKey(),
            'format' => 'curto',
            'duration_seconds' => 4,
        ])
        ->assertRedirect();

    $asset = MediaAsset::query()->where('name', 'Intro principal')->firstOrFail();
    expect($asset->kind)->toBe('intro')
        ->and($asset->format)->toBe('curto')
        ->and($asset->duration_seconds)->toBe(4)
        ->and($asset->destination_channel_id)->toBe($channel->getKey());
    Storage::disk('branding')->assertExists($asset->path);
});

it('exposes media readiness and destination scopes in settings', function () {
    $this->withoutVite();
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create(['name' => 'Canal Futebol']);
    MediaAsset::create([
        'kind' => 'intro',
        'name' => 'Intro',
        'path' => 'media/intro/a.mp4',
        'destination_channel_id' => $channel->getKey(),
    ]);
    MediaAsset::create([
        'kind' => 'outro',
        'name' => 'Outro',
        'path' => 'media/outro/a.mp4',
        'destination_channel_id' => $channel->getKey(),
    ]);
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

it('rejects an audio file sent as intro and a video sent as music', function () {
    Storage::fake('branding');
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create();

    actingAs($user)
        ->post('/painel/configuracoes/midia', [
            'kind' => 'intro',
            'name' => 'Intro errada',
            'file' => UploadedFile::fake()->create('trilha.mp3', 64, 'audio/mpeg'),
            'destination_channel_id' => $channel->getKey(),
        ])
        ->assertSessionHasErrors('file');

    actingAs($user)
        ->post('/painel/configuracoes/midia', [
            'kind' => 'music',
            'name' => 'Trilha errada',
            'file' => UploadedFile::fake()->create('video.mp4', 64, 'video/mp4'),
            'destination_channel_id' => $channel->getKey(),
        ])
        ->assertSessionHasErrors('file');

    expect(MediaAsset::query()->whereIn('name', ['Intro errada', 'Trilha errada'])->count())->toBe(0);
});

it('requires a destination channel so no asset is global', function () {
    Storage::fake('branding');
    $user = User::factory()->create();

    actingAs($user)
        ->post('/painel/configuracoes/midia', [
            'kind' => 'intro',
            'name' => 'Sem canal',
            'file' => UploadedFile::fake()->create('intro.mp4', 64, 'video/mp4'),
        ])
        ->assertSessionHasErrors('destination_channel_id');
});

it('defaults music volume to 0.24 and updates scope, priority and active flag', function () {
    Storage::fake('branding');
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create();
    $other = DestinationChannel::factory()->create();

    actingAs($user)
        ->post('/painel/configuracoes/midia', [
            'kind' => 'music',
            'name' => 'Trilha padrao',
            'file' => UploadedFile::fake()->create('trilha.mp3', 64, 'audio/mpeg'),
            'destination_channel_id' => $channel->getKey(),
        ])
        ->assertRedirect();

    $asset = MediaAsset::query()->where('name', 'Trilha padrao')->firstOrFail();
    expect($asset->music_volume)->toBe(0.24)
        ->and($asset->duration_seconds)->toBeNull();

    actingAs($user)
        ->patch("/painel/configuracoes/midia/{$asset->getKey()}", [
            'destination_channel_id' => $other->getKey(),
            'format' => 'longo',
            'priority' => 5,
            'active' => false,
        ])
        ->assertRedirect();

    $asset->refresh();
    expect($asset->destination_channel_id)->toBe($other->getKey())
        ->and($asset->format)->toBe('longo')
        ->and($asset->priority)->toBe(5)
        ->and($asset->active)->toBeFalse();
});

it('does not count inactive or unassigned assets as ready in settings', function () {
    $this->withoutVite();
    $user = User::factory()->create();
    $channel = DestinationChannel::factory()->create(['active' => true]);
    MediaAsset::create([
        'kind' => 'intro',
        'name' => 'Intro pausada',
        'path' => 'media/intro/p.mp4',
        'destination_channel_id' => $channel->getKey(),
        'active' => false,
    ]);
    MediaAsset::create([
        'kind' => 'outro',
        'name' => 'Outro sem canal',
        'path' => 'media/outro/s.mp4',
    ]);

    actingAs($user)
        ->get('/painel/configuracoes')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->where('mediaConfiguration.ready', false)
            ->where('mediaConfiguration.introCount', 0)
            ->where('mediaConfiguration.outroCount', 0));
});

it('removes the channel media when the destination channel is deleted, keeping the file record unassigned', function () {
    $channel = DestinationChannel::factory()->create();
    $asset = MediaAsset::create([
        'kind' => 'intro',
        'name' => 'Intro',
        'path' => 'media/intro/x.mp4',
        'destination_channel_id' => $channel->getKey(),
    ]);

    $channel->delete();

    expect($asset->fresh()->destination_channel_id)->toBeNull();
});
