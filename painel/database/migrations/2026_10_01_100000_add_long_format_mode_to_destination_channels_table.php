<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     * Valores: auto (duração da fonte decide) | short_only | both (Shorts + um longo).
     */
    public function up(): void
    {
        Schema::table('destination_channels', function (Blueprint $table) {
            $table->string('long_format_mode', 20)->default('auto')->after('template_config');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('destination_channels', function (Blueprint $table) {
            $table->dropColumn('long_format_mode');
        });
    }
};
