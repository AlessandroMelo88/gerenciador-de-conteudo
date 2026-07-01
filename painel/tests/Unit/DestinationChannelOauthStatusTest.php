<?php

use App\Models\DestinationChannel;

it('returns expired when oauth_expired_flag is true', function () {
    $channel = new DestinationChannel(['slug' => 'x', 'oauth_expired_flag' => true]);
    $channel->oauth_expired_flag = true;
    expect($channel->oauth_status)->toBe('expired');
});

it('returns missing when no token file exists and flag is false', function () {
    $channel = new DestinationChannel(['slug' => 'nao-existe-jamais-slug', 'oauth_expired_flag' => false]);
    $channel->oauth_expired_flag = false;
    // Point token_dir para um path garantidamente inexistente durante o teste
    config(['services.clip_processor.token_dir' => '/tmp/does-not-exist-panel-test']);
    expect($channel->oauth_status)->toBe('missing');
});

it('returns authorized when token file exists and flag is false', function () {
    $dir = sys_get_temp_dir().'/panel-oauth-test';
    @mkdir($dir);
    $slug = 'authorized-slug';
    file_put_contents("{$dir}/token-{$slug}.json", '{}');
    config(['services.clip_processor.token_dir' => $dir]);

    $channel = new DestinationChannel(['slug' => $slug, 'oauth_expired_flag' => false]);
    $channel->oauth_expired_flag = false;
    expect($channel->oauth_status)->toBe('authorized');

    @unlink("{$dir}/token-{$slug}.json");
});
