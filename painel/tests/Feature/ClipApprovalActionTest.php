<?php

use App\Models\GeneratedClip;
use App\Models\User;
use App\Services\ClipProcessorClient;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

beforeEach(function () {
    Http::fake([
        '*/internal/publish-now' => Http::response(['ok' => true], 200),
        '*/internal/reject-clip' => function ($request) {
            // Simula o sidecar: rejeita só pending/approved e devolve o exit code dele.
            $clip = GeneratedClip::find($request['clip_id']);
            if (! $clip) {
                return Http::response(['exit_code' => 1], 200);
            }
            if (! in_array($clip->status, ['pending', 'approved'], true)) {
                return Http::response(['exit_code' => 2], 200);
            }
            $clip->update(['status' => 'rejected']);

            return Http::response(['exit_code' => 0], 200);
        },
    ]);
});

it('approves a pending clip via panel action (UPDATE guard: only pending)', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);
    $this->actingAs($user)
        ->post("/painel/clips/{$clip->id}/approve")
        ->assertRedirect();
    expect($clip->refresh()->status)->toBe('approved');
    Http::assertSent(fn ($request) => str_contains($request->url(), '/internal/publish-now'));
});

it('does not approve a non-pending clip', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'published']);
    $this->actingAs($user)
        ->post("/painel/clips/{$clip->id}/approve")
        ->assertRedirect();
    expect($clip->refresh()->status)->toBe('published');
});

it('rejects a clip via panel action and updates status to rejected', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);

    $this->actingAs($user)
        ->post("/painel/clips/{$clip->id}/reject")
        ->assertRedirect();
    expect($clip->refresh()->status)->toBe('rejected');
});

it('does not reject a clip with invalid status', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'published']);

    $this->actingAs($user)
        ->post("/painel/clips/{$clip->id}/reject")
        ->assertSessionHas('error');
    expect($clip->refresh()->status)->toBe('published');
});

it('rejects through the sidecar, which is the only one able to delete the files', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);

    $this->actingAs($user)->post("/painel/clips/{$clip->id}/reject")->assertSessionHas('success');

    Http::assertSent(fn ($request) => str_contains($request->url(), '/internal/reject-clip')
        && $request['clip_id'] === $clip->id);
});

it('keeps the clip and shows an error when the sidecar is unreachable', function () {
    // O fake do beforeEach tem precedência sobre um novo Http::fake da mesma URL,
    // então a falha HTTP é simulada no client (o que rejectClip lança em 5xx/timeout).
    $this->mock(ClipProcessorClient::class, fn ($mock) => $mock
        ->shouldReceive('rejectClip')
        ->andThrow(new \RuntimeException('Erro ao rejeitar clip: HTTP 500')));
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);

    $this->actingAs($user)->post("/painel/clips/{$clip->id}/reject")->assertSessionHas('error');
    expect($clip->refresh()->status)->toBe('pending');
});

it('bulk rejects each clip through the sidecar and skips invalid statuses', function () {
    $user = User::factory()->create();
    $pending = GeneratedClip::factory()->create(['status' => 'pending']);
    $approved = GeneratedClip::factory()->create(['status' => 'approved']);
    $published = GeneratedClip::factory()->create(['status' => 'published']);

    $this->actingAs($user)
        ->post('/painel/clips/bulk-reject', ['ids' => [$pending->id, $approved->id, $published->id]])
        ->assertSessionHas('success', '2 clip(s) rejeitado(s)');

    expect($pending->refresh()->status)->toBe('rejected');
    expect($approved->refresh()->status)->toBe('rejected');
    expect($published->refresh()->status)->toBe('published');
    Http::assertSentCount(2);
});
