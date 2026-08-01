<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\DestinationChannelController;
use App\Http\Controllers\DocumentationController;
use App\Http\Controllers\NicheController;
use App\Http\Controllers\ProcessVideoController;
use App\Http\Controllers\SourceChannelController;
use App\Http\Controllers\SettingsController;
use App\Http\Controllers\SourceVideoController;
use App\Http\Controllers\TelegramWebhookController;
use App\Http\Controllers\TranscriptionController;
use App\Models\GeneratedClip;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Storage;

Route::middleware('guest')->group(function () {
    Route::get('/login', [AuthController::class, 'show'])->name('login');
    Route::post('/login', [AuthController::class, 'login']);
});

Route::post('/logout', [AuthController::class, 'logout'])
    ->middleware(['web', 'auth'])
    ->name('logout');

Route::middleware(['web', 'auth'])->group(function () {
    Route::get('/painel', [DashboardController::class, 'index'])->name('dashboard');
    Route::post('/painel/clips/{clip}/approve', [DashboardController::class, 'approve'])->name('dashboard.clips.approve');
    Route::post('/painel/clips/{clip}/reject', [DashboardController::class, 'reject'])->name('dashboard.clips.reject');
    Route::post('/painel/clips/{clip}/reprocess', [DashboardController::class, 'reprocess'])->name('dashboard.clips.reprocess');
    Route::post('/painel/clips/bulk-approve', [DashboardController::class, 'bulkApprove'])->name('dashboard.clips.bulk-approve');
    Route::post('/painel/clips/bulk-reject', [DashboardController::class, 'bulkReject'])->name('dashboard.clips.bulk-reject');
    Route::post('/painel/videos/reorder', [DashboardController::class, 'reorderVideos'])->name('dashboard.videos.reorder');
    Route::post('/painel/videos/{video}/delete', [DashboardController::class, 'deleteVideo'])->name('dashboard.videos.delete');
    Route::post('/painel/videos/{video}/pause', [DashboardController::class, 'pauseVideo'])->name('dashboard.videos.pause');
    Route::post('/painel/videos/{video}/resume', [DashboardController::class, 'resumeVideo'])->name('dashboard.videos.resume');
    Route::post('/painel/videos/{video}/prioritize', [DashboardController::class, 'prioritizeVideo'])->name('dashboard.videos.prioritize');

    // Preview leve do clip cortado direto no dashboard (checar legenda/qualidade
    // antes de aprovar) — serve o .mp4 já compartilhado via volume com o
    // clip-processor (ver docker-compose.yml e config/filesystems.php 'clips-videos').
    Route::get('/painel/clips/{clip}/preview', function (GeneratedClip $clip) {
        $relativePath = "clips/{$clip->id}.mp4";

        if (! Storage::disk('clips-videos')->exists($relativePath)) {
            abort(404);
        }

        return response()->file(Storage::disk('clips-videos')->path($relativePath));
    })->name('clips.preview');

    Route::post('/painel/niches', [NicheController::class, 'store'])->name('niches.store');

    Route::get('/painel/canais-destino', [DestinationChannelController::class, 'index'])->name('destination-channels.index');
    Route::post('/painel/canais-destino', [DestinationChannelController::class, 'store'])->name('destination-channels.store');
    Route::put('/painel/canais-destino/{destinationChannel}', [DestinationChannelController::class, 'update']);
    Route::post('/painel/canais-destino/{destinationChannel}/watermark', [DestinationChannelController::class, 'uploadWatermark']);
    Route::delete('/painel/canais-destino/{destinationChannel}', [DestinationChannelController::class, 'destroy']);

    Route::get('/painel/canais-fonte', [SourceChannelController::class, 'index'])->name('source-channels.index');
    Route::post('/painel/canais-fonte', [SourceChannelController::class, 'store'])->name('source-channels.store');
    Route::put('/painel/canais-fonte/{sourceChannel}', [SourceChannelController::class, 'update'])->name('source-channels.update');
    Route::delete('/painel/canais-fonte/{sourceChannel}', [SourceChannelController::class, 'destroy']);

    Route::get('/painel/videos', [SourceVideoController::class, 'index'])->name('source-videos.index');
    Route::post('/painel/videos/{video}/delete-file', [SourceVideoController::class, 'deleteFile']);
    Route::post('/painel/videos/bulk-delete-files', [SourceVideoController::class, 'bulkDeleteFiles']);
    Route::post('/painel/videos/purge-old', [SourceVideoController::class, 'purgeOld']);

    Route::get('/painel/processar-video', [ProcessVideoController::class, 'show'])->name('process-video.show');
    Route::post('/painel/processar-video', [ProcessVideoController::class, 'store']);

    Route::get('/painel/transcricoes', [TranscriptionController::class, 'index'])->name('transcriptions.index');
    Route::post('/painel/transcricoes', [TranscriptionController::class, 'store']);
    Route::get('/painel/transcricoes/{job}/download', [TranscriptionController::class, 'download'])->name('transcriptions.download');

    Route::get('/painel/documentacao', [DocumentationController::class, 'show'])->name('documentation.show');

    Route::get('/painel/configuracoes', [SettingsController::class, 'show'])->name('settings.show');
    Route::put('/painel/configuracoes/senha', [SettingsController::class, 'updatePassword'])->name('settings.password');
});

// URL raiz = o painel (decisão CONTEXT.md: "canaldecortes.local raiz, sem
// subdomínio 'painel' — o painel É o Canal de Cortes para o operador").
// Logado vai direto pro painel; deslogado vai pro login (sem redirect duplo).
Route::get('/', fn () => redirect(auth()->check() ? '/painel' : '/login'));

// Phase 9 (BOT-01, BOT-03): rotas sem autenticação — chamadas por Telegram e pelo clip-processor.
// CSRF excluído para ambas em bootstrap/app.php (Plan 09-01).
Route::post('/telegramcanal', [TelegramWebhookController::class, 'handle']);
Route::post('/internal/pipeline-event', [TelegramWebhookController::class, 'pipelineEvent']);
