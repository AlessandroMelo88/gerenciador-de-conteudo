<?php

namespace App\Telegram\Commands;

use App\Services\ClipProcessorClient;
use Telegram\Bot\Commands\Command;

class ProcessarCommand extends Command
{
    protected string $name        = 'processar';
    protected string $description = 'Adiciona vídeo ao pipeline pelo URL do YouTube';
    protected string $pattern     = '{url}';

    public function handle(): void
    {
        $url = $this->argument('url');

        if (! $url) {
            $this->replyWithMessage(['text' => 'Uso: /processar <url_youtube>']);

            return;
        }

        try {
            $exit = app(ClipProcessorClient::class)->processUrl($url);
        } catch (\RuntimeException $e) {
            $this->replyWithMessage(['text' => "Erro ao processar URL: {$e->getMessage()}"]);

            return;
        }

        $text = match ($exit) {
            0       => 'URL enfileirada com sucesso. Pipeline processará em breve.',
            2       => 'URL inválida — verifique o link do YouTube.',
            3       => 'Falha ao buscar metadados do vídeo (yt-dlp).',
            default => "exit_code={$exit}.",
        };

        $this->replyWithMessage(['text' => $text]);
    }
}
