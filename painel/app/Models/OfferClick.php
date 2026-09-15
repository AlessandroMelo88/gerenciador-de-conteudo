<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class OfferClick extends Model
{
    // Tabela só tem created_at (log append-only).
    public const UPDATED_AT = null;

    protected $fillable = [
        'offer_id',
        'channel',
        'ip_hash',
        'user_agent',
        'referer',
    ];

    public function offer(): BelongsTo
    {
        return $this->belongsTo(Offer::class);
    }
}
