<?php

namespace App\Http\Controllers;

use App\Models\DestinationChannel;
use App\Models\Niche;
use App\Models\PromptProfile;
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
            'channels' => DestinationChannel::query()
                ->with('promptProfile')
                ->latest()
                ->get()
                ->map(fn (DestinationChannel $c) => [
                    'id' => $c->id,
                    'slug' => $c->slug,
                    'name' => $c->name,
                    'niche' => $c->niche,
                    'promptProfileId' => $c->prompt_profile_id,
                    'promptProfileName' => $c->promptProfile?->name,
                    'youtubeChannelId' => $c->youtube_channel_id,
                    'creditTemplate' => $c->credit_template,
                    'active' => $c->active,
                    'oauthStatus' => $c->oauth_status,
                    'hasWatermark' => Storage::disk('branding')->exists("watermark-{$c->slug}.png"),
                ]),
            'niches' => Niche::query()->orderBy('label')->get(['slug', 'label']),
            'promptProfiles' => PromptProfile::query()
                ->active()
                ->orderBy('name')
                ->get(['id', 'slug', 'name', 'niche', 'niche_aliases'])
                ->map(fn (PromptProfile $profile) => [
                    'id' => $profile->id,
                    'slug' => $profile->slug,
                    'name' => $profile->name,
                    'niche' => $profile->niche,
                    'nicheAliases' => $profile->niche_aliases ?? [],
                ])
                ->values(),
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'slug' => ['required', 'string', 'max:50', 'unique:destination_channels,slug'],
            'name' => ['required', 'string', 'max:120'],
            'niche' => ['required', 'string'],
            'prompt_profile_id' => ['nullable', 'integer', 'exists:prompt_profiles,id'],
            'youtube_channel_id' => ['required', 'string', 'unique:destination_channels,youtube_channel_id'],
            'credit_template' => ['sometimes', 'nullable', 'string'],
            'active' => ['sometimes', 'boolean'],
        ]);

        $promptProfileId = PromptProfile::resolveId(
            isset($data['prompt_profile_id']) ? (int) $data['prompt_profile_id'] : null,
            $data['niche'],
        );
        if ($promptProfileId === null) {
            return back()
                ->withErrors(['prompt_profile_id' => 'O nicho precisa de um perfil de prompt ativo.'])
                ->withInput();
        }

        DestinationChannel::create([
            ...$data,
            'prompt_profile_id' => $promptProfileId,
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
            'prompt_profile_id' => ['sometimes', 'nullable', 'integer', 'exists:prompt_profiles,id'],
            'youtube_channel_id' => ['sometimes', 'string', 'unique:destination_channels,youtube_channel_id,'.$destinationChannel->id],
            'credit_template' => ['sometimes', 'nullable', 'string'],
            'active' => ['sometimes', 'boolean'],
        ]);

        if (array_key_exists('prompt_profile_id', $data) || array_key_exists('niche', $data)) {
            $promptProfileId = PromptProfile::resolveId(
                array_key_exists('prompt_profile_id', $data) && $data['prompt_profile_id'] !== null
                    ? (int) $data['prompt_profile_id']
                    : null,
                $data['niche'] ?? $destinationChannel->niche,
            );
            if ($promptProfileId === null) {
                return back()->withErrors([
                    'prompt_profile_id' => 'Selecione um perfil de prompt ativo para este nicho.',
                ]);
            }
            $data['prompt_profile_id'] = $promptProfileId;
        }

        $destinationChannel->update($data);

        return back()->with('success', "Canal #{$destinationChannel->id} atualizado");
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
        if ($destinationChannel->generatedClips()->exists()) {
            return back()->with('error', 'Canal-destino possui clips e não pode ser apagado');
        }

        $destinationChannel->delete();

        return back()->with('success', 'Canal-destino apagado');
    }
}
