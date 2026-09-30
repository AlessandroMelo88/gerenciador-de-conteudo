<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class TranscriptionJob extends Model
{
    protected $guarded = [];

    protected function casts(): array
    {
        return [
            'duration_seconds' => 'integer',
            'progress_percent' => 'integer',
        ];
    }

    public function chunks(): HasMany
    {
        return $this->hasMany(TranscriptChunk::class, 'job_id');
    }
}
