<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        DB::table('source_channels')->insertOrIgnore([
            [
                'youtube_channel_id' => 'UCrD2l7nEg6AATX5qfugm8Xg',
                'channel_name' => 'SporTV',
                'channel_handle' => null,
                'target_niche' => null,
                'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id=UCrD2l7nEg6AATX5qfugm8Xg',
            ],
            [
                'youtube_channel_id' => 'UCS710QGV74b0wPETkrcVB7w',
                'channel_name' => 'ge.globo',
                'channel_handle' => null,
                'target_niche' => null,
                'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id=UCS710QGV74b0wPETkrcVB7w',
            ],
            [
                'youtube_channel_id' => 'UCw5-xj3AKqEizC7MvHaIPqA',
                'channel_name' => 'ESPN Brasil',
                'channel_handle' => null,
                'target_niche' => null,
                'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id=UCw5-xj3AKqEizC7MvHaIPqA',
            ],
            [
                'youtube_channel_id' => 'UCx0RRbF4EJOUQ28SurIU7Eg',
                'channel_name' => 'Canal do Nicola',
                'channel_handle' => null,
                'target_niche' => null,
                'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id=UCx0RRbF4EJOUQ28SurIU7Eg',
            ],
            [
                'youtube_channel_id' => 'UCs-6sCz2LJm1PrWQN4ErsPw',
                'channel_name' => 'TNT Sports Brasil',
                'channel_handle' => null,
                'target_niche' => null,
                'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id=UCs-6sCz2LJm1PrWQN4ErsPw',
            ],
            [
                'youtube_channel_id' => 'UC1VZDEtGNxfQzh7EYcD2frg',
                'channel_name' => 'mano deyvin',
                'channel_handle' => '@manodeyvin',
                'target_niche' => 'hacker-libertario',
                'rss_url' => 'https://www.youtube.com/feeds/videos.xml?channel_id=UC1VZDEtGNxfQzh7EYcD2frg',
            ],
        ]);

        DB::table('source_channels')
            ->whereNull('target_niche')
            ->where('active', true)
            ->update(['target_niche' => 'futebol']);

        DB::table('destination_channels')->insertOrIgnore([
            [
                'slug' => 'futebol-em-cortes',
                'name' => 'Futebol em Cortes',
                'niche' => 'futebol',
                'youtube_channel_id' => 'UC_PLACEHOLDER_FUTEBOL',
                'credit_template' => 'Créditos: @{channel_handle}',
                'active' => false,
            ],
            [
                'slug' => 'podcast-cortes',
                'name' => 'Podcast Cortes',
                'niche' => 'podcast',
                'youtube_channel_id' => 'UC_PLACEHOLDER_PODCAST',
                'credit_template' => 'Créditos: @{channel_handle}',
                'active' => false,
            ],
        ]);
    }

    public function down(): void
    {
        // Seeds operacionais podem ter sido editados pelo operador; não removê-los no rollback.
    }
};
