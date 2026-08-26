<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Hash;

class CreatePainelUser extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'painel:create-user';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Cria o usuário operador do painel (interativo, senha nunca ecoa).';

    /**
     * Execute the console command.
     */
    public function handle(): int
    {
        $email = $this->ask('Email do operador');

        if (! is_string($email) || ! filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $this->error('Email inválido.');

            return self::FAILURE;
        }

        if (User::query()->where('email', $email)->exists()) {
            $this->error("Já existe usuário com email {$email}. Use painel:reset-password para alterar a senha.");

            return self::FAILURE;
        }

        $pass = $this->secret('Senha (mínimo 10 caracteres, não será exibida)');
        if (! is_string($pass) || strlen($pass) < 10) {
            $this->error('Senha deve ter no mínimo 10 caracteres.');

            return self::FAILURE;
        }

        User::create([
            'name' => 'Operador',
            'email' => $email,
            'password' => Hash::make($pass),
        ]);

        $this->info("Usuário {$email} criado com sucesso.");

        return self::SUCCESS;
    }
}
