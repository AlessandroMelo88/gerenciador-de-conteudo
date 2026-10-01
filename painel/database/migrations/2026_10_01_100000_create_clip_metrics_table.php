<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Histórico de visualizações dos clips publicados (etapa 2 do plano "longo por canal").
 *
 * O coletor do clip-processor (`src/metrics_collector.py`) grava UMA linha por clip por coleta:
 * a tabela é um histórico, nunca é atualizada. Daí saem "views nas primeiras 24 h / aos 7 dias"
 * por formato e por canal-fonte.
 *
 * FK com ON DELETE CASCADE de propósito: as FKs de generated_clips no projeto não têm cascade
 * (apagar `source_videos` com clips falha por FK), mas aqui o filho é só medição descartável.
 * Com o cascade, apagar um clip leva as métricas junto e nunca falha por causa delas.
 *
 * Idempotente (`hasTable`), no estilo das outras migrations do projeto. Compatível com
 * PostgreSQL e MySQL (só tipos portáveis do Schema Builder).
 */
return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('clip_metrics')) {
            return;
        }

        Schema::create('clip_metrics', function (Blueprint $table) {
            $table->id();
            $table->foreignId('generated_clip_id')->constrained('generated_clips')->cascadeOnDelete();
            $table->timestamp('collected_at')->index();
            $table->unsignedBigInteger('views');
            $table->unsignedBigInteger('likes')->nullable();
            $table->unsignedBigInteger('comments')->nullable();

            // Última coleta de um clip e histórico dele em ordem de tempo.
            $table->index(['generated_clip_id', 'collected_at'], 'clip_metrics_clip_collected_idx');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('clip_metrics');
    }
};
