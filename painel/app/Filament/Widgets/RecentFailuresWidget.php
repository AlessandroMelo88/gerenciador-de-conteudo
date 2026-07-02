<?php

namespace App\Filament\Widgets;

use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;
use Filament\Widgets\TableWidget as BaseWidget;

class RecentFailuresWidget extends BaseWidget
{
    protected static ?int $sort = 4;

    protected int|string|array $columnSpan = 'full';

    public static function canView(): bool
    {
        return false;
    }

    protected static ?string $heading = 'Últimas falhas';

    // Widgets Filament 5 são lazy por padrão (x-intersect/AJAX) — desabilitado por
    // consistência com os demais widgets do dashboard (ver PendingApprovalWidget).
    protected static bool $isLazy = false;

    public function table(Table $table): Table
    {
        // Fallback documentado no 08-08-PLAN.md: Filament\Tables\Table::applyQueryScopes()
        // exige Illuminate\Database\Eloquent\Builder — um UNION ALL via DB::table() (Query
        // Builder puro) não é aceito pelo componente de tabela. A tabela mostra as falhas
        // de generated_clips (Eloquent); a contagem de source_videos falhados é exposta na
        // descrição do cabeçalho, sem precisar de um 5º widget dedicado.
        return $table
            ->query(GeneratedClip::query()->where('status', 'failed')->latest('updated_at')->limit(20))
            ->poll('5s')
            ->description(fn () => 'Vídeos-fonte com falha: '.SourceVideo::query()->where('status', 'failed')->count())
            ->columns([
                TextColumn::make('id')->label('ID'),
                TextColumn::make('title')->label('Título')->limit(60),
                TextColumn::make('destinationChannel.name')->label('Destino')->toggleable(),
                TextColumn::make('updated_at')->label('Quando')->since(),
            ]);
    }
}
