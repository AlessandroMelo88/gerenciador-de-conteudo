<?php

namespace Database\Seeders;

use App\Models\Offer;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

/**
 * Massa fixa para os testes E2E do Playwright (painel/e2e). Idempotente.
 *
 *   php artisan db:seed --class=E2ESeeder
 *
 * Recusa rodar em produção: cria uma conta de senha conhecida (ver o aviso em DatabaseSeeder).
 */
class E2ESeeder extends Seeder
{
    public const EMAIL = 'e2e@canaldecortes.test';

    public const PASSWORD = 'e2e-senha-segura-123';

    public const OFFER_SLUG = 'e2eoffer';

    public const OFFER_URL = 'https://go.hotmart.com/E2E-DESTINO';

    public function run(): void
    {
        if (app()->environment('production')) {
            $this->command?->error('E2ESeeder recusado em produção.');

            return;
        }

        User::query()->updateOrCreate(
            ['email' => self::EMAIL],
            ['name' => 'Operador E2E', 'password' => Hash::make(self::PASSWORD)],
        );

        DB::table('niches')->insertOrIgnore([
            'slug' => 'futebol', 'label' => 'Futebol', 'created_at' => now(), 'updated_at' => now(),
        ]);

        $offer = Offer::query()->firstOrNew(['slug' => self::OFFER_SLUG]);
        $offer->fill(Offer::factory()->approved()->make([
            'title' => 'Oferta E2E',
            'affiliate_url' => self::OFFER_URL,
        ])->getAttributes());
        $offer->slug = self::OFFER_SLUG;
        $offer->save();
    }
}
