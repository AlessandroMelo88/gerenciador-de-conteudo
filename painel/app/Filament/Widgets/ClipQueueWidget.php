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

    public function formatTrecho(?float $start, ?float $end): string
    {
        if ($start === null || $end === null) {
            return '—';
        }

        $fmt = fn (float $seconds): string => sprintf('%d:%02d', intdiv((int) $seconds, 60), (int) $seconds % 60);

        return "{$fmt($start)}–{$fmt($end)}";
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

    /**
     * Reenvia um clip 'failed' para reprocessamento: volta pra 'pending_cut' se o
     * corte nunca terminou (clip_path vazio), ou pro status publicável (approved/
     * pending, conforme MANUAL_APPROVAL_REQUIRED) se o corte existe e só o upload falhou.
     */
    public function reprocessar(int $id): void
    {
        $clip = GeneratedClip::find($id);

        if (! $clip || $clip->status !== 'failed') {
            Notification::make()->title('Clip não está mais em falha')->warning()->send();

            return;
        }

        $manualApproval = filter_var(env('MANUAL_APPROVAL_REQUIRED', false), FILTER_VALIDATE_BOOLEAN);
        $newStatus = $clip->clip_path ? ($manualApproval ? 'approved' : 'pending') : 'pending_cut';

        $affected = GeneratedClip::query()
            ->where('id', $id)
            ->where('status', 'failed')
            ->update(['status' => $newStatus, 'upload_error' => null]);

        if ($affected === 0) {
            Notification::make()->title('Clip não está mais em falha')->warning()->send();

            return;
        }

        Notification::make()->title("Clip #{$id} reenviado para reprocessamento")->success()->send();
    }

    /** IDs marcados via checkbox nas tabs "Fila de aprovação" e "Na fila". */
    public array $selected = [];

    public function toggleSelectAll(string $tab): void
    {
        $ids = match ($tab) {
            'pending' => $this->getViewData()['pendingClips']->pluck('id')->all(),
            'queued' => $this->getViewData()['queuedClips']->pluck('id')->all(),
            default => [],
        };

        $this->selected = array_intersect($this->selected, $ids) === $this->selected && count($this->selected) === count($ids)
            ? []
            : $ids;
    }

    public function aprovarSelecionados(): void
    {
        if (empty($this->selected)) {
            return;
        }

        $affected = GeneratedClip::query()
            ->whereIn('id', $this->selected)
            ->where('status', 'pending')
            ->update(['status' => 'approved']);

        $this->selected = [];
        Notification::make()->title("{$affected} clip(s) aprovado(s)")->success()->send();
    }

    public function rejeitarSelecionados(): void
    {
        if (empty($this->selected)) {
            return;
        }

        $client = app(ClipProcessorClient::class);
        $ok = 0;
        $fail = 0;

        foreach ($this->selected as $id) {
            try {
                $exit = $client->rejectClip((int) $id);
                $exit === 0 ? $ok++ : $fail++;
            } catch (RuntimeException) {
                $fail++;
            }
        }

        $this->selected = [];

        Notification::make()
            ->title("{$ok} clip(s) rejeitado(s)".($fail ? ", {$fail} falharam" : ''))
            ->color($fail ? 'warning' : 'success')
            ->send();
    }

    protected function getViewData(): array
    {
        return [
            'pendingClips' => GeneratedClip::with(['sourceVideo.sourceChannel', 'destinationChannel'])
                ->where('status', 'pending')
                ->latest()
                ->get(),
            'queuedClips' => GeneratedClip::with(['sourceVideo.sourceChannel', 'destinationChannel'])
                ->where('status', 'approved')
                ->oldest('created_at')
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
