<?php

namespace App\Support;

use Illuminate\Support\Facades\DB;
use RuntimeException;

class PromptProfileImporter
{
    private const REQUIRED_FIELDS = [
        'slug',
        'name',
        'niche',
        'niche_aliases',
        'active',
        'selection_short_prompt',
        'selection_long_prompt',
        'metadata_short_prompt',
        'metadata_long_prompt',
        'thumbnail_prompt',
    ];

    public function syncDirectory(string $directory): int
    {
        if (! is_dir($directory)) {
            throw new RuntimeException("Diretório de prompts compilados não encontrado: {$directory}");
        }

        $files = glob(rtrim($directory, DIRECTORY_SEPARATOR).DIRECTORY_SEPARATOR.'*.json') ?: [];
        if ($files === []) {
            throw new RuntimeException("Nenhum perfil JSON encontrado em: {$directory}");
        }

        $profiles = [];
        $seenSlugs = [];
        foreach ($files as $file) {
            $profile = $this->readProfile($file);
            if (isset($seenSlugs[$profile['slug']])) {
                throw new RuntimeException("Slug duplicado {$profile['slug']} nos prompts compilados.");
            }

            $seenSlugs[$profile['slug']] = true;
            $profiles[] = $profile;
        }

        $synced = 0;
        DB::transaction(function () use ($profiles, &$synced): void {
            foreach ($profiles as $profile) {
                $now = now();
                $values = [
                    'name' => $profile['name'],
                    'niche' => $profile['niche'],
                    'niche_aliases' => json_encode(
                        $profile['niche_aliases'],
                        JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE,
                    ),
                    'active' => $profile['active'],
                    'selection_short_prompt' => $profile['selection_short_prompt'],
                    'selection_long_prompt' => $profile['selection_long_prompt'],
                    'metadata_short_prompt' => $profile['metadata_short_prompt'],
                    'metadata_long_prompt' => $profile['metadata_long_prompt'],
                    'thumbnail_prompt' => $profile['thumbnail_prompt'],
                    'updated_at' => $now,
                ];

                if (! DB::table('prompt_profiles')->where('slug', $profile['slug'])->exists()) {
                    $values['created_at'] = $now;
                }

                DB::table('prompt_profiles')->updateOrInsert(['slug' => $profile['slug']], $values);
                $synced++;
            }
        });

        return $synced;
    }

    /** @return array<string, bool|string|list<string>> */
    private function readProfile(string $file): array
    {
        $payload = json_decode((string) file_get_contents($file), true, 512, JSON_THROW_ON_ERROR);
        if (! is_array($payload)) {
            throw new RuntimeException("Perfil JSON inválido: {$file}");
        }

        foreach (self::REQUIRED_FIELDS as $field) {
            if (! array_key_exists($field, $payload)) {
                throw new RuntimeException("Campo obrigatório {$field} ausente em {$file}");
            }
        }

        foreach ([
            'slug',
            'name',
            'niche',
            'selection_short_prompt',
            'selection_long_prompt',
            'metadata_short_prompt',
            'metadata_long_prompt',
            'thumbnail_prompt',
        ] as $field) {
            if (! is_string($payload[$field]) || trim($payload[$field]) === '') {
                throw new RuntimeException("Campo {$field} inválido em {$file}");
            }
        }

        $slug = trim($payload['slug']);
        if (! preg_match('/^[a-z0-9][a-z0-9_-]*$/', $slug)) {
            throw new RuntimeException("Slug inválido em {$file}");
        }

        if (! is_array($payload['niche_aliases']) || ! array_is_list($payload['niche_aliases'])) {
            throw new RuntimeException("niche_aliases precisa ser uma lista em {$file}");
        }
        foreach ($payload['niche_aliases'] as $alias) {
            if (! is_string($alias) || trim($alias) === '') {
                throw new RuntimeException("Cada alias precisa ser um texto não vazio em {$file}");
            }
        }

        if (! is_bool($payload['active'])) {
            throw new RuntimeException("Campo active precisa ser booleano em {$file}");
        }

        return [
            'slug' => $slug,
            'name' => trim($payload['name']),
            'niche' => trim($payload['niche']),
            'niche_aliases' => array_map('trim', $payload['niche_aliases']),
            'active' => $payload['active'],
            'selection_short_prompt' => trim($payload['selection_short_prompt']),
            'selection_long_prompt' => trim($payload['selection_long_prompt']),
            'metadata_short_prompt' => trim($payload['metadata_short_prompt']),
            'metadata_long_prompt' => trim($payload['metadata_long_prompt']),
            'thumbnail_prompt' => trim($payload['thumbnail_prompt']),
        ];
    }
}
