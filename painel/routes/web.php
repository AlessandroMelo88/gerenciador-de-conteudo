<?php

use App\Models\DestinationChannel;
use App\Models\SourceChannel;
use App\Services\ClipProcessorClient;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

// Rotas REST usadas pelo SourceChannelResource (Plan 08-05, PANEL-01).
// O painel Filament (Livewire) cobre o fluxo real do operador via /admin/source-channels,
// mas o contrato de testes RED (Plan 08-03) exige endpoints REST diretos para criar/atualizar.
Route::middleware(['web', 'auth'])->group(function () {
    Route::post('/admin/source-channels', function (Request $request, ClipProcessorClient $client) {
        $data = $request->validate([
            'url' => ['required', 'string'],
            'target_niche' => ['required', 'string'],
        ]);

        try {
            $resolved = $client->resolveChannel($data['url']);
        } catch (RuntimeException $e) {
            return back()->withErrors(['url' => $e->getMessage()])->withInput();
        }

        $ytId = $resolved['channel_id'];

        SourceChannel::create([
            'youtube_channel_id' => $ytId,
            'channel_name' => $resolved['channel_name'],
            'channel_handle' => $resolved['channel_handle'],
            'rss_url' => "https://www.youtube.com/feeds/videos.xml?channel_id={$ytId}",
            'active' => true,
            'blacklisted' => false,
            'target_niche' => $data['target_niche'],
        ]);

        return redirect('/admin/source-channels');
    })->name('source-channels.store');

    Route::patch('/admin/source-channels/{sourceChannel}', function (Request $request, SourceChannel $sourceChannel) {
        $data = $request->validate([
            'blacklisted' => ['sometimes', 'boolean'],
            'active' => ['sometimes', 'boolean'],
        ]);

        $sourceChannel->update($data);

        return redirect('/admin/source-channels');
    })->name('source-channels.update');

    // Rota REST usada pelo DestinationChannelResource (Plan 08-06, PANEL-02).
    // Mesmo motivo do bloco source-channels acima: Filament Resource só expõe GET/HEAD
    // (submit real via Livewire); o contrato de testes RED (Plan 08-03) exige POST direto.
    Route::post('/admin/destination-channels', function (Request $request) {
        $data = $request->validate([
            'slug' => ['required', 'string'],
            'name' => ['required', 'string'],
            'niche' => ['required', 'string'],
            'youtube_channel_id' => ['required', 'string'],
            'credit_template' => ['sometimes', 'nullable', 'string'],
            'active' => ['sometimes', 'boolean'],
        ]);

        DestinationChannel::create([
            'slug' => $data['slug'],
            'name' => $data['name'],
            'niche' => $data['niche'],
            'youtube_channel_id' => $data['youtube_channel_id'],
            'credit_template' => $data['credit_template'] ?? 'Créditos: @{channel_handle}',
            'active' => $data['active'] ?? true,
        ]);

        return redirect('/admin/destination-channels');
    })->name('destination-channels.store');
});
