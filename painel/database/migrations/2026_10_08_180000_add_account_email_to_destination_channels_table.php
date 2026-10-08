<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * E-mail da conta Google / YouTube vinculada ao canal.
     * Identifica em qual conta Google (ex: moneyintel@..., alessandrobm1988@gmail.com)
     * o canal de destino está hospedado e onde os tokens OAuth foram autorizados.
     */
    public function up(): void
    {
        if (Schema::hasTable('destination_channels') && ! Schema::hasColumn('destination_channels', 'account_email')) {
            Schema::table('destination_channels', function (Blueprint $table) {
                $table->string('account_email', 255)->nullable()->after('youtube_channel_id');
            });
        }
    }

    public function down(): void
    {
        if (Schema::hasTable('destination_channels') && Schema::hasColumn('destination_channels', 'account_email')) {
            Schema::table('destination_channels', function (Blueprint $table) {
                $table->dropColumn('account_email');
            });
        }
    }
};
