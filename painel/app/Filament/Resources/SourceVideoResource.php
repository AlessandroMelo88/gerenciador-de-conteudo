<?php

namespace App\Filament\Resources;

use App\Filament\Resources\SourceVideoResource\Pages;
use App\Models\SourceVideo;
use App\Services\ClipProcessorClient;
use BackedEnum;
use Filament\Actions\Action;
use Filament\Actions\ActionGroup;
use Filament\Actions\BulkAction;
use Filament\Forms\Components\DatePicker;
use Filament\Notifications\Notification;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\Filter;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Collection;
use RuntimeException;

class SourceVideoResource extends Resource
{
    protected static ?string $model = SourceVideo::class;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-film';

    protected static ?string $navigationLabel = 'Vídeos';

    protected static ?string $pluralModelLabel = 'Vídeos';

    protected static ?string $modelLabel = 'Vídeo';

    protected static ?int $navigationSort = 5;

    /** Espelha NON_TERMINAL_CLIP_STATUSES de clip-processor/src/publisher.py. */
    protected const NON_TERMINAL_CLIP_STATUSES = ['pending_cut', 'cutting', 'pending', 'approved', 'publishing'];

    public static function form(Schema $schema): Schema
    {
        return $schema->schema([]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->modifyQueryUsing(fn (Builder $query) => $query->withCount([
                'generatedClips as total_clips_count',
                'generatedClips as em_andamento_count' => fn (Builder $q) => $q->whereIn('status', self::NON_TERMINAL_CLIP_STATUSES),
                'generatedClips as publicados_count' => fn (Builder $q) => $q->where('status', 'published'),
            ]))
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
                    ->size('xs')
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

                TextColumn::make('local_path')
                    ->label('Arquivo local')
                    ->state(fn (SourceVideo $record): string => filled($record->local_path) ? 'Sim' : 'Não')
                    ->badge()
                    ->color(fn (string $state): string => $state === 'Sim' ? 'info' : 'gray'),

                TextColumn::make('uso')
                    ->label('Uso')
                    ->state(function (SourceVideo $record): string {
                        if ($record->status === 'failed') {
                            return 'Falhou — pode apagar';
                        }

                        if ((int) $record->total_clips_count > 0
                            && (int) $record->em_andamento_count === 0
                            && (int) $record->publicados_count === 0) {
                            return 'Sem uso — pode apagar';
                        }

                        if ((int) $record->publicados_count > 0 && (int) $record->em_andamento_count === 0) {
                            return 'Publicado';
                        }

                        return 'Em uso';
                    })
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'Falhou — pode apagar', 'Sem uso — pode apagar' => 'danger',
                        'Publicado' => 'success',
                        default => 'gray',
                    }),

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

                Filter::make('seguro_apagar')
                    ->label('Só sem uso (seguro apagar)')
                    ->toggle()
                    ->query(function (Builder $query): Builder {
                        return $query->where(function (Builder $q) {
                            $q->where('status', 'failed')
                                ->orWhere(function (Builder $q2) {
                                    $q2->whereHas('generatedClips')
                                        ->whereDoesntHave('generatedClips', function (Builder $sub) {
                                            $sub->whereIn('status', self::NON_TERMINAL_CLIP_STATUSES);
                                        })
                                        ->whereDoesntHave('generatedClips', function (Builder $sub) {
                                            $sub->where('status', 'published');
                                        });
                                });
                        });
                    }),

