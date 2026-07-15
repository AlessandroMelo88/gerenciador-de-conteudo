<?php

use App\Models\GeneratedClip;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

it('approves a pending clip via panel action (UPDATE guard: only pending)', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);
    $this->actingAs($user)
        ->post("/painel/clips/{$clip->id}/approve")
        ->assertRedirect();
    expect($clip->refresh()->status)->toBe('approved');
});

it('does not approve a non-pending clip', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'published']);
    $this->actingAs($user)
        ->post("/painel/clips/{$clip->id}/approve")
        ->assertRedirect();
    expect($clip->refresh()->status)->toBe('published');
});

it('rejects a clip via internal API and shows exit code result', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);
    Http::fake(['*/internal/reject-clip' => Http::response(['exit_code' => 0], 200)]);

    $this->actingAs($user)
        ->post("/painel/clips/{$clip->id}/reject")
        ->assertRedirect();
    Http::assertSent(function ($request) use ($clip) {
        return str_contains($request->url(), '/internal/reject-clip')
            && $request['clip_id'] === $clip->id;
    });
});

it('propagates rejeitar exit_code=1 as a validation error notification', function () {
    $user = User::factory()->create();
    $clip = GeneratedClip::factory()->create(['status' => 'pending']);
    Http::fake(['*/internal/reject-clip' => Http::response(['exit_code' => 1], 200)]);

    $this->actingAs($user)
        ->post("/painel/clips/{$clip->id}/reject")
        ->assertSessionHas('error');
});
