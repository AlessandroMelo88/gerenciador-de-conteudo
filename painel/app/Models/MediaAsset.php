<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class MediaAsset extends Model
{
    use HasFactory;

    protected $table = 'media_assets';

    protected $fillable = [
        'kind',
        'name',
        'path',
        'destination_channel_id',
        'format',
        'duration_seconds',
        'music_volume',
        'priority',
        'active',
    ];

    protected $casts = [
        'destination_channel_id' => 'integer',
        'duration_seconds' => 'integer',
        'music_volume' => 'float',
        'priority' => 'integer',
        'active' => 'boolean',
    ];

    /** @return BelongsTo<DestinationChannel, $this> */
    public function destinationChannel(): BelongsTo
    {
        return $this->belongsTo(DestinationChannel::class);
    }
}
