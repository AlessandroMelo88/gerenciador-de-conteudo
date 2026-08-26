<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Permite adotar um volume PostgreSQL já inicializado pelo bootstrap SQL anterior.
        if (Schema::hasTable('destination_channels')) {
            return;
        }

        Schema::create('destination_channels', function (Blueprint $table) {
            $table->id();
            $table->string('slug', 50)->unique();
            $table->string('name', 120);
            $table->string('niche', 50);
            $table->string('youtube_channel_id', 64)->unique();
            $table->text('credit_template')->nullable();
            $table->boolean('active')->default(true);
            $table->boolean('oauth_expired_flag')->default(false);
            $table->timestampTz('created_at')->useCurrent();
            $table->timestampTz('updated_at')->useCurrent();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('destination_channels');
    }
};
