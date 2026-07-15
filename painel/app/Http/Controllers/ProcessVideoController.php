<?php

namespace App\Http\Controllers;

use App\Services\ClipProcessorClient;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;
use RuntimeException;

class ProcessVideoController extends Controller
{
    public function show(): Response
    {
        return Inertia::render('ProcessVideo');
    }

    public function store(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $data = $request->validate([
            'format' => ['required', 'in:curto,longo'],
            'urls' => ['required', 'string'],
        ]);

        $urls = collect(preg_split('/\r\n|\r|\n/', $data['urls']))
            ->map(fn ($u) => trim($u))
            ->filter()
            ->unique()
            ->values();

        if ($urls->isEmpty()) {
            return back();
        }

        $ok = [];
        $failed = [];

        foreach ($urls as $url) {
            try {
                $exitCode = $client->processUrl($url, $data['format']);
            } catch (RuntimeException $e) {
                $failed[] = "{$url} — {$e->getMessage()}";

                continue;
            }

            match ($exitCode) {
                0 => $ok[] = $url,
                2 => $failed[] = "{$url} — URL inválida",
                3 => $failed[] = "{$url} — não consegui buscar metadados (vídeo privado/removido/bloqueado por região)",
                default => $failed[] = "{$url} — erro desconhecido (exit code {$exitCode})",
            };
        }

        $success = null;
        if (count($ok) > 0) {
            $success = count($ok) === 1 ? 'Vídeo enfileirado' : count($ok).' vídeos enfileirados';
        }

        $response = back();
        if ($success) {
            $response->with('success', $success);
        }
        if (count($failed) > 0) {
            $response->with('error', implode("\n", $failed));
        }

        return $response;
    }
}
