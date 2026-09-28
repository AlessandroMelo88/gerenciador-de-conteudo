<?php

// deploy.sh põe o painel em `artisan down` do rsync até o restart do php.

afterEach(fn () => app()->maintenanceMode()->deactivate());

it('em manutenção o painel mostra a página de atualização', function () {
    app()->maintenanceMode()->activate([]);

    $this->get('/login')
        ->assertStatus(503)
        ->assertSee('Atualizando o painel');
});

it('em manutenção evento do pipeline e webhook do Telegram continuam atendidos', function () {
    app()->maintenanceMode()->activate([]);

    expect($this->postJson('/internal/pipeline-event', [])->status())->not->toBe(503);
    expect($this->postJson('/telegramcanal', [])->status())->not->toBe(503);
});

it('fora da manutenção o login responde normal', function () {
    $this->get('/login')->assertOk();
});
