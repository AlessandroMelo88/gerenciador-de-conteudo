<?php

namespace App\Http\Controllers;

use App\Models\Niche;
use App\Models\PromptProfile;
use App\Models\SourceChannel;
use App\Services\ClipProcessorClient;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Carbon;
use Inertia\Inertia;
use Inertia\Response;
use RuntimeException;

class SourceChannelController extends Controller
{
    public function index(Request $request): Response
    {
        $tab = $request->query('tab', 'todos');

        $query = SourceChannel::query()->with('promptProfile')->orderByDesc('created_at');
        if ($tab !== 'todos') {
            $query->where('target_niche', $tab);
        }

        return Inertia::render('SourceChannels', [
            'channels' => $query->get()->map(fn (SourceChannel $c) => [
                'id' => $c->id,
                'channelName' => $c->channel_name,
                'channelHandle' => $c->channel_handle,
                'targetNiche' => $c->target_niche,
                'promptProfileId' => $c->prompt_profile_id,
                'promptProfileName' => $c->promptProfile?->name,
                'active' => $c->active,
                'blacklisted' => $c->blacklisted,
                'createdAt' => $c->created_at ? Carbon::parse($c->created_at)->diffForHumans() : null,
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
            'activeTab' => $tab,
        ]);
    }

    public function store(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $data = $request->validate([
            'url' => ['required', 'string'],
            'target_niche' => ['required', 'string'],
            'prompt_profile_id' => ['nullable', 'integer', 'exists:prompt_profiles,id'],
        ]);

        $promptProfileId = PromptProfile::resolveId(
            isset($data['prompt_profile_id']) ? (int) $data['prompt_profile_id'] : null,
            $data['target_niche'],
        );
        if ($promptProfileId === null) {
            return back()
                ->withErrors(['prompt_profile_id' => 'O nicho precisa de um perfil de prompt ativo.'])
                ->withInput();
        }

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
            'prompt_profile_id' => $promptProfileId,
        ]);

        return back()->with('success', "Canal \"{$resolved['channel_name']}\" adicionado");
    }

    public function update(Request $request, SourceChannel $sourceChannel): RedirectResponse
    {
        $data = $request->validate([
            'blacklisted' => ['sometimes', 'boolean'],
            'active' => ['sometimes', 'boolean'],
            'prompt_profile_id' => ['sometimes', 'nullable', 'integer', 'exists:prompt_profiles,id'],
        ]);

        if (array_key_exists('prompt_profile_id', $data)) {
            $promptProfileId = PromptProfile::resolveId(
                $data['prompt_profile_id'] === null ? null : (int) $data['prompt_profile_id'],
                $sourceChannel->target_niche,
            );
            if ($promptProfileId === null) {
                return back()->withErrors([
                    'prompt_profile_id' => 'Selecione um perfil de prompt ativo.',
                ]);
            }
            $data['prompt_profile_id'] = $promptProfileId;
        }

        $sourceChannel->update($data);

        return back();
    }

    public function destroy(SourceChannel $sourceChannel): RedirectResponse
    {
        if ($sourceChannel->sourceVideos()->exists()) {
            return back()->with('error', 'Canal-fonte possui vídeos e não pode ser apagado');
        }

        $sourceChannel->delete();

        return back()->with('success', 'Canal-fonte apagado');
    }
}
