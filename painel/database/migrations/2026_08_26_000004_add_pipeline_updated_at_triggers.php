<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    private const TABLES = [
        'source_videos',
        'destination_channels',
        'generated_clips',
    ];

    public function up(): void
    {
        if (DB::getDriverName() !== 'pgsql') {
            return;
        }

        DB::unprepared(<<<'SQL'
            CREATE OR REPLACE FUNCTION touch_updated_at()
            RETURNS TRIGGER
            LANGUAGE plpgsql
            AS $function$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $function$
        SQL);

        foreach (self::TABLES as $table) {
            DB::unprepared("DROP TRIGGER IF EXISTS {$table}_touch_updated_at ON {$table}");
            DB::unprepared("CREATE TRIGGER {$table}_touch_updated_at
                BEFORE UPDATE ON {$table}
                FOR EACH ROW EXECUTE FUNCTION touch_updated_at()");
        }
    }

    public function down(): void
    {
        if (DB::getDriverName() !== 'pgsql') {
            return;
        }

        foreach (self::TABLES as $table) {
            DB::unprepared("DROP TRIGGER IF EXISTS {$table}_touch_updated_at ON {$table}");
        }

        DB::unprepared('DROP FUNCTION IF EXISTS touch_updated_at()');
    }
};
