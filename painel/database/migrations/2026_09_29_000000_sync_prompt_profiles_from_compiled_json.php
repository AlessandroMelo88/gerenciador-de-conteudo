<?php

use App\Support\PromptProfileImporter;
use Illuminate\Database\Migrations\Migration;

return new class extends Migration
{
    public function up(): void
    {
        $directory = base_path('../prompts/compiled');

        // Sem os JSONs compilados (ex.: container sem o volume ./prompts) o sync é
        // adiado para `php artisan prompts:sync`; falhar aqui abortaria as migrations
        // de schema seguintes, das quais o clip-processor depende.
        if (! is_dir($directory) || (glob($directory.'/*.json') ?: []) === []) {
            return;
        }

        app(PromptProfileImporter::class)->syncDirectory($directory);
    }

    public function down(): void
    {
        // Prompt data is editable and can contain later user changes; do not restore stale text.
    }
};
