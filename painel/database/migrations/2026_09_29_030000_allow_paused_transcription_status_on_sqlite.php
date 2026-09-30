<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    private const BEFORE = ['pending', 'downloading', 'transcribing', 'done', 'failed'];

    public function up(): void
    {
        if (DB::getDriverName() !== 'sqlite' || ! Schema::hasTable('transcription_jobs')) {
            return;
        }

        Schema::table('transcription_jobs', function (Blueprint $table): void {
            $table->string('status', 30)->default('pending')->change();
        });
    }

    public function down(): void
    {
        if (DB::getDriverName() !== 'sqlite' || ! Schema::hasTable('transcription_jobs')) {
            return;
        }

        DB::table('transcription_jobs')->where('status', 'paused')->update(['status' => 'failed']);

        Schema::table('transcription_jobs', function (Blueprint $table): void {
            $table->enum('status', self::BEFORE)->default('pending')->change();
        });
    }
};
