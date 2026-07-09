<?php

namespace App\Filament\Widgets;

use App\Models\GeneratedClip;
use App\Services\ClipProcessorClient;
use Filament\Actions\Action;
use Filament\Notifications\Notification;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;
use Filament\Widgets\TableWidget as BaseWidget;
use RuntimeException;

class PendingApprovalWidget extends BaseWidget
{
    protected static ?int $sort = 2;

    protected int|string|array $columnSpan = 'full';

    public static function canView(): bool { return false; }

    protected static ?string $heading = 'Fila de aprovação';

    // Widgets Filament 5 são lazy por padrão (x-intersect/AJAX) — desabilitado para
    // que ->poll('5s') apareça no HTML inicial e a fila fique visível de imediato.
    protected static bool $isLazy = false;

    public function table(Table $table): Table
    {
        return $table
            ->query(GeneratedClip::query()->where('status', 'pending')->latest())
            ->poll('5s')
            ->columns([
                TextColumn::make('id')->label('ID')->sortable(),
                TextColumn::make('title')->label('Título')->limit(60),
                TextColumn::make('sourceVideo.title')->label('Vídeo-fonte')->limit(40)->toggleable(),
                TextColumn::make('destinationChannel.name')->label('Destino'),
                TextColumn::make('score')->label('Score')->badge(),
                TextColumn::make('created_at')->label('Criado')->since(),
            ])
            ->recordActions([
                Action::make('aprovar')
                    ->label('Aprovar')
                    ->color('success')
                    ->icon('heroicon-o-check-badge')
                    ->requiresConfirmation()
                    ->action(function (GeneratedClip $record) {
                        $affected = GeneratedClip::query()
                            ->where('id', $record->id)
                            ->where('status', 'pending')
                            ->update(['status' => 'approved']);

                        if ($affected === 0) {
                            Notification::make()->title('Clip não estava mais pending')->warning()->send();

                            return;
                        }

                        Notification::make()->title("Clip #{$record->id} aprovado")->success()->send();
                    }),
                Action::make('rejeitar')
                    ->label('Rejeitar')
                    ->color('danger')
                    ->icon('heroicon-o-x-circle')
                    ->requiresConfirmation()
                    ->action(function (GeneratedClip $record) {
                        $client = app(ClipProcessorClient::class);

                        try {
                            $exit = $client->rejectClip($record->id);
                        } catch (RuntimeException $e) {
                            Notification::make()->title('Falha ao rejeitar')->body($e->getMessage())->danger()->send();
                            session()->flash('error', $e->getMessage());

                            return;
                        }

                        match ($exit) {
                            0 => Notification::make()->title("Clip #{$record->id} rejeitado (MP4 removido)")->success()->send(),
                            1 => $this->flashRejectError('Clip não existe'),
                            2 => $this->flashRejectError('Status inválido para rejeitar'),
                            default => $this->flashRejectError("exit_code={$exit}"),
                        };
                    }),
            ]);
    }

    protected function flashRejectError(string $message): void
    {
        session()->flash('error', $message);
        Notification::make()->title($message)->danger()->send();
    }
}
