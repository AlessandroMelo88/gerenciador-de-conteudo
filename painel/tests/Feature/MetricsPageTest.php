<?php

use App\Models\GeneratedClip;
use App\Models\SourceChannel;
use App\Models\SourceVideo;
use App\Models\User;
use App\Services\MetricsReport;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;
use Inertia\Testing\AssertableInertia as Assert;

uses(DatabaseTransactions::class);

const NOW_ISO = '2026-10-10 12:00:00';

/** Cria um clip publicado ligado a um canal-fonte e a um formato. */
function publishedClip(SourceChannel $source, string $format, Carbon $publishedAt, ?string $videoId = 'yt'): GeneratedClip
{
    $video = SourceVideo::factory()->create(['channel_id' => $source->id]);
    DB::table('source_videos')->where('id', $video->id)->update(['format' => $format]);

    $clip = GeneratedClip::factory()->create(['source_video_id' => $video->id, 'status' => 'published']);
    DB::table('generated_clips')->where('id', $clip->id)->update([
        'published_at' => $publishedAt,
        'youtube_video_id' => $videoId === null ? null : $videoId.$clip->id,
    ]);

    return $clip;
}

function metric(GeneratedClip $clip, Carbon $at, int $views): void
{
    DB::table('clip_metrics')->insert([
        'generated_clip_id' => $clip->id,
        'collected_at' => $at,
        'views' => $views,
        'likes' => null,
        'comments' => null,
    ]);
}

function metricsProps(): array
{
    return test()->actingAs(User::factory()->create())
        ->get('/painel/metricas')
        ->assertOk()
        ->viewData('page')['props'];
}

beforeEach(function () {
    Carbon::setTestNow(Carbon::parse(NOW_ISO, 'UTC'));
    $this->source = SourceChannel::factory()->create(['channel_name' => 'Fonte Teste Métricas']);
});

afterEach(fn () => Carbon::setTestNow());

it('exige login', function () {
    $this->get('/painel/metricas')->assertRedirect('/login');
});

it('cria clip_metrics com as colunas e índices pedidos', function () {
    expect(Schema::hasTable('clip_metrics'))->toBeTrue()
        ->and(Schema::hasColumns('clip_metrics', ['id', 'generated_clip_id', 'collected_at', 'views', 'likes', 'comments']))->toBeTrue();

    $indexes = collect(Schema::getIndexes('clip_metrics'))->pluck('columns');
    expect($indexes->contains(['generated_clip_id', 'collected_at']))->toBeTrue()
        ->and($indexes->contains(['collected_at']))->toBeTrue();
});

it('apagar um clip leva as métricas junto (cascade) sem falhar por FK', function () {
    $clip = publishedClip($this->source, 'curto', now()->subDays(2));
    metric($clip, now()->subDay(), 10);
    metric($clip, now(), 20);

    DB::table('generated_clips')->where('id', $clip->id)->delete();

    expect(DB::table('clip_metrics')->where('generated_clip_id', $clip->id)->count())->toBe(0);
});

it('renderiza Metrics com o contrato de props e o estado vazio sem medições', function () {
    $this->actingAs(User::factory()->create())
        ->get('/painel/metricas')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('Metrics', false)
            ->has('hasData')
            ->has('publishedClips')
            ->has('measuredClips')
            ->has('byFormat', 2)
            ->has('bySource')
            ->has('lowViews')
            ->where('lowViewsThreshold', MetricsReport::LOW_VIEWS));
});

