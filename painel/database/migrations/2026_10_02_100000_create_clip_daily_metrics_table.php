<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Retenção diária dos clips publicados (SPEC-001, etapa 1 de 3).
 *
 * Grão clip × dia, diferente da `clip_metrics`: aquela é snapshot append-only do contador
 * cumulativo (videos.list part=statistics); esta é o relatório da YouTube Analytics API por dia,
 * e o YouTube REVISA o número de um dia depois de fechá-lo — daí o único em
 * (generated_clip_id, date) e o upsert do lado do coletor.
 *
 * `average_view_percentage` é a nota de retenção: a única métrica que mede o que o selector de
 * fato decide, que é se o TRECHO escolhido é bom. As etapas 2 e 3 consomem essa coluna.
 *
 * FK com ON DELETE CASCADE pelo mesmo motivo da `clip_metrics`: medição é filho descartável, e
 * apagar um clip nunca pode falhar por causa dela.
 *
 * Idempotente (`hasTable`), como as outras migrations do projeto. Só tipos portáveis do Schema
 * Builder, para valer igual em PostgreSQL e MySQL.
 */
return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('clip_daily_metrics')) {
            return;
        }

        Schema::create('clip_daily_metrics', function (Blueprint $table) {
            $table->id();
            $table->foreignId('generated_clip_id')->constrained('generated_clips')->cascadeOnDelete();
            $table->date('date');
            $table->unsignedBigInteger('views')->default(0);
            $table->unsignedBigInteger('estimated_minutes_watched')->default(0);
            $table->unsignedInteger('average_view_duration')->default(0);
            $table->decimal('average_view_percentage', 5, 2)->default(0);
            $table->unsignedBigInteger('likes')->nullable();
            $table->unsignedBigInteger('comments')->nullable();
            $table->unsignedBigInteger('shares')->nullable();
            $table->integer('subscribers_gained')->nullable();

            $table->unique(['generated_clip_id', 'date'], 'clip_daily_metrics_clip_date_uniq');
            $table->index('date', 'clip_daily_metrics_date_idx');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('clip_daily_metrics');
    }
};
