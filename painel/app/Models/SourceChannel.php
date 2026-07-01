<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class SourceChannel extends Model
{
    use HasFactory;

    protected $table = 'source_channels';

    public $timestamps = false;

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
    ];
}
