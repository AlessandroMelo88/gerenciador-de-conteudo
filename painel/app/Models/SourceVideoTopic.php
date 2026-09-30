<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class SourceVideoTopic extends Model
{
    use HasFactory;

    protected $table = 'source_video_topics';

    protected $fillable = [
        'source_video_id',
        'position',
        'title',
        'start_seconds',
        'end_seconds',
        'first_segment_index',
        'last_segment_index',
        'transcript_text',
    ];

    protected $casts = [
        'source_video_id' => 'integer',
        'position' => 'integer',
        'start_seconds' => 'float',
        'end_seconds' => 'float',
        'first_segment_index' => 'integer',
        'last_segment_index' => 'integer',
    ];

    /** @return BelongsTo<SourceVideo, $this> */
    public function sourceVideo(): BelongsTo
    {
        return $this->belongsTo(SourceVideo::class, 'source_video_id');
    }
}
