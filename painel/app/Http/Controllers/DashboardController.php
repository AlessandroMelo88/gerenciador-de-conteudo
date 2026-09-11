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
use Illuminate\Support\Facades\Storage;
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
                    ->limit(10)
                    ->get()
            ),
            'queuedClips' => $this->clipPayload(
                GeneratedClip::with(['sourceVideo.sourceChannel', 'destinationChannel'])
                    ->where('status', 'approved')
                    ->oldest('created_at')
                    ->limit(10)
                    ->get()
            ),
            'failures' => $this->clipPayload(
                GeneratedClip::with(['destinationChannel'])
                    ->where('status', 'failed')
                    ->latest('updated_at')
                    ->limit(10)
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
        $processing = ['downloading', 'transcribing', 'selecting'];

        $destinationChannels = DestinationChannel::all();
        $destMap = [];
        foreach ($destinationChannels as $dc) {
            $destMap[strtolower(trim($dc->niche))] = $dc->name;
        }

        return SourceVideo::query()
            ->whereNotNull('local_path')
            ->where('local_path', '!=', '')
            ->where(function ($query) {
                $query->whereIn('status', ['downloading', 'downloaded', 'transcribing', 'selecting', 'cutting'])
                    ->orWhereHas('generatedClips', function ($clipQuery) {
                        $clipQuery->whereIn('status', ['pending_cut', 'cutting', 'pending']);
                    });
            })
            ->with(['sourceChannel', 'generatedClips.destinationChannel'])
            ->get()
            ->sortBy([
                // Processando agora no topo; depois ordem DnD / prioridade / score baixo
                [fn (SourceVideo $video) => in_array($video->status, $processing, true) ? 0 : 1, 'asc'],
                [fn (SourceVideo $video) => $video->paused ? 1 : 0, 'asc'],
                [fn (SourceVideo $video) => -((int) ($video->priority ?? 0)), 'asc'],
                [fn (SourceVideo $video) => $video->queue_position ?? 9999, 'asc'],
                [fn (SourceVideo $video) => $video->generatedClips->max('score') ?? 999, 'asc'],
                [fn (SourceVideo $video) => $video->published_at, 'asc'],
            ])
            ->map(function (SourceVideo $video) use ($processing, $destMap) {
                $needsRaw = $video->generatedClips
                    ->whereIn('status', ['pending_cut', 'cutting'])
                    ->isNotEmpty();

                $progress = match ($video->status) {
                    'pending', 'failed' => 0,
                    'downloading' => 20,
                    'downloaded' => 40,
                    'transcribing' => 60,
                    'selecting' => $needsRaw ? 90 : ($video->generatedClips->isNotEmpty() ? 100 : 80),
                    'cutting' => 90,
                    'publishing', 'published' => 100,
                    default => 0,
                };

                $niche = strtolower(trim($video->sourceChannel?->target_niche ?? ''));
                if (empty($niche)) {
                    $firstClipDest = $video->generatedClips->first()?->destinationChannel;
                    $niche = $firstClipDest ? strtolower(trim($firstClipDest->niche)) : '';
                }

                if (empty($niche)) {
                    $ch = strtolower($video->sourceChannel?->channel_name ?? '');
                    if (str_contains($ch, 'espn') || str_contains($ch, 'cazé') || str_contains($ch, 'caze') || str_contains($ch, 'esporte') || str_contains($ch, 'futebol')) {
                        $niche = 'futebol';
                    } elseif (str_contains($ch, 'flow') || str_contains($ch, 'inteligência') || str_contains($ch, 'inteligencia') || str_contains($ch, 'pod')) {
                        $niche = 'podcast';
                    } else {
                        $niche = 'politica';
                    }
                }

                $destinationChannelName = $destMap[$niche] ?? match ($niche) {
                    'futebol' => 'Futebol em Cortes',
                    'politica' => 'Cortes da Política',
                    default => ucfirst($niche),
                };

                return [
                    'id' => $video->id,
                    'title' => $video->title,
                    'format' => $video->format,
                    'status' => $video->status,
                    'progress' => $progress,
                    'paused' => (bool) $video->paused,
                    'priority' => (int) ($video->priority ?? 0),
                    'queuePosition' => $video->queue_position,
                    'processing' => in_array($video->status, $processing, true),
                    'canDelete' => ! in_array($video->status, ['downloading', 'cutting'], true) && ! $needsRaw,
                    'sourceChannelName' => $video->sourceChannel?->channel_name,
                    'niche' => $niche,
                    'destinationChannelName' => $destinationChannelName,
                    'publishedAt' => $video->published_at?->diffForHumans(),
                    'score' => $video->generatedClips->max('score'),
                    'clipCount' => $video->generatedClips->count(),
                ];
            })
            ->values()
            ->all();
    }

    private function quotaData(): array
    {
        $date = Carbon::now('America/Sao_Paulo')->format('Y-m-d');
        $today = Carbon::today('America/Sao_Paulo');
        // min(MAX_UPLOADS_PER_DAY, 6) espelha ABSOLUTE_MAX_UPLOADS_PER_DAY em
        // clip-processor/src/quota_manager.py — mesma env var, mesmo teto.
        $limit = min((int) env('MAX_UPLOADS_PER_DAY', 5), 6);

        return DestinationChannel::query()->where('active', true)->get()
            ->map(function (DestinationChannel $channel) use ($date, $today, $limit) {
                $key = "youtube_uploads:{$channel->youtube_channel_id}:{$date}";
                try {
                    $redisCount = (int) (Redis::connection('pipeline')->get($key) ?? 0);
                } catch (\Throwable) {
                    $redisCount = 0;
                }

                $dbCount = GeneratedClip::query()
                    ->where('destination_channel_id', $channel->id)
                    ->where('status', 'published')
                    ->whereDate('updated_at', $today)
                    ->count();

                return [
                    'name' => $channel->name,
                    'slug' => $channel->slug,
                    'niche' => $channel->niche,
                    'count' => max($redisCount, $dbCount),
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

        $publishedTotal = $publishedCurto + $publishedLongo;
        $rejectedTotal = GeneratedClip::query()
            ->where('status', 'rejected')
            ->where('updated_at', '>=', $since)
            ->count();
        $decidedTotal = $publishedTotal + $rejectedTotal;
        $approvalRate = $decidedTotal > 0 ? (int) round(($publishedTotal / $decidedTotal) * 100) : null;

        return [
            'publishedCurto' => $publishedCurto,
            'publishedLongo' => $publishedLongo,
            'approvalRate' => $approvalRate,
            'backlogCurto' => SourceVideo::query()->where('status', 'pending')->where(fn ($q) => $q->where('format', 'curto')->orWhereNull('format'))->count(),
            'backlogLongo' => SourceVideo::query()->where('status', 'pending')->where('format', 'longo')->count(),
        ];
    }

    private function clipPayload($clips): array
    {
        $disk = Storage::disk('clips-videos');

        return $clips->map(function (GeneratedClip $clip) use ($disk) {
            $hasVideo = $disk->exists("clips/{$clip->id}.mp4");
            $hasThumb = $disk->exists("thumbnails/{$clip->id}.jpg");

            return [
                'id' => $clip->id,
                'title' => $clip->title,
                'score' => $clip->score,
                'trecho' => $this->formatTrecho($clip->start_time, $clip->end_time),
                'startTime' => $clip->start_time,
                'endTime' => $clip->end_time,
                'sourceVideoTitle' => $clip->sourceVideo?->title,
                'sourceChannelName' => $clip->sourceVideo?->sourceChannel?->channel_name,
                'format' => $clip->sourceVideo?->format ?? 'curto',
                'destinationChannelName' => $clip->destinationChannel?->name,
                'destinationChannelSlug' => $clip->destinationChannel?->slug,
                'niche' => $clip->destinationChannel?->niche ?? $clip->sourceVideo?->sourceChannel?->target_niche ?? 'futebol',
                'createdAt' => $clip->created_at?->diffForHumans(),
                'updatedAt' => $clip->updated_at?->diffForHumans(),
                'uploadError' => $clip->upload_error,
                'previewUrl' => route('clips.preview', $clip->id),
                'thumbnailUrl' => route('clips.thumbnail', $clip->id),
                'hasVideoFile' => $hasVideo,
                'hasThumbnailFile' => $hasThumb,
                'description' => $clip->description,
                'tags' => $clip->tags,
                'destinationTemplate' => $clip->destinationChannel?->effective_template_config,
                'destinationChannelWatermarkUrl' => $clip->destinationChannel?->slug
                    ? (Storage::disk('branding')->exists("watermark-{$clip->destinationChannel->slug}.png")
                        ? route('destination-channels.watermark', $clip->destinationChannel->id)
                        : null)
                    : null,
                'destinationChannelBackgroundUrl' => $clip->destinationChannel?->id
                    ? route('destination-channels.background', $clip->destinationChannel->id)
                    : null,
            ];
        })->values()->all();
    }

    private function formatTrecho(?float $start, ?float $end): string
    {
        if ($start === null || $end === null) {
            return '—';
        }

        $fmt = fn (float $seconds): string => sprintf('%d:%02d', intdiv((int) $seconds, 60), (int) $seconds % 60);

        return "{$fmt($start)}–{$fmt($end)}";
    }

    public function approve(GeneratedClip $clip, ClipProcessorClient $client): RedirectResponse
    {
        $affected = GeneratedClip::query()
            ->where('id', $clip->id)
            ->where('status', 'pending')
            ->update(['status' => 'approved']);

        if ($affected) {
            $client->publishNow();
        }

        return back()->with($affected ? 'success' : 'error', $affected
            ? "Clip #{$clip->id} aprovado e enviado para publicação"
            : 'Clip não estava mais pendente');
    }

    public function reject(GeneratedClip $clip): RedirectResponse
    {
        if (! in_array($clip->status, ['pending', 'approved'], true)) {
            return back()->with('error', 'Status inválido para rejeitar');
        }

        $disk = Storage::disk('clips-videos');
        $id = $clip->id;
        $disk->delete([
            "clips/{$id}.mp4",
            "clips/{$id}_raw.mp4",
            "clips/{$id}_subtitled.mp4",
            "clips/{$id}.srt",
            "thumbnails/{$id}.jpg",
        ]);

        $clip->update(['status' => 'rejected']);

        return back()->with('success', "Clip #{$clip->id} rejeitado");
    }

    /**
     * Reenvia um clip 'failed' para reprocessamento: volta pra 'pending_cut' se o
     * corte nunca terminou (clip_path vazio), ou pro status publicável (approved/
     * pending, conforme MANUAL_APPROVAL_REQUIRED) se o corte existe e só o upload falhou.
     */
    public function reprocess(GeneratedClip $clip, ClipProcessorClient $client): RedirectResponse
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

        if ($affected && $newStatus === 'approved') {
            $client->publishNow();
        }

        return back()->with($affected ? 'success' : 'error', $affected
            ? "Clip #{$clip->id} reenviado para reprocessamento"
            : 'Clip não está mais em falha');
    }

    public function bulkApprove(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $ids = $request->validate(['ids' => ['required', 'array'], 'ids.*' => ['integer']])['ids'];

        $affected = GeneratedClip::query()
            ->whereIn('id', $ids)
            ->where('status', 'pending')
            ->update(['status' => 'approved']);

        if ($affected > 0) {
            $client->publishNow();
        }

        return back()->with('success', "{$affected} clip(s) aprovado(s) e enviado(s) para publicação");
    }

    public function bulkDeleteVideos(Request $request): RedirectResponse
    {
        $ids = $request->validate([
            'ids' => ['required', 'array', 'min:1'],
            'ids.*' => ['integer'],
        ])['ids'];

        $videos = SourceVideo::whereIn('id', $ids)->get();
        $disk = Storage::disk('clips-videos');
        $deletedCount = 0;

        foreach ($videos as $video) {
            $ytId = $video->youtube_video_id;
            if ($ytId) {
                $disk->delete(["{$ytId}.mp4", "{$ytId}_raw.mp4"]);
            }
            $video->update([
                'local_path' => null,
                'status' => in_array($video->status, ['selecting', 'downloaded', 'transcribing', 'downloading']) ? 'failed' : $video->status,
            ]);
            $deletedCount++;
        }

        return back()->with('success', "{$deletedCount} vídeo(s) apagado(s) com sucesso");
    }

    /**
     * Apaga o arquivo bruto (.mp4) de um vídeo fonte pra liberar espaço/vaga na
     * janela de download. Não mexe nos clips já cortados a partir dele.
     */
    public function deleteVideo(SourceVideo $video): RedirectResponse
    {
        $disk = Storage::disk('clips-videos');
        $ytId = $video->youtube_video_id;
        if ($ytId) {
            $disk->delete(["{$ytId}.mp4", "{$ytId}_raw.mp4"]);
        }

        $video->update([
            'local_path' => null,
            'status' => in_array($video->status, ['selecting', 'downloaded', 'transcribing', 'downloading']) ? 'failed' : $video->status,
        ]);

        return back()->with('success', "Vídeo #{$video->id} apagado com sucesso");
    }

    public function pauseVideo(SourceVideo $video, ClipProcessorClient $client): RedirectResponse
    {
        try {
            $client->pauseVideo($video->id);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        return back()->with('success', "Vídeo #{$video->id} pausado");
    }

    public function resumeVideo(SourceVideo $video, ClipProcessorClient $client): RedirectResponse
    {
        try {
            $client->resumeVideo($video->id);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        return back()->with('success', "Vídeo #{$video->id} retomado");
    }

    public function prioritizeVideo(SourceVideo $video, ClipProcessorClient $client): RedirectResponse
    {
        try {
            $client->prioritizeVideo($video->id);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        return back()->with('success', "Vídeo #{$video->id} priorizado");
    }

    public function reorderVideos(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $ids = $request->validate([
            'ids' => ['required', 'array', 'min:1'],
            'ids.*' => ['integer'],
        ])['ids'];

        try {
            $client->reorderVideos($ids);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        return back()->with('success', 'Ordem da janela atualizada');
    }

    public function bulkReject(Request $request): RedirectResponse
    {
        $ids = $request->validate(['ids' => ['required', 'array'], 'ids.*' => ['integer']])['ids'];

        $clips = GeneratedClip::query()
            ->whereIn('id', $ids)
            ->whereIn('status', ['pending', 'approved'])
            ->get();

        $disk = Storage::disk('clips-videos');
        foreach ($clips as $clip) {
            $id = $clip->id;
            $disk->delete([
                "clips/{$id}.mp4",
                "clips/{$id}_raw.mp4",
                "clips/{$id}_subtitled.mp4",
                "clips/{$id}.srt",
                "thumbnails/{$id}.jpg",
            ]);
        }

        $affected = GeneratedClip::query()
            ->whereIn('id', $ids)
            ->whereIn('status', ['pending', 'approved'])
            ->update(['status' => 'rejected']);

        return back()->with('success', "{$affected} clip(s) rejeitado(s)");
    }
}
