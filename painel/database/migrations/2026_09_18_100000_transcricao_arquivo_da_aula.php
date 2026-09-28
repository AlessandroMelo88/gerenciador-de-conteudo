<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Arquivo da aula guardado junto com a transcrição, para o botão "Baixar aula".
     * Caminho relativo ao disco `conteudo-cursos` (ex.: `aulas/12.mp4`); o worker do
     * Mac grava a mesma árvore no Mac e em /mnt/videos/conteudo-cursos na A1.
     */
    public function up(): void
    {
        Schema::table('transcription_jobs', function (Blueprint $table) {
            $table->string('media_path', 255)->nullable()->after('transcript_srt');
            $table->unsignedBigInteger('media_bytes')->nullable()->after('media_path');
        });
    }

    public function down(): void
    {
        Schema::table('transcription_jobs', function (Blueprint $table) {
            $table->dropColumn(['media_path', 'media_bytes']);
        });
    }
};
