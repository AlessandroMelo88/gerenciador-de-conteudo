<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class Offer extends Model
{
    use HasFactory;

    public const NETWORKS = ['hotmart', 'eduzz', 'kiwify', 'monetizze', 'amazon', 'mercadolivre', 'shopee', 'awin', 'manual'];

    public const STATUSES = ['draft', 'approved', 'rejected', 'archived'];

    public const AI_PROVIDERS = ['anthropic', 'groq', 'claude-local', 'manual'];

    public const CHANNELS = ['telegram', 'youtube', 'blog', 'bio', 'instagram', 'tiktok', 'outro'];

    /** Campos de conteúdo que o worker pode enviar/atualizar (status nunca vem do cliente). */
    public const CONTENT_FIELDS = [
        'niche', 'title', 'description', 'product_url', 'affiliate_url', 'image_url',
        'price_cents', 'currency', 'commission_percent', 'cta_text', 'copy_short',
        'copy_long', 'ai_provider',
    ];

    protected $fillable = [
        'network', 'external_id', 'niche', 'title', 'description', 'product_url',
        'affiliate_url', 'slug', 'image_url', 'price_cents', 'currency',
        'commission_percent', 'cta_text', 'copy_short', 'copy_long', 'ai_provider',
        'status', 'approved_at', 'telegram_posted_at',
    ];

    protected $attributes = [
        'status' => 'draft',
        'currency' => 'BRL',
        'clicks_count' => 0,
    ];

    protected function casts(): array
    {
        return [
            'price_cents' => 'integer',
            'commission_percent' => 'decimal:2',
            'clicks_count' => 'integer',
            'approved_at' => 'datetime',
            'telegram_posted_at' => 'datetime',
        ];
    }

    protected static function booted(): void
    {
        static::creating(function (Offer $offer) {
            if (empty($offer->slug)) {
                $offer->slug = static::generateSlug();
            }
        });
    }

    /** Slug curto e aleatório (8 chars base62), único na tabela. */
    public static function generateSlug(): string
    {
        do {
            $slug = Str::random(8);
        } while (static::query()->where('slug', $slug)->exists());

        return $slug;
    }

    /** Só http/https — bloqueia javascript:, data: etc. (open redirect / XSS). */
    public static function isSafeUrl(?string $url): bool
    {
        if (! is_string($url) || $url === '') {
            return false;
        }

        $scheme = strtolower((string) parse_url($url, PHP_URL_SCHEME));

        return in_array($scheme, ['http', 'https'], true)
            && filter_var($url, FILTER_VALIDATE_URL) !== false;
    }

    public function trackingUrl(): string
    {
        return url('/o/'.$this->slug);
    }

    public function clicks(): HasMany
    {
        return $this->hasMany(OfferClick::class);
    }
}
