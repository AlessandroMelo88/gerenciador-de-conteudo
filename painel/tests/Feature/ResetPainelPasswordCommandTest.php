<?php

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Hash;

uses(DatabaseTransactions::class);

it('resets the password for an existing user via painel:reset-password', function () {
    $user = User::factory()->create([
        'email' => 'reset@example.com',
        'password' => Hash::make('old-password-123'),
    ]);

    $this->artisan('painel:reset-password', ['email' => 'reset@example.com'])
        ->expectsQuestion('Nova senha (mínimo 10 caracteres, não será exibida)', 'nova-senha-123')
        ->assertExitCode(0);

    $user->refresh();

    expect(Hash::check('nova-senha-123', $user->password))->toBeTrue();
});

it('fails with exit code 1 when the user does not exist', function () {
    $this->artisan('painel:reset-password', ['email' => 'nao-existe@example.com'])
        ->assertExitCode(1);
});
