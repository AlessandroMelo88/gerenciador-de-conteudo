<?php

use App\Http\Middleware\HandleInertiaRequests;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Http\Request;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->trustProxies(at: '*');
        $middleware->preventRequestForgery(except: [
            'telegramcanal',
            'internal/pipeline-event',
        ]);
        // Durante o deploy (`artisan down`) o painel mostra a página de manutenção,
        // mas evento do pipeline, webhook do Telegram e link rastreável seguem
        // atendidos — perder um deles custa mais que os segundos de deploy.
        $middleware->preventRequestsDuringMaintenance(except: [
            'internal/*',
            'telegramcanal',
            'o/*',
        ]);
        $middleware->web(append: [
            HandleInertiaRequests::class,
        ]);
        $middleware->redirectGuestsTo('/login');
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->shouldRenderJsonWhen(
            fn (Request $request) => $request->is('api/*'),
        );
    })->create();
