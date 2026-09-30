<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Frescor e prioridade por canal-fonte (origem: release/rico, adaptado).
 *
 * - `freshness_days`: quantos dias de idade um vídeo `pending` do canal ainda pode ter
 *   para entrar na janela de download. DEFAULT 1 = política atual ("hoje/ontem");
 *   o valor 1500 da release/rico foi rejeitado de propósito, pois liberaria o backlog antigo.
 * - `input_priority`: desempate entre canais na fila justa (-10..10, 0 = neutro).
 *
 * Idempotente: só adiciona a coluna que ainda não existe e ignora tabela ausente.
 */
return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('source_channels')) {
            return;
        }

        Schema::table('source_channels', function (Blueprint $table) {
            if (! Schema::hasColumn('source_channels', 'freshness_days')) {
                $table->unsignedSmallInteger('freshness_days')->default(1);
            }
            if (! Schema::hasColumn('source_channels', 'input_priority')) {
                $table->smallInteger('input_priority')->default(0);
            }
        });
    }

    public function down(): void
    {
        if (! Schema::hasTable('source_channels')) {
            return;
        }

        Schema::table('source_channels', function (Blueprint $table) {
            if (Schema::hasColumn('source_channels', 'freshness_days')) {
                $table->dropColumn('freshness_days');
            }
            if (Schema::hasColumn('source_channels', 'input_priority')) {
                $table->dropColumn('input_priority');
            }
        });
    }
};
