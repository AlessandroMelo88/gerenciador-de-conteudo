<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
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
        'channel_handle',
        'blacklisted',
    ];

    protected $casts = [
        'active' => 'bool',
        'blacklisted' => 'bool',
        'created_at' => 'datetime',
    ];

    /** @return HasMany<SourceVideo, $this> */
    public function sourceVideos(): HasMany
    {
        return $this->hasMany(SourceVideo::class, 'channel_id');
    }
}
