<?php

namespace App\Filament\Resources\SourceChannelResource\Pages;

use App\Filament\Resources\SourceChannelResource;
use App\Models\Niche;
use App\Models\SourceChannel;
use App\Services\ClipProcessorClient;
use Filament\Actions\CreateAction;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\ListRecords;
use Filament\Schemas\Components\Tabs\Tab;
use Illuminate\Validation\ValidationException;
use RuntimeException;

class ListSourceChannels extends ListRecords
{
    protected static string $resource = SourceChannelResource::class;

    /**
     * Uma tab por nicho cadastrado (tabela niches) + "Todos" — ao criar um
     * nicho novo (ex.: política) via Niche::selectField(), a tab aparece aqui
     * sozinha no próximo carregamento, sem precisar mexer em código.
     */
    public function getTabs(): array
    {
        $tabs = ['todos' => Tab::make('Todos')];

        foreach (Niche::query()->orderBy('label')->get() as $niche) {
            $tabs[$niche->slug] = Tab::make($niche->label)
                ->modifyQueryUsing(fn ($query) => $query->where('target_niche', $niche->slug));
        }

        return $tabs;
    }

    protected function getHeaderActions(): array
    {
        return [
            CreateAction::make()
                ->label('Novo Canal-fonte')
                ->modalHeading('Adicionar canal-fonte')
                ->modalSubmitActionLabel('Adicionar')
                ->form([
                    TextInput::make('url')
                        ->label('URL do canal YouTube')
                        ->helperText('Ex: https://youtube.com/@sportv  ou  https://youtube.com/channel/UC...')
                        ->placeholder('https://youtube.com/@...')
                        ->required(),

                    Niche::selectField('target_niche', 'Nicho de destino'),
                ])
                ->using(function (array $data): SourceChannel {
                    $client = app(ClipProcessorClient::class);

                    try {
                        $resolved = $client->resolveChannel((string) $data['url']);
                    } catch (RuntimeException $e) {
                        Notification::make()
                            ->title('Erro ao resolver canal')
                            ->body($e->getMessage())
                            ->danger()
                            ->persistent()
                            ->send();

                        throw ValidationException::withMessages(['url' => $e->getMessage()]);
                    }

                    $ytId = $resolved['channel_id'];

                    return SourceChannel::create([
                        'youtube_channel_id' => $ytId,
                        'channel_name'       => $resolved['channel_name'],
                        'channel_handle'     => $resolved['channel_handle'],
                        'rss_url'            => "https://www.youtube.com/feeds/videos.xml?channel_id={$ytId}",
                        'active'             => true,
                        'blacklisted'        => false,
                        'target_niche'       => $data['target_niche'] ?? 'futebol',
                    ]);
                }),
        ];
    }
}
