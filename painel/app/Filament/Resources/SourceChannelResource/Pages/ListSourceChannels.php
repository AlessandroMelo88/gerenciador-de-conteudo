<?php

namespace App\Filament\Resources\SourceChannelResource\Pages;

use App\Filament\Resources\SourceChannelResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListSourceChannels extends ListRecords
{
    protected static string $resource = SourceChannelResource::class;

    protected function getHeaderActions(): array
    {
        return [
            CreateAction::make(),
        ];
    }
}
