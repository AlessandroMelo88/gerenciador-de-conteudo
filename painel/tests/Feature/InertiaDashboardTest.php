<?php

use App\Models\DestinationChannel;
use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Inertia\Testing\AssertableInertia as Assert;

uses(DatabaseTransactions::class);

it('renders the Inertia dashboard page for an authenticated user', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->get('/painel')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page->component('Dashboard'));
});

it('shows both output formats for RSS sources and counts clips by their own format', function () {
    $user = User::factory()->create();
    $source = SourceVideo::factory()->create([
        'status' => 'downloaded',
        'local_path' => '/tmp/source-video.mp4',
        'format' => 'curto',
        'generate_both_formats' => true,
    ]);
    GeneratedClip::factory()->create([
        'source_video_id' => $source->id,
        'format' => 'longo',
        'status' => 'published',
    ]);

    $this->actingAs($user)
        ->get('/painel')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('Dashboard')
            ->where('activeWindow.0.format', 'ambos')
            ->where('overview.publishedCurto', 0)
            ->where('overview.publishedLongo', 1));
});

it('uses cached pipeline config for the source video window capacity', function () {
    $previous = getenv('DOWNLOAD_WINDOW_PER_CHANNEL');
    putenv('DOWNLOAD_WINDOW_PER_CHANNEL=10');
    config(['pipeline.download_window_per_channel' => 3]);
    DestinationChannel::factory()->count(2)->create();

    try {
        $this->actingAs(User::factory()->create())
            ->get('/painel/videos')
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page
                ->component('SourceVideos')
                ->where('downloadWindow.cap', 6));
    } finally {
        putenv($previous === false
            ? 'DOWNLOAD_WINDOW_PER_CHANNEL'
            : 'DOWNLOAD_WINDOW_PER_CHANNEL='.$previous);
    }
});

it('redirects guests away from the Inertia dashboard', function () {
    $this->get('/painel')->assertRedirect('/login');
});
