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
        'freshness_days',
        'input_priority',
    ];

    protected $casts = [
        'active' => 'bool',
        'blacklisted' => 'bool',
        'freshness_days' => 'integer',
        'input_priority' => 'integer',
    ];

    /** Janelas de frescor aceitas: 1 = hoje/ontem (padrão da produção), 3 = últimos 3 dias. */
    public const FRESHNESS_OPTIONS = [1, 3];

    public const DEFAULT_FRESHNESS_DAYS = 1;

    public const INPUT_PRIORITY_MIN = -10;

    public const INPUT_PRIORITY_MAX = 10;
}
