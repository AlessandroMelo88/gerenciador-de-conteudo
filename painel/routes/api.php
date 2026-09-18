<?php

use App\Http\Controllers\Api\OfferApiController;
use App\Http\Middleware\AffiliateApiToken;
use Illuminate\Support\Facades\Route;

// API máquina-a-máquina do worker de afiliados (PLANO-MESTRE seção 6).
// Prefixo /api vem de bootstrap/app.php. Sem Sanctum: Bearer fixo (AFFILIATE_API_TOKEN).
// Throttle antes do token para limitar tentativa de força bruta.
Route::middleware(['throttle:60,1', AffiliateApiToken::class])->group(function () {
    Route::get('/offers', [OfferApiController::class, 'index'])->name('api.offers.index');
    Route::post('/offers', [OfferApiController::class, 'store'])->name('api.offers.store');
});
