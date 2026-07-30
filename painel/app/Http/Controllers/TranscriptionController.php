<?php

namespace App\Http\Controllers;

use App\Models\TranscriptionJob;
use App\Services\ClipProcessorClient;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Inertia\Inertia;
use Inertia\Response;
use RuntimeException;
use Symfony\Component\HttpFoundation\StreamedResponse;

class TranscriptionController extends Controller
{
    public function index(): Response
    {
        return Inertia::render('TranscricaoLocal', [
            'jobs' => TranscriptionJob::latest()->limit(20)->get(),
        ]);
    }

    public function store(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $data = $request->validate(['url' => ['required', 'string', 'url']]);

        try {
            $client->transcribe($data['url']);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        return back()->with('success', 'Transcrição iniciada');
    }

    /**
     * Serve o .srt gerado pelo clip-processor. O `srt_path` gravado pelo Python é o
     * caminho absoluto DENTRO do container clip-processor (/app/videos/transcripts/{id}.srt);
     * nunca usar esse caminho absoluto diretamente aqui — remontamos via basename() + disco
     * clips-videos, porque os dois containers montam o mesmo host path em pontos diferentes.
     */
    public function download(TranscriptionJob $job): StreamedResponse
    {
        if ($job->status !== 'done' || ! $job->srt_path) {
            abort(404);
        }

        $relative = 'transcripts/'.basename($job->srt_path);

        if (! Storage::disk('clips-videos')->exists($relative)) {
            abort(404);
        }

        return Storage::disk('clips-videos')->download($relative);
    }
}
