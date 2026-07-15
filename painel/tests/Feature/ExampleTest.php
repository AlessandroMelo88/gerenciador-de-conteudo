<?php

namespace Tests\Feature;

use Tests\TestCase;

class ExampleTest extends TestCase
{
    /**
     * A raiz do painel redireciona para /painel (decisão CONTEXT.md: "o painel
     * É o Canal de Cortes" — sem welcome page genérica).
     */
    public function test_the_application_redirects_root_to_painel(): void
    {
        $response = $this->get('/');

        $response->assertRedirect('/painel');
    }
}
