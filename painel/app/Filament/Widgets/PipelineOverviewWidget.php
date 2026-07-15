<?php

namespace App\Filament\Widgets;

use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Carbon;

class PipelineOverviewWidget extends BaseWidget
{
    protected ?string $heading = 'Mix curto/longo e backlog';

    protected static ?int $sort = 1;

    // Consistente com os demais widgets do dashboard (ver QuotaTodayWidget) — sem
    // isso o conteúdo só aparece após x-intersect/AJAX do browser.
    protected static bool $isLazy = false;

    protected function getStats(): array
    {
        $since = Carbon::now('America/Sao_Paulo')->subDays(7);

        $publishedCurto = GeneratedClip::query()
            ->where('status', 'published')
            ->where('updated_at', '>=', $since)
            ->whereHas('sourceVideo', fn ($q) => $q->where('format', 'curto'))
            ->count();

        $publishedLongo = GeneratedClip::query()
            ->where('status', 'published')
            ->where('updated_at', '>=', $since)
            ->whereHas('sourceVideo', fn ($q) => $q->where('format', 'longo'))
            ->count();

        $totalPublished = $publishedCurto + $publishedLongo;
        $longoShare = $totalPublished > 0 ? round(($publishedLongo / $totalPublished) * 100) : 0;

        $backlogCurto = SourceVideo::query()->where('format', 'curto')->where('status', 'pending')->count();
        $backlogLongo = SourceVideo::query()->where('format', 'longo')->where('status', 'pending')->count();

        return [
            Stat::make('Publicados (7 dias)', "{$publishedCurto} curto / {$publishedLongo} longo")
                ->description("{$longoShare}% do total foi longo")
                ->color('success'),
            Stat::make('Backlog aguardando download', "{$backlogCurto} curto / {$backlogLongo} longo")
                ->description('Descobertos via RSS, ainda não baixados')
                ->color($backlogCurto + $backlogLongo > 200 ? 'warning' : 'gray'),
        ];
    }
}
