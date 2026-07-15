<?php

namespace App\Http\Controllers;

use App\Models\DestinationChannel;
use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use App\Services\ClipProcessorClient;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\Redis;
use Inertia\Inertia;
use Inertia\Response;
use RuntimeException;

class DashboardController extends Controller
{
    public function index(): Response
    {
        return Inertia::render('Dashboard', [
            'quota' => $this->quotaData(),
            'overview' => $this->overviewData(),
            'pendingClips' => $this->clipPayload(
                GeneratedClip::with(['sourceVideo.sourceChannel', 'destinationChannel'])
                    ->where('status', 'pending')
                    ->latest()
                    ->get()
            ),
            'queuedClips' => $this->clipPayload(
                GeneratedClip::with(['sourceVideo.sourceChannel', 'destinationChannel'])
                    ->where('status', 'approved')
                    ->oldest('created_at')
                    ->get()
            ),
            'failures' => $this->clipPayload(
                GeneratedClip::with(['destinationChannel'])
                    ->where('status', 'failed')
                    ->latest('updated_at')
                    ->limit(20)
                    ->get()
            ),
            'failedSourceVideoCount' => SourceVideo::where('status', 'failed')->count(),
            'activeWindow' => $this->activeWindowData(),
        ]);
    }

    /**
     * Vídeos com arquivo em disco agora (janela de download ativo — ver
     * DOWNLOAD_WINDOW_CURTO/LONGO em clip-processor/src/pipeline_runner.py).
     * Score = maior nota entre os clips já gerados desse vídeo (null enquanto
     * ainda não tem clip, ex: baixando/transcrevendo/selecionando).
     */
    private function activeWindowData(): array
    {
        return SourceVideo::query()
            ->whereNotNull('local_path')
            ->with(['sourceChannel', 'generatedClips'])
            ->get()
            ->sortBy([
                // score null (ainda sem clip gerado) é ruído — manda pro fim, não pro topo
                [fn (SourceVideo $video) => $video->generatedClips->max('score') ?? 999, 'asc'],
                [fn (SourceVideo $video) => $video->published_at, 'asc'],
            ])
            ->map(fn (SourceVideo $video) => [
                'id' => $video->id,
                'title' => $video->title,
                'format' => $video->format,
                'status' => $video->status,
                'sourceChannelName' => $video->sourceChannel?->channel_name,
                'publishedAt' => $video->published_at?->diffForHumans(),
                'score' => $video->generatedClips->max('score'),
                'clipCount' => $video->generatedClips->count(),
            ])
            ->values()
            ->all();
    }

    private function quotaData(): array
    {
        $date = Carbon::now('America/Sao_Paulo')->format('Y-m-d');
        // min(MAX_UPLOADS_PER_DAY, 6) espelha ABSOLUTE_MAX_UPLOADS_PER_DAY em
        // clip-processor/src/quota_manager.py — mesma env var, mesmo teto.
        $limit = min((int) env('MAX_UPLOADS_PER_DAY', 2), 6);

        return DestinationChannel::query()->where('active', true)->get()
            ->map(function (DestinationChannel $channel) use ($date, $limit) {
                $key = "youtube_uploads:{$channel->youtube_channel_id}:{$date}";
                try {
                    $count = (int) (Redis::connection('pipeline')->get($key) ?? 0);
                } catch (\Throwable) {
                    $count = 0;
                }

                return [
                    'name' => $channel->name,
                    'count' => $count,
                    'limit' => $limit,
                ];
            })->values()->all();
    }

    private function overviewData(): array
    {
        $since = Carbon::now('America/Sao_Paulo')->subDays(7);

        $publishedCurto = GeneratedClip::query()
            ->where('status', 'published')
            ->where('updated_at', '>=', $since)
            ->whereHas('sourceVideo', fn ($q) => $q->where('format', 'curto'))
            ->count();

        $publishedLongo = GeneratedClip::query()
            ->where('status', 'published')
            ->where('updated_at', '>=', $since)
            ->whereHas('sourceVideo', fn ($q) => $q->where('format', 'longo'))
            ->count();

        return [
            'publishedCurto' => $publishedCurto,
            'publishedLongo' => $publishedLongo,
            'backlogCurto' => SourceVideo::query()->where('format', 'curto')->where('status', 'pending')->count(),
            'backlogLongo' => SourceVideo::query()->where('format', 'longo')->where('status', 'pending')->count(),
        ];
    }

