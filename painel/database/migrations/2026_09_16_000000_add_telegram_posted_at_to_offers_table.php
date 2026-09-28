<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Marca quando a oferta foi divulgada no Telegram (offers:publish-telegram).
     * NULL = ainda não enviada. Coluna nullable: não exige default nem backfill,
     * portável MySQL 8.4 / PostgreSQL 17.
     */
    public function up(): void
    {
        Schema::table('offers', function (Blueprint $table) {
            $table->timestamp('telegram_posted_at')->nullable()->after('approved_at');
            $table->index(['status', 'telegram_posted_at']);
        });
    }

    public function down(): void
    {
        Schema::table('offers', function (Blueprint $table) {
            $table->dropIndex(['status', 'telegram_posted_at']);
            $table->dropColumn('telegram_posted_at');
        });
    }
};
