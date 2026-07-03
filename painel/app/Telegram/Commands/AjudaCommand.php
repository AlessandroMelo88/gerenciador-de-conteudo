<?php

namespace App\Telegram\Commands;

use Telegram\Bot\Commands\Command;

class AjudaCommand extends Command
{
    protected string $name        = 'ajuda';
    protected string $description = 'Lista os comandos disponíveis';

    public function handle(): void
    {
        $text = implode("\n", [
            'Comandos disponíveis:',
            '/status — status do pipeline',
            '/clipes — clips aguardando aprovação',
            '/aprovar <id> — aprova clip para publicação',
            '/rejeitar <id> — rejeita clip e apaga MP4',
            '/processar <url> — adiciona vídeo ao pipeline',
            '/ajuda — exibe esta mensagem',
        ]);

        $this->replyWithMessage(['text' => $text]);
    }
}
