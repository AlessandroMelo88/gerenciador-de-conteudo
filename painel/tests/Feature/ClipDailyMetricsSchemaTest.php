<?php

use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

// A suíte do projeto roda contra o banco local com RefreshDatabase desligado (tests/Pest.php),
// então um teste que insere deixa lixo para sempre. Transação + rollback resolve sem o
// migrate:fresh do RefreshDatabase, que apagaria o banco de desenvolvimento inteiro.
uses(DatabaseTransactions::class);

/**
 * SPEC-001 R1/R2/R3: grão clip × dia, único em (generated_clip_id, date), FK em cascata.
 */
function clipParaMetrica(string $sufixo): int
{
    $canalId = DB::table('source_channels')->insertGetId([
        'youtube_channel_id' => 'uc-'.$sufixo,
        'channel_name' => 'Canal '.$sufixo,
        'rss_url' => 'https://example.test/'.$sufixo,
    ]);

    $videoId = DB::table('source_videos')->insertGetId([
        'youtube_video_id' => 'src-'.$sufixo,
        'channel_id' => $canalId,
        'title' => 'fonte '.$sufixo,
        'status' => 'published',
    ]);

    return DB::table('generated_clips')->insertGetId([
        'source_video_id' => $videoId,
        'title' => 'clip '.$sufixo,
        'status' => 'published',
    ]);
}

it('cria clip_daily_metrics com as colunas do contrato', function () {
    expect(Schema::hasTable('clip_daily_metrics'))->toBeTrue();

    foreach ([
        'generated_clip_id', 'date', 'views', 'estimated_minutes_watched',
        'average_view_duration', 'average_view_percentage', 'likes', 'comments',
        'shares', 'subscribers_gained',
    ] as $coluna) {
        expect(Schema::hasColumn('clip_daily_metrics', $coluna))->toBeTrue("falta a coluna {$coluna}");
    }
});

it('recusa duas linhas para o mesmo clip no mesmo dia', function () {
    $clipId = clipParaMetrica('unico');

    $linha = [
        'generated_clip_id' => $clipId, 'date' => '2026-10-01', 'views' => 10,
        'estimated_minutes_watched' => 5, 'average_view_duration' => 30,
        'average_view_percentage' => 42.50,
    ];

    DB::table('clip_daily_metrics')->insert($linha);

    expect(fn () => DB::table('clip_daily_metrics')->insert($linha))
        ->toThrow(QueryException::class);
});

it('apaga as métricas junto com o clip', function () {
    $clipId = clipParaMetrica('cascata');

    DB::table('clip_daily_metrics')->insert([
        'generated_clip_id' => $clipId, 'date' => '2026-10-01', 'views' => 10,
        'estimated_minutes_watched' => 5, 'average_view_duration' => 30,
        'average_view_percentage' => 42.50,
    ]);

    DB::table('generated_clips')->where('id', $clipId)->delete();

    expect(DB::table('clip_daily_metrics')->where('generated_clip_id', $clipId)->count())->toBe(0);
});
