<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    /**
     * Status `paused` para o botão de pausar da aba Transcrições.
     *
     * O `enum()` da migration original vira coisas diferentes em cada banco: CHECK
     * constraint no PostgreSQL e ENUM nativo no MySQL. Por isso SQL por driver.
     */
    private const ANTES = ['pending', 'downloading', 'transcribing', 'done', 'failed'];

    private const DEPOIS = ['pending', 'downloading', 'transcribing', 'paused', 'done', 'failed'];

    public function up(): void
    {
        $this->trocar(self::DEPOIS);
    }

    public function down(): void
    {
        DB::table('transcription_jobs')->where('status', 'paused')->update(['status' => 'failed']);
        $this->trocar(self::ANTES);
    }

    private function trocar(array $status): void
    {
        $lista = "'".implode("', '", $status)."'";

        $driver = DB::getDriverName();

        if ($driver === 'pgsql') {
            DB::statement('ALTER TABLE transcription_jobs DROP CONSTRAINT IF EXISTS transcription_jobs_status_check');
            DB::statement("ALTER TABLE transcription_jobs ADD CONSTRAINT transcription_jobs_status_check CHECK (status IN ({$lista}))");
        } elseif (in_array($driver, ['mysql', 'mariadb'], true)) {
            DB::statement("ALTER TABLE transcription_jobs MODIFY status ENUM({$lista}) NOT NULL DEFAULT 'pending'");
        }
        // sqlite: sem restrição de valores a manter
    }
};
