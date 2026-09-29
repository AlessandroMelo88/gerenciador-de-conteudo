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

it('accepts the lower source input priority boundary', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    $this->actingAs($user)
        ->put("/painel/canais-fonte/{$channel->id}", ['input_priority' => -10])
        ->assertRedirect();

    expect($channel->refresh()->input_priority)->toBe(-10);
});

it('rejects source input priorities outside the configured range', function () {
    $user = User::factory()->create();
    $channel = SourceChannel::factory()->create();

    foreach ([11, -11] as $invalidPriority) {
        $this->actingAs($user)
            ->put("/painel/canais-fonte/{$channel->id}", ['input_priority' => $invalidPriority])
            ->assertSessionHasErrors('input_priority');
    }

    expect($channel->refresh()->input_priority)->toBe(0);
});
