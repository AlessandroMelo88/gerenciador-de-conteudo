<?php

use Illuminate\Support\Facades\Schedule;

/**
 * Resumo diário às 18h no fuso da aplicação.
 * O comando sai silenciosamente quando não existem clips pendentes.
 */
Schedule::command('painel:daily-summary')
    ->dailyAt('18:00')
    ->timezone(config('app.timezone'));
