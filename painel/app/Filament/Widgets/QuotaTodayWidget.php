<?php

namespace App\Filament\Widgets;

use App\Models\DestinationChannel;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\Redis;

class QuotaTodayWidget extends BaseWidget
{
    protected ?string $heading = 'Cota de Uploads';

    // Filament\Widgets\Concerns\CanPoll já define $pollingInterval = '5s' (instance
    // property, não static) como default — não redeclarar aqui (FatalError:
    // "Cannot redeclare non static ... as static").
    protected static ?int $sort = 1;

    // Filament 5 widgets são lazy por padrão (renderizam via x-intersect/AJAX após o
    // primeiro paint) — desabilitado para que o dashboard mostre a cota imediatamente
    // no HTML inicial (sem esperar o viewport intersection do browser).
    protected static bool $isLazy = false;

    protected function getStats(): array
    {
        $date = Carbon::now('America/Sao_Paulo')->format('Y-m-d');
        $palette = ['info', 'warning', 'success', 'primary'];
        $stats = [];
        $index = 0;

        foreach (DestinationChannel::query()->where('active', true)->get() as $channel) {
            $key = "youtube_uploads:{$channel->youtube_channel_id}:{$date}";
            try {
                $count = (int) (Redis::connection('pipeline')->get($key) ?? 0);
            } catch (\Throwable $e) {
                $count = 0;
            }
            $limit = 3;
            $color = $count >= $limit ? 'danger' : $palette[$index % count($palette)];
            $stats[] = Stat::make(
                label: $channel->name,
                value: "{$count}/{$limit}",
            )->description('uploads hoje')
                ->color($color);
            $index++;
        }

        if (empty($stats)) {
            $stats[] = Stat::make('Uploads hoje', '—')->description('Nenhum canal-destino ativo');
        }

        return $stats;
    }
}
