<?php

namespace App\Http\Controllers;

use App\Models\GeneratedClip;
use App\Models\SourceVideo;
use App\Services\ClipProcessorClient;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Inertia\Inertia;
use Inertia\Response;
use RuntimeException;

class SourceVideoController extends Controller
{
    private const NON_TERMINAL_CLIP_STATUSES = ['pending_cut', 'cutting', 'pending', 'approved', 'publishing'];

    private const STATUS_LABEL = [
        'pending' => 'Pendente',
        'downloading' => 'Baixando',
        'downloaded' => 'Baixado',
        'transcribing' => 'Transcrevendo',
        'selecting' => 'Selecionando',
        'cutting' => 'Cortando',
        'publishing' => 'Publicando',
        'published' => 'Publicado',
        'failed' => 'Falha',
    ];

    public function index(Request $request): Response
    {
        $tab = $request->query('tab', 'ativos');
        $perPage = min(max((int) $request->query('per_page', 20), 1), 100);
        $search = $request->query('search');

        $query = SourceVideo::query()
            ->with('sourceChannel')
            ->withCount([
                'generatedClips as total_clips_count',
                'generatedClips as em_andamento_count' => fn ($q) => $q->whereIn('status', self::NON_TERMINAL_CLIP_STATUSES),
                'generatedClips as publicados_count' => fn ($q) => $q->where('status', 'published'),
            ]);

        match ($tab) {
            'falharam' => $query->where('status', 'failed'),
            'todos' => null,
            default => $query->whereNotIn('status', ['failed', 'published']),
        };

        if ($request->filled('status')) {
            $query->where('status', $request->query('status'));
        }

        if ($request->boolean('seguro_apagar')) {
            $query->where(function ($q) {
                $q->where('status', 'failed')
                    ->orWhere(function ($q2) {
                        $q2->whereHas('generatedClips')
                            ->whereDoesntHave('generatedClips', fn ($q3) => $q3->whereIn('status', self::NON_TERMINAL_CLIP_STATUSES))
                            ->whereDoesntHave('generatedClips', fn ($q3) => $q3->where('status', 'published'));
                    });
            });
        }

        if ($request->filled('published_from')) {
            $query->whereDate('published_at', '>=', $request->query('published_from'));
        }
        if ($request->filled('published_until')) {
            $query->whereDate('published_at', '<=', $request->query('published_until'));
        }

        if ($search) {
            $query->where(function ($q) use ($search) {
                $q->where('title', 'ilike', "%{$search}%")
                    ->orWhere('transcript_text', 'ilike', "%{$search}%")
                    ->orWhereHas('sourceChannel', fn ($q2) => $q2->where('channel_name', 'ilike', "%{$search}%"))
                    ->orWhereHas('generatedClips', fn ($clips) => $clips->where(function ($fields) use ($search) {
                        $fields->where('title', 'ilike', "%{$search}%")
                            ->orWhere('description', 'ilike', "%{$search}%")
                            ->orWhere('reason', 'ilike', "%{$search}%");
                    }));
            });
        }

        $videos = $query->orderByDesc('updated_at')->paginate($perPage)->withQueryString();

        return Inertia::render('SourceVideos', [
            'videos' => [
                'data' => collect($videos->items())->map(fn (SourceVideo $v) => $this->payload($v)),
                'currentPage' => $videos->currentPage(),
                'lastPage' => $videos->lastPage(),
                'total' => $videos->total(),
                'perPage' => $videos->perPage(),
            ],
            'filters' => [
                'tab' => $tab,
                'status' => $request->query('status'),
                'seguro_apagar' => $request->boolean('seguro_apagar'),
                'published_from' => $request->query('published_from'),
                'published_until' => $request->query('published_until'),
                'search' => $search,
                'per_page' => $perPage,
            ],
            'statusOptions' => self::STATUS_LABEL,
            'failedCount' => SourceVideo::where('status', 'failed')->count(),
            'storage' => $this->storageMetrics(),
            'downloadWindow' => $this->downloadWindowMetrics(),
        ]);
    }

