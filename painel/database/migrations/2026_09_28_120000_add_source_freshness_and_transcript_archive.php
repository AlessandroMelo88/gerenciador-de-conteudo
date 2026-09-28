<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('source_channels') && ! Schema::hasColumn('source_channels', 'freshness_days')) {
            Schema::table('source_channels', function (Blueprint $table) {
                // Preserva o comportamento atual; cada canal pode escolher 3 dias.
                $table->unsignedSmallInteger('freshness_days')->default(1500);
            });
        }

        if (Schema::hasTable('source_videos')) {
            Schema::table('source_videos', function (Blueprint $table) {
                if (! Schema::hasColumn('source_videos', 'transcript_data')) {
                    $table->json('transcript_data')->nullable();
                }
                if (! Schema::hasColumn('source_videos', 'transcript_text')) {
                    $table->longText('transcript_text')->nullable();
                }
            });
        }
    }

    public function down(): void
    {
        if (Schema::hasTable('source_videos')) {
            Schema::table('source_videos', function (Blueprint $table) {
                if (Schema::hasColumn('source_videos', 'transcript_data')) {
                    $table->dropColumn('transcript_data');
                }
                if (Schema::hasColumn('source_videos', 'transcript_text')) {
                    $table->dropColumn('transcript_text');
                }
            });
        }

        if (Schema::hasTable('source_channels') && Schema::hasColumn('source_channels', 'freshness_days')) {
            Schema::table('source_channels', function (Blueprint $table) {
                $table->dropColumn('freshness_days');
            });
        }
    }
};
