<?php

use App\Models\TranscriptionJob;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;

uses(DatabaseTransactions::class);

function temColunaEmbedding(): bool
{
    return DB::selectOne(
        "SELECT 1 AS ok FROM information_schema.columns
         WHERE table_schema = current_schema() AND table_name = 'transcript_chunks' AND column_name = 'embedding'"
    ) !== null;
}

/** Vetor de 384 dimensões com 1.0 na posição $i (cosseno 1 com ele mesmo, 0 com os outros). */
function vetorBase(int $i): array
{
    $v = array_fill(0, 384, 0.0);
    $v[$i] = 1.0;

    return $v;
}

function jobBusca(string $titulo = 'Aula de funil'): TranscriptionJob
{
    return TranscriptionJob::create([
        'source_url' => 'https://vimeo.com/'.random_int(1, 999999),
        'status' => 'done',
        'progress_percent' => 100,
        'title' => $titulo,
        'platform' => 'Vimeo',
        'duration_seconds' => 3725,
    ]);
}

function chunkBusca(int $jobId, int $indice, string $texto, ?float $inicio = 10.0, ?int $vetor = null): int
{
    $row = [
        'job_id' => $jobId,
        'chunk_index' => $indice,
        'content' => $texto,
        'start_seconds' => $inicio,
        'end_seconds' => $inicio !== null ? $inicio + 40 : null,
        'created_at' => now(),
    ];
    if ($vetor !== null) {
        $row['embedding'] = '['.implode(',', vetorBase($vetor)).']';
        $row['embedding_model'] = 'teste';
    }

    return DB::table('transcript_chunks')->insertGetId($row);
}

function fakeEmbedder(int $posicao): void
{
    Http::fake(['*/embed' => Http::response([
        'model' => 'teste', 'dim' => 384, 'vectors' => [vetorBase($posicao)],
    ])]);
}

function buscar(string $query): Illuminate\Testing\TestResponse
{
    return test()->actingAs(User::factory()->create())->getJson('/painel/transcricoes/busca?'.$query);
}

// --- sempre rodam -----------------------------------------------------------

it('exige login', function () {
    $this->get('/painel/transcricoes/busca?q=funil')->assertRedirect('/login');
});

it('valida q, modo e limit', function () {
    Http::fake();

    buscar('q=a')->assertStatus(422)->assertJsonValidationErrors('q');
    buscar('')->assertStatus(422)->assertJsonValidationErrors('q');
    buscar('q='.str_repeat('a', 201))->assertStatus(422)->assertJsonValidationErrors('q');
    buscar('q=funil&modo=xyz')->assertStatus(422)->assertJsonValidationErrors('modo');
    buscar('q=funil&limit=0')->assertStatus(422)->assertJsonValidationErrors('limit');
    buscar('q=funil&limit=51')->assertStatus(422)->assertJsonValidationErrors('limit');
    Http::assertNothingSent();
});

it('rota busca não é confundida com /{job}', function () {
    Http::fake();

    buscar('q=funil&modo=texto')->assertOk()->assertJsonPath('results', []);
});

it('busca por texto ignora acento e caixa e devolve o contrato', function () {
    Http::fake();
    $job = jobBusca();
    $id = chunkBusca($job->id, 0, 'Hoje vamos falar sobre validação de oferta antes de gastar com anúncios.', 812.4);
    chunkBusca($job->id, 1, 'Assunto totalmente diferente sobre culinária.', 900.0);

    $r = buscar('q='.urlencode('VALIDACAO oferta').'&modo=texto')->assertOk();

    $r->assertJsonPath('query', 'VALIDACAO oferta')
        ->assertJsonPath('mode', 'texto')
        ->assertJsonPath('mode_used', 'texto')
        ->assertJsonPath('degraded', false)
        ->assertJsonCount(1, 'results')
        ->assertJsonPath('results.0.job_id', $job->id)
        ->assertJsonPath('results.0.title', 'Aula de funil')
        ->assertJsonPath('results.0.platform', 'Vimeo')
        ->assertJsonPath('results.0.duration_seconds', 3725)
        ->assertJsonCount(1, 'results.0.hits')
        ->assertJsonPath('results.0.hits.0.chunk_id', $id)
        ->assertJsonPath('results.0.hits.0.chunk_index', 0)
        ->assertJsonPath('results.0.hits.0.link', "/painel/transcricoes/{$job->id}?t=812&q=VALIDACAO%20oferta");
    expect($r->json('results.0.hits.0.snippet'))->toContain('<mark>');
    Http::assertNothingSent();
});

