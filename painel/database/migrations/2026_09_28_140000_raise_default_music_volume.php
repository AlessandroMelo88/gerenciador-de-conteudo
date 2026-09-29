<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('media_assets') || ! Schema::hasColumn('media_assets', 'music_volume')) {
            return;
        }

        DB::table('media_assets')
            ->where('kind', 'music')
            ->where(function ($query) {
                $query->whereNull('music_volume')->orWhere('music_volume', 0.120);
            })
            ->update([
                'music_volume' => 0.240,
                'updated_at' => now(),
            ]);
    }

    public function down(): void
    {
        // Não rebaixa volumes definidos pelo operador após a aplicação desta migration.
    }
};
