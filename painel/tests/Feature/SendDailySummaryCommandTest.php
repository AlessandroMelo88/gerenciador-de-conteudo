<?php

namespace Tests\Feature;

use App\Models\GeneratedClip;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

final class SendDailySummaryCommandTest extends TestCase
{
    use DatabaseTransactions;

    protected function setUp(): void
    {
        parent::setUp();

        Http::fake([
            '*api.telegram.org*' => Http::response(['ok' => true, 'result' => ['message_id' => 1]], 200),
        ]);
    }

    public function test_no_summary_is_sent_without_pending_clips(): void
    {
        $this->artisan('painel:daily-summary')->assertSuccessful();

        Http::assertNothingSent();
    }

    public function test_summary_contains_the_pending_clip_count(): void
    {
        GeneratedClip::factory()->create(['status' => 'pending']);

        $this->artisan('painel:daily-summary')->assertSuccessful();

        Http::assertSent(fn ($request) => str_contains($request['text'] ?? '', '1 clip(s)'));
    }
}
