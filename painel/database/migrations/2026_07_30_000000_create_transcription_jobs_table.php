<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * "Transcrição Local": ferramenta avulsa do operador para transcrever uma URL do
     * YouTube via whisper-cpp local no clip-processor, sem consumir cota do YouTube nem
     * entrar na fila de aprovação de clips (source_videos/generated_clips). Tabela isolada,
     * fonte única de verdade do progresso — persistido aqui (não em memória/Redis) para
     * sobreviver a reload/saída da página do operador.
     */
    public function up(): void
    {
        Schema::create('transcription_jobs', function (Blueprint $table) {
            $table->id();
            $table->string('youtube_url', 500);
            $table->enum('status', ['pending', 'downloading', 'transcribing', 'done', 'failed'])
                ->default('pending');
            $table->unsignedTinyInteger('progress_percent')->default(0);
            $table->string('srt_path')->nullable();
            $table->text('error_message')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('transcription_jobs');
    }
};
