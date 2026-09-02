<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class DestinationChannel extends Model
{
    use HasFactory;

    protected $table = 'destination_channels';

    public $timestamps = true;

    protected $fillable = [
        'slug',
        'name',
        'niche',
        'youtube_channel_id',
        'credit_template',
        'template_config',
        'active',
        'oauth_expired_flag',
    ];

    protected $casts = [
        'active' => 'bool',
        'oauth_expired_flag' => 'bool',
        'template_config' => 'array',
    ];

    public static function defaultTemplateConfig(string $name, ?string $niche): array
    {
        $n = strtolower($niche ?? '');
        $isPolitica = str_contains($n, 'pol');
        $isFutebol = str_contains($n, 'fut');

        return [
            'headerTitle' => mb_strtoupper($name, 'UTF-8'),
            'headerBadge' => $isPolitica ? '🔴 DEBATE AO VIVO' : ($isFutebol ? '⚽ LANCE DECISIVO' : '🎙️ CORTES EXCLUSIVOS'),
            'accentColor' => $isPolitica ? '#E50914' : ($isFutebol ? '#10B981' : '#8B5CF6'),
            'bgStyle' => 'blur_dark',
            'subtitleColor' => '#facc15',
            'ctaText' => 'INSCREVA-SE NO CANAL',
        ];
    }

    protected static function booted(): void
    {
        static::creating(function (DestinationChannel $channel) {
            if (empty($channel->template_config)) {
                $channel->template_config = static::defaultTemplateConfig($channel->name ?? '', $channel->niche ?? '');
            }
        });
    }

    public function getEffectiveTemplateConfigAttribute(): array
    {
        return array_merge(
            static::defaultTemplateConfig($this->name ?? '', $this->niche ?? ''),
            $this->template_config ?? []
        );
    }

    /**
     * Contrato (definido em 08-VALIDATION.md / tests/Unit/DestinationChannelOauthStatusTest.php):
     *   'expired'    if oauth_expired_flag == TRUE
     *   'authorized' if oauth_expired_flag == FALSE AND token file exists
     *   'missing'    otherwise
     */
    public function getOauthStatusAttribute(): string
    {
        if ($this->oauth_expired_flag) {
            return 'expired';
        }

        $tokenDir = config('services.clip_processor.token_dir', base_path('../youtube'));
        $exists = file_exists("{$tokenDir}/token-{$this->slug}.json");

        return $exists ? 'authorized' : 'missing';
    }
}
