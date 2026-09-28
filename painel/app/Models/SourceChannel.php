<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class SourceChannel extends Model
{
    use HasFactory;

    protected $table = 'source_channels';

    public const UPDATED_AT = null;

    public $timestamps = true;

    protected $fillable = [
        'youtube_channel_id',
        'channel_name',
        'rss_url',
        'active',
        'target_niche',
        'prompt_profile_id',
        'channel_handle',
        'blacklisted',
        'freshness_days',
        'input_priority',
    ];

    protected $casts = [
        'active' => 'bool',
        'blacklisted' => 'bool',
        'freshness_days' => 'integer',
        'input_priority' => 'integer',
        'created_at' => 'datetime',
    ];

    /** @return BelongsTo<PromptProfile, $this> */
    public function promptProfile(): BelongsTo
    {
        return $this->belongsTo(PromptProfile::class, 'prompt_profile_id');
    }

    /** @return HasMany<SourceVideo, $this> */
    public function sourceVideos(): HasMany
    {
        return $this->hasMany(SourceVideo::class, 'channel_id');
    }
}
