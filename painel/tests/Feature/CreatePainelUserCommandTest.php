<?php

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Hash;

uses(DatabaseTransactions::class);

it('creates a painel user with hashed password via painel:create-user', function () {
    $this->artisan('painel:create-user')
        ->expectsQuestion('Email do operador', 'operador@example.com')
        ->expectsQuestion('Senha (mínimo 10 caracteres, não será exibida)', 'senhasegura123')
        ->assertExitCode(0);

    $user = User::query()->where('email', 'operador@example.com')->first();

    expect($user)->not->toBeNull();
    expect(Hash::check('senhasegura123', $user->password))->toBeTrue();
});

it('does not create a duplicate user when the email already exists', function () {
    User::factory()->create(['email' => 'ja-existe@example.com']);

    $this->artisan('painel:create-user')
        ->expectsQuestion('Email do operador', 'ja-existe@example.com')
        ->assertExitCode(1);

    expect(User::query()->where('email', 'ja-existe@example.com')->count())->toBe(1);
});
