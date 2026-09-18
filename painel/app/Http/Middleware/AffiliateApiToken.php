<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Autenticação máquina-a-máquina do worker de afiliados (Bearer token fixo).
 * Fail-closed: sem AFFILIATE_API_TOKEN no servidor a API fica indisponível.
 */
class AffiliateApiToken
{
    public function handle(Request $request, Closure $next): Response
    {
        $expected = (string) config('services.affiliate.token');

        if ($expected === '') {
            return response()->json(['error' => 'affiliate_api_not_configured'], 503);
        }

        $given = (string) $request->bearerToken();

        if ($given === '' || ! hash_equals($expected, $given)) {
            return response()->json(['error' => 'unauthorized'], 401);
        }

        return $next($request);
    }
}
