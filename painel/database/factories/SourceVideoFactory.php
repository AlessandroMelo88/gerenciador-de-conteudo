<?php

namespace Database\Factories;

use App\Models\SourceChannel;
use App\Models\SourceVideo;
use Illuminate\Database\Eloquent\Factories\Factory;

class SourceVideoFactory extends Factory
{
    protected $model = SourceVideo::class;

    public function definition(): array
    {
        return [
            'youtube_video_id' => $this->faker->unique()->regexify('[A-Za-z0-9_-]{11}'),
            'channel_id' => SourceChannel::factory(),
            'title' => $this->faker->sentence(),
            'published_at' => now(),
            'status' => 'pending',
            'local_path' => null,
        ];
    }
}