it('o 1º dia e os 7 dias usam a última medição dentro da janela', function () {
    DB::table('clip_metrics')->delete();
    DB::table('generated_clips')->update(['status' => 'rejected']);

    $pub = now()->subDays(8);
    $a = publishedClip($this->source, 'curto', $pub);
    metric($a, $pub->copy()->addHours(6), 100);
    metric($a, $pub->copy()->addHours(23), 300);
    metric($a, $pub->copy()->addHours(30), 400);
    metric($a, $pub->copy()->addDays(6), 1000);
    metric($a, $pub->copy()->addDays(7)->addHours(2), 1100);
    metric($a, now(), 1200);

    $b = publishedClip($this->source, 'curto', now()->subDays(3));
    metric($b, now()->subDays(3)->addHours(20), 50);
    metric($b, now(), 90);

    $c = publishedClip($this->source, 'curto', now()->subHours(5));
    metric($c, now(), 7);

    $curto = collect((new MetricsReport)->build(now())['byFormat'])->firstWhere('format', 'curto');

    expect($curto['clips'])->toBe(3)
        ->and($curto['clips24h'])->toBe(2)            // a e b; c ainda não tem 24 h
        ->and($curto['avgViews24h'])->toBe(175)       // (300 + 50) / 2
        ->and($curto['clips7d'])->toBe(1)             // só a tem 7 dias
        ->and($curto['avgViews7d'])->toBe(1000)
        ->and($curto['avgViewsNow'])->toBe((int) round((1200 + 90 + 7) / 3));

    $longo = collect((new MetricsReport)->build(now())['byFormat'])->firstWhere('format', 'longo');
    expect($longo['clips'])->toBe(0)->and($longo['avgViews24h'])->toBeNull();
});

it('ranqueia canal-fonte por views médias com o nº de clips', function () {
    DB::table('clip_metrics')->delete();
    DB::table('generated_clips')->update(['status' => 'rejected']);

    $forte = SourceChannel::factory()->create(['channel_name' => 'Fonte Forte']);
    $fraca = SourceChannel::factory()->create(['channel_name' => 'Fonte Fraca']);

    foreach ([1000, 3000] as $views) {
        $c = publishedClip($forte, 'curto', now()->subDays(2));
        metric($c, now(), $views);
    }
    $c = publishedClip($fraca, 'longo', now()->subDays(2));
    metric($c, now(), 10);

    $ranking = collect((new MetricsReport)->build(now())['bySource']);

    expect($ranking->pluck('source')->all())->toBe(['Fonte Forte', 'Fonte Fraca'])
        ->and($ranking[0]['clips'])->toBe(2)
        ->and($ranking[0]['avgViewsNow'])->toBe(2000)
        ->and($ranking[1]['clips'])->toBe(1);
});

it('lista clips que nunca passaram de poucas dezenas de views, só os com 2+ dias', function () {
    DB::table('clip_metrics')->delete();
    DB::table('generated_clips')->update(['status' => 'rejected']);

    $fraco = publishedClip($this->source, 'curto', now()->subDays(5));
    metric($fraco, now()->subDays(4), 12);
    metric($fraco, now(), 30);

    $bom = publishedClip($this->source, 'curto', now()->subDays(5));
    metric($bom, now(), 5000);

    $novo = publishedClip($this->source, 'curto', now()->subHours(10)); // cedo demais para julgar
    metric($novo, now(), 1);

    $semMedicao = publishedClip($this->source, 'curto', now()->subDays(5)); // nunca medido: não aparece

    $low = (new MetricsReport)->build(now())['lowViews'];

    expect(collect($low)->pluck('id')->all())->toBe([$fraco->id])
        ->and($low[0]['views'])->toBe(30)
        ->and($low[0]['daysOnline'])->toBe(5)
        ->and($low[0]['url'])->toStartWith('https://www.youtube.com/watch?v=');
});

it('sem nenhuma medição devolve hasData=false e conta os publicados à espera', function () {
    DB::table('clip_metrics')->delete();
    DB::table('generated_clips')->update(['status' => 'rejected']);
    publishedClip($this->source, 'curto', now()->subDays(1));

    $props = metricsProps();

    expect($props['hasData'])->toBeFalse()
        ->and($props['publishedClips'])->toBe(1)
        ->and($props['measuredClips'])->toBe(0)
        ->and($props['bySource'])->toBe([])
        ->and($props['lowViews'])->toBe([]);
});
