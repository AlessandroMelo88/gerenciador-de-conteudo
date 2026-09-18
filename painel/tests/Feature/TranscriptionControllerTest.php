<?php

use App\Models\TranscriptionJob;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

function transcricaoPronta(array $attrs = []): TranscriptionJob
{
    return TranscriptionJob::create(array_merge([
        'source_url' => 'https://vimeo.com/123',
        'status' => 'done',
        'progress_percent' => 100,
        'title' => 'Aula de funil',
        'platform' => 'Vimeo',
        'duration_seconds' => 3725,
        'transcript_text' => "Primeiro parágrafo.\n\nSegundo parágrafo.",
        'transcript_srt' => "1\n00:00:00,000 --> 00:00:02,000\nPrimeiro parágrafo.\n",
    ], $attrs));
}

it('enfileira o job como pending sem chamar o clip-processor', function () {
    Http::fake();

    $this->actingAs(User::factory()->create())
        ->post('/painel/transcricoes', ['url' => 'https://www.tiktok.com/@alguem/video/1'])
        ->assertRedirect();

    $job = TranscriptionJob::query()->latest('id')->first();
    expect($job->source_url)->toBe('https://www.tiktok.com/@alguem/video/1')
        ->and($job->status)->toBe('pending');
    Http::assertNothingSent();
});

it('recusa o que não é URL', function () {
    $this->actingAs(User::factory()->create())
        ->post('/painel/transcricoes', ['url' => 'nao é url'])
        ->assertSessionHasErrors('url');
});

it('busca pelo texto da transcrição, sem diferenciar maiúscula', function () {
    transcricaoPronta(['title' => 'Aula A', 'transcript_text' => 'fala sobre COPYWRITING persuasivo']);
    transcricaoPronta(['title' => 'Aula B', 'transcript_text' => 'fala sobre tráfego pago']);

    $this->actingAs(User::factory()->create())
        ->get('/painel/transcricoes?q=copywriting')
        ->assertInertia(fn ($page) => $page
            ->component('TranscricaoLocal')
            ->has('jobs.data', 1)
            ->where('jobs.data.0.title', 'Aula A'));
});

it('a lista não carrega o texto inteiro, só um trecho', function () {
    transcricaoPronta(['transcript_text' => str_repeat('palavra ', 500)]);

    $this->actingAs(User::factory()->create())
        ->get('/painel/transcricoes')
        ->assertInertia(fn ($page) => $page
            ->missing('jobs.data.0.transcript_text')
            ->missing('jobs.data.0.transcript_srt')
            ->where('jobs.data.0.excerpt', fn ($excerpt) => mb_strlen($excerpt) <= 300));
});

it('mostra a transcrição completa para leitura', function () {
    $job = transcricaoPronta();

    $this->actingAs(User::factory()->create())
        ->get("/painel/transcricoes/{$job->id}")
        ->assertInertia(fn ($page) => $page
            ->component('TranscricaoDetalhe')
            ->where('job.transcript_text', "Primeiro parágrafo.\n\nSegundo parágrafo."));
});

it('baixa .txt com o texto corrido', function () {
    $job = transcricaoPronta();

    $response = $this->actingAs(User::factory()->create())
        ->get("/painel/transcricoes/{$job->id}/download/txt");

    $response->assertOk();
    expect($response->streamedContent())->toBe("Primeiro parágrafo.\n\nSegundo parágrafo.");
    expect($response->headers->get('content-disposition'))->toContain('aula-de-funil.txt');
});

it('baixa .md com cabeçalho de fonte, plataforma e duração', function () {
    $job = transcricaoPronta();

    $md = $this->actingAs(User::factory()->create())
        ->get("/painel/transcricoes/{$job->id}/download/md")
        ->assertOk()
        ->streamedContent();

    expect($md)->toContain('# Aula de funil')
        ->toContain('https://vimeo.com/123')
        ->toContain('Vimeo')
        ->toContain('1h02min')
        ->toContain('Segundo parágrafo.');
});

it('baixa .srt guardado no banco', function () {
    $job = transcricaoPronta();

    $srt = $this->actingAs(User::factory()->create())
        ->get("/painel/transcricoes/{$job->id}/download/srt")
        ->assertOk()
        ->streamedContent();

    expect($srt)->toStartWith("1\n00:00:00,000");
});

it('não baixa o que ainda não terminou', function () {
    $job = transcricaoPronta(['status' => 'transcribing', 'transcript_text' => null]);

    $this->actingAs(User::factory()->create())
        ->get("/painel/transcricoes/{$job->id}/download/txt")
        ->assertNotFound();
});

it('formato desconhecido é 404', function () {
    $job = transcricaoPronta();

    $this->actingAs(User::factory()->create())
        ->get("/painel/transcricoes/{$job->id}/download/exe")
        ->assertNotFound();
});

it('exige login', function () {
    $job = transcricaoPronta();

    $this->get("/painel/transcricoes/{$job->id}")->assertRedirect();
});

it('pausa job que está na fila ou andando', function (string $status) {
    $job = transcricaoPronta(['status' => $status, 'progress_percent' => 40]);

    $this->actingAs(User::factory()->create())
        ->post("/painel/transcricoes/{$job->id}/pausar")
        ->assertRedirect();

    expect($job->fresh()->status)->toBe('paused')
        ->and($job->fresh()->progress_percent)->toBe(40);
})->with(['pending', 'downloading', 'transcribing']);

it('não pausa o que já terminou', function () {
    $job = transcricaoPronta();

    $this->actingAs(User::factory()->create())
        ->post("/painel/transcricoes/{$job->id}/pausar");

    expect($job->fresh()->status)->toBe('done');
});

it('retoma pausado ou falho voltando para a fila do zero', function (string $status) {
    $job = transcricaoPronta(['status' => $status, 'progress_percent' => 60, 'error_message' => 'x']);

    $this->actingAs(User::factory()->create())
        ->post("/painel/transcricoes/{$job->id}/retomar")
        ->assertRedirect();

    $job->refresh();
    expect($job->status)->toBe('pending')
        ->and($job->progress_percent)->toBe(0)
        ->and($job->error_message)->toBeNull();
})->with(['paused', 'failed']);

it('não retoma o que já terminou', function () {
    $job = transcricaoPronta();

    $this->actingAs(User::factory()->create())
        ->post("/painel/transcricoes/{$job->id}/retomar");

    expect($job->fresh()->status)->toBe('done');
});

it('apaga a transcrição', function () {
    $job = transcricaoPronta();

    $this->actingAs(User::factory()->create())
        ->delete("/painel/transcricoes/{$job->id}")
        ->assertRedirect('/painel/transcricoes');

    expect(TranscriptionJob::find($job->id))->toBeNull();
});

it('apagar exige login', function () {
    $job = transcricaoPronta();

    $this->delete("/painel/transcricoes/{$job->id}")->assertRedirect();

    expect(TranscriptionJob::find($job->id))->not->toBeNull();
});
