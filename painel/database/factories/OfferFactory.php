<?php

namespace Database\Factories;

use App\Models\Offer;
use Illuminate\Database\Eloquent\Factories\Factory;

class OfferFactory extends Factory
{
    protected $model = Offer::class;

    public function definition(): array
    {
        return [
            'network' => 'hotmart',
            'external_id' => 'EXT-'.$this->faker->unique()->bothify('??####??'),
            'niche' => 'futebol',
            'title' => $this->faker->sentence(4),
            'description' => $this->faker->paragraph(),
            'product_url' => 'https://example.com/produto/'.$this->faker->slug(2),
            'affiliate_url' => 'https://go.hotmart.com/'.$this->faker->bothify('?#?#?#?#'),
            'price_cents' => $this->faker->numberBetween(990, 49990),
            'currency' => 'BRL',
            'commission_percent' => 40.5,
            'cta_text' => 'Compre agora',
            'copy_short' => $this->faker->sentence(),
            'copy_long' => $this->faker->paragraph(),
            'ai_provider' => 'groq',
            'status' => 'draft',
        ];
    }

    public function approved(): static
    {
        return $this->state(fn () => ['status' => 'approved', 'approved_at' => now()]);
    }
}
