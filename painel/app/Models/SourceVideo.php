<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

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
        'status',
        'local_path',
        'priority',
        'paused',
        'queue_position',
    ];

    protected $casts = [
        'published_at' => 'datetime',
        'paused' => 'boolean',
        'priority' => 'integer',
        'queue_position' => 'integer',
    ];

    public function sourceChannel()
    {
        return $this->belongsTo(SourceChannel::class, 'channel_id');
    }

    public function generatedClips()
    {
        return $this->hasMany(GeneratedClip::class, 'source_video_id');
    }
}
