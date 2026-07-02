<?php

namespace App\Filament\Resources\SourceChannelResource\Pages;

use App\Filament\Resources\SourceChannelResource;
use Filament\Actions\DeleteAction;
use Filament\Resources\Pages\EditRecord;

class EditSourceChannel extends EditRecord
{
    protected static string $resource = SourceChannelResource::class;

    protected function getHeaderActions(): array
    {
        return [
            DeleteAction::make(),
        ];
    }
}
