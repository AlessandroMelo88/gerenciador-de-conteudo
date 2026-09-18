<?php

/*
 * Afiliados — divulgação de ofertas aprovadas.
 *
 * AFFILIATE_TELEGRAM_CHANNELS mapeia nicho → chat do Telegram, separado por vírgula:
 *   AFFILIATE_TELEGRAM_CHANNELS="futebol=@canal_futebol,politica=-1001234567890"
 * Nicho fora do mapa não é divulgado (a oferta fica aprovada, sem envio).
 * O bot precisa ser administrador do canal para postar.
 */

$channels = [];
foreach (explode(',', (string) env('AFFILIATE_TELEGRAM_CHANNELS', '')) as $pair) {
    [$niche, $chat] = array_pad(explode('=', $pair, 2), 2, '');
    $niche = trim($niche);
    $chat = trim($chat);
    if ($niche !== '' && $chat !== '') {
        $channels[$niche] = $chat;
    }
}

return [
    // Fuso dos relatórios (tela de performance). O banco grava em UTC.
    'report_timezone' => 'America/Sao_Paulo',

    'telegram' => [
        'bot' => 'mybot',
        'channels' => $channels,
        // Teto por execução do agendador — evita despejar o acervo inteiro de uma vez no canal.
        'per_run' => (int) env('AFFILIATE_TELEGRAM_PER_RUN', 3),
    ],
];
