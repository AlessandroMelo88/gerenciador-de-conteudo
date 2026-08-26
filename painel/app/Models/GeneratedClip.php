<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class GeneratedClip extends Model
{
    use HasFactory;

    protected $table = 'generated_clips';

    public $timestamps = true;

    protected $fillable = [
        'source_video_id',
        'destination_channel_id',
        'clip_path',
        'thumbnail_path',
        'title',
        'description',
        'tags',
        'score',
        'reason',
        'start_time',
        'end_time',
        'youtube_video_id',
        'scheduled_for',
        'upload_error',
    ];

    protected $casts = [
        'start_time' => 'float',
        'end_time' => 'float',
        'score' => 'float',
        'published_at' => 'datetime',
        'scheduled_for' => 'datetime',
    ];

    /** @return BelongsTo<SourceVideo, $this> */
    public function sourceVideo(): BelongsTo
    {
        return $this->belongsTo(SourceVideo::class);
    }

    /** @return BelongsTo<DestinationChannel, $this> */
    public function destinationChannel(): BelongsTo
    {
        return $this->belongsTo(DestinationChannel::class);
    }
}
