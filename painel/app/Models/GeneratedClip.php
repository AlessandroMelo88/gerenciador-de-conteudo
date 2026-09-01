<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

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
        'start_time',
        'end_time',
        'youtube_video_id',
        'status',
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

    public function destinationChannel()
    {
        return $this->belongsTo(DestinationChannel::class);
    }
}
