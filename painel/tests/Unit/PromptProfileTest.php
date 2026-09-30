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

it('does not apply the Hacker Libertario profile to generic technology niches', function () {
    expect(PromptProfile::resolveId(null, 'tecnologia'))->toBeNull();
    expect(PromptProfile::resolveId(null, 'linux'))->toBeNull();
});
