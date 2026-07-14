<?php

namespace App\Filament\Resources;

use App\Filament\Resources\SourceChannelResource\Pages;
use App\Models\Niche;
use App\Models\SourceChannel;
use BackedEnum;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteAction;
use Filament\Actions\DeleteBulkAction;
use Filament\Forms\Components\TextInput;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Columns\ToggleColumn;
use Filament\Tables\Table;

class SourceChannelResource extends Resource
{
    protected static ?string $model = SourceChannel::class;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-rss';

    protected static ?string $modelLabel = 'Canal fonte';

    protected static ?string $pluralModelLabel = 'Canais fonte';

    public static function form(Schema $schema): Schema
    {
        return $schema->schema([
            TextInput::make('url')
                ->label('URL do canal YouTube (ou channel_id)')
                ->helperText('Exemplo: https://youtube.com/@sportv OU https://youtube.com/channel/UC...')
                ->required()
                ->live()
                ->dehydrated(false),  // não persiste em source_channels; usado só para resolver via yt-dlp

            Niche::selectField('target_niche', 'Nicho de destino'),
        ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('channel_name')->label('Nome')->searchable(),
                TextColumn::make('channel_handle')->label('Handle'),
                TextColumn::make('target_niche')->label('Nicho')->badge(),
                ToggleColumn::make('active')->label('Ativo'),
                ToggleColumn::make('blacklisted')
                    ->label('Blacklisted')
                    ->tooltip('Afeta apenas novos vídeos. Para purgar a fila use SQL manual.'),
                TextColumn::make('created_at')->label('Criado')->dateTime()->since(),
            ])
            ->actions([
                DeleteAction::make(),
            ])
            ->bulkActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ])
            ->defaultSort('created_at', 'desc');
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListSourceChannels::route('/'),
            'edit'  => Pages\EditSourceChannel::route('/{record}/edit'),
        ];
    }
}
