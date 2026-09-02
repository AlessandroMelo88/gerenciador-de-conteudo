<?php

use App\Models\GeneratedClip;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schedule;
use Telegram\Bot\Laravel\Facades\Telegram;

// Comando legado
Artisan::command('inspire', function () {
    $this->comment(\Illuminate\Foundation\Inspiring::quote());
})->purpose('Display an inspiring quote');

/**
 * Resumo diário às 18h BRT — substitui o workflow n8n 06-cron-resumo-diario.json.
 * Regra Phase 6: skip silencioso se 0 clips pendentes.
 */
Schedule::call(function () {
    $pending = GeneratedClip::where('status', 'pending')->count();
    if ($pending === 0) {
        return;  // skip se não há clips aguardando — idêntico ao comportamento do n8n
    }

    Telegram::sendMessage([
        'chat_id' => config('telegram.bots.mybot.chat_id_allowed'),
        'text'    => "Resumo diário: {$pending} clip(s) aguardando aprovação.",
    ]);
})->dailyAt('18:00')->timezone('America/Sao_Paulo');

/**
 * Backup diário automatizado do banco de dados com compressão e retenção.
 */
Schedule::command('db:backup')->dailyAt('03:15')->withoutOverlapping();

