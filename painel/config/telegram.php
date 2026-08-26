<?php

use App\Telegram\Commands\AjudaCommand;
use App\Telegram\Commands\AprovarCommand;
use App\Telegram\Commands\ClipesCommand;
use App\Telegram\Commands\ProcessarCommand;
use App\Telegram\Commands\RejeitarCommand;
use App\Telegram\Commands\StatusCommand;

return [
    'bots' => [
        'mybot' => [
            'token' => env('TELEGRAM_BOT_TOKEN'),
            'webhook_url' => env('TELEGRAM_WEBHOOK_URL', 'https://alessandromelo.com.br/telegramcanal'),
            'chat_id_allowed' => env('TELEGRAM_CHAT_ID_ALLOWED', '5760918317'),
            'commands' => [
                StatusCommand::class,
                ClipesCommand::class,
                AprovarCommand::class,
                RejeitarCommand::class,
                ProcessarCommand::class,
                AjudaCommand::class,
            ],
        ],
    ],
    'default' => 'mybot',

    // Configurações globais do SDK (manter defaults do vendor)
    'async_requests' => false,
    'http_client_handler' => null,
    'resolve_command_class' => true,
];
