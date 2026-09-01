<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Hash;

use function Laravel\Prompts\password;
use function Laravel\Prompts\text;

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
        $email = text(
            label: 'Email do operador',
            required: true,
            validate: fn (string $value) => filter_var($value, FILTER_VALIDATE_EMAIL) ? null : 'Email inválido.',
        );

        if (User::query()->where('email', $email)->exists()) {
            $this->error("Já existe usuário com email {$email}. Use painel:reset-password para alterar a senha.");

            return self::FAILURE;
        }

        $pass = password(
            label: 'Senha (mínimo 10 caracteres, não será exibida)',
            required: true,
            validate: fn (string $value) => strlen($value) >= 10 ? null : 'Senha deve ter no mínimo 10 caracteres.',
        );

        User::create([
            'name' => 'Operador',
            'email' => $email,
            'password' => Hash::make($pass),
        ]);

        $this->info("Usuário {$email} criado com sucesso.");

        return self::SUCCESS;
    }
}
