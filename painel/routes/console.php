<?php

use Illuminate\Support\Facades\Schedule;

/**
 * Resumo diário às 18h no fuso da aplicação.
 * O comando sai silenciosamente quando não existem clips pendentes.
 */
Schedule::command('painel:daily-summary')
    ->dailyAt('18:00')
    ->timezone(config('app.timezone', 'America/Sao_Paulo'));

/**
 * Backup diário automatizado do banco de dados com compressão e retenção.
 */
Schedule::command('db:backup')->dailyAt('03:15')->withoutOverlapping();

/**
 * Afiliados: divulga ofertas aprovadas no canal do Telegram do nicho.
 * Poucas por rodada e só em horário comercial — canal não vira spam.
 */
Schedule::command('offers:publish-telegram')
    ->everyThirtyMinutes()
    ->between('08:00', '22:00')
    ->timezone('America/Sao_Paulo')
    ->withoutOverlapping();
