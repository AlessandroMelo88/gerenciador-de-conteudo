<?php

use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;

uses(DatabaseTransactions::class);

it('syncs compiled prompt profiles idempotently', function () {
    $directory = sys_get_temp_dir().'/prompt-profiles-'.bin2hex(random_bytes(6));
    mkdir($directory, 0777, true);
    $file = $directory.'/sync-test.json';
    $payload = [
        'slug' => 'sync-test',
        'name' => 'Sync Test',
        'niche' => 'sync-test',
        'niche_aliases' => [],
        'active' => true,
        'selection_short_prompt' => 'Short selection',
        'selection_long_prompt' => 'Long selection',
        'metadata_short_prompt' => 'Short metadata',
        'metadata_long_prompt' => 'Long metadata',
        'thumbnail_prompt' => 'Literal thumbnail',
    ];

    try {
        file_put_contents($file, json_encode($payload, JSON_THROW_ON_ERROR));
        $this->artisan('prompts:sync', ['--path' => $directory])->assertSuccessful();

        $payload['selection_short_prompt'] = 'Updated short selection';
        file_put_contents($file, json_encode($payload, JSON_THROW_ON_ERROR));
        $this->artisan('prompts:sync', ['--path' => $directory])->assertSuccessful();

        expect(DB::table('prompt_profiles')->where('slug', 'sync-test')->value('selection_short_prompt'))
            ->toBe('Updated short selection');
    } finally {
        @unlink($file);
        @rmdir($directory);
    }
});

it('validates every compiled profile before writing any of them', function () {
    $directory = sys_get_temp_dir().'/prompt-profiles-invalid-'.bin2hex(random_bytes(6));
    mkdir($directory, 0777, true);
    $firstFile = $directory.'/a-valid.json';
    $invalidFile = $directory.'/b-invalid.json';
    $validPayload = [
        'slug' => 'must-not-be-inserted',
        'name' => 'Valid Profile',
        'niche' => 'valid-profile',
        'niche_aliases' => [],
        'active' => true,
        'selection_short_prompt' => 'Short selection',
        'selection_long_prompt' => 'Long selection',
        'metadata_short_prompt' => 'Short metadata',
        'metadata_long_prompt' => 'Long metadata',
        'thumbnail_prompt' => 'Literal thumbnail',
    ];
    $invalidPayload = [...$validPayload, 'slug' => 'invalid-profile', 'active' => 'false'];

    try {
        file_put_contents($firstFile, json_encode($validPayload, JSON_THROW_ON_ERROR));
        file_put_contents($invalidFile, json_encode($invalidPayload, JSON_THROW_ON_ERROR));

        $this->artisan('prompts:sync', ['--path' => $directory])->assertFailed();

        expect(DB::table('prompt_profiles')->where('slug', 'must-not-be-inserted')->exists())
            ->toBeFalse();
    } finally {
        @unlink($firstFile);
        @unlink($invalidFile);
        @rmdir($directory);
    }
});
