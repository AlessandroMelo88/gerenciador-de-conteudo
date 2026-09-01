<?php

namespace App\Http\Middleware;

use Illuminate\Http\Request;
use Inertia\Middleware;

class HandleInertiaRequests extends Middleware
{
    /**
     * The root template that's loaded on the first page visit.
     *
     * @see https://inertiajs.com/server-side-setup#root-template
     *
     * @var string
     */
    protected $rootView = 'app';

    /**
     * Determines the current asset version.
     *
     * @see https://inertiajs.com/asset-versioning
     */
    public function version(Request $request): ?string
    {
        return parent::version($request);
    }

    /**
     * Define the props that are shared by default.
     *
     * @see https://inertiajs.com/shared-data
     *
     * @return array<string, mixed>
     */
    public function share(Request $request): array
    {
        return [
            ...parent::share($request),
            'auth' => [
                'user' => $request->user() ? [
                    'name' => $request->user()->name,
                    'email' => $request->user()->email,
                ] : null,
            ],
            'flash' => [
                'success' => fn () => $request->session()->get('success'),
                'error' => fn () => $request->session()->get('error'),
            ],
            'workers' => [
                'downloader' => \App\Models\SourceVideo::query()->where('status', 'downloading')->count() . '/' . \App\Models\SourceVideo::query()->whereNotNull('local_path')->count(),
                'transcriber' => \App\Models\SourceVideo::query()->where('status', 'transcribing')->count() > 0 ? \App\Models\SourceVideo::query()->where('status', 'transcribing')->count() . ' ativo' : 'idle',
                'cutter' => \App\Models\GeneratedClip::query()->where('status', 'cutting')->count() > 0 ? \App\Models\GeneratedClip::query()->where('status', 'cutting')->count() . ' cortando' : 'idle',
            ],
            'destinationQuotas' => \App\Models\DestinationChannel::query()->where('active', true)->get(['id', 'slug', 'name', 'niche'])->map(fn ($c) => [
                'name' => $c->name,
                'slug' => $c->slug,
                'niche' => $c->niche,
                'count' => 0,
                'limit' => 5,
            ]),
        ];
    }
}
