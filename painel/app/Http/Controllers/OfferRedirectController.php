<?php

namespace App\Http\Controllers;

use App\Models\Offer;
use App\Models\OfferClick;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class OfferRedirectController extends Controller
{
    /** GET /o/{slug} — link público rastreável: grava clique e redireciona pro link da rede. */
    public function __invoke(Request $request, string $slug): RedirectResponse
    {
        $offer = Offer::query()
            ->where('slug', $slug)
            ->where('status', 'approved')
            ->first();

        // Revalida o esquema no redirect: dado antigo/editado não pode virar open redirect.
        if ($offer === null || ! Offer::isSafeUrl($offer->affiliate_url)) {
            abort(404);
        }

        $channel = $request->query('c');
        $channel = is_string($channel) && in_array($channel, Offer::CHANNELS, true) ? $channel : null;

        $ip = $request->ip();

        OfferClick::create([
            'offer_id' => $offer->id,
            'channel' => $channel,
            // LGPD: só o hash salgado com app.key, nunca o IP cru.
            'ip_hash' => $ip ? hash('sha256', $ip.config('app.key')) : null,
            'user_agent' => $this->truncate($request->userAgent(), 255),
            'referer' => $this->truncate($request->headers->get('referer'), 512),
        ]);

        // UPDATE ... SET clicks_count = clicks_count + 1 (atômico, sem read-modify-write).
        Offer::query()->whereKey($offer->id)->toBase()->increment('clicks_count');

        return redirect()->away($offer->affiliate_url, 302);
    }

    private function truncate(?string $value, int $max): ?string
    {
        return $value === null || $value === '' ? null : Str::substr($value, 0, $max);
    }
}
