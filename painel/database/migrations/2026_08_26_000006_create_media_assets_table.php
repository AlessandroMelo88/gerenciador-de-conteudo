<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('media_assets', function (Blueprint $table) {
            $table->id();
            $table->string('kind', 16);
            $table->string('name', 120);
            $table->string('path', 1024);
            $table->foreignId('destination_channel_id')
                ->nullable()
                ->constrained('destination_channels')
                ->nullOnDelete();
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
