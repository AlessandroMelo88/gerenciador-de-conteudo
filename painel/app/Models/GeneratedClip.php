<?php

namespace App\Models;

use Database\Factories\GeneratedClipFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class GeneratedClip extends Model
{
    /** @use HasFactory<GeneratedClipFactory> */
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
        'start_time',
        'end_time',
        'youtube_video_id',
        'status',
        'privacy_status',
        'reason',
        'upload_error',
        'format',
    ];

    protected $casts = [
        'start_time' => 'float',
        'end_time' => 'float',
        'score' => 'int',
    ];

    public function sourceVideo()
    {
        return $this->belongsTo(SourceVideo::class);
    }

    /** @return BelongsTo<DestinationChannel, $this> */
    public function destinationChannel(): BelongsTo
    {
        return $this->belongsTo(DestinationChannel::class);
    }
}
