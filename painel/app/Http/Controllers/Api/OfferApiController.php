<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Offer;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Arr;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\Rule;

class OfferApiController extends Controller
{
    /**
     * Lote de ofertas vindo do worker local. Upsert por (network, external_id):
     * - não existe            → cria como draft   (created)
     * - existe e é draft      → atualiza conteúdo (updated)
     * - existe e não é draft  → não toca          (skipped) — decisão do operador prevalece
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'offers' => ['required', 'array', 'min:1', 'max:100'],
            'offers.*' => ['required', 'array'],
            'offers.*.network' => ['required', 'string', Rule::in(Offer::NETWORKS)],
            'offers.*.external_id' => ['nullable', 'string', 'max:191'],
            'offers.*.niche' => ['required', 'string', 'exists:niches,slug'],
            'offers.*.title' => ['required', 'string', 'max:255'],
            'offers.*.affiliate_url' => ['required', 'string', 'max:4096', 'url:http,https'],
            'offers.*.description' => ['nullable', 'string'],
            'offers.*.product_url' => ['nullable', 'string', 'max:4096', 'url:http,https'],
            'offers.*.image_url' => ['nullable', 'string', 'max:4096', 'url:http,https'],
            'offers.*.price_cents' => ['nullable', 'integer', 'min:0', 'max:4294967295'],
            'offers.*.currency' => ['nullable', 'string', 'size:3'],
            'offers.*.commission_percent' => ['nullable', 'numeric', 'min:0', 'max:100'],
            'offers.*.cta_text' => ['nullable', 'string', 'max:255'],
            'offers.*.copy_short' => ['nullable', 'string'],
            'offers.*.copy_long' => ['nullable', 'string'],
            'offers.*.ai_provider' => ['nullable', 'string', Rule::in(Offer::AI_PROVIDERS)],
        ]);

        $counts = ['created' => 0, 'updated' => 0, 'skipped' => 0];
        $results = [];

        DB::transaction(function () use ($validated, &$counts, &$results) {
            foreach ($validated['offers'] as $item) {
                // Só campos de conteúdo presentes no payload; status/slug/clicks nunca vêm do cliente.
                $content = Arr::only($item, Offer::CONTENT_FIELDS);
                if (array_key_exists('currency', $content)) {
                    $content['currency'] = strtoupper($content['currency'] ?? 'BRL');
                }

                $externalId = $item['external_id'] ?? null;
                $existing = $externalId === null ? null : Offer::query()
                    ->where('network', $item['network'])
                    ->where('external_id', $externalId)
                    ->lockForUpdate()
                    ->first();

                if ($existing === null) {
                    $offer = Offer::create($content + [
                        'network' => $item['network'],
                        'external_id' => $externalId,
                        'status' => 'draft',
                    ]);
                    $result = 'created';
                } elseif ($existing->status === 'draft') {
                    $existing->update($content);
                    $offer = $existing;
                    $result = 'updated';
                } else {
                    $offer = $existing;
                    $result = 'skipped';
                }

                $counts[$result]++;
                $results[] = [
                    'id' => $offer->id,
                    'slug' => $offer->slug,
                    'status' => $offer->status,
                    'result' => $result,
                    'tracking_url' => $offer->trackingUrl(),
                ];
            }
        });

        return response()->json($counts + ['offers' => $results]);
    }

    public function index(Request $request): JsonResponse
    {
        $data = $request->validate([
            'status' => ['sometimes', 'string', Rule::in(Offer::STATUSES)],
            'niche' => ['sometimes', 'string', 'max:50'],
            'per_page' => ['sometimes', 'integer', 'min:1', 'max:100'],
        ]);

        $query = Offer::query()
            ->where('status', $data['status'] ?? 'approved')
            ->orderByDesc('id');

        if (! empty($data['niche'])) {
            $query->where('niche', $data['niche']);
        }

        $paginator = $query->paginate((int) ($data['per_page'] ?? 20))->withQueryString();

        return response()->json($paginator->through(fn (Offer $o) => [
            'id' => $o->id,
            'network' => $o->network,
            'external_id' => $o->external_id,
            'niche' => $o->niche,
            'title' => $o->title,
            'description' => $o->description,
            'product_url' => $o->product_url,
            'affiliate_url' => $o->affiliate_url,
            'slug' => $o->slug,
            'image_url' => $o->image_url,
            'price_cents' => $o->price_cents,
            'currency' => $o->currency,
            'commission_percent' => $o->commission_percent !== null ? (float) $o->commission_percent : null,
            'cta_text' => $o->cta_text,
            'copy_short' => $o->copy_short,
            'copy_long' => $o->copy_long,
            'ai_provider' => $o->ai_provider,
            'status' => $o->status,
            'clicks_count' => $o->clicks_count,
            'approved_at' => $o->approved_at?->toIso8601String(),
            'created_at' => $o->created_at?->toIso8601String(),
            'updated_at' => $o->updated_at?->toIso8601String(),
            'tracking_url' => $o->trackingUrl(),
        ]));
    }
}
