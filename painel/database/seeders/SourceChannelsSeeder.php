<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class SourceChannelsSeeder extends Seeder
{
    public function run(): void
    {
        $inteligenciaId = DB::table('prompt_profiles')
            ->where('slug', 'conteudo-inteligencia')
            ->value('id');

        DB::table('source_channels')->insertOrIgnore([
            [
                'youtube_channel_id' => 'UCc-Nvq1SYmXVTO5_UwQbg6w',
                'channel_name' => 'Rafael Quintanilha',
                'channel_handle' => '@QuantBrasil',
                'target_niche' => 'hacker-libertario',
                'prompt_profile_id' => $inteligenciaId,
                'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id=UCc-Nvq1SYmXVTO5_UwQbg6w',
                'active' => true,
                'blacklisted' => false,
            ],
            [
                'youtube_channel_id' => 'UCyHOBY6IDZF9zOKJPou2Rgg',
                'channel_name' => 'Lucas Montano',
                'channel_handle' => '@LucasMontano',
                'target_niche' => 'hacker-libertario',
                'prompt_profile_id' => $inteligenciaId,
                'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id=UCyHOBY6IDZF9zOKJPou2Rgg',
                'active' => true,
                'blacklisted' => false,
            ],
        ]);
    }
}
