<?php

namespace App\Http\Controllers;

use App\Models\SourceVideo;
use App\Services\ClipProcessorClient;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
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
        ]);
    }

    private function payload(SourceVideo $video): array
    {
        $uso = match (true) {
            $video->status === 'failed' => 'Falhou — pode apagar',
            $video->total_clips_count > 0 && $video->em_andamento_count === 0 && $video->publicados_count === 0 => 'Sem uso — pode apagar',
            $video->publicados_count > 0 && $video->em_andamento_count === 0 => 'Publicado',
            default => 'Em uso',
        };

        return [
            'id' => $video->id,
            'title' => $video->title,
            'channelName' => $video->sourceChannel?->channel_name,
            'status' => $video->status,
            'statusLabel' => self::STATUS_LABEL[$video->status] ?? $video->status,
            'youtubeVideoId' => $video->youtube_video_id,
            'hasLocalFile' => filled($video->local_path),
            'uso' => $uso,
            'publishedAt' => $video->published_at?->format('d/m/Y H:i'),
            'updatedAt' => $video->updated_at?->diffForHumans(),
        ];
    }

    public function deleteFile(SourceVideo $video, ClipProcessorClient $client): RedirectResponse
    {
        try {
            $result = $client->deleteSourceVideo($video->id);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        $mb = round($result['freed_bytes'] / 1024 / 1024, 1);

        return back()->with('success', "Arquivo apagado ({$mb} MB liberados)");
    }

    public function bulkDeleteFiles(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $ids = $request->validate(['ids' => ['required', 'array'], 'ids.*' => ['integer']])['ids'];
        $videos = SourceVideo::query()->whereIn('id', $ids)->get();

        $freedBytes = 0;
        $failures = 0;
        $skipped = 0;

        foreach ($videos as $video) {
            if (blank($video->local_path)) {
                $skipped++;

                continue;
            }

            try {
                $result = $client->deleteSourceVideo($video->id);
                $freedBytes += $result['freed_bytes'];
            } catch (RuntimeException) {
                $failures++;
            }
        }

        $mb = round($freedBytes / 1024 / 1024, 1);
        $extra = collect([
            $failures > 0 ? "{$failures} arquivo(s) não puderam ser apagados." : null,
            $skipped > 0 ? "{$skipped} já não tinham arquivo local (ignorados)." : null,
        ])->filter()->implode(' ');

        return back()->with('success', trim("{$mb} MB liberados. {$extra}"));
    }

    public function purgeOld(Request $request, ClipProcessorClient $client): RedirectResponse
    {
        $data = $request->validate(['before_date' => ['required', 'date']]);

        try {
            $result = $client->purgeOldVideos($data['before_date']);
        } catch (RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }

        $mb = round($result['freed_bytes'] / 1024 / 1024, 1);

        return back()->with('success', "{$result['deleted_rows']} vídeo(s) removido(s) do banco, {$mb} MB liberados");
    }
}
