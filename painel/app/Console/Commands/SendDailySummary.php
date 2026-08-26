<?php

namespace App\Console\Commands;

use App\Models\GeneratedClip;
use Illuminate\Console\Command;
use Telegram\Bot\Laravel\Facades\Telegram;

class SendDailySummary extends Command
{
    protected $signature = 'painel:daily-summary';

    protected $description = 'Envia ao operador um resumo dos clips pendentes.';

    public function handle(): int
    {
        $pending = GeneratedClip::query()
            ->where('status', 'pending')
            ->count();

        if ($pending === 0) {
            return self::SUCCESS;
        }

        Telegram::sendMessage([
            'chat_id' => config('telegram.bots.mybot.chat_id_allowed'),
            'text' => "Resumo diário: {$pending} clip(s) aguardando aprovação.",
        ]);

        return self::SUCCESS;
    }
}
