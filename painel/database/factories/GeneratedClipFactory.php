<?php

namespace Database\Factories;

use App\Models\DestinationChannel;
use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use Illuminate\Database\Eloquent\Factories\Factory;

class GeneratedClipFactory extends Factory
{
    protected $model = GeneratedClip::class;

    public function definition(): array
    {
        return [
            'source_video_id' => SourceVideo::factory(),
            'destination_channel_id' => DestinationChannel::factory(),
            'clip_path' => '/app/videos/clips/'.$this->faker->uuid().'.mp4',
            'thumbnail_path' => '/app/videos/thumbnails/'.$this->faker->uuid().'.jpg',
            'title' => $this->faker->sentence(6),
            'description' => $this->faker->paragraph(),
            'tags' => 'futebol,cortes',
            'score' => 8,
            'start_time' => 10.5,
            'end_time' => 40.0,
            'youtube_video_id' => null,
            'status' => 'pending',
        ];
    }
}
