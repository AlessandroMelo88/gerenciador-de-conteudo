<?php

namespace App\Services;

use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

/**
 * Relatório de visualizações (tela "Métricas"): o que rende mais, por formato e por canal-fonte.
 *
 * Fonte: `clip_metrics` (histórico gravado pelo coletor do clip-processor), ligado a
 * `generated_clips` -> `source_videos` (formato curto/longo) -> `source_channels` (canal-fonte).
 *
 * A conta é feita em PHP, não em SQL, para valer igual em PostgreSQL e MySQL: o volume é pequeno
 * (a coleta para aos 30 dias; no máximo algumas centenas de clips na janela).
 *
 * "Views nas primeiras 24 h" = a última medição feita até 24 h depois da publicação; "aos 7 dias",
 * idem até 7 dias. Só entra o clip que já tem essa idade (senão a média sairia puxada para baixo
 * por clips ainda novos).
 */
class MetricsReport
{
    /** Clips publicados há mais que isso saem do relatório (a coleta já parou aos 30 dias). */
    public const WINDOW_DAYS = 60;

    /** Abaixo disso o clip conta como "sem tração". */
    public const LOW_VIEWS = 50;

    /** Só julga "sem tração" quem já teve tempo de render: pelo menos 2 dias no ar. */
    public const LOW_MIN_AGE_HOURS = 48;

    public const LOW_LIMIT = 30;

    private const FORMAT_LABELS = ['curto' => 'Short (curto)', 'longo' => 'Vídeo longo'];

    /** @return array<string, mixed> */
    public function build(?Carbon $now = null): array
    {
        $now ??= now();
        $tz = config('app.timezone');

        $clips = DB::table('generated_clips as gc')
            ->join('source_videos as sv', 'sv.id', '=', 'gc.source_video_id')
            ->leftJoin('source_channels as sc', 'sc.id', '=', 'sv.channel_id')
            ->where('gc.status', 'published')
            ->whereNotNull('gc.published_at')
            ->where('gc.published_at', '>=', $now->copy()->subDays(self::WINDOW_DAYS))
            ->select('gc.id', 'gc.title', 'gc.youtube_video_id', 'gc.published_at',
                // Formato do clip (gc.format) quando existe; senão o da fonte.
                Schema::hasColumn('generated_clips', 'format')
                    ? DB::raw('COALESCE(gc.format, sv.format) as format')
                    : 'sv.format',
                'sc.id as source_channel_id', 'sc.channel_name')
            ->get();

        $snapshots = [];
        foreach ($clips->pluck('id')->chunk(1000) as $ids) {
            DB::table('clip_metrics')
                ->whereIn('generated_clip_id', $ids->all())
                ->orderBy('collected_at')
                ->get(['generated_clip_id', 'collected_at', 'views'])
                ->each(function ($row) use (&$snapshots, $tz) {
                    $snapshots[$row->generated_clip_id][] = [
                        'at' => Carbon::parse($row->collected_at, $tz),
                        'views' => (int) $row->views,
                    ];
                });
        }

        $measured = [];
        foreach ($clips as $clip) {
            $snaps = $snapshots[$clip->id] ?? [];
            if ($snaps === []) {
                continue;
            }
            $publishedAt = Carbon::parse($clip->published_at, $tz);
            $measured[] = [
                'id' => (int) $clip->id,
                'title' => $clip->title ?: '(sem título)',
                'youtubeVideoId' => $clip->youtube_video_id,
                'format' => $clip->format ?: 'curto',
                'sourceId' => $clip->source_channel_id,
                'source' => $clip->channel_name ?: 'Canal-fonte desconhecido',
                'publishedAt' => $publishedAt,
                'latest' => end($snaps)['views'],
                'views24h' => $this->viewsUntil($snaps, $publishedAt, 24, $now),
                'views7d' => $this->viewsUntil($snaps, $publishedAt, 24 * 7, $now),
            ];
        }

        return [
            'hasData' => $measured !== [],
            'publishedClips' => $clips->count(),
            'measuredClips' => count($measured),
            'lastCollectedAt' => $this->lastCollected($snapshots)?->copy()->setTimezone('America/Sao_Paulo')->format('d/m/Y H:i'),
            'lowViewsThreshold' => self::LOW_VIEWS,
            'byFormat' => $this->byFormat($measured),
            'bySource' => $this->bySource($measured),
            'lowViews' => $this->lowViews($measured, $now),
        ];
    }

