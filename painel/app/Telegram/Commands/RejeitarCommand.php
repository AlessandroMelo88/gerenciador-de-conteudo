<?php

namespace App\Telegram\Commands;

use App\Services\ClipProcessorClient;
use Telegram\Bot\Commands\Command;

class RejeitarCommand extends Command
{
    protected string $name        = 'rejeitar';
    protected string $description = 'Rejeita um clip e apaga o MP4';
    protected string $pattern     = '{clip_id}';

    public function handle(): void
    {
        $clipId = (int) $this->argument('clip_id');

        if (! $clipId) {
            $this->replyWithMessage(['text' => 'Uso: /rejeitar <id>']);

            return;
        }

        try {
            $exit = app(ClipProcessorClient::class)->rejectClip($clipId);
        } catch (\RuntimeException $e) {
            $this->replyWithMessage(['text' => "Erro ao rejeitar clip #{$clipId}: {$e->getMessage()}"]);

            return;
        }

        $text = match ($exit) {
            0       => "Clip #{$clipId} rejeitado e MP4 apagado.",
            1       => "Clip #{$clipId} não encontrado.",
            2       => "Clip #{$clipId} já está em status inválido para rejeição.",
            default => "Clip #{$clipId}: exit_code={$exit}.",
        };

        $this->replyWithMessage(['text' => $text]);
    }
}
