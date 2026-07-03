<?php

namespace App\Telegram\Commands;

use App\Models\GeneratedClip;
use Telegram\Bot\Commands\Command;

class ClipesCommand extends Command
{
    protected string $name        = 'clipes';
    protected string $description = 'Lista clips aguardando aprovação';

    public function handle(): void
    {
        $clips = GeneratedClip::query()
            ->whereIn('status', ['pending', 'approved'])
            ->orderBy('created_at', 'desc')
            ->limit(10)
            ->get(['id', 'title', 'status', 'created_at']);

        if ($clips->isEmpty()) {
            $this->replyWithMessage(['text' => 'Nenhum clip aguardando aprovação.']);

            return;
        }

        $lines = ['Clips pendentes:'];
        foreach ($clips as $clip) {
            $lines[] = "  #{$clip->id} [{$clip->status}] {$clip->title}";
        }

        $this->replyWithMessage(['text' => implode("\n", $lines)]);
    }
}
