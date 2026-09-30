<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/** Trecho de uma transcrição. Escrito só pelo indexador Python; o painel apenas lê. */
class TranscriptChunk extends Model
{
    public $timestamps = false;

    protected $fillable = [];

    protected $hidden = ['embedding', 'search_vector'];

    protected function casts(): array
    {
        return [
            'chunk_index' => 'integer',
            'start_seconds' => 'float',
            'end_seconds' => 'float',
            'token_estimate' => 'integer',
        ];
    }

    public function job(): BelongsTo
    {
        return $this->belongsTo(TranscriptionJob::class, 'job_id');
    }
}
