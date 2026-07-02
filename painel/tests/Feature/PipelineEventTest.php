<?php

use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

beforeEach(function () {
    Http::fake([
        '*api.telegram.org*' => Http::response(['ok' => true, 'result' => ['message_id' => 1]], 200),
    ]);
});

it('POST /internal/pipeline-event without token returns 401', function () {
    $this->postJson('/internal/pipeline-event', [
        'event'   => 'upload_published',
        'payload' => [],
    ])->assertStatus(401);
});

it('POST /internal/pipeline-event upload_published sends Telegram message with title', function () {
    $token = config('services.clip_processor.token');

    $this->postJson('/internal/pipeline-event', [
        'event'   => 'upload_published',
        'payload' => [
            'title'       => 'Gol do Brasil',
            'youtube_url' => 'https://youtube.com/watch?v=abc',
        ],
    ], ['X-Internal-Token' => $token])
        ->assertStatus(200)
        ->assertJson(['ok' => true]);

    Http::assertSent(fn ($req) =>
        str_contains($req->url(), 'api.telegram.org') &&
        str_contains($req['text'] ?? '', 'Gol do Brasil')
    );
});

it('POST /internal/pipeline-event pipeline_failure sends message with stage', function () {
    $token = config('services.clip_processor.token');

    $this->postJson('/internal/pipeline-event', [
        'event'   => 'pipeline_failure',
        'payload' => ['stage' => 'cutting', 'error_msg' => 'ffmpeg crashed'],
    ], ['X-Internal-Token' => $token])
        ->assertStatus(200);

    Http::assertSent(fn ($req) =>
        str_contains($req->url(), 'api.telegram.org') &&
        str_contains($req['text'] ?? '', 'cutting')
    );
});

it('POST /internal/pipeline-event daily_summary sends the summary text', function () {
    $token = config('services.clip_processor.token');

    $this->postJson('/internal/pipeline-event', [
        'event'   => 'daily_summary',
        'payload' => ['text' => 'Resumo: 3 clips aguardando.'],
    ], ['X-Internal-Token' => $token])
        ->assertStatus(200);

    Http::assertSent(fn ($req) =>
        str_contains($req->url(), 'api.telegram.org') &&
        str_contains($req['text'] ?? '', 'Resumo')
    );
});
