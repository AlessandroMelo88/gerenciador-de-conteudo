<?php

namespace Database\Factories;

use App\Models\SourceChannel;
use Illuminate\Database\Eloquent\Factories\Factory;

class SourceChannelFactory extends Factory
{
    protected $model = SourceChannel::class;

    public function definition(): array
    {
        $id = 'UC'.$this->faker->regexify('[A-Za-z0-9_-]{22}');

        return [
            'youtube_channel_id' => $id,
            'channel_name' => $this->faker->company(),
            'rss_url' => "https://www.youtube.com/feeds/videos.xml?channel_id={$id}",
            'active' => true,
            'target_niche' => 'futebol',
            'channel_handle' => '@'.$this->faker->userName(),
            'blacklisted' => false,
        ];
    }
}
