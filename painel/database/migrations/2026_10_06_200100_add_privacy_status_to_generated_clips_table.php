<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Privacidade escolhida na aprovação daquele clip: private | public.
     *
     * NULL significa "usa o padrão do canal destino" — é o caminho comum, em que o operador
     * clica Confirmar sem mexer em nada.
     */
    public function up(): void
    {
        Schema::table('generated_clips', function (Blueprint $table) {
            $table->string('privacy_status', 20)->nullable()->after('format');
        });
    }

    public function down(): void
    {
        Schema::table('generated_clips', function (Blueprint $table) {
            $table->dropColumn('privacy_status');
        });
    }
};
