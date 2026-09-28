<?php

namespace App\Http\Controllers;

use App\Models\Niche;
use App\Models\Offer;
use App\Services\OfferCopywriter;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use Inertia\Inertia;
use Inertia\Response;

class OfferController extends Controller
{
    public function index(Request $request): Response
    {
        $status = $request->query('status', 'draft');
        if (! in_array($status, ['todos', ...Offer::STATUSES], true)) {
            $status = 'draft';
        }

        $query = Offer::query()->orderByDesc('created_at')->orderByDesc('id')->limit(200);
        if ($status !== 'todos') {
            $query->where('status', $status);
        }

        $byStatus = Offer::query()
            ->selectRaw('status, COUNT(*) as total')
            ->groupBy('status')
            ->pluck('total', 'status');

        $counts = ['todos' => (int) $byStatus->sum()];
        foreach (Offer::STATUSES as $s) {
            $counts[$s] = (int) ($byStatus[$s] ?? 0);
        }

        return Inertia::render('Offers', [
            'offers' => $query->get()->map(fn (Offer $o) => [
                'id' => $o->id,
                'network' => $o->network,
                'externalId' => $o->external_id,
                'niche' => $o->niche,
                'title' => $o->title,
                'description' => $o->description,
                'productUrl' => $o->product_url,
                'affiliateUrl' => $o->affiliate_url,
                'trackingUrl' => $o->trackingUrl(),
                'imageUrl' => $o->image_url,
                'priceCents' => $o->price_cents,
                'currency' => $o->currency,
                'commissionPercent' => $o->commission_percent !== null ? (float) $o->commission_percent : null,
                'ctaText' => $o->cta_text,
                'copyShort' => $o->copy_short,
                'copyLong' => $o->copy_long,
                'aiProvider' => $o->ai_provider,
                'status' => $o->status,
                'clicksCount' => (int) $o->clicks_count,
                'createdAt' => $o->created_at?->diffForHumans(),
                'approvedAt' => $o->approved_at?->diffForHumans(),
                'telegramPostedAt' => $o->telegram_posted_at?->diffForHumans(),
            ]),
            'counts' => $counts,
            'niches' => Niche::query()->orderBy('label')->get(['slug', 'label']),
            'activeStatus' => $status,
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'affiliate_url' => ['required', 'string', 'max:4096', 'url:http,https'],
            'niche' => ['required', 'string', 'exists:niches,slug'],
            'product_url' => ['nullable', 'string', 'max:4096', 'url:http,https'],
            'cta_text' => ['nullable', 'string', 'max:255'],
            'copy_short' => ['nullable', 'string'],
            'copy_long' => ['nullable', 'string'],
            'ai_provider' => ['nullable', 'string', Rule::in(['anthropic', 'groq'])],
        ]);

        // Texto gerado pelo botão "Gerar com IA" guarda o provedor; digitado à mão fica 'manual'.
        $data['ai_provider'] ??= 'manual';

        Offer::create($data + [
            'network' => 'manual',
            'status' => 'draft',
        ]);

        return back()->with('success', "Oferta \"{$data['title']}\" criada");
    }

    /** Gera CTA + textos a partir da página do produto (ou do link de afiliado). Não grava nada. */
    public function generateCopy(Request $request, OfferCopywriter $copywriter): JsonResponse
    {
        $data = $request->validate([
            'affiliate_url' => ['nullable', 'required_without:product_url', 'string', 'max:4096', 'url:http,https'],
            'product_url' => ['nullable', 'string', 'max:4096', 'url:http,https'],
            'title' => ['nullable', 'string', 'max:255'],
            'niche' => ['nullable', 'string', 'max:64'],
        ]);

        try {
            return response()->json($copywriter->generate(
                $data['product_url'] ?? $data['affiliate_url'],
                $data['title'] ?? null,
                $data['niche'] ?? null,
            ));
        } catch (\RuntimeException $e) {
            return response()->json(['message' => $e->getMessage()], 422);
        }
    }

    public function update(Request $request, Offer $offer): RedirectResponse
    {
        $data = $request->validate([
            'status' => ['sometimes', 'string', Rule::in(Offer::STATUSES)],
            'title' => ['sometimes', 'string', 'max:255'],
            'niche' => ['sometimes', 'string', 'exists:niches,slug'],
            'cta_text' => ['sometimes', 'nullable', 'string', 'max:255'],
            'copy_short' => ['sometimes', 'nullable', 'string'],
            'copy_long' => ['sometimes', 'nullable', 'string'],
            'affiliate_url' => ['sometimes', 'string', 'max:4096', 'url:http,https'],
        ]);

        if (array_key_exists('status', $data) && $data['status'] !== $offer->status) {
            $data['approved_at'] = $data['status'] === 'approved' ? now() : null;
        }

        $offer->update($data);

        return back();
    }

    public function destroy(Offer $offer): RedirectResponse
    {
        $offer->delete();

        return back()->with('success', 'Oferta apagada');
    }
}
