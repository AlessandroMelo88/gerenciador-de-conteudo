<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Permite adotar um volume PostgreSQL já inicializado pelo bootstrap SQL anterior.
        if (Schema::hasTable('source_videos')) {
            return;
        }

        Schema::create('source_videos', function (Blueprint $table) {
            $table->id();
            $table->string('youtube_video_id', 64)->unique();
            $table->foreignId('channel_id')->constrained('source_channels');
            $table->string('title', 500)->nullable();
            $table->timestampTz('published_at')->nullable();
            $table->enum('status', [
                'pending',
                'downloading',
                'downloaded',
                'transcribing',
                'selecting',
                'cutting',
                'publishing',
                'published',
                'failed',
            ])->default('pending');
            $table->string('local_path', 1024)->nullable();
            $table->string('transcript_path', 500)->nullable();
            $table->enum('format', ['curto', 'longo'])->default('curto');
            $table->integer('priority')->default(0);
            $table->boolean('paused')->default(false);
            $table->integer('queue_position')->nullable();
            $table->timestampTz('created_at')->useCurrent();
            $table->timestampTz('updated_at')->useCurrent();

            $table->index(['status', 'format'], 'source_videos_status_format_idx');
            $table->index('published_at', 'source_videos_published_at_idx');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('source_videos');
    }
};
