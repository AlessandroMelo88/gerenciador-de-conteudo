<?php

namespace App\Filament\Resources\SourceVideoResource\Pages;

use App\Filament\Resources\SourceVideoResource;
use Filament\Resources\Pages\ListRecords;
use Filament\Schemas\Components\Tabs\Tab;
use Illuminate\Database\Eloquent\Builder;

class ListSourceVideos extends ListRecords
{
    protected static string $resource = SourceVideoResource::class;

    public function getTabs(): array
    {
        return [
            'ativos' => Tab::make('Ativos')
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', '!=', 'failed')),

            'falharam' => Tab::make('Falharam')
                ->modifyQueryUsing(fn (Builder $query) => $query->where('status', 'failed')),

            'todos' => Tab::make('Todos'),
        ];
    }
}
