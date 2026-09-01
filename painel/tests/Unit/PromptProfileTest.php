<?php

use App\Models\PromptProfile;
use Illuminate\Foundation\Testing\DatabaseTransactions;

uses(DatabaseTransactions::class);

it('does not resolve a profile from another niche', function () {
    $technologyProfileId = PromptProfile::query()
        ->where('slug', 'conteudo-inteligencia')
        ->value('id');

    expect(PromptProfile::resolveId($technologyProfileId, 'futebol'))->toBeNull();
});

it('resolves a profile through its niche alias', function () {
    $profileId = PromptProfile::query()
        ->where('slug', 'conteudo-inteligencia')
        ->value('id');

    expect(PromptProfile::resolveId(null, 'tecnologia'))->toBe($profileId);
});