it('agrupa por transcrição com no máximo 3 trechos', function () {
    Http::fake();
    $a = jobBusca('A');
    $b = jobBusca('B');
    foreach (range(0, 4) as $i) {
        chunkBusca($a->id, $i, "Trecho {$i} sobre remarketing e público frio.", $i * 30.0);
    }
    chunkBusca($b->id, 0, 'Um único trecho de remarketing.', 5.0);

    $r = buscar('q=remarketing&modo=texto')->assertOk();

    $r->assertJsonCount(2, 'results');
    $porJob = collect($r->json('results'))->keyBy('job_id');
    expect($porJob[$a->id]['hits'])->toHaveCount(3)
        ->and($porJob[$b->id]['hits'])->toHaveCount(1);
});

it('respeita limit em número de transcrições', function () {
    Http::fake();
    foreach (range(1, 3) as $n) {
        chunkBusca(jobBusca("J{$n}")->id, 0, 'conversão de checkout', 1.0);
    }

    buscar('q='.urlencode('conversão').'&modo=texto&limit=2')->assertOk()->assertJsonCount(2, 'results');
});

it('cai no trigram quando o FTS não acha (erro de digitação)', function () {
    Http::fake();
    $job = jobBusca();
    chunkBusca($job->id, 0, 'A automatização do funil de vendas economiza tempo.', null);

    $r = buscar('q=automatizacaoo&modo=texto')->assertOk();

    $r->assertJsonPath('results.0.job_id', $job->id)
        ->assertJsonPath('results.0.hits.0.start_seconds', null);
    expect($r->json('results.0.hits.0.link'))->not->toContain('t=');
});

it('escapa o snippet: só <mark> passa (XSS)', function () {
    Http::fake();
    $job = jobBusca();
    chunkBusca($job->id, 0, 'promoção <script>alert(1)</script> <img src=x onerror=alert(2)> <mark>falso</mark> "aspas" & cia', 1.0);

    $snippet = buscar('q='.urlencode('promoção').'&modo=texto')->assertOk()->json('results.0.hits.0.snippet');

    expect($snippet)->toContain('<mark>promoção</mark>')
        ->and($snippet)->not->toContain('<script')
        ->and($snippet)->not->toContain('<img')
        ->and($snippet)->toContain('&lt;img');
    // O <mark> que veio no conteúdo (falso) nunca vira tag; o do ts_headline é só o do termo buscado.
    expect(substr_count($snippet, '<mark>'))->toBe(1);
    // Removendo os <mark> legítimos, nenhum '<' pode sobrar.
    expect(str_replace(['<mark>', '</mark>'], '', $snippet))->not->toContain('<');
});

it('degrada para texto quando o embedder dá timeout', function () {
    Http::fake(['*/embed' => fn () => throw new Illuminate\Http\Client\ConnectionException('timeout')]);
    $job = jobBusca();
    chunkBusca($job->id, 0, 'Estratégia de lançamento perpétuo.', 3.0);

    foreach (['hibrida', 'semantica'] as $modo) {
        buscar("q=lancamento&modo={$modo}")->assertOk()
            ->assertJsonPath('mode', $modo)
            ->assertJsonPath('mode_used', 'texto')
            ->assertJsonPath('degraded', true)
            ->assertJsonPath('results.0.job_id', $job->id);
    }
});

it('degrada para texto quando o embedder responde 503 ou lixo', function () {
    $job = jobBusca();
    chunkBusca($job->id, 0, 'Estratégia de lançamento perpétuo.', 3.0);

    Http::fake(['*/embed' => Http::response(['detail' => 'modelo não carregado'], 503)]);
    buscar('q=lancamento')->assertOk()->assertJsonPath('mode_used', 'texto')->assertJsonPath('degraded', true);

    Http::fake(['*/embed' => Http::response(['vectors' => []])]);
    buscar('q=lancamento')->assertOk()->assertJsonPath('mode_used', 'texto')->assertJsonPath('degraded', true);
});

it('envia token Bearer e o tipo query ao embedder', function () {
    config(['services.embedder.token' => 'segredo-teste']);
    fakeEmbedder(0);

    buscar('q=qualquer+coisa&modo=hibrida')->assertOk();

    Http::assertSent(fn ($req) => str_ends_with($req->url(), '/embed')
        && $req->hasHeader('Authorization', 'Bearer segredo-teste')
        && $req['kind'] === 'query'
        && $req['texts'] === ['qualquer coisa']);
})->skip(fn () => ! temColunaEmbedding(), 'sem coluna embedding: nem chama o embedder');

it('sem coluna embedding degrada para texto sem chamar o embedder', function () {
    Http::fake();
    chunkBusca(jobBusca()->id, 0, 'lançamento perpétuo');

    buscar('q=lancamento&modo=hibrida')->assertOk()
        ->assertJsonPath('mode_used', 'texto')
        ->assertJsonPath('degraded', true);
    Http::assertNothingSent();
})->skip(fn () => temColunaEmbedding(), 'só vale sem a extensão vector');

