<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Biblioteca de mídia por canal (origem: release/rico, adaptada).
 *
 * Cada linha é uma intro, um encerramento ou uma trilha de fundo associada a um canal de
 * destino, opcionalmente restrita a um formato (curto/longo). Só guarda o caminho relativo
 * ao disco `branding`; o arquivo em si nunca vai para o repositório.
 *
 * Idempotente: se a tabela já existir (ambiente que recebeu a criação por outro caminho), não
 * faz nada. A FK para destination_channels só é criada quando a tabela existe.
 */
return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('media_assets')) {
            return;
        }

        $hasDestinations = Schema::hasTable('destination_channels');

        Schema::create('media_assets', function (Blueprint $table) use ($hasDestinations) {
            $table->id();
            $table->string('kind', 16);
            $table->string('name', 120);
            $table->string('path', 1024);
            if ($hasDestinations) {
                $table->foreignId('destination_channel_id')
                    ->nullable()
                    ->constrained('destination_channels')
                    ->nullOnDelete();
            } else {
                $table->unsignedBigInteger('destination_channel_id')->nullable();
            }
            $table->string('format', 10)->nullable();
            $table->unsignedSmallInteger('duration_seconds')->nullable();
            $table->decimal('music_volume', 4, 3)->nullable();
            $table->unsignedInteger('priority')->default(0);
            $table->boolean('active')->default(true);
            $table->timestampsTz();

            $table->index(['kind', 'active'], 'media_assets_kind_active_idx');
            $table->index(
                ['destination_channel_id', 'kind', 'format'],
                'media_assets_scope_idx',
            );
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('media_assets');
    }
};
