<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Hash;

use function Laravel\Prompts\password;

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

        $pass = password(
            label: 'Nova senha (mínimo 10 caracteres, não será exibida)',
            required: true,
            validate: fn (string $value) => strlen($value) >= 10 ? null : 'Senha deve ter no mínimo 10 caracteres.',
        );

        $user->password = Hash::make($pass);
        $user->save();

        $this->info("Senha de {$email} atualizada.");

        return self::SUCCESS;
    }
}