it('modo texto nunca chama o embedder', function () {
    Http::fake();
    jobBusca();

    buscar('q=funil&modo=texto')->assertOk();

    Http::assertNothingSent();
});

it('sem resultados devolve results vazio', function () {
    Http::fake();

    buscar('q=zzzinexistentezzz&modo=texto')->assertOk()
        ->assertJsonPath('results', [])
        ->assertJsonPath('degraded', false);
});

// --- precisam de pgvector ---------------------------------------------------

it('busca semântica ordena por similaridade e aplica o piso', function () {
    fakeEmbedder(5);
    $job = jobBusca();
    $perto = chunkBusca($job->id, 0, 'nada a ver com a consulta em palavras', 10.0, 5);
    chunkBusca($job->id, 1, 'outro vetor ortogonal', 50.0, 6);

    $r = buscar('q=algo+conceitual&modo=semantica')->assertOk();

    $r->assertJsonPath('mode_used', 'semantica')
        ->assertJsonPath('degraded', false)
        ->assertJsonCount(1, 'results.0.hits')
        ->assertJsonPath('results.0.hits.0.chunk_id', $perto);
    expect($r->json('results.0.hits.0.score'))->toBeGreaterThan(0.99);
})->skip(fn () => ! temColunaEmbedding(), 'sem coluna embedding (pgvector)');

it('piso de similaridade é configurável', function () {
    config(['services.embedder.min_similarity' => -1.0]);
    fakeEmbedder(5);
    $job = jobBusca();
    chunkBusca($job->id, 0, 'perto', 10.0, 5);
    chunkBusca($job->id, 1, 'longe', 50.0, 6);

    buscar('q=algo&modo=semantica')->assertOk()->assertJsonCount(2, 'results.0.hits');
})->skip(fn () => ! temColunaEmbedding(), 'sem coluna embedding (pgvector)');

it('híbrida combina texto e vetor por RRF', function () {
    fakeEmbedder(7);
    $job = jobBusca();
    $ambos = chunkBusca($job->id, 0, 'escala de tráfego pago com orçamento pequeno', 10.0, 7);
    $soTexto = chunkBusca($job->id, 1, 'tráfego orgânico também funciona', 60.0, 8);
    $soVetor = chunkBusca($job->id, 2, 'conversa sem relação lexical', 110.0, 7);

    $r = buscar('q='.urlencode('tráfego pago').'&modo=hibrida')->assertOk();

    $r->assertJsonPath('mode_used', 'hibrida')->assertJsonPath('degraded', false);
    $ids = collect($r->json('results.0.hits'))->pluck('chunk_id')->all();
    expect($ids[0])->toBe($ambos)
        ->and($ids)->toContain($soTexto, $soVetor);
    // Os dois primeiros aparecem nas duas listas ou têm score RRF > 1/(60+1)
    expect($r->json('results.0.hits.0.score'))->toBeGreaterThan(1 / 61);
})->skip(fn () => ! temColunaEmbedding(), 'sem coluna embedding (pgvector)');

// --- detalhe, lista e comando ------------------------------------------------

it('detalhe recebe focus sanitizado a partir de ?t= e ?q=', function () {
    $job = jobBusca();
    $user = User::factory()->create();

    $this->actingAs($user)->get("/painel/transcricoes/{$job->id}?t=812.9&q=".urlencode("  <b>validar</b>\noferta "))
        ->assertOk()
        ->assertInertia(fn ($p) => $p->where('focus.t', 812)->where('focus.q', 'validar oferta'));

    $this->actingAs($user)->get("/painel/transcricoes/{$job->id}?t=abc&q[]=x")
        ->assertOk()
        ->assertInertia(fn ($p) => $p->where('focus.t', null)->where('focus.q', null));

    $this->actingAs($user)->get("/painel/transcricoes/{$job->id}")
        ->assertOk()
        ->assertInertia(fn ($p) => $p->where('focus.t', null)->where('focus.q', null));
});

it('lista filtra por título/URL e não varre mais o texto', function () {
    $achada = jobBusca('Funil perpétuo');
    $achada->update(['transcript_text' => 'conteúdo com palavra rara zebra']);

    $user = User::factory()->create();
    $this->actingAs($user)->get('/painel/transcricoes?q=perp')
        ->assertInertia(fn ($p) => $p->where('jobs.data.0.id', $achada->id));
    $this->actingAs($user)->get('/painel/transcricoes?q=zebra')
        ->assertInertia(fn ($p) => $p->where('jobs.total', 0));
});

it('transcricoes:indexar --status conta jobs sem chunks e chunks sem vetor', function () {
    jobBusca();
    chunkBusca(jobBusca()->id, 0, 'algum texto');

    $this->artisan('transcricoes:indexar', ['--status' => true])
        ->expectsOutputToContain('Transcrições prontas sem chunks')
        ->assertSuccessful();
});
