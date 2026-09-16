<?php

namespace Database\Seeders;

use App\Models\SourceChannel;
use Illuminate\Database\Seeder;

/**
 * Canais-fonte de baixo risco de direitos autorais.
 *
 * Contexto: a advertência de 14/09/2026 (reclamante Supernova) veio de clip de
 * imagem de partida, cortado do TiaGOL — que por sua vez é canal de cortes.
 * Ver Docs/sistema/PLANO-MESTRE.md, seção 1.
 *
 * Critério de entrada desta lista, nesta ordem:
 *   1. Canal de pessoa física ou produção própria — o titular é ele mesmo,
 *      não uma emissora que vendeu exclusividade de transmissão.
 *   2. Conteúdo é gente falando (análise, opinião, podcast), não lance de jogo.
 *   3. Não é canal de cortes — cortar de quem já cortou acumula o risco de
 *      dois elos, que é exatamente o que gerou a advertência.
 *
 * Emissora e detentora de transmissão (ESPN, TNT, CazéTV, SporTV, ge.globo)
 * ficam de fora de propósito. Este seeder não desativa nada que já exista:
 * só insere e atualiza as linhas abaixo.
 *
 * Idempotente — pode rodar quantas vezes precisar, local ou produção:
 *   php artisan db:seed --class=SourceChannelsSeeder
 */
class SourceChannelsSeeder extends Seeder
{
    /**
     * formato: duração típica observada em 15/09/2026, só para referência.
     * O pipeline decide curto/longo em runtime por MIN_LONGFORM_SECONDS (420s).
     */
    private const CANAIS = [
        // --- entregam vídeo curto: mantêm a cadência de Shorts do canal ---
        [
            'youtube_channel_id' => 'UCPWaLO0FTmgBxS8Tw1r1-GQ',
            'channel_name' => 'PVC',
            'channel_handle' => '@PVCoelho',
            'target_niche' => 'futebol',
            'formato' => 'curto (299-452s)',
        ],
        [
            'youtube_channel_id' => 'UCnlR7Byv1irGXGokMXf9nAQ',
            'channel_name' => 'Denílson Show',
            'channel_handle' => '@DenilsonShow',
            'target_niche' => 'futebol',
            'formato' => 'curto (163-378s)',
        ],
        [
            'youtube_channel_id' => 'UCPHvx0NxJubMU8QqZ6X_Efw',
            'channel_name' => 'Charla Podcast',
            'channel_handle' => '@CharlaPodcast',
            'target_niche' => 'futebol',
            'formato' => 'misto (165-913s)',
        ],

        // --- análise longa: viram corte horizontal de 7+ min ---
        [
            'youtube_channel_id' => 'UCRcRAyb5Y4x3HVNKBZ9SMLA',
            'channel_name' => 'Mauro Cezar Pereira',
            'channel_handle' => '@MauroCezar',
            'target_niche' => 'futebol',
            'formato' => 'longo (491-983s)',
        ],
        [
            'youtube_channel_id' => 'UCkYRv-hbWjbq8YC_ZsoYoMg',
            'channel_name' => 'Rica Perrone',
            'channel_handle' => '@RicaPerrone',
            'target_niche' => 'futebol',
            'formato' => 'longo (457-696s)',
        ],
        [
            'youtube_channel_id' => 'UCLRLY0-mxf8x7p5nMgmYmyQ',
            'channel_name' => 'Tati Mantovani',
            'channel_handle' => '@TatiMantovani',
            'target_niche' => 'futebol',
            'formato' => 'longo (502-866s)',
        ],
        [
            'youtube_channel_id' => 'UCr3S50A3UmXeBsHBTHCW-Ow',
            'channel_name' => 'Marcelo Bechler',
            'channel_handle' => '@MarceloBechler1',
            'target_niche' => 'futebol',
            'formato' => 'longo (481-2878s)',
        ],
        [
            'youtube_channel_id' => 'UCMLMnpzB7f06mq0Kx3oFzew',
            'channel_name' => 'Fred Caldeira',
            'channel_handle' => '@FredCaldeira',
            'target_niche' => 'futebol',
            'formato' => 'longo (701-3903s)',
        ],
        [
            'youtube_channel_id' => 'UCFjrDmEnxrG5TRGVO0TPHLA',
            'channel_name' => 'Desimpedidos',
            'channel_handle' => '@Desimpedidos',
            'target_niche' => 'futebol',
            'formato' => 'misto (493-2077s)',
        ],
    ];

    public function run(): void
    {
        foreach (self::CANAIS as $canal) {
            SourceChannel::updateOrCreate(
                ['youtube_channel_id' => $canal['youtube_channel_id']],
                [
                    'channel_name' => $canal['channel_name'],
                    'channel_handle' => $canal['channel_handle'],
                    'target_niche' => $canal['target_niche'],
                    'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id='.$canal['youtube_channel_id'],
                    'active' => true,
                    'blacklisted' => false,
                ]
            );

            $this->command?->info("  ✓ {$canal['channel_name']} ({$canal['channel_handle']}) — {$canal['formato']}");
        }

        $this->command?->info('  '.count(self::CANAIS).' canais-fonte de baixo risco garantidos.');
    }
}
