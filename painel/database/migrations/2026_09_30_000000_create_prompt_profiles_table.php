<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Perfis de prompt por camadas (geral + canal + alvo), compilados de prompts/*.yaml.
 * Sem seeds: a tabela nasce vazia e source_channels.prompt_profile_id é opcional —
 * NULL significa "usar os prompts padrão do clip-processor" (comportamento anterior).
 */
return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('prompt_profiles')) {
            Schema::create('prompt_profiles', function (Blueprint $table) {
                $table->id();
                $table->string('slug', 80)->unique();
                $table->string('name', 120);
                $table->string('niche', 80)->index();
                $table->jsonb('niche_aliases')->default('[]');
                $table->text('selection_short_prompt');
                $table->text('selection_long_prompt');
                $table->text('metadata_short_prompt');
                $table->text('metadata_long_prompt');
                $table->text('thumbnail_prompt');
                $table->boolean('active')->default(true);
                $table->timestampsTz();
            });
        }

        if (Schema::hasTable('source_channels') && ! Schema::hasColumn('source_channels', 'prompt_profile_id')) {
            Schema::table('source_channels', function (Blueprint $table) {
                $table->foreignId('prompt_profile_id')
                    ->nullable()
                    ->constrained('prompt_profiles')
                    ->nullOnDelete();
            });
        }
    }

    public function down(): void
    {
        if (Schema::hasTable('source_channels') && Schema::hasColumn('source_channels', 'prompt_profile_id')) {
            Schema::table('source_channels', function (Blueprint $table) {
                $table->dropForeign(['prompt_profile_id']);
                $table->dropColumn('prompt_profile_id');
            });
        }

        Schema::dropIfExists('prompt_profiles');
    }
};
