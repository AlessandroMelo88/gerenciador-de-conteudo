<?php

namespace App\Filament\Resources\DestinationChannelResource\Pages;

use App\Filament\Resources\DestinationChannelResource;
use Filament\Actions\CreateAction;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Resources\Pages\ListRecords;

class ListDestinationChannels extends ListRecords
{
    protected static string $resource = DestinationChannelResource::class;

    protected function getHeaderActions(): array
    {
        return [
            CreateAction::make()
                ->label('Novo Canal-destino')
                ->modalHeading('Adicionar canal-destino')
                ->modalSubmitActionLabel('Adicionar')
                ->form([
                    TextInput::make('slug')
                        ->label('Slug')
                        ->required()
                        ->helperText('Identificador único (ex: futebol-em-cortes)'),

                    TextInput::make('name')
                        ->label('Nome')
                        ->required(),

                    Select::make('niche')
                        ->label('Nicho')
                        ->options(['futebol' => 'Futebol', 'podcast' => 'Podcast'])
                        ->required(),

                    TextInput::make('youtube_channel_id')
                        ->label('YouTube Channel ID (UC...)')
                        ->required(),

                    Textarea::make('credit_template')
                        ->label('Template de créditos')
                        ->helperText('Placeholder disponível: {channel_handle}')
                        ->default('Créditos: @{channel_handle}'),

                    Toggle::make('active')
                        ->label('Ativo')
                        ->default(true),
                ]),
        ];
    }
}
