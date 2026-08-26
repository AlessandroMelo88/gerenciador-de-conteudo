<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Permite adotar um volume PostgreSQL já inicializado pelo bootstrap SQL anterior.
        if (Schema::hasTable('generated_clips')) {
            return;
        }

        Schema::create('generated_clips', function (Blueprint $table) {
            $table->id();
            $table->foreignId('source_video_id')->constrained('source_videos');
            $table->foreignId('destination_channel_id')->nullable()->constrained('destination_channels');
            $table->string('clip_path', 1024)->nullable();
            $table->string('thumbnail_path', 1024)->nullable();
            $table->string('title', 200)->nullable();
            $table->text('description')->nullable();
            $table->text('tags')->nullable();
            $table->double('score')->nullable();
            $table->text('reason')->nullable();
            $table->double('start_time')->nullable();
            $table->double('end_time')->nullable();
            $table->string('youtube_video_id', 64)->nullable();
            $table->timestampTz('published_at')->nullable();
            $table->timestampTz('scheduled_for')->nullable();
            $table->text('upload_error')->nullable();
            $table->enum('status', [
                'pending_cut',
                'pending',
                'cutting',
                'publishing',
                'published',
                'failed',
                'approved',
                'rejected',
            ])->default('pending_cut');
            $table->timestampTz('created_at')->useCurrent();
            $table->timestampTz('updated_at')->useCurrent();

            $table->index(['source_video_id', 'status'], 'generated_clips_source_video_status_idx');
            $table->index(['destination_channel_id', 'status'], 'generated_clips_destination_status_idx');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('generated_clips');
    }
};
