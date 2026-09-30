<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('source_videos')) {
            return;
        }

        Schema::table('source_videos', function (Blueprint $table) {
            if (! Schema::hasColumn('source_videos', 'topic_segmentation_status')) {
                $table->string('topic_segmentation_status', 20)->default('not_ready');
            }
            if (! Schema::hasColumn('source_videos', 'topic_segmentation_error')) {
                $table->text('topic_segmentation_error')->nullable();
            }
        });

        DB::table('source_videos')
            ->where('topic_segmentation_status', 'not_ready')
            ->where(function ($query) {
                $query->where(function ($query) {
                    $query->whereNotNull('transcript_text')->where('transcript_text', '<>', '');
                })->orWhereNotNull('transcript_data');
            })
            ->update(['topic_segmentation_status' => 'pending']);

        if (! Schema::hasTable('source_video_topics')) {
            Schema::create('source_video_topics', function (Blueprint $table) {
                $table->id();
                $table->foreignId('source_video_id')->constrained('source_videos');
                $table->unsignedInteger('position');
                $table->string('title', 500);
                $table->double('start_seconds');
                $table->double('end_seconds');
                $table->unsignedInteger('first_segment_index');
                $table->unsignedInteger('last_segment_index');
                $table->longText('transcript_text');
                $table->timestampsTz();

                // A unicidade também fornece o índice principal de leitura por vídeo/ordem.
                $table->unique(
                    ['source_video_id', 'position'],
                    'source_video_topics_video_position_unique'
                );
                $table->index(
                    ['source_video_id', 'first_segment_index'],
                    'source_video_topics_video_segment_idx'
                );
            });
        }

        $this->addCheckConstraintIfMissing(
            'source_video_topics_end_after_start_check',
            'end_seconds >= start_seconds'
        );
        $this->addCheckConstraintIfMissing(
            'source_video_topics_segment_order_check',
            'last_segment_index >= first_segment_index'
        );
    }

    public function down(): void
    {
        Schema::dropIfExists('source_video_topics');

        if (Schema::hasTable('source_videos')) {
            Schema::table('source_videos', function (Blueprint $table) {
                $columns = [];
                if (Schema::hasColumn('source_videos', 'topic_segmentation_status')) {
                    $columns[] = 'topic_segmentation_status';
                }
                if (Schema::hasColumn('source_videos', 'topic_segmentation_error')) {
                    $columns[] = 'topic_segmentation_error';
                }
                if ($columns !== []) {
                    $table->dropColumn($columns);
                }
            });
        }
    }

    private function addCheckConstraintIfMissing(string $name, string $expression): void
    {
        if (DB::getDriverName() !== 'pgsql' || ! Schema::hasTable('source_video_topics')) {
            return;
        }

        $exists = DB::selectOne(
            'SELECT 1 FROM pg_constraint '
            .'WHERE conrelid = ?::regclass AND conname = ?',
            ['source_video_topics', $name]
        );

        if ($exists === null) {
            DB::statement("ALTER TABLE source_video_topics ADD CONSTRAINT {$name} CHECK ({$expression})");
        }
    }
};
