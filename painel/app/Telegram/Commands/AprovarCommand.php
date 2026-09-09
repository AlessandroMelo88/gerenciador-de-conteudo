<?php

namespace App\Telegram\Commands;

use App\Models\GeneratedClip;
use Telegram\Bot\Commands\Command;

class AprovarCommand extends Command
{
    protected string $name        = 'aprovar';
    protected string $description = 'Aprova um clip para publicação';
    protected string $pattern     = '{clip_id}';

    public function handle(): void
    {
        $clipId = (int) $this->argument('clip_id');

        if (! $clipId) {
            $this->replyWithMessage(['text' => 'Uso: /aprovar <id>']);

            return;
        }

        $affected = GeneratedClip::query()
            ->where('id', $clipId)
            ->where('status', 'pending')
            ->update(['status' => 'approved']);

        $text = $affected
            ? "Clip #{$clipId} aprovado e enviado para publicação."
            : "Clip #{$clipId} não encontrado ou status inválido para aprovação.";

        if ($affected) {
            try {
                app(\App\Services\ClipProcessorClient::class)->publishNow();
            } catch (\Throwable) {}
        }

        $this->replyWithMessage(['text' => $text]);
    }
}