    private function clipPayload($clips): array
    {
        return $clips->map(fn (GeneratedClip $clip) => [
            'id' => $clip->id,
            'title' => $clip->title,
            'score' => $clip->score,
            'trecho' => $this->formatTrecho($clip->start_time, $clip->end_time),
            'sourceVideoTitle' => $clip->sourceVideo?->title,
            'sourceChannelName' => $clip->sourceVideo?->sourceChannel?->channel_name,
            'format' => $clip->sourceVideo?->format ?? 'curto',
            'destinationChannelName' => $clip->destinationChannel?->name,
            'createdAt' => $clip->created_at?->diffForHumans(),
            'updatedAt' => $clip->updated_at?->diffForHumans(),
            'uploadError' => $clip->upload_error,
            'previewUrl' => route('clips.preview', $clip->id),
        ])->values()->all();
    }

    private function formatTrecho(?float $start, ?float $end): string
    {
        if ($start === null || $end === null) {
            return '—';
        }

        $fmt = fn (float $seconds): string => sprintf('%d:%02d', intdiv((int) $seconds, 60), (int) $seconds % 60);

        return "{$fmt($start)}–{$fmt($end)}";
    }

    public function approve(GeneratedClip $clip): RedirectResponse
    {
        $affected = GeneratedClip::query()
            ->where('id', $clip->id)
            ->where('status', 'pending')
            ->update(['status' => 'approved']);

        return back()->with($affected ? 'success' : 'error', $affected
            ? "Clip #{$clip->id} aprovado"
            : 'Clip não estava mais pendente');
    }

    public function reject(GeneratedClip $clip, ClipProcessorClient $client): RedirectResponse
    {
        try {
            $exit = $client->rejectClip($clip->id);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        return match ($exit) {
            0 => back()->with('success', "Clip #{$clip->id} rejeitado (MP4 removido)"),
            1 => back()->with('error', 'Clip não existe'),
            2 => back()->with('error', 'Status inválido para rejeitar'),
            default => back()->with('error', "exit_code={$exit}"),
        };
    }

    /**
     * Reenvia um clip 'failed' para reprocessamento: volta pra 'pending_cut' se o
     * corte nunca terminou (clip_path vazio), ou pro status publicável (approved/
     * pending, conforme MANUAL_APPROVAL_REQUIRED) se o corte existe e só o upload falhou.
     */
    public function reprocess(GeneratedClip $clip): RedirectResponse
    {
        if ($clip->status !== 'failed') {
            return back()->with('error', 'Clip não está mais em falha');
        }

        $manualApproval = filter_var(env('MANUAL_APPROVAL_REQUIRED', false), FILTER_VALIDATE_BOOLEAN);
        $newStatus = $clip->clip_path ? ($manualApproval ? 'approved' : 'pending') : 'pending_cut';

        $affected = GeneratedClip::query()
            ->where('id', $clip->id)
            ->where('status', 'failed')
            ->update(['status' => $newStatus, 'upload_error' => null]);

        return back()->with($affected ? 'success' : 'error', $affected
            ? "Clip #{$clip->id} reenviado para reprocessamento"
            : 'Clip não está mais em falha');
    }

    public function bulkApprove(Request $request): RedirectResponse
    {
        $ids = $request->validate(['ids' => ['required', 'array'], 'ids.*' => ['integer']])['ids'];

        $affected = GeneratedClip::query()
            ->whereIn('id', $ids)
            ->where('status', 'pending')
            ->update(['status' => 'approved']);

        return back()->with('success', "{$affected} clip(s) aprovado(s)");
    }

    /**
     * Apaga o arquivo bruto (.mp4) de um vídeo fonte pra liberar espaço/vaga na
     * janela de download. Não mexe nos clips já cortados a partir dele.
     */
    public function deleteVideo(SourceVideo $video, ClipProcessorClient $client): RedirectResponse
    {
        try {
            $result = $client->deleteSourceVideo($video->id);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        $mb = round($result['freed_bytes'] / 1024 / 1024, 1);

        return back()->with('success', "Vídeo #{$video->id} apagado ({$mb} MB liberados)");
    }

    public function bulkReject(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $ids = $request->validate(['ids' => ['required', 'array'], 'ids.*' => ['integer']])['ids'];

        $ok = 0;
        $fail = 0;
        foreach ($ids as $id) {
            try {
                $client->rejectClip((int) $id) === 0 ? $ok++ : $fail++;
            } catch (RuntimeException) {
                $fail++;
            }
        }

        $message = "{$ok} clip(s) rejeitado(s)".($fail ? ", {$fail} falharam" : '');

        return back()->with($fail ? 'error' : 'success', $message);
    }
}
