<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Permite adotar um volume PostgreSQL já inicializado pelo bootstrap SQL anterior.
        if (Schema::hasTable('source_channels')) {
            return;
        }

        Schema::create('source_channels', function (Blueprint $table) {
            $table->id();
            $table->string('youtube_channel_id', 64)->unique();
            $table->string('channel_name', 255);
            $table->string('target_niche', 50)->nullable();
            $table->string('channel_handle', 100)->nullable();
            $table->boolean('blacklisted')->default(false);
            $table->string('rss_url', 512);
            $table->boolean('active')->default(true);
            $table->timestampTz('created_at')->useCurrent();

            $table->index('blacklisted', 'source_channels_blacklisted_idx');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('source_channels');
    }
};
