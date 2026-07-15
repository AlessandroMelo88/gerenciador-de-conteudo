<?php

namespace App\Http\Controllers;

use App\Models\Niche;
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

        $query = SourceChannel::query()->orderByDesc('created_at');
        if ($tab !== 'todos') {
            $query->where('target_niche', $tab);
        }

        return Inertia::render('SourceChannels', [
            'channels' => $query->get()->map(fn (SourceChannel $c) => [
                'id' => $c->id,
                'channelName' => $c->channel_name,
                'channelHandle' => $c->channel_handle,
                'targetNiche' => $c->target_niche,
                'active' => $c->active,
                'blacklisted' => $c->blacklisted,
                'createdAt' => $c->created_at ? Carbon::parse($c->created_at)->diffForHumans() : null,
            ]),
            'niches' => Niche::query()->orderBy('label')->get(['slug', 'label']),
            'activeTab' => $tab,
        ]);
    }

    public function store(Request $request, ClipProcessorClient $client): RedirectResponse
    {
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

        return back()->with('success', "Canal \"{$resolved['channel_name']}\" adicionado");
    }

    public function update(Request $request, SourceChannel $sourceChannel): RedirectResponse
    {
        $data = $request->validate([
            'blacklisted' => ['sometimes', 'boolean'],
            'active' => ['sometimes', 'boolean'],
        ]);

        $sourceChannel->update($data);

        return back();
    }

    public function destroy(SourceChannel $sourceChannel): RedirectResponse
    {
        $sourceChannel->delete();

        return back()->with('success', 'Canal-fonte apagado');
    }
}
