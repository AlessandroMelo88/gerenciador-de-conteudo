<?php

namespace Database\Factories;

use App\Models\DestinationChannel;
use Illuminate\Database\Eloquent\Factories\Factory;

class DestinationChannelFactory extends Factory
{
    protected $model = DestinationChannel::class;

    public function definition(): array
    {
        $slug = $this->faker->unique()->slug(2);

        return [
            'slug' => $slug,
            'name' => $this->faker->company(),
            'niche' => 'futebol',
            'youtube_channel_id' => 'UC'.$this->faker->unique()->regexify('[A-Za-z0-9_-]{22}'),
            'credit_template' => 'Créditos: @{channel_handle}',
            'active' => true,
            'oauth_expired_flag' => false,
        ];
    }
}
