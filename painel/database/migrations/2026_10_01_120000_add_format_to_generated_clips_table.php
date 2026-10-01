<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Formato do clip (`curto` | `longo`), fonte da verdade quando a mesma fonte gera os dois (modo `both`).
 * Nulo = herda de source_videos.format (clips antigos): o código lê COALESCE(gc.format, sv.format).
 */
return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('generated_clips') && !Schema::hasColumn('generated_clips', 'format')) {
            Schema::table('generated_clips', function (Blueprint $table) {
                $table->string('format', 20)->nullable();
            });
        }
    }

    public function down(): void
    {
        if (Schema::hasTable('generated_clips') && Schema::hasColumn('generated_clips', 'format')) {
            Schema::table('generated_clips', function (Blueprint $table) {
                $table->dropColumn('format');
            });
        }
    }
};
