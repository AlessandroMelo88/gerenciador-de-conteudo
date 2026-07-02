<?php

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;

uses(DatabaseTransactions::class);

it('redirects unauthenticated visitor from /admin/profile to /admin/login', function () {
    $this->get('/admin/profile')->assertRedirect('/admin/login');
});

it('serves /admin/profile with a change-password form for an authenticated user', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)->get('/admin/profile');

    $response->assertOk();
    $response->assertSee('currentPassword', escape: false);
});
