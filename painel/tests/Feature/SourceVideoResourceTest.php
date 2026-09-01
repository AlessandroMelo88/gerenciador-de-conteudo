<?php

use App\Models\SourceVideo;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Inertia\Testing\AssertableInertia as Assert;

use function Pest\Laravel\actingAs;

uses(DatabaseTransactions::class);

it('keeps completed source videos out of the active tab', function () {
    $user = User::factory()->create();
    $active = SourceVideo::factory()->create([
        'status' => 'pending',
        'title' => 'filtro fonte concluida unico',
    ]);
    SourceVideo::factory()->create([
        'status' => 'published',
        'title' => 'filtro fonte concluida unico',
    ]);
    SourceVideo::factory()->create([
        'status' => 'failed',
        'title' => 'filtro fonte concluida unico',
    ]);

    actingAs($user)
        ->get('/painel/videos?search=filtro+fonte+concluida+unico')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('SourceVideos')
            ->where('filters.tab', 'ativos')
            ->has('videos.data', 1)
            ->where('videos.data.0.id', $active->getKey()));
});

it('keeps completed source videos available in the all tab', function () {
    $user = User::factory()->create();
    $published = SourceVideo::factory()->create([
        'status' => 'published',
        'title' => 'historico fonte concluida unico',
    ]);

    actingAs($user)
        ->get('/painel/videos?tab=todos&search=historico+fonte+concluida+unico')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('SourceVideos')
            ->where('filters.tab', 'todos')
            ->where('videos.data', fn ($videos) => collect($videos)
                ->contains(fn ($video) => data_get($video, 'id') === $published->getKey())));
});
