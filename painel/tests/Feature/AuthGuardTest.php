<?php

use Illuminate\Foundation\Testing\DatabaseTransactions;

uses(DatabaseTransactions::class);

it('redirects unauthenticated visitor from /admin to /admin/login', function () {
    $this->get('/admin')->assertRedirect('/admin/login');
});

it('serves /admin/login without authentication', function () {
    $this->get('/admin/login')->assertOk();
});

it('rejects /register route entirely', function () {
    $this->post('/register', [
        'name' => 'x', 'email' => 'x@example.com', 'password' => 'secret1234',
    ])->assertStatus(404);
});
