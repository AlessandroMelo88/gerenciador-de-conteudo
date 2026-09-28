<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

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
}
