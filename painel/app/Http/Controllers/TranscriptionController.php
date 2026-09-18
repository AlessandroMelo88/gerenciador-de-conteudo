<?php

namespace App\Http\Controllers;

use App\Models\TranscriptionJob;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Inertia\Inertia;
use Inertia\Response;
use Symfony\Component\HttpFoundation\StreamedResponse;

/**
 * Base de conhecimento por transcrição. O painel só enfileira (`pending`); quem baixa
 * o áudio e transcreve é o worker do Mac (scripts/transcription_worker.py), porque o
 * YouTube bloqueia o IP do servidor e o whisper.cpp da A1 roda a 1× tempo real.
 */
class TranscriptionController extends Controller
{
    private const FORMATOS = ['srt', 'txt', 'md'];

    public function index(Request $request): Response
    {
        $busca = trim((string) $request->query('q', ''));

        $jobs = TranscriptionJob::query()
            // Lista leve: o texto inteiro pode ter centenas de KB por linha.
            ->select(['id', 'source_url', 'title', 'platform', 'duration_seconds', 'status',
                'progress_percent', 'srt_path', 'error_message', 'created_at'])
            ->selectRaw('SUBSTRING(transcript_text, 1, 300) AS excerpt')
            ->when($busca !== '', fn ($q) => $q->where(fn ($w) => $w
                ->whereLike('title', "%{$busca}%")
                ->orWhereLike('source_url', "%{$busca}%")
                ->orWhereLike('transcript_text', "%{$busca}%")))
            ->latest('id')
            ->paginate(20)
            ->withQueryString();

        return Inertia::render('TranscricaoLocal', [
            'jobs' => $jobs,
            'busca' => $busca,
        ]);
    }

    public function show(TranscriptionJob $job): Response
    {
        return Inertia::render('TranscricaoDetalhe', [
            'job' => $job->only(['id', 'source_url', 'title', 'platform', 'duration_seconds',
                'status', 'transcript_text', 'created_at']),
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        $data = $request->validate(['url' => ['required', 'string', 'url', 'max:500']]);

        TranscriptionJob::create(['source_url' => $data['url'], 'status' => 'pending']);

        return back()->with('success', 'Na fila. O worker do Mac pega em até um minuto.');
    }

    public function download(TranscriptionJob $job, string $formato = 'srt'): StreamedResponse
    {
        if (! in_array($formato, self::FORMATOS, true) || $job->status !== 'done') {
            abort(404);
        }

        // Job anterior a 17/09/2026: só existe o .srt em disco no servidor.
        if ($formato === 'srt' && ! $job->transcript_srt) {
            return $this->downloadSrtLegado($job);
        }

        $conteudo = match ($formato) {
            'srt' => $job->transcript_srt,
            'txt' => $job->transcript_text,
            'md' => $this->markdown($job),
        };

        if ($conteudo === null) {
            abort(404);
        }

        $nome = (Str::slug((string) $job->title) ?: "transcricao-{$job->id}").".{$formato}";

        return response()->streamDownload(fn () => print($conteudo), $nome, [
            'Content-Type' => 'text/plain; charset=UTF-8',
        ]);
    }

    /** Formato pensado para colar em outra IA: metadados em cima, texto embaixo. */
    private function markdown(TranscriptionJob $job): ?string
    {
        if ($job->transcript_text === null) {
            return null;
        }

        $linhas = [
            '# '.($job->title ?: "Transcrição {$job->id}"),
            '',
            "- **Fonte:** {$job->source_url}",
        ];
        if ($job->platform) {
            $linhas[] = "- **Plataforma:** {$job->platform}";
        }
        if ($job->duration_seconds) {
            $linhas[] = '- **Duração:** '.self::duracao($job->duration_seconds);
        }
        $linhas[] = '- **Transcrito em:** '.$job->updated_at?->format('d/m/Y');

        return implode("\n", $linhas)."\n\n---\n\n".$job->transcript_text."\n";
    }

    private static function duracao(int $segundos): string
    {
        $h = intdiv($segundos, 3600);
        $min = intdiv($segundos % 3600, 60);

        return $h > 0 ? sprintf('%dh%02dmin', $h, $min) : "{$min}min";
    }

    /**
     * O `srt_path` gravado pelo Python é o caminho DENTRO do container clip-processor;
     * remontamos via basename() + disco clips-videos, porque os dois containers montam
     * o mesmo host path em pontos diferentes.
     */
    private function downloadSrtLegado(TranscriptionJob $job): StreamedResponse
    {
        if (! $job->srt_path) {
            abort(404);
        }

        $relative = 'transcripts/'.basename($job->srt_path);

        if (! Storage::disk('clips-videos')->exists($relative)) {
            abort(404);
        }

        return Storage::disk('clips-videos')->download($relative);
    }
}
