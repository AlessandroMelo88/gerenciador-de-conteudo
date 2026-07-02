<?php

namespace Tests\Feature;

// use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ExampleTest extends TestCase
{
    /**
     * A raiz do painel redireciona para /admin (decisão CONTEXT.md: "o painel
     * É o Canal de Cortes" — sem welcome page genérica).
     */
    public function test_the_application_redirects_root_to_admin_panel(): void
    {
        $response = $this->get('/');

        $response->assertRedirect('/admin');
    }
}
