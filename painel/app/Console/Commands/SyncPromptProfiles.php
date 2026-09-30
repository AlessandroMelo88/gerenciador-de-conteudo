<?php

namespace App\Console\Commands;

use App\Support\PromptProfileImporter;
use Illuminate\Console\Command;
use Throwable;

class SyncPromptProfiles extends Command
{
    protected $signature = 'prompts:sync {--path= : Diretório com os JSONs compilados}';

    protected $description = 'Aplica os perfis compilados em prompts/compiled ao banco do pipeline';

    public function handle(PromptProfileImporter $importer): int
    {
        $directory = $this->option('path') ?: base_path('../prompts/compiled');

        try {
            $synced = $importer->syncDirectory($directory);
        } catch (Throwable $error) {
            $this->error($error->getMessage());

            return self::FAILURE;
        }

        $this->info("{$synced} perfil(is) de prompt sincronizado(s). Canais e fontes não foram alterados.");

        return self::SUCCESS;
    }
}
