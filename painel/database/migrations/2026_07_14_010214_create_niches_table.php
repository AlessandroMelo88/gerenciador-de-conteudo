<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Nichos existiam só como valores soltos digitados nos selects de
     * source_channels.target_niche / destination_channels.niche (varchar, sem
     * validação). Esta tabela vira a fonte única de verdade: cada linha aqui
     * gera automaticamente uma opção nos selects e uma tab em Canais Fonte.
     */
    public function up(): void
    {
        Schema::create('niches', function (Blueprint $table) {
            $table->id();
            $table->string('slug', 50)->unique();
            $table->string('label', 100);
            $table->timestamps();
        });

        DB::table('niches')->insert([
            ['slug' => 'futebol', 'label' => 'Futebol', 'created_at' => now(), 'updated_at' => now()],
            ['slug' => 'podcast', 'label' => 'Podcast', 'created_at' => now(), 'updated_at' => now()],
        ]);
    }

    public function down(): void
    {
        Schema::dropIfExists('niches');
    }
};
