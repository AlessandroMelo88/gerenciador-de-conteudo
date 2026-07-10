<?php

namespace App\Filament\Resources;

use App\Filament\Resources\SourceVideoResource\Pages;
use App\Models\SourceVideo;
use BackedEnum;
use Filament\Actions\Action;
use Filament\Actions\BulkAction;
use Filament\Notifications\Notification;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Collection;

class SourceVideoResource extends Resource
{
    protected static ?string $model = SourceVideo::class;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-film';

    protected static ?string $navigationLabel = 'Vídeos';

    protected static ?string $pluralModelLabel = 'Vídeos';

    protected static ?string $modelLabel = 'Vídeo';

    protected static ?int $navigationSort = 5;

    public static function form(Schema $schema): Schema
    {
        return $schema->schema([]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->defaultSort('updated_at', 'desc')
            ->columns([
                TextColumn::make('id')
                    ->label('ID')
                    ->sortable()
                    ->width('60px'),

                TextColumn::make('title')
                    ->label('Título')
                    ->searchable()
                    ->limit(55)
                    ->tooltip(fn (SourceVideo $record): string => $record->title ?? ''),

                TextColumn::make('sourceChannel.channel_name')
                    ->label('Canal')
                    ->searchable()
                    ->sortable()
                    ->placeholder('—'),

                TextColumn::make('status')
                    ->label('Status')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'published'   => 'success',
                        'failed'      => 'danger',
                        'downloading', 'transcribing', 'selecting', 'cutting', 'publishing' => 'warning',
                        'downloaded'  => 'info',
                        default       => 'gray',
                    }),

                TextColumn::make('youtube_video_id')
                    ->label('YouTube ID')
                    ->copyable()
                    ->copyMessage('ID copiado!')
                    ->fontFamily('mono')
                    ->color('primary'),

                TextColumn::make('published_at')
                    ->label('Publicado em')
                    ->dateTime('d/m/Y H:i')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('updated_at')
                    ->label('Atualizado')
                    ->since()
                    ->sortable(),
            ])
            ->filters([
                SelectFilter::make('status')
                    ->label('Status')
                    ->options([
                        'pending'      => 'Pendente',
                        'downloading'  => 'Baixando',
                        'downloaded'   => 'Baixado',
                        'transcribing' => 'Transcrevendo',
                        'selecting'    => 'Selecionando',
                        'cutting'      => 'Cortando',
                        'publishing'   => 'Publicando',
                        'published'    => 'Publicado',
                        'failed'       => 'Falha',
                    ]),
            ])
            ->actions([
                Action::make('open_youtube')
                    ->label('YouTube')
                    ->icon('heroicon-o-arrow-top-right-on-square')
                    ->color('gray')
                    ->url(fn (SourceVideo $record): string => "https://youtube.com/watch?v={$record->youtube_video_id}")
                    ->openUrlInNewTab(),

                Action::make('copy_url')
                    ->label('Copiar URL')
                    ->icon('heroicon-o-clipboard-document')
                    ->color('gray')
                    ->action(function (SourceVideo $record, $livewire): void {
                        $url = "https://youtube.com/watch?v={$record->youtube_video_id}";
                        $livewire->js("navigator.clipboard.writeText('{$url}').catch(()=>{})");
                        Notification::make()
                            ->title('URL copiada')
                            ->body($url)
                            ->success()
                            ->duration(3000)
                            ->send();
                    }),
            ])
            ->bulkActions([
                BulkAction::make('copy_urls')
                    ->label('Copiar URLs selecionadas')
                    ->icon('heroicon-o-clipboard-document-list')
                    ->action(function (Collection $records, $livewire): void {
                        $urls = $records
                            ->map(fn (SourceVideo $r) => "https://youtube.com/watch?v={$r->youtube_video_id}")
                            ->implode("\\n");

                        $livewire->js("navigator.clipboard.writeText(\"{$urls}\").catch(()=>{})");

                        Notification::make()
                            ->title("{$records->count()} URL(s) copiada(s)")
                            ->success()
                            ->duration(3000)
                            ->send();
                    })
                    ->deselectRecordsAfterCompletion(),

                BulkAction::make('copy_ids')
                    ->label('Copiar IDs selecionados')
                    ->icon('heroicon-o-hashtag')
                    ->color('gray')
                    ->action(function (Collection $records, $livewire): void {
                        $ids = $records->pluck('youtube_video_id')->implode("\\n");
                        $livewire->js("navigator.clipboard.writeText(\"{$ids}\").catch(()=>{})");

                        Notification::make()
                            ->title("{$records->count()} ID(s) copiado(s)")
                            ->success()
                            ->duration(3000)
                            ->send();
                    })
                    ->deselectRecordsAfterCompletion(),
            ])
            ->poll('10s')
            ->striped();
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListSourceVideos::route('/'),
        ];
    }
}
