<?php

namespace App\Filament\Widgets;

use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use App\Services\ClipProcessorClient;
use Filament\Notifications\Notification;
use Filament\Widgets\Widget;
use RuntimeException;

class ClipQueueWidget extends Widget
{
    protected string $view = 'filament.widgets.clip-queue';

    protected static ?int $sort = 2;

    protected int|string|array $columnSpan = 'full';

    protected static bool $isLazy = false;

    public string $activeTab = 'pending';

    public function setTab(string $tab): void
    {
        $this->activeTab = $tab;
    }

    public function aprovar(int $id): void
    {
        $affected = GeneratedClip::query()
            ->where('id', $id)
            ->where('status', 'pending')
            ->update(['status' => 'approved']);

        if ($affected === 0) {
            Notification::make()->title('Clip não estava mais pendente')->warning()->send();

            return;
        }

        Notification::make()->title("Clip #{$id} aprovado")->success()->send();
    }

    public function rejeitar(int $id): void
    {
        $client = app(ClipProcessorClient::class);

        try {
            $exit = $client->rejectClip($id);
        } catch (RuntimeException $e) {
            Notification::make()->title('Falha ao rejeitar')->body($e->getMessage())->danger()->send();

            return;
        }

        match ($exit) {
            0 => Notification::make()->title("Clip #{$id} rejeitado (MP4 removido)")->success()->send(),
            1 => Notification::make()->title('Clip não existe')->danger()->send(),
            2 => Notification::make()->title('Status inválido para rejeitar')->danger()->send(),
            default => Notification::make()->title("Erro exit_code={$exit}")->danger()->send(),
        };
    }

    protected function getViewData(): array
    {
        return [
            'pendingClips' => GeneratedClip::with(['sourceVideo', 'destinationChannel'])
                ->where('status', 'pending')
                ->latest()
                ->get(),
            'uploads' => GeneratedClip::with(['destinationChannel'])
                ->where('status', 'published')
                ->latest()
                ->limit(10)
                ->get(),
            'failures' => GeneratedClip::with(['destinationChannel'])
                ->where('status', 'failed')
                ->latest('updated_at')
                ->limit(20)
                ->get(),
            'failedSourceVideoCount' => SourceVideo::where('status', 'failed')->count(),
        ];
    }
}
