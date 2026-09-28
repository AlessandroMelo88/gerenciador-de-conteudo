<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * A transcrição deixa de ser "URL do YouTube → .srt que se perde" e vira base de
     * conhecimento: qualquer site que o yt-dlp aceite, executado pelo worker do Mac
     * (scripts/transcription_worker.py), com o texto guardado aqui para busca e leitura.
     *
     * `srt_path` fica para os jobs antigos, cujo .srt está em disco no servidor.
     */
    public function up(): void
    {
        Schema::table('transcription_jobs', function (Blueprint $table) {
            $table->renameColumn('youtube_url', 'source_url');
        });

        Schema::table('transcription_jobs', function (Blueprint $table) {
            $table->string('title', 500)->nullable()->after('source_url');
            $table->string('platform', 50)->nullable()->after('title');
            $table->unsignedInteger('duration_seconds')->nullable()->after('platform');
            $table->longText('transcript_text')->nullable()->after('srt_path');
            $table->longText('transcript_srt')->nullable()->after('transcript_text');
        });
    }

    public function down(): void
    {
        Schema::table('transcription_jobs', function (Blueprint $table) {
            $table->dropColumn(['title', 'platform', 'duration_seconds', 'transcript_text', 'transcript_srt']);
        });

        Schema::table('transcription_jobs', function (Blueprint $table) {
            $table->renameColumn('source_url', 'youtube_url');
        });
    }
};
