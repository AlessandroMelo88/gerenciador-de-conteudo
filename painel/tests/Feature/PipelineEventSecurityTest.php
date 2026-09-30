<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

final class PipelineEventSecurityTest extends TestCase
{
    use DatabaseTransactions;

    protected function setUp(): void
    {
        parent::setUp();

        config(['services.clip_processor.token' => 'test-internal-token']);
        Http::fake([
            '*api.telegram.org*' => Http::response(['ok' => true, 'result' => ['message_id' => 1]], 200),
        ]);
    }

    public function test_incomplete_payload_uses_safe_defaults(): void
    {
        $this->postJson('/internal/pipeline-event', [
            'event' => 'upload_published',
            'payload' => [],
        ], ['X-Internal-Token' => 'test-internal-token'])
            ->assertOk()
            ->assertJson(['ok' => true]);

        Http::assertSent(fn ($request) => str_contains($request['text'] ?? '', 'sem título'));
    }

    public function test_missing_internal_token_is_rejected(): void
    {
        config(['services.clip_processor.token' => null]);

        $this->postJson('/internal/pipeline-event', [
            'event' => 'daily_summary',
            'payload' => [],
        ])->assertUnauthorized();
    }
}
