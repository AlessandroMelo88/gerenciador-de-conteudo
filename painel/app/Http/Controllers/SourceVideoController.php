<?php

namespace App\Http\Controllers;

use App\Models\SourceVideo;
use App\Services\ClipProcessorClient;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
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
        $perPage = (int) $request->query('per_page', 100);
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
            default => $query->where('status', '!=', 'failed'),
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
                $q->where('title', 'like', "%{$search}%")
                    ->orWhereHas('sourceChannel', fn ($q2) => $q2->where('channel_name', 'like', "%{$search}%"));
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
        $activeVideos = SourceVideo::whereNotNull('local_path')
            ->orWhereIn('status', ['downloading', 'downloaded', 'transcribing', 'selecting', 'cutting', 'publishing'])
            ->get();

        $curtoCount = $activeVideos->where('format', 'curto')->count();
        $longoCount = $activeVideos->where('format', 'longo')->count();
        $total = $activeVideos->count();
        $processingCount = $activeVideos->whereIn('status', ['downloading', 'transcribing', 'selecting', 'cutting'])->count();

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
        $uso = match (true) {
            $video->status === 'failed' => 'Falhou — pode apagar',
            $video->total_clips_count > 0 && $video->em_andamento_count === 0 && $video->publicados_count === 0 => 'Sem uso — pode apagar',
            $video->publicados_count > 0 && $video->em_andamento_count === 0 => 'Publicado',
            default => 'Em uso',
        };

        $canDelete = ! in_array($video->status, ['downloading', 'cutting'], true)
            && $video->em_andamento_count === 0;

        return [
            'id' => $video->id,
            'title' => $video->title,
            'channelName' => $video->sourceChannel?->channel_name,
            'status' => $video->status,
            'statusLabel' => self::STATUS_LABEL[$video->status] ?? $video->status,
            'youtubeVideoId' => $video->youtube_video_id,
            'hasLocalFile' => filled($video->local_path),
            'canDelete' => $canDelete,
            'uso' => $uso,
            'publishedAt' => $video->published_at?->format('d/m/Y H:i'),
            'updatedAt' => $video->updated_at?->diffForHumans(),
        ];
    }

    public function deleteFile(SourceVideo $video): RedirectResponse
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

        return back()->with('success', "Arquivos apagados com sucesso");
    }

    public function bulkDeleteFiles(Request $request): RedirectResponse
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
            $video->update([
                'local_path' => null,
                'status' => in_array($video->status, ['selecting', 'downloaded', 'transcribing', 'downloading']) ? 'failed' : $video->status,
            ]);
            $deletedCount++;
        }

        return back()->with('success', "{$deletedCount} arquivo(s) de vídeo apagado(s)");
    }

    public function purgeOld(Request $request): RedirectResponse
    {
        $data = $request->validate(['before_date' => ['required', 'date']]);
        $date = $data['before_date'];

        $videos = SourceVideo::where('published_at', '<', $date)->get();
        $disk = Storage::disk('clips-videos');
        $count = 0;

        foreach ($videos as $video) {
            $ytId = $video->youtube_video_id;
            if ($ytId) {
                $disk->delete(["{$ytId}.mp4", "{$ytId}_raw.mp4"]);
            }
            $video->delete();
            $count++;
        }

        return back()->with('success', "{$count} vídeo(s) antigo(s) removido(s)");
    }
}
