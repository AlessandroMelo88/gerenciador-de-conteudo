<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Tests\TestCase;

final class AuthenticatedRootTest extends TestCase
{
    use DatabaseTransactions;

    public function test_authenticated_user_is_redirected_to_panel(): void
    {
        $user = User::factory()->create();

        $this->actingAs($user)
            ->get('/')
            ->assertRedirect('/painel');
    }
}