    private function storageMetrics(): array
    {
        $path = config('filesystems.disks.clips-videos.root') ?: storage_path('app/clips-videos');
        $freeBytes = @disk_free_space($path);
        $totalBytes = @disk_total_space($path);

        if ($freeBytes === false || $totalBytes === false || $totalBytes <= 0) {
            return [
                'freeGb' => 0,
                'totalGb' => 0,
                'usedGb' => 0,
                'usedPercentage' => 0,
                'status' => 'unknown',
            ];
        }

        $usedBytes = $totalBytes - $freeBytes;
        $usedPercentage = round(($usedBytes / $totalBytes) * 100, 1);

        return [
            'freeGb' => round($freeBytes / 1024 / 1024 / 1024, 1),
            'totalGb' => round($totalBytes / 1024 / 1024 / 1024, 1),
            'usedGb' => round($usedBytes / 1024 / 1024 / 1024, 1),
            'usedPercentage' => $usedPercentage,
            'status' => $usedPercentage >= 90 ? 'critical' : ($usedPercentage >= 80 ? 'warning' : 'ok'),
        ];
    }

    private function downloadWindowMetrics(): array
    {
        $base = SourceVideo::query()
            ->where(function ($q) {
                $q->whereNotNull('local_path')
                    ->where('local_path', '!=', '')
                    ->orWhereIn('status', ['downloading', 'downloaded', 'transcribing', 'selecting', 'cutting', 'publishing']);
            });

        $total = (clone $base)->count();
        $curtoCount = (clone $base)->where('format', 'curto')->count();
        $longoCount = (clone $base)->where('format', 'longo')->count();
        $processingCount = SourceVideo::whereIn('status', ['downloading', 'transcribing', 'selecting', 'cutting'])->count();

        return [
            'total' => $total,
            'cap' => 10,
            'curtoCount' => $curtoCount,
            'curtoCap' => 6,
            'longoCount' => $longoCount,
            'longoCap' => 4,
            'processingCount' => $processingCount,
        ];
    }

    private function payload(SourceVideo $video): array
    {
        $status = (string) $video->status;
        $uso = match (true) {
            $status === 'failed' => 'Falhou — pode apagar',
            $video->total_clips_count > 0 && $video->em_andamento_count === 0 && $video->publicados_count === 0 => 'Sem uso — pode apagar',
            $video->publicados_count > 0 && $video->em_andamento_count === 0 => 'Publicado',
            default => 'Em uso',
        };

        $canDelete = ! in_array($status, ['downloading', 'cutting'], true)
            && $video->em_andamento_count === 0;

        return [
            'id' => $video->id,
            'title' => $video->title,
            'channelName' => $video->sourceChannel?->channel_name,
            'status' => $status,
            'statusLabel' => self::STATUS_LABEL[$status],
            'youtubeVideoId' => $video->youtube_video_id,
            'hasLocalFile' => filled($video->local_path),
            'canDelete' => $canDelete,
            'uso' => $uso,
            'publishedAt' => $video->published_at?->format('d/m/Y H:i'),
            'updatedAt' => $video->updated_at?->diffForHumans(),
        ];
    }

    public function deleteFile(SourceVideo $video, ClipProcessorClient $client): RedirectResponse
    {
        try {
            $client->deleteSourceVideo($video->id);
        } catch (RuntimeException $exception) {
            return back()->with('error', $exception->getMessage());
        }

        return back()->with('success', 'Arquivos locais apagados; histórico e transcrição preservados.');
    }

    public function destroyRecord(SourceVideo $video): RedirectResponse
    {
        $disk = Storage::disk('clips-videos');
        $ytId = $video->youtube_video_id;
        if ($ytId) {
            $disk->delete(["{$ytId}.mp4", "{$ytId}_raw.mp4"]);
        }

        foreach ($video->generatedClips as $clip) {
            $id = $clip->id;
            $disk->delete([
                "clips/{$id}.mp4",
                "clips/{$id}_raw.mp4",
                "clips/{$id}_subtitled.mp4",
                "clips/{$id}.srt",
                "thumbnails/{$id}.jpg",
            ]);
            $clip->delete();
        }

        $video->delete();

        return back()->with('success', "Registro do vídeo #{$video->id} removido do banco com sucesso");
    }

