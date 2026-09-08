<?php

namespace App\Providers;

use App\Services\TelegramHttpClientHandler;
use Illuminate\Support\ServiceProvider;
use Telegram\Bot\BotsManager;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        \Illuminate\Support\Carbon::setLocale('pt_BR');
        setlocale(LC_TIME, 'pt_BR.utf8', 'pt_BR', 'portuguese');

        // Substitui o GuzzleHttpClient padrão do SDK Telegram pelo handler Laravel.
        // TelegramServiceProvider é DeferrableProvider — o singleton BotsManager::class é
        // criado lazily (na primeira resolução). Usamos BotsManager::class como abstract
        // (não o alias 'telegram') para que o extender seja encontrado pela chave canônica
        // quando o container resolve a dependência.
        //
        // Benefício: Http::fake() intercepta todas as chamadas à API do Telegram em testes,
        // habilitando Http::assertSent() e Http::assertSentCount() nos Feature tests.
        $this->app->extend(BotsManager::class, function (BotsManager $manager, $app) {
            $config = config('telegram');
            $config['http_client_handler'] = new TelegramHttpClientHandler();

            return (new BotsManager($config))->setContainer($app);
        });
    }
}
