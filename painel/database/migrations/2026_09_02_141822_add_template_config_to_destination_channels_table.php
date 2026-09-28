<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('destination_channels', function (Blueprint $table) {
            $table->json('template_config')->nullable()->after('credit_template');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('destination_channels', function (Blueprint $table) {
            $table->dropColumn('template_config');
        });
    }
};
