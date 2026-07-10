<?php

namespace App\Filament\Pages;

use App\Services\ClipProcessorClient;
use BackedEnum;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Filament\Schemas\Schema;
use Filament\Actions\Action;
use RuntimeException;

class ProcessVideo extends Page implements HasForms
{
    use InteractsWithForms;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-link';

    protected static ?string $navigationLabel = 'Processar Vídeo';

    protected static ?string $title = 'Processar Vídeo Manualmente';

    protected static ?int $navigationSort = 10;

    protected string $view = 'filament.pages.process-video';

    /** @var array<string, mixed> */
    public array $data = [];

    public function mount(): void
    {
        $this->form->fill();
    }

    public function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Textarea::make('urls')
                    ->label('URLs do YouTube (uma por linha)')
                    ->helperText('Cole um ou mais links de vídeos do YouTube, um por linha. Cada vídeo entra na fila normal do pipeline (download → transcrição → seleção → corte).')
                    ->placeholder("https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...")
                    ->rows(6)
                    ->required(),
            ])
            ->statePath('data');
    }

    protected function getFormActions(): array
    {
        return [
            Action::make('submit')
                ->label('Enfileirar vídeo(s)')
                ->submit('submit'),
        ];
    }

    public function submit(): void
    {
        $state = $this->form->getState();

        $urls = collect(preg_split('/\r\n|\r|\n/', (string) $state['urls']))
            ->map(fn ($url) => trim($url))
            ->filter()
            ->unique()
            ->values();

        if ($urls->isEmpty()) {
            return;
        }

        $client = app(ClipProcessorClient::class);

        $ok = [];
        $failed = [];

        foreach ($urls as $url) {
            try {
                $exitCode = $client->processUrl($url);

                match ($exitCode) {
                    0 => $ok[] = $url,
                    2 => $failed[] = "{$url} — URL inválida",
                    3 => $failed[] = "{$url} — não consegui buscar metadados (vídeo privado/removido/bloqueado por região)",
                    default => $failed[] = "{$url} — erro desconhecido (exit code {$exitCode})",
                };
            } catch (RuntimeException $e) {
                $failed[] = "{$url} — {$e->getMessage()}";
            }
        }

        if (count($ok) > 0) {
            Notification::make()
                ->title(count($ok) === 1 ? 'Vídeo enfileirado' : count($ok).' vídeos enfileirados')
                ->body('Entraram na fila do pipeline. Acompanhe o status em Canais Fonte / dashboard.')
                ->success()
                ->send();
        }

        if (count($failed) > 0) {
            Notification::make()
                ->title('Alguns vídeos falharam')
                ->body(implode("\n", $failed))
                ->danger()
                ->persistent()
                ->send();
        }

        if (count($ok) > 0) {
            $this->form->fill();
        }
    }
}
