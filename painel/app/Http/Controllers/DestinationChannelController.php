<?php

namespace App\Http\Controllers;

use App\Models\DestinationChannel;
use App\Models\Niche;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Inertia\Inertia;
use Inertia\Response;

class DestinationChannelController extends Controller
{
    public function index(): Response
    {
        return Inertia::render('DestinationChannels', [
            'channels' => DestinationChannel::query()->latest()->get()->map(fn (DestinationChannel $c) => [
                'id' => $c->id,
                'slug' => $c->slug,
                'name' => $c->name,
                'niche' => $c->niche,
                'youtubeChannelId' => $c->youtube_channel_id,
                'creditTemplate' => $c->credit_template,
                'templateConfig' => $c->effective_template_config,
                'active' => $c->active,
                'oauthStatus' => $c->oauth_status,
                'hasWatermark' => Storage::disk('branding')->exists("watermark-{$c->slug}.png"),
                'watermarkUrl' => Storage::disk('branding')->exists("watermark-{$c->slug}.png")
                    ? route('destination-channels.watermark', $c->id)
                    : null,
            ]),
            'niches' => Niche::query()->orderBy('label')->get(['slug', 'label']),
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'slug' => ['required', 'string', 'max:50', 'unique:destination_channels,slug'],
            'name' => ['required', 'string', 'max:120'],
            'niche' => ['required', 'string'],
            'youtube_channel_id' => ['required', 'string', 'unique:destination_channels,youtube_channel_id'],
            'credit_template' => ['sometimes', 'nullable', 'string'],
            'template_config' => ['sometimes', 'nullable'],
            'active' => ['sometimes', 'boolean'],
        ]);

        DestinationChannel::create([
            ...$data,
            'credit_template' => $data['credit_template'] ?? 'Créditos: @{channel_handle}',
            'active' => $data['active'] ?? true,
        ]);

        return back()->with('success', 'Canal-destino criado');
    }

    public function update(Request $request, DestinationChannel $destinationChannel): RedirectResponse
    {
        $data = $request->validate([
            'slug' => ['sometimes', 'string', 'max:50', 'unique:destination_channels,slug,'.$destinationChannel->id],
            'name' => ['sometimes', 'string', 'max:120'],
            'niche' => ['sometimes', 'string'],
            'youtube_channel_id' => ['sometimes', 'string', 'unique:destination_channels,youtube_channel_id,'.$destinationChannel->id],
            'credit_template' => ['sometimes', 'nullable', 'string'],
            'template_config' => ['sometimes', 'nullable'],
            'active' => ['sometimes', 'boolean'],
        ]);

        $destinationChannel->update($data);

        return back()->with('success', "Canal #{$destinationChannel->id} atualizado");
    }

    public function watermark(DestinationChannel $destinationChannel)
    {
        $relativePath = "watermark-{$destinationChannel->slug}.png";
        if (! Storage::disk('branding')->exists($relativePath)) {
            // fallback template
            $templateFallback = base_path("../template/{$destinationChannel->slug}/imagens/politica-avatar-800x800.png");
            if (file_exists($templateFallback)) {
                return response()->file($templateFallback);
            }
            abort(404);
        }

        return response()->file(Storage::disk('branding')->path($relativePath));
    }

    public function uploadWatermark(Request $request, DestinationChannel $destinationChannel): RedirectResponse
    {
        $request->validate([
            'watermark' => ['required', 'image', 'max:5120'],
        ]);

        $request->file('watermark')->storeAs('', "watermark-{$destinationChannel->slug}.png", 'branding');

        return back()->with('success', 'Marca d\'água atualizada');
    }

    public function destroy(DestinationChannel $destinationChannel): RedirectResponse
    {
        $destinationChannel->delete();

        return back()->with('success', 'Canal-destino apagado');
    }
}
