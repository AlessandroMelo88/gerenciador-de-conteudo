<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class SourceVideo extends Model
{
    use HasFactory;

    protected $table = 'source_videos';

    public $timestamps = true;

    protected $fillable = [
        'youtube_video_id',
        'channel_id',
        'title',
        'published_at',
        'local_path',
        'transcript_path',
        'transcript_data',
        'transcript_text',
        'format',
        'generate_both_formats',
        'priority',
        'paused',
        'queue_position',
    ];

    protected $casts = [
        'published_at' => 'datetime',
        'paused' => 'boolean',
        'generate_both_formats' => 'boolean',
        'priority' => 'integer',
        'queue_position' => 'integer',
        'transcript_data' => 'array',
    ];

    /** @return BelongsTo<SourceChannel, $this> */
    public function sourceChannel(): BelongsTo
    {
        return $this->belongsTo(SourceChannel::class, 'channel_id');
    }

    /** @return HasMany<GeneratedClip, $this> */
    public function generatedClips(): HasMany
    {
        return $this->hasMany(GeneratedClip::class, 'source_video_id');
    }

    /** @return HasMany<SourceVideoTopic, $this> */
    public function topics(): HasMany
    {
        return $this->hasMany(SourceVideoTopic::class, 'source_video_id')->orderBy('position');
    }
}