    public function bulkDeleteFiles(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $ids = $request->validate(['ids' => ['required', 'array'], 'ids.*' => ['integer']])['ids'];
        $videos = SourceVideo::query()->whereIn('id', $ids)->get();
        $deletedCount = 0;
        $failedIds = [];

        foreach ($videos as $video) {
            try {
                if ($client->deleteSourceVideo($video->id)['deleted']) {
                    $deletedCount++;
                }
            } catch (RuntimeException) {
                $failedIds[] = $video->id;
            }
        }

        if ($failedIds !== []) {
            return back()->with('error', "{$deletedCount} arquivo(s) apagado(s); não foi possível limpar: #".implode(', #', $failedIds));
        }

        return back()->with('success', "{$deletedCount} arquivo(s) de vídeo apagado(s)");
    }

    public function bulkDestroyRecords(Request $request): RedirectResponse
    {
        $ids = $request->validate(['ids' => ['required', 'array'], 'ids.*' => ['integer']])['ids'];
        $videos = SourceVideo::query()->whereIn('id', $ids)->get();
        $disk = Storage::disk('clips-videos');
        $deletedCount = 0;

        foreach ($videos as $video) {
            $ytId = $video->youtube_video_id;
            if ($ytId) {
                $disk->delete(["{$ytId}.mp4", "{$ytId}_raw.mp4"]);
            }
            foreach ($video->generatedClips as $clip) {
                $id = $clip->id;
                $disk->delete([
                    "clips/{$id}.mp4",
                    "clips/{$id}_raw.mp4",
                    "clips/{$id}_subtitled.mp4",
                    "clips/{$id}.srt",
                    "thumbnails/{$id}.jpg",
                ]);
                $clip->delete();
            }
            $video->delete();
            $deletedCount++;
        }

        return back()->with('success', "{$deletedCount} registro(s) excluído(s) do banco de dados");
    }

    public function purgeFailed(ClipProcessorClient $client): RedirectResponse
    {
        $failedVideos = SourceVideo::where('status', 'failed')->get();
        $disk = Storage::disk('clips-videos');
        $videoCount = 0;
        $failedIds = [];

        foreach ($failedVideos as $video) {
            try {
                if ($client->deleteSourceVideo($video->id)['deleted']) {
                    $videoCount++;
                }
            } catch (RuntimeException) {
                $failedIds[] = $video->id;
            }
        }

        $failedClips = GeneratedClip::where('status', 'failed')->get();
        $clipCount = 0;
        foreach ($failedClips as $clip) {
            $id = $clip->id;
            $disk->delete([
                "clips/{$id}.mp4",
                "clips/{$id}_raw.mp4",
                "clips/{$id}_subtitled.mp4",
                "clips/{$id}.srt",
                "thumbnails/{$id}.jpg",
            ]);
            $clip->update(['clip_path' => null, 'thumbnail_path' => null]);
            $clipCount++;
        }

        if ($failedIds !== []) {
            return back()->with('error', "{$videoCount} vídeo(s) e {$clipCount} clip(s) limpos; histórico preservado. Falha nos vídeos: #".implode(', #', $failedIds));
        }

        return back()->with('success', "{$videoCount} vídeo(s) e {$clipCount} clip(s) limpos; registros e transcrições preservados");
    }

    public function purgeOld(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $data = $request->validate(['before_date' => ['required', 'date']]);
        try {
            $result = $client->purgeOldVideos($data['before_date']);
        } catch (RuntimeException $exception) {
            return back()->with('error', $exception->getMessage());
        }

        $message = "{$result['cleaned_videos']} arquivo(s) bruto(s) removido(s), "
            ."{$result['retained_rows']} histórico(s) mantido(s) e "
            ."{$result['transcripts_archived']} transcrição(ões) preservada(s)";

        if ($result['skipped_rows'] > 0) {
            return back()->with('error', $message."; {$result['skipped_rows']} item(ns) em uso foram preservados no disco");
        }

        return back()->with('success', $message);
    }
}
