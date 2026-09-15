<?php

namespace App\Http\Controllers;

use App\Models\Niche;
use App\Models\Offer;
use App\Models\OfferClick;
use Carbon\CarbonPeriod;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Http\Request;
use Illuminate\Support\Carbon;
use Inertia\Inertia;
use Inertia\Response;

class OfferPerformanceController extends Controller
{
    private const PERIODS = [7, 30, 90];

    private const OFFER_LIMIT = 100;

    /**
     * GET /painel/ofertas/performance — cliques por oferta, canal (?c=) e dia.
     * Tudo agregado no banco; ip_hash só entra em COUNT(DISTINCT), nunca sai nas props.
     */
    public function index(Request $request): Response
    {
        $days = (int) $request->query('days', 30);
        if (! in_array($days, self::PERIODS, true)) {
            $days = 30;
        }

        $today = now()->startOfDay();
        $since = $today->copy()->subDays($days - 1);
        $clicks = fn (): Builder => OfferClick::query()->where('created_at', '>=', $since);

        $byChannel = $clicks()
            ->selectRaw('channel, COUNT(*) as clicks, COUNT(DISTINCT ip_hash) as visitors')
            ->groupBy('channel')
            ->orderByDesc('clicks')
            ->get()
            ->map(fn ($row) => [
                // NULL = link sem ?c= (ou valor inválido).
                'channel' => $row->channel ?? 'direto',
                'clicks' => (int) $row->clicks,
                'uniqueVisitors' => (int) $row->visitors,
            ])
            ->values();

        // DATE() existe em MySQL, PostgreSQL e SQLite.
        $perDay = $clicks()
            ->selectRaw('DATE(created_at) as day, COUNT(*) as clicks')
            ->groupBy('day')
            ->pluck('clicks', 'day');

        // Série contínua: dia sem clique aparece com zero.
        $byDay = [];
        foreach (CarbonPeriod::create($since, $today) as $day) {
            $date = $day->toDateString();
            $byDay[] = ['date' => $date, 'clicks' => (int) ($perDay[$date] ?? 0)];
        }

        $offerRows = $clicks()
            ->selectRaw('offer_id, COUNT(*) as clicks, COUNT(DISTINCT ip_hash) as visitors, MAX(created_at) as last_click_at')
            ->groupBy('offer_id')
            ->orderByDesc('clicks')
            ->limit(self::OFFER_LIMIT)
            ->get();

        $offerIds = $offerRows->pluck('offer_id')->all();

        $channelsByOffer = $clicks()
            ->whereIn('offer_id', $offerIds)
            ->selectRaw('offer_id, channel, COUNT(*) as clicks')
            ->groupBy('offer_id', 'channel')
            ->get()
            ->groupBy('offer_id');

        $offers = Offer::query()
            ->whereIn('id', $offerIds)
            ->get(['id', 'title', 'niche', 'network', 'status', 'slug'])
            ->keyBy('id');

        $byOffer = $offerRows
            ->filter(fn ($row) => $offers->has($row->offer_id))
            ->map(function ($row) use ($offers, $channelsByOffer) {
                $offer = $offers[$row->offer_id];

                return [
                    'id' => $offer->id,
                    'title' => $offer->title,
                    'niche' => $offer->niche,
                    'network' => $offer->network,
                    'status' => $offer->status,
                    'trackingUrl' => $offer->trackingUrl(),
                    'clicks' => (int) $row->clicks,
                    'uniqueVisitors' => (int) $row->visitors,
                    'lastClickAt' => $row->last_click_at ? Carbon::parse($row->last_click_at)->diffForHumans() : null,
                    'channels' => collect($channelsByOffer[$row->offer_id] ?? [])
                        ->map(fn ($c) => ['channel' => $c->channel ?? 'direto', 'clicks' => (int) $c->clicks])
                        ->sortByDesc('clicks')
                        ->values(),
                ];
            })
            ->values();

        return Inertia::render('OfferPerformance', [
            'days' => $days,
            'periods' => self::PERIODS,
            'totals' => [
                'clicks' => (int) $byChannel->sum('clicks'),
                'uniqueVisitors' => (int) $clicks()->distinct()->count('ip_hash'),
                'offersWithClicks' => (int) $clicks()->distinct()->count('offer_id'),
                'approvedOffers' => Offer::query()->where('status', 'approved')->count(),
            ],
            'byChannel' => $byChannel,
            'byDay' => $byDay,
            'byOffer' => $byOffer,
            'niches' => Niche::query()->orderBy('label')->get(['slug', 'label']),
        ]);
    }
}
