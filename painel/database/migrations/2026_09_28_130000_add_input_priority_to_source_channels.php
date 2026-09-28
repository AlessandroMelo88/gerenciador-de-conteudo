<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('source_channels') || Schema::hasColumn('source_channels', 'input_priority')) {
            return;
        }

        Schema::table('source_channels', function (Blueprint $table) {
            $table->smallInteger('input_priority')->default(0);
        });
    }

    public function down(): void
    {
        if (! Schema::hasTable('source_channels') || ! Schema::hasColumn('source_channels', 'input_priority')) {
            return;
        }

        Schema::table('source_channels', function (Blueprint $table) {
            $table->dropColumn('input_priority');
        });
    }
};