                Filter::make('published_at')
                    ->label('Publicado no YouTube')
                    ->schema([
                        DatePicker::make('published_from')->label('De'),
                        DatePicker::make('published_until')->label('Até'),
                    ])
                    ->query(function (Builder $query, array $data): Builder {
                        return $query
                            ->when($data['published_from'] ?? null, fn (Builder $q, $date) => $q->whereDate('published_at', '>=', $date))
                            ->when($data['published_until'] ?? null, fn (Builder $q, $date) => $q->whereDate('published_at', '<=', $date));
                    })
                    ->indicateUsing(function (array $data): array {
                        $indicators = [];
                        if ($data['published_from'] ?? null) {
                            $indicators[] = 'Publicado de '.$data['published_from'];
                        }
                        if ($data['published_until'] ?? null) {
                            $indicators[] = 'até '.$data['published_until'];
                        }

                        return $indicators;
                    }),
            ])
            ->headerActions([
                Action::make('purge_old_videos')
                    ->label('Limpar vídeos antigos')
                    ->icon('heroicon-o-trash')
                    ->color('danger')
                    ->schema([
                        DatePicker::make('before_date')
                            ->label('Apagar vídeos publicados antes de')
                            ->required()
                            ->default(now()->subDays(3)->toDateString())
                            ->maxDate(now()),
                    ])
                    ->requiresConfirmation()
                    ->modalHeading('Limpar vídeos antigos')
                    ->modalDescription('Apaga do banco os vídeos publicados antes da data escolhida que nunca chegaram a gerar clip (nunca vão mais ser processados, já que o download sempre prioriza notícia recente). Além disso, libera do disco o arquivo bruto dos vídeos mais antigos que já geraram clip mas não precisam mais dele. Clips já cortados e publicados NÃO são afetados.')
                    ->modalSubmitActionLabel('Limpar')
                    ->action(function (array $data): void {
                        $client = app(ClipProcessorClient::class);

                        try {
                            $result = $client->purgeOldVideos($data['before_date']);
                        } catch (RuntimeException $e) {
                            Notification::make()->title('Falha ao limpar')->body($e->getMessage())->danger()->send();

                            return;
                        }

                        $mb = round($result['freed_bytes'] / 1024 / 1024, 1);

                        Notification::make()
                            ->title("{$result['deleted_rows']} vídeo(s) removido(s) do banco, {$mb} MB liberados")
                            ->success()
                            ->send();
                    }),
            ])
            ->actions([
                ActionGroup::make([
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

                    Action::make('delete_file')
                        ->label('Apagar arquivo local')
                        ->icon('heroicon-o-trash')
                        ->color('danger')
                        ->visible(fn (SourceVideo $record): bool => filled($record->local_path))
                        ->requiresConfirmation()
                        ->modalHeading('Apagar arquivo local')
                        ->modalDescription('Apaga o vídeo bruto (.mp4) do disco para liberar espaço. Os cortes já gerados a partir dele NÃO são afetados. Essa ação não pode ser desfeita — o vídeo precisaria ser baixado de novo se for necessário no futuro.')
                        ->modalSubmitActionLabel('Apagar')
                        ->action(function (SourceVideo $record): void {
                            $client = app(ClipProcessorClient::class);

                            try {
                                $result = $client->deleteSourceVideo($record->id);
                            } catch (RuntimeException $e) {
                                Notification::make()
                                    ->title('Falha ao apagar')
                                    ->body($e->getMessage())
                                    ->danger()
                                    ->send();

                                return;
                            }

                            $record->refresh();
                            $mb = round($result['freed_bytes'] / 1024 / 1024, 1);

                            Notification::make()
                                ->title("Arquivo apagado ({$mb} MB liberados)")
                                ->success()
                                ->send();
                        }),
                ]),
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

                BulkAction::make('delete_files')
                    ->label('Apagar arquivos selecionados')
                    ->icon('heroicon-o-trash')
                    ->color('danger')
                    ->requiresConfirmation()
                    ->modalHeading('Apagar arquivos locais selecionados')
                    ->modalDescription(function (Collection $records): string {
                        $deletable = $records->filter(fn (SourceVideo $r) => filled($r->local_path))->count();
                        $skipped = $records->count() - $deletable;

                        $text = "Apaga os vídeos brutos (.mp4) do disco para liberar espaço. Os cortes já gerados NÃO são afetados. {$deletable} de {$records->count()} selecionados têm arquivo local e serão apagados.";

                        if ($skipped > 0) {
                            $text .= " {$skipped} já não têm arquivo local e serão ignorados.";
                        }

                        return $text;
                    })
                    ->modalSubmitActionLabel('Apagar')
                    ->action(function (Collection $records): void {
                        $client = app(ClipProcessorClient::class);
                        $freedBytes = 0;
                        $failures = 0;
                        $skipped = 0;

                        foreach ($records as $record) {
                            if (blank($record->local_path)) {
                                $skipped++;

                                continue;
                            }

                            try {
                                $result = $client->deleteSourceVideo($record->id);
                                $freedBytes += $result['freed_bytes'];
                            } catch (RuntimeException) {
                                $failures++;
                            }
                        }

                        $mb = round($freedBytes / 1024 / 1024, 1);
                        $bodyLines = [];
                        if ($failures > 0) {
                            $bodyLines[] = "{$failures} arquivo(s) não puderam ser apagados.";
                        }
                        if ($skipped > 0) {
                            $bodyLines[] = "{$skipped} já não tinham arquivo local (ignorados).";
                        }

                        Notification::make()
                            ->title("{$mb} MB liberados")
                            ->body(implode(' ', $bodyLines) ?: null)
                            ->success()
                            ->send();
                    })
                    ->deselectRecordsAfterCompletion(),
            ])
            ->checkIfRecordIsSelectableUsing(fn (SourceVideo $record): bool => filled($record->local_path))
            ->poll('10s')
            ->striped()
            ->paginationPageOptions([25, 50, 100, 250, 500])
            ->defaultPaginationPageOption(100);
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListSourceVideos::route('/'),
        ];
    }
}
