<?php

namespace App\Console\Commands;

use App\Models\Offer;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Telegram\Bot\Laravel\Facades\Telegram;
use Throwable;

class PublishOffersToTelegram extends Command
{
    protected $signature = 'offers:publish-telegram
        {--limit= : Máximo de ofertas nesta execução (default: affiliates.telegram.per_run)}
        {--dry-run : Mostra o que seria enviado, sem enviar nem marcar}';

    protected $description = 'Divulga no Telegram as ofertas aprovadas ainda não enviadas (canal por nicho)';

    /** Telegram corta em 4096; sobra espaço para o link. */
    private const MAX_BODY = 3500;

    public function handle(): int
    {
        $bot = config('affiliates.telegram.bot');
        $channels = (array) config('affiliates.telegram.channels', []);

        if (blank(config("telegram.bots.{$bot}.token"))) {
            $this->warn('TELEGRAM_BOT_TOKEN vazio — nada enviado.');

            return self::FAILURE;
        }

        if ($channels === []) {
            $this->warn('AFFILIATE_TELEGRAM_CHANNELS vazio — nenhum nicho tem canal de destino.');

            return self::FAILURE;
        }

        $limit = max(1, (int) ($this->option('limit') ?? config('affiliates.telegram.per_run', 3)));
        $dryRun = (bool) $this->option('dry-run');

        // Só nichos com canal entram: oferta de nicho sem canal não trava a fila dos outros.
        $offers = Offer::query()
            ->where('status', 'approved')
            ->whereNull('telegram_posted_at')
            ->whereIn('niche', array_keys($channels))
            ->orderBy('approved_at')
            ->orderBy('id')
            ->limit($limit)
            ->get();

        $sent = 0;
        $failed = 0;

        foreach ($offers as $offer) {
            $chatId = $channels[$offer->niche];
            $text = $this->message($offer);

            if ($dryRun) {
                $this->line("[dry-run] #{$offer->id} → {$chatId}\n{$text}\n");

                continue;
            }

            // Reserva atômica antes de enviar: duas execuções simultâneas não postam a mesma
            // oferta. Queda entre a reserva e o envio perde o post (at-most-once) — preferível
            // a repetir oferta no canal.
            $claimed = Offer::query()
                ->whereKey($offer->id)
                ->where('status', 'approved')
                ->whereNull('telegram_posted_at')
                ->toBase()
                ->update(['telegram_posted_at' => now()]);

            if ($claimed === 0) {
                continue;
            }

            try {
                Telegram::bot($bot)->sendMessage([
                    'chat_id' => $chatId,
                    'text' => $text,
                ]);
                $sent++;
                $this->info("#{$offer->id} enviada para {$chatId}");
            } catch (Throwable $e) {
                // Devolve para a fila: a próxima execução tenta de novo.
                Offer::query()->whereKey($offer->id)->toBase()->update(['telegram_posted_at' => null]);
                $failed++;
                Log::warning('offers:publish-telegram falhou', ['offer_id' => $offer->id, 'error' => $e->getMessage()]);
                $this->error("#{$offer->id} falhou: {$e->getMessage()}");
            }
        }

        if (! $dryRun) {
            $this->line("Enviadas: {$sent}. Falhas: {$failed}.");
        }

        return $failed > 0 ? self::FAILURE : self::SUCCESS;
    }

    private function message(Offer $offer): string
    {
        $body = trim((string) ($offer->copy_short ?: $offer->cta_text ?: $offer->title));

        return Str::limit($body, self::MAX_BODY)."\n\n".$offer->trackingUrl().'?c=telegram';
    }
}
