<?php

namespace App\Filament\Resources\SourceChannelResource\Pages;

use App\Filament\Resources\SourceChannelResource;
use App\Models\SourceChannel;
use App\Services\ClipProcessorClient;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\CreateRecord;
use RuntimeException;

class CreateSourceChannel extends CreateRecord
{
    protected static string $resource = SourceChannelResource::class;

    protected function handleRecordCreation(array $data): SourceChannel
    {
        $client = app(ClipProcessorClient::class);

        try {
            $resolved = $client->resolveChannel((string) $data['url']);
        } catch (RuntimeException $e) {
            Notification::make()
                ->title('Erro ao resolver canal')
                ->body($e->getMessage())
                ->danger()
                ->send();

            $this->halt();  // impede persistência
        }

        $ytId = $resolved['channel_id'];

        return SourceChannel::create([
            'youtube_channel_id' => $ytId,
            'channel_name' => $resolved['channel_name'],
            'channel_handle' => $resolved['channel_handle'],
            'rss_url' => "https://www.youtube.com/feeds/videos.xml?channel_id={$ytId}",
            'active' => true,
            'blacklisted' => false,
            'target_niche' => $data['target_niche'] ?? 'futebol',
        ]);
    }
}
