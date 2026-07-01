<?php

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;

uses(DatabaseTransactions::class);

it('renders dashboard widgets with 5s polling attribute', function () {
    $user = User::factory()->create();
    $response = $this->actingAs($user)->get('/admin');
    $response->assertOk();
    // Assert cada widget expõe polling 5s no HTML renderizado (wire:poll ou similar).
    // O Plan 08-08 vai atender este requisito via TableWidget->poll('5s').
    $response->assertSee('wire:poll.5s', false);
});

it('renders quota widget with youtube_uploads key format', function () {
    $user = User::factory()->create();
    $response = $this->actingAs($user)->get('/admin');
    $response->assertOk();
    // Widget de cota deve ser visível — Plan 08-08 detalha layout.
    $response->assertSee('Cota', false);
});
