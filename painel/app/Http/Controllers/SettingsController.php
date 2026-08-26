<?php

namespace App\Http\Controllers;

use App\Models\DestinationChannel;
use App\Models\MediaAsset;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;
use Inertia\Inertia;
use Inertia\Response;

class SettingsController extends Controller
{
    public function show(): Response
    {
        $assets = MediaAsset::query()
            ->with('destinationChannel:id,name')
            ->latest()
            ->get()
            ->map(fn (MediaAsset $asset) => [
                'id' => $asset->id,
                'kind' => $asset->kind,
                'name' => $asset->name,
                'format' => $asset->format,
                'durationSeconds' => $asset->duration_seconds,
                'musicVolume' => $asset->music_volume,
                'priority' => $asset->priority,
                'active' => $asset->active,
                'fileName' => basename($asset->path),
                'destinationChannelId' => $asset->destination_channel_id,
                'destinationChannelName' => $asset->destinationChannel?->name,
            ]);

        $counts = $assets->where('active', true)->groupBy('kind')->map->count();

        return Inertia::render('Settings', [
            'mediaAssets' => $assets->values(),
            'destinationChannels' => DestinationChannel::query()
                ->orderBy('name')
                ->get(['id', 'name']),
            'mediaConfiguration' => [
                'introCount' => $counts->get('intro', 0),
                'outroCount' => $counts->get('outro', 0),
                'musicCount' => $counts->get('music', 0),
                'ready' => $counts->get('intro', 0) > 0
                    && $counts->get('outro', 0) > 0
                    && $counts->get('music', 0) > 0,
            ],
        ]);
    }

    public function updatePassword(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'current_password' => ['required', 'current_password'],
            'password' => ['required', Password::min(8), 'confirmed'],
        ]);

        Auth::user()->update(['password' => Hash::make($data['password'])]);

        return back()->with('success', 'Senha atualizada');
    }
}
