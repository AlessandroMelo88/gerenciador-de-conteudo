<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (!Schema::hasTable('destination_channels')) {
            Schema::create('destination_channels', function (Blueprint $table) {
                $table->id();
                $table->string('slug', 50)->unique();
                $table->string('name', 120);
                $table->string('niche', 50);
                $table->string('youtube_channel_id', 50)->unique();
                $table->text('credit_template')->nullable();
                $table->boolean('active')->default(true);
                $table->boolean('oauth_expired_flag')->default(false);
                $table->timestamps();
            });
        }

        if (!Schema::hasTable('source_channels')) {
            Schema::create('source_channels', function (Blueprint $table) {
                $table->id();
                $table->string('youtube_channel_id', 64)->unique();
                $table->string('channel_name', 255);
                $table->string('channel_handle', 100)->nullable();
                $table->string('target_niche', 50)->nullable();
                $table->boolean('blacklisted')->default(false);
                $table->string('rss_url', 512);
                $table->boolean('active')->default(true);
                $table->timestamp('created_at')->useCurrent();
            });
        }

        if (!Schema::hasTable('source_videos')) {
            Schema::create('source_videos', function (Blueprint $table) {
                $table->id();
                $table->string('youtube_video_id', 64)->unique();
                $table->unsignedBigInteger('channel_id');
                $table->string('title', 500)->nullable();
                $table->timestamp('published_at')->nullable();
                $table->string('status', 30)->default('pending');
                $table->integer('priority')->default(0);
                $table->boolean('paused')->default(false);
                $table->integer('queue_position')->nullable();
                $table->string('local_path', 1024)->nullable();
                $table->string('format', 20)->default('curto');
                $table->string('transcript_path', 500)->nullable();
                $table->timestamps();
            });
        }

        if (!Schema::hasTable('generated_clips')) {
            Schema::create('generated_clips', function (Blueprint $table) {
                $table->id();
                $table->unsignedBigInteger('source_video_id');
                $table->string('clip_path', 1024)->nullable();
                $table->string('thumbnail_path', 1024)->nullable();
                $table->string('title', 200)->nullable();
                $table->text('description')->nullable();
                $table->text('tags')->nullable();
                $table->integer('score')->nullable();
                $table->float('start_time')->nullable();
                $table->float('end_time')->nullable();
                $table->string('youtube_video_id', 64)->nullable();
                $table->string('status', 30)->default('pending');
                $table->text('rejection_reason')->nullable();
                $table->unsignedBigInteger('destination_channel_id')->nullable();
                $table->timestamp('scheduled_at')->nullable();
                $table->timestamp('published_at')->nullable();
                $table->timestamps();
            });
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('generated_clips');
        Schema::dropIfExists('source_videos');
        Schema::dropIfExists('source_channels');
        Schema::dropIfExists('destination_channels');
    }
};
