<?php

return [
    'bots' => [
        'mybot' => [
            'token'           => env('TELEGRAM_BOT_TOKEN'),
            'webhook_url'     => env('TELEGRAM_WEBHOOK_URL', 'https://alessandromelo.com.br/telegramcanal'),
            'chat_id_allowed' => env('TELEGRAM_CHAT_ID_ALLOWED', '5760918317'),
            'commands'        => [],  // preenchido no Plan 09-02
        ],
    ],
    'default' => 'mybot',

    // Configurações globais do SDK (manter defaults do vendor)
    'async_requests'    => false,
    'http_client_handler' => null,
    'resolve_command_class' => true,
];