    /** Última medição feita até $hours depois de publicar; null se o clip ainda não tem essa idade. */
    private function viewsUntil(array $snaps, Carbon $publishedAt, int $hours, Carbon $now): ?int
    {
        $limit = $publishedAt->copy()->addHours($hours);
        if ($now->lt($limit)) {
            return null;
        }
        $views = null;
        foreach ($snaps as $snap) {
            if ($snap['at']->gt($limit)) {
                break;
            }
            $views = $snap['views'];
        }

        return $views;
    }

    private function lastCollected(array $snapshots): ?Carbon
    {
        $last = null;
        foreach ($snapshots as $snaps) {
            $at = end($snaps)['at'];
            if ($last === null || $at->gt($last)) {
                $last = $at;
            }
        }

        return $last;
    }

    private function avg(array $values): ?int
    {
        $values = array_values(array_filter($values, fn ($v) => $v !== null));

        return $values === [] ? null : (int) round(array_sum($values) / count($values));
    }

    /** @return list<array<string, mixed>> */
    private function byFormat(array $measured): array
    {
        $rows = [];
        foreach (self::FORMAT_LABELS as $format => $label) {
            $group = array_filter($measured, fn ($c) => $c['format'] === $format);
            $rows[] = [
                'format' => $format,
                'label' => $label,
                'clips' => count($group),
                'avgViews24h' => $this->avg(array_column($group, 'views24h')),
                'clips24h' => count(array_filter(array_column($group, 'views24h'), fn ($v) => $v !== null)),
                'avgViews7d' => $this->avg(array_column($group, 'views7d')),
                'clips7d' => count(array_filter(array_column($group, 'views7d'), fn ($v) => $v !== null)),
                'avgViewsNow' => $this->avg(array_column($group, 'latest')),
            ];
        }

        return $rows;
    }

    /** @return list<array<string, mixed>> */
    private function bySource(array $measured): array
    {
        $groups = [];
        foreach ($measured as $clip) {
            $groups[$clip['sourceId'] ?? 0][] = $clip;
        }

        $rows = [];
        foreach ($groups as $group) {
            $rows[] = [
                'source' => $group[0]['source'],
                'clips' => count($group),
                'avgViewsNow' => $this->avg(array_column($group, 'latest')),
                'totalViews' => array_sum(array_column($group, 'latest')),
                'shortClips' => count(array_filter($group, fn ($c) => $c['format'] === 'curto')),
                'longClips' => count(array_filter($group, fn ($c) => $c['format'] === 'longo')),
            ];
        }
        usort($rows, fn ($a, $b) => [$b['avgViewsNow'], $b['clips']] <=> [$a['avgViewsNow'], $a['clips']]);

        return $rows;
    }

    /** @return list<array<string, mixed>> */
    private function lowViews(array $measured, Carbon $now): array
    {
        $low = array_filter($measured, fn ($c) => $c['latest'] < self::LOW_VIEWS
            && $c['publishedAt']->lte($now->copy()->subHours(self::LOW_MIN_AGE_HOURS)));
        usort($low, fn ($a, $b) => [$a['latest'], $a['publishedAt']] <=> [$b['latest'], $b['publishedAt']]);

        return array_map(fn ($c) => [
            'id' => $c['id'],
            'title' => $c['title'],
            'source' => $c['source'],
            'format' => $c['format'],
            'views' => $c['latest'],
            'daysOnline' => (int) $c['publishedAt']->diffInDays($now),
            'url' => $c['youtubeVideoId'] ? 'https://www.youtube.com/watch?v='.$c['youtubeVideoId'] : null,
        ], array_slice($low, 0, self::LOW_LIMIT));
    }
}
