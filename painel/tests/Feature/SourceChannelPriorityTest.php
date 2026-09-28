<?php

use App\Models\SourceChannel;
use App\Models\User;

it('defaults source input priority to neutral', function () {
    $channel = SourceChannel::factory()->create();

    expect($channel->fresh()->input_priority)->toBe(0);
});

it('updates source input priority in the configured range', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    $this->actingAs($user)
        ->put("/painel/canais-fonte/{$channel->id}", ['input_priority' => 8])
        ->assertRedirect();

    expect($channel->refresh()->input_priority)->toBe(8);
});

it('rejects source input priorities outside the configured range', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    $this->actingAs($user)
        ->put("/painel/canais-fonte/{$channel->id}", ['input_priority' => 11])
        ->assertSessionHasErrors('input_priority');

    expect($channel->refresh()->input_priority)->toBe(0);
});
