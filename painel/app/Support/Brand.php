<?php

namespace App\Support;

use Illuminate\Http\Request;

/**
 * Resolve a marca do request (host → BRAND_DOMAINS, senão APP_BRAND).
 * Só apresentação: rotas, banco e dados são os mesmos para todas as marcas.
 */
class Brand
{
    public const FALLBACK = 'canaldecortes';

    /** @return array{key: string, name: string, tagline: string, icon: string, logo: ?string} */
    public static function resolve(?Request $request = null): array
    {
        $brands = (array) config('branding.brands', []);
        // Lido como array: config('branding.domains.<host>') quebraria no ponto do host.
        $domains = (array) config('branding.domains', []);
        $host = $request ? strtolower($request->getHost()) : '';

        $key = $domains[$host] ?? config('branding.default', self::FALLBACK);
        if (! isset($brands[$key])) {
            $key = self::FALLBACK;
        }

        $brand = $brands[$key] ?? [];

        return [
            'key' => $key,
            'name' => (string) ($brand['name'] ?? 'Canal de Cortes'),
            'tagline' => (string) ($brand['tagline'] ?? ''),
            'icon' => (string) ($brand['icon'] ?? 'clapperboard'),
            'logo' => filled($brand['logo'] ?? null) ? (string) $brand['logo'] : null,
        ];
    }
}
