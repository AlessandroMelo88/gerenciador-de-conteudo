<?php

namespace Database\Seeders;

use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

/**
 * Seeder padrão — deixado vazio de propósito.
 *
 * Até 15/09/2026 este `run()` criava `User::factory()->create([...])`. A factory do Laravel usa a
 * senha padrão `password`, então qualquer `php artisan db:seed` sem `--class` plantava uma conta de
 * senha conhecida no banco alvo. Foi assim que três contas de teste acabaram vivendo no banco de
 * produção (bug 14 em Docs/sistema/BUGS.md).
 *
 * Dado de verdade mora em seeder avulso, chamado explicitamente:
 *
 *   php artisan db:seed --class=BaselineSeeder        # nichos + canais de destino
 *   php artisan db:seed --class=SourceChannelsSeeder  # canais-fonte
 *
 * Conta de painel se cria só com `php artisan painel:create-user`, que pede a senha e nunca a ecoa.
 * Não voltar a criar usuário aqui.
 */
class DatabaseSeeder extends Seeder
{
    use WithoutModelEvents;

    public function run(): void
    {
        // Intencionalmente vazio. Ver o bloco de documentação acima antes de adicionar qualquer coisa.
    }
}
