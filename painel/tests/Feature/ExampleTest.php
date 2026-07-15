<?php

namespace Tests\Feature;

use App\Models\User;
use Tests\TestCase;

class ExampleTest extends TestCase
{
    /**
     * A raiz do painel redireciona pro painel se estiver logado, ou pro login
     * se não estiver (decisão CONTEXT.md: "o painel É o Canal de Cortes" —
     * sem welcome page genérica).
     */
    public function test_root_redirects_to_login_when_guest(): void
    {
        $response = $this->get('/');

        $response->assertRedirect('/login');
    }

    public function test_root_redirects_to_painel_when_authenticated(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get('/');

        $response->assertRedirect('/painel');
    }
}
