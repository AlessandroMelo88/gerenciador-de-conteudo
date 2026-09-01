<?php

use Illuminate\Foundation\Testing\DatabaseTransactions;

uses(DatabaseTransactions::class);

it('redirects unauthenticated visitor from /painel to /login', function () {
    $this->get('/painel')->assertRedirect('/login');
});

it('serves /login without authentication', function () {
    $this->get('/login')->assertOk();
});

it('rejects /register route entirely', function () {
    $this->post('/register', [
        'name' => 'x', 'email' => 'x@example.com', 'password' => 'secret1234',
    ])->assertStatus(404);
});
