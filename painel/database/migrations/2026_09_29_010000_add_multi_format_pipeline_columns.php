<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('source_videos') && ! Schema::hasColumn('source_videos', 'generate_both_formats')) {
            Schema::table('source_videos', function (Blueprint $table) {
                $table->boolean('generate_both_formats')->default(false);
            });
        }

        if (Schema::hasTable('generated_clips') && ! Schema::hasColumn('generated_clips', 'format')) {
            Schema::table('generated_clips', function (Blueprint $table) {
                $table->string('format', 16)->nullable();
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

        if (Schema::hasTable('source_videos') && Schema::hasColumn('source_videos', 'generate_both_formats')) {
            Schema::table('source_videos', function (Blueprint $table) {
                $table->dropColumn('generate_both_formats');
            });
        }
    }
};
