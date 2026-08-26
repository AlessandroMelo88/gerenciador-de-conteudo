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
            'webhook_url' => env('TELEGRAM_WEBHOOK_URL'),
            'chat_id_allowed' => env('TELEGRAM_CHAT_ID_ALLOWED'),
            'webhook_secret' => env('TELEGRAM_WEBHOOK_SECRET'),
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

    // Handler substituído em AppServiceProvider para permitir Http::fake() nos testes.
    'async_requests' => false,
    'http_client_handler' => null,
    'resolve_command_class' => true,
];
