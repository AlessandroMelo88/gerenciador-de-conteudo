<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Privacidade padrão do canal no upload: private | public.
     *
     * Default 'private' preserva o comportamento de hoje (YOUTUBE_PRIVACY_STATUS=private no
     * compose valia para todos os canais) até o operador decidir canal a canal.
     */
    public function up(): void
    {
        Schema::table('destination_channels', function (Blueprint $table) {
            $table->string('default_privacy', 20)->default('private')->after('long_format_mode');
        });
    }

    public function down(): void
    {
        Schema::table('destination_channels', function (Blueprint $table) {
            $table->dropColumn('default_privacy');
        });
    }
};
