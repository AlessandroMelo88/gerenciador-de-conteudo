<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (Schema::hasTable('generated_clips') && !Schema::hasColumn('generated_clips', 'upload_error')) {
            Schema::table('generated_clips', function (Blueprint $table) {
                $table->text('upload_error')->nullable()->after('rejection_reason');
            });
        }
    }

    public function down(): void
    {
        if (Schema::hasTable('generated_clips') && Schema::hasColumn('generated_clips', 'upload_error')) {
            Schema::table('generated_clips', function (Blueprint $table) {
                $table->dropColumn('upload_error');
            });
        }
    }
};
