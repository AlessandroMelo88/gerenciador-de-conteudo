<?php

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

it('redirects guests away from the Inertia dashboard', function () {
    $this->get('/painel')->assertRedirect('/login');
});
