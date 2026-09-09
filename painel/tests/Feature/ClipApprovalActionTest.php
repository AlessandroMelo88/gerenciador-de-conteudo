<?php

use App\Models\GeneratedClip;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

beforeEach(function () {
    Http::fake([
        '*/internal/publish-now' => Http::response(['ok' => true], 200),
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

