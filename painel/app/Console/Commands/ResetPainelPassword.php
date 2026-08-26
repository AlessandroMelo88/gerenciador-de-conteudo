<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Hash;

class ResetPainelPassword extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'painel:reset-password {email}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Reseta a senha do operador do painel.';

    /**
     * Execute the console command.
     */
    public function handle(): int
    {
        $email = $this->argument('email');

        $user = User::query()->where('email', $email)->first();

        if (! $user) {
            $this->error("Nenhum usuário com email {$email}.");

            return self::FAILURE;
        }

        $pass = $this->secret('Nova senha (mínimo 10 caracteres, não será exibida)');
        if (! is_string($pass) || strlen($pass) < 10) {
            $this->error('Senha deve ter no mínimo 10 caracteres.');

            return self::FAILURE;
        }

        $user->password = Hash::make($pass);
        $user->save();

        $this->info("Senha de {$email} atualizada.");

        return self::SUCCESS;
    }
}
