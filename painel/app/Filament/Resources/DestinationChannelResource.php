<?php

namespace App\Filament\Resources;

use App\Filament\Resources\DestinationChannelResource\Pages;
use App\Models\DestinationChannel;
use BackedEnum;
use Filament\Forms\Components\Placeholder;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ToggleColumn;
use Filament\Tables\Table;
use Illuminate\Support\HtmlString;

class DestinationChannelResource extends Resource
{
    protected static ?string $model = DestinationChannel::class;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-tv';

    protected static ?string $modelLabel = 'Canal-destino';

    protected static ?string $pluralModelLabel = 'Canais-destino';

    public static function form(Schema $schema): Schema
    {
        return $schema->schema([
            TextInput::make('slug')
                ->required()
                ->helperText('Identificador único (ex: futebol-em-cortes)'),

            TextInput::make('name')->label('Nome')->required(),

            // EXPLÍCITO — nunca --generate em ENUM
            Select::make('niche')
                ->label('Nicho')
                ->options([
                    'futebol' => 'Futebol',
                    'podcast' => 'Podcast',
                ])
                ->required(),

            TextInput::make('youtube_channel_id')
                ->required()
                ->label('YouTube Channel ID (UC...)'),

            Textarea::make('credit_template')
                ->label('Template de créditos')
                ->helperText('Placeholder disponível: {channel_handle}')
                ->default('Créditos: @{channel_handle}'),

            Toggle::make('active')->label('Ativo')->default(true),

            Placeholder::make('oauth_instructions')
                ->label('OAuth')
                ->content(fn (?DestinationChannel $record) => new HtmlString(
                    $record
                        ? '<div class="text-sm">'
                            .'Rode no host para autorizar este canal: '
                            .'<pre class="mt-1 p-2 bg-gray-100 rounded">docker exec -it clip-processor python -m src.youtube_oauth --channel '.e($record->slug).'</pre>'
                          .'</div>'
                        : '<em>Salve o canal primeiro para ver o comando OAuth.</em>'
                ))
                ->columnSpanFull(),
        ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('slug')->searchable(),
                TextColumn::make('name')->label('Nome'),
                TextColumn::make('niche')->label('Nicho')->badge(),
                TextColumn::make('oauth_status')
                    ->label('OAuth')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'authorized' => 'success',
                        'expired' => 'danger',
                        'missing' => 'gray',
                        default => 'primary',
                    }),
                ToggleColumn::make('active')->label('Ativo'),
                TextColumn::make('youtube_channel_id')->label('YT Channel ID')->copyable(),
            ])
            ->defaultSort('created_at', 'desc');
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListDestinationChannels::route('/'),
            'create' => Pages\CreateDestinationChannel::route('/create'),
            'edit' => Pages\EditDestinationChannel::route('/{record}/edit'),
        ];
    }
}
