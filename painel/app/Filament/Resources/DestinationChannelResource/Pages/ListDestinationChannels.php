<?php

namespace App\Filament\Resources\DestinationChannelResource\Pages;

use App\Filament\Resources\DestinationChannelResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListDestinationChannels extends ListRecords
{
    protected static string $resource = DestinationChannelResource::class;

    protected function getHeaderActions(): array
    {
        return [
            CreateAction::make(),
        ];
    }
}
