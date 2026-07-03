<?php

namespace App\Telegram\Commands;

use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use Telegram\Bot\Commands\Command;

class StatusCommand extends Command
{
    protected string $name        = 'status';
    protected string $description = 'Mostra status do pipeline';

    public function handle(): void
    {
        $videos = SourceVideo::query()
            ->selectRaw('status, count(*) as n')
            ->groupBy('status')
            ->pluck('n', 'status');

        $clips = GeneratedClip::query()
            ->selectRaw('status, count(*) as n')
            ->groupBy('status')
            ->pluck('n', 'status');

        $lines = ['Pipeline status:'];
        foreach ($videos as $s => $n) {
            $lines[] = "  vídeos {$s}: {$n}";
        }
        foreach ($clips as $s => $n) {
            $lines[] = "  clips {$s}: {$n}";
        }

        $this->replyWithMessage(['text' => implode("\n", $lines)]);
    }
}
