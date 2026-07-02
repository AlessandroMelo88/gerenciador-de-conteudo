<?php

namespace App\Filament\Resources\DestinationChannelResource\Pages;

use App\Filament\Resources\DestinationChannelResource;
use Filament\Actions\DeleteAction;
use Filament\Resources\Pages\EditRecord;

class EditDestinationChannel extends EditRecord
{
    protected static string $resource = DestinationChannelResource::class;

    protected function getHeaderActions(): array
    {
        return [
            DeleteAction::make(),
        ];
    }
}
