<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

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
        'active',
        'oauth_expired_flag',
    ];

    protected $casts = [
        'active' => 'bool',
        'oauth_expired_flag' => 'bool',
    ];

    /** @return HasMany<GeneratedClip, $this> */
    public function generatedClips(): HasMany
    {
        return $this->hasMany(GeneratedClip::class, 'destination_channel_id');
    }

    /** @return HasMany<MediaAsset, $this> */
    public function mediaAssets(): HasMany
    {
        return $this->hasMany(MediaAsset::class, 'destination_channel_id');
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
