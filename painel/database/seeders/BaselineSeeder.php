<?php

namespace Database\Seeders;

use App\Models\DestinationChannel;
use App\Models\Niche;
use Illuminate\Database\Seeder;

/**
 * Dados de base do painel: nichos e canais de destino.
 *
 * Existe porque um banco recém-migrado (o Postgres local da fase A, por exemplo)
 * sobe com o schema certo e **zero linha** — sem nicho e sem canal destino o painel
 * abre vazio e o pipeline não tem para onde publicar.
 *
 * Os valores espelham a produção apurada em 15/09/2026. Idempotente: casa por
 * chave única (`slug` do nicho, `youtube_channel_id` do destino), então rodar de
 * novo não duplica nem sobrescreve o que já existe com outro id.
 *
 *   php artisan db:seed --class=BaselineSeeder
 *
 * Não cria usuário. Conta de painel se cria com `php artisan painel:create-user`,
 * que pede senha — nunca por factory, que usa senha padrão (ver bug 14).
 */
class BaselineSeeder extends Seeder
{
    private const NICHOS = [
        ['slug' => 'futebol', 'label' => 'Futebol'],
        ['slug' => 'podcast', 'label' => 'Podcast'],
        ['slug' => 'politica', 'label' => 'Política'],
    ];

    private const DESTINOS = [
        [
            'slug' => 'futebol-em-cortes',
            'name' => 'Futebol em Cortes',
            'niche' => 'futebol',
            'youtube_channel_id' => 'UCcyeBQFAkUNeDJbBM7JJqLw',
            'credit_template' => 'Créditos: @{channel_handle}',
            'active' => true,
        ],
        [
            'slug' => 'fatos-e-debates',
            'name' => 'Fatos & Debates',
            'niche' => 'politica',
            'youtube_channel_id' => 'UCCx9rlpbNdfLBTLqGah78cA',
            'credit_template' => 'Cortes e destaques dos principais debates e análises da política nacional. Créditos: @{channel_handle}',
            'active' => true,
        ],
        [
            'slug' => 'podcast-cortes',
            'name' => 'Podcast Cortes',
            'niche' => 'podcast',
            'youtube_channel_id' => 'UC_PLACEHOLDER_PODCAST',
            'credit_template' => 'Créditos: @{channel_handle}',
            'active' => false,
        ],
    ];

    public function run(): void
    {
        foreach (self::NICHOS as $nicho) {
            Niche::updateOrCreate(['slug' => $nicho['slug']], ['label' => $nicho['label']]);
            $this->command?->info("  ✓ nicho {$nicho['slug']}");
        }

        foreach (self::DESTINOS as $destino) {
            DestinationChannel::updateOrCreate(
                ['youtube_channel_id' => $destino['youtube_channel_id']],
                [
                    'slug' => $destino['slug'],
                    'name' => $destino['name'],
                    'niche' => $destino['niche'],
                    'credit_template' => $destino['credit_template'],
                    'active' => $destino['active'],
                ]
            );
            $this->command?->info("  ✓ destino {$destino['slug']}");
        }
    }
}
