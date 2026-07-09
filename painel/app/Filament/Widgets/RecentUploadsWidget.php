<?php

namespace App\Filament\Widgets;

use App\Models\GeneratedClip;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;
use Filament\Widgets\TableWidget as BaseWidget;

class RecentUploadsWidget extends BaseWidget
{
    protected static ?int $sort = 3;

    protected int|string|array $columnSpan = 'full';



    public static function canView(): bool { return false; }

    protected static ?string $heading = 'Últimos uploads';

    // Widgets Filament 5 são lazy por padrão (x-intersect/AJAX) — desabilitado por
    // consistência com os demais widgets do dashboard (ver PendingApprovalWidget).
    protected static bool $isLazy = false;

    public function table(Table $table): Table
    {
        return $table
            ->query(GeneratedClip::query()->where('status', 'published')->latest()->limit(10))
            ->poll('5s')
            ->columns([
                TextColumn::make('id')->sortable(),
                TextColumn::make('title')->label('Título')->limit(60),
                TextColumn::make('destinationChannel.name')->label('Canal'),
                TextColumn::make('youtube_video_id')
                    ->label('YouTube')
                    ->formatStateUsing(fn (?string $state) => $state ? "https://youtu.be/{$state}" : '')
                    ->url(fn ($state) => $state ? "https://youtu.be/{$state}" : null, shouldOpenInNewTab: true),
                TextColumn::make('updated_at')->label('Publicado')->since(),
            ]);
    }
}
