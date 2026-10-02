<?php

use App\Services\MetricsReport;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;

// A suíte roda contra o banco local com RefreshDatabase desligado (tests/Pest.php): sem transação,
// cada execução deixaria clips de mentira no banco de desenvolvimento para sempre.
uses(DatabaseTransactions::class);

function clipComMedicao(string $titulo, string $canal, ?float $retencao, int $views = 100): int
{
    $canalId = DB::table('source_channels')->insertGetId([
        'youtube_channel_id' => 'uc-'.$titulo,
        'channel_name' => $canal,
        'rss_url' => 'https://example.test/'.$titulo,
        'target_niche' => 'futebol',
    ]);

    $videoId = DB::table('source_videos')->insertGetId([
        'youtube_video_id' => 'src-'.$titulo,
        'channel_id' => $canalId,
        'title' => 'fonte',
        'status' => 'published',
        'format' => 'curto',
    ]);

    $clipId = DB::table('generated_clips')->insertGetId([
        'source_video_id' => $videoId,
        'title' => $titulo,
        'status' => 'published',
        'youtube_video_id' => 'yt-'.$titulo,
        'published_at' => now()->subDays(10),
    ]);

    // Sem clip_metrics o clip nem entra no relatório: é ele que define "medido".
    DB::table('clip_metrics')->insert([
        'generated_clip_id' => $clipId,
        'collected_at' => now()->subDays(9),
        'views' => $views,
    ]);

    if ($retencao !== null) {
        DB::table('clip_daily_metrics')->insert([
            'generated_clip_id' => $clipId,
            'date' => now()->subDays(9)->toDateString(),
            'views' => $views,
            'estimated_minutes_watched' => 10,
            'average_view_duration' => 20,
            'average_view_percentage' => $retencao,
        ]);
    }

    return $clipId;
}

it('ordena os canais-fonte por retenção média quando há dado', function () {
    clipComMedicao('clip-fraco', 'Canal Fraco', retencao: 20.0, views: 900);
    clipComMedicao('clip-forte', 'Canal Forte', retencao: 75.0, views: 10);

    $dados = app(MetricsReport::class)->build();

    expect($dados['hasRetention'])->toBeTrue();

    // O Canal Forte tem MENOS views e MAIS retenção: se ele vier primeiro, a ordem mudou mesmo.
    $forte = collect($dados['bySource'])->firstWhere('source', 'Canal Forte');
    $fraco = collect($dados['bySource'])->firstWhere('source', 'Canal Fraco');
    $posicaoForte = collect($dados['bySource'])->search(fn ($r) => $r['source'] === 'Canal Forte');
    $posicaoFraco = collect($dados['bySource'])->search(fn ($r) => $r['source'] === 'Canal Fraco');

    expect($forte['avgRetention'])->toBe(75.0)
        ->and($fraco['avgRetention'])->toBe(20.0)
        ->and($posicaoForte)->toBeLessThan($posicaoFraco);
});

it('não quebra nem inventa zero quando ainda não há retenção coletada', function () {
    clipComMedicao('clip-sem-retencao', 'Canal Sem Dado', retencao: null, views: 100);

    $dados = app(MetricsReport::class)->build();

    $linha = collect($dados['bySource'])->firstWhere('source', 'Canal Sem Dado');

    expect($dados['hasRetention'])->toBeFalse()
        ->and($linha['avgRetention'])->toBeNull()
        ->and($linha['avgViewsNow'])->toBe(100);
});

it('leva a retenção para a lista de clips que não pegaram', function () {
    clipComMedicao('clip-parado', 'Canal Parado', retencao: 12.5, views: 3);

    $dados = app(MetricsReport::class)->build();
    $linha = collect($dados['lowViews'])->firstWhere('title', 'clip-parado');

    expect($linha)->not->toBeNull()
        ->and($linha['retention'])->toBe(12.5);
});
