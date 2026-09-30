<?php

namespace App\Services;

use App\Exceptions\EmbedderException;
use App\Models\TranscriptionJob;
use Illuminate\Support\Facades\DB;

/**
 * Busca nas transcrições (tabela transcript_chunks): texto (FTS `pt_unaccent` com
 * fallback trigram), semântica (pgvector, cosseno) e híbrida (RRF, k=60).
 * Nunca lança por causa do embedder: degrada para texto e avisa com `degraded`.
 */
class TranscriptSearch
{
    public const MODOS = ['hibrida', 'semantica', 'texto'];

    private const RRF_K = 60;

    private const POOL = 50;

    private const MAX_HITS_POR_JOB = 3;

    private const EF_SEARCH = 100;

    /** Marcadores privados do ts_headline; o resto do snippet é escapado antes de virarem <mark>. */
    private const MARK_OPEN = "\u{E000}";

    private const MARK_CLOSE = "\u{E001}";

    private ?bool $temEmbedding = null;

    public function __construct(private readonly EmbedderClient $embedder) {}

    /**
     * @return array{query: string, mode: string, mode_used: string, degraded: bool, results: list<array<string, mixed>>}
     */
    public function search(string $query, string $modo = 'hibrida', int $limit = 20): array
    {
        $modo = in_array($modo, self::MODOS, true) ? $modo : 'hibrida';
        $limit = max(1, min(50, $limit));
        $modoUsado = $modo;
        $degraded = false;
        $vetor = null;

        if ($modo !== 'texto') {
            try {
                if (! $this->temColunaEmbedding()) {
                    throw new EmbedderException('transcript_chunks sem coluna embedding.');
                }
                $vetor = $this->embedder->embedQuery($query);
            } catch (EmbedderException) {
                $modoUsado = 'texto';
                $degraded = true;
            }
        }

        $linhas = $this->temTabela()
            ? $this->consultar($query, $modoUsado, $vetor, $limit)
            : [];

        return [
            'query' => $query,
            'mode' => $modo,
            'mode_used' => $modoUsado,
            'degraded' => $degraded,
            'results' => $this->agrupar($linhas, $query, $limit),
        ];
    }

    /** @return list<object> */
    private function consultar(string $q, string $modo, ?array $vetor, int $limit): array
    {
        $pool = max(self::POOL, $limit * self::MAX_HITS_POR_JOB);

        if ($modo === 'texto') {
            $linhas = $this->consultaTexto($q, $pool);

            return $linhas !== [] ? $linhas : $this->consultaTrigram($q, $pool);
        }

        $literal = '['.implode(',', $vetor).']';

        return DB::transaction(function () use ($modo, $q, $literal, $pool) {
            DB::statement('SET LOCAL hnsw.ef_search = '.self::EF_SEARCH);

            return $modo === 'semantica'
                ? $this->consultaSemantica($literal, $pool)
                : $this->consultaHibrida($q, $literal, $pool);
        });
    }

    private function consultaTexto(string $q, int $pool): array
    {
        return DB::select(<<<'SQL'
            WITH q AS (SELECT websearch_to_tsquery('pt_unaccent', :q) AS tsq)
            SELECT c.id, c.job_id, c.chunk_index, c.start_seconds, c.end_seconds, c.content,
                   ts_rank_cd(c.search_vector, q.tsq) AS score,
                   ts_headline('pt_unaccent', c.content, q.tsq, :opts) AS snippet
            FROM transcript_chunks c, q
            WHERE c.search_vector @@ q.tsq
            ORDER BY score DESC, c.id
            LIMIT :pool
            SQL, ['q' => $q, 'opts' => $this->headlineOpts(), 'pool' => $pool]);
    }

    /** Erro de digitação / termo parcial: só entra quando o FTS não achou nada. */
    private function consultaTrigram(string $q, int $pool): array
    {
        return DB::select(<<<'SQL'
            SELECT c.id, c.job_id, c.chunk_index, c.start_seconds, c.end_seconds, c.content,
                   word_similarity(:q, c.content) AS score,
                   NULL AS snippet
            FROM transcript_chunks c
            WHERE :q2 <% c.content
            ORDER BY score DESC, c.id
            LIMIT :pool
            SQL, ['q' => $q, 'q2' => $q, 'pool' => $pool]);
    }

    private function consultaSemantica(string $literal, int $pool): array
    {
        return DB::select(<<<'SQL'
            SELECT * FROM (
                SELECT c.id, c.job_id, c.chunk_index, c.start_seconds, c.end_seconds, c.content,
                       1 - (c.embedding <=> CAST(:v AS vector)) AS score,
                       NULL AS snippet
                FROM transcript_chunks c
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> CAST(:v2 AS vector)
                LIMIT :pool
            ) t
            WHERE t.score >= :piso
            ORDER BY t.score DESC
            SQL, [
            'v' => $literal, 'v2' => $literal, 'pool' => $pool,
            'piso' => (float) config('services.embedder.min_similarity', 0.83),
        ]);
    }

    private function consultaHibrida(string $q, string $literal, int $pool): array
    {
        return DB::select(<<<'SQL'
            WITH q AS (SELECT websearch_to_tsquery('pt_unaccent', :q) AS tsq),
            fts AS (
                SELECT c.id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(c.search_vector, q.tsq) DESC, c.id) AS r
                FROM transcript_chunks c, q
                WHERE c.search_vector @@ q.tsq
                LIMIT :pool1
            ),
            vec AS (
                -- Mesmo piso da busca semântica: sem ele, uma consulta sem sentido (ou fora do
                -- assunto de todas as aulas) trazia o acervo inteiro na Híbrida.
                SELECT t.id, ROW_NUMBER() OVER (ORDER BY t.dist) AS r
                FROM (
                    SELECT c.id, c.embedding <=> CAST(:v AS vector) AS dist
                    FROM transcript_chunks c
                    WHERE c.embedding IS NOT NULL
                    ORDER BY c.embedding <=> CAST(:v2 AS vector)
                    LIMIT :pool2
                ) t
                WHERE 1 - t.dist >= :piso
            ),
            rrf AS (
                SELECT id, SUM(1.0 / (:k + r)) AS score
                FROM (SELECT * FROM fts UNION ALL SELECT * FROM vec) x
                GROUP BY id
            )
            SELECT c.id, c.job_id, c.chunk_index, c.start_seconds, c.end_seconds, c.content,
                   rrf.score AS score,
                   ts_headline('pt_unaccent', c.content, (SELECT tsq FROM q), :opts) AS snippet
            FROM rrf JOIN transcript_chunks c ON c.id = rrf.id
            ORDER BY rrf.score DESC, c.id
            LIMIT :pool3
            SQL, [
            'q' => $q, 'v' => $literal, 'v2' => $literal, 'k' => self::RRF_K,
            'pool1' => $pool, 'pool2' => $pool, 'pool3' => $pool * 2,
            'piso' => (float) config('services.embedder.min_similarity', 0.83),
            'opts' => $this->headlineOpts(),
        ]);
    }

    /**
     * Agrupa por transcrição (máx. 3 trechos), mantendo a ordem de relevância.
     *
     * @param  list<object>  $linhas  já ordenadas por score desc
     * @return list<array<string, mixed>>
     */
    private function agrupar(array $linhas, string $query, int $limit): array
    {
        $porJob = [];
        foreach ($linhas as $l) {
            $jobId = (int) $l->job_id;
            if (! isset($porJob[$jobId])) {
                if (count($porJob) >= $limit) {
                    continue;
                }
                $porJob[$jobId] = ['score' => (float) $l->score, 'hits' => []];
            }
            if (count($porJob[$jobId]['hits']) < self::MAX_HITS_POR_JOB) {
                $porJob[$jobId]['hits'][] = $this->hit($l, $query);
            }
        }

        if ($porJob === []) {
            return [];
        }

        $jobs = TranscriptionJob::query()
            ->whereIn('id', array_keys($porJob))
            ->get(['id', 'title', 'platform', 'source_url', 'duration_seconds'])
            ->keyBy('id');

        $resultados = [];
        foreach ($porJob as $jobId => $grupo) {
            $job = $jobs->get($jobId);
            if (! $job) {
                continue;
            }
            $hits = array_map(fn (array $hit) => $this->linkDoYoutube($hit, $job), $grupo['hits']);
            $resultados[] = [
                'job_id' => $jobId,
                'title' => $job->title,
                'platform' => $job->platform,
                'source_url' => $job->source_url,
                'duration_seconds' => $job->duration_seconds,
                'score' => round($grupo['score'], 6),
                'hits' => $hits,
            ];
        }

        return $resultados;
    }

    /**
     * Contrato: aula do YouTube abre o vídeo no minuto (`source_url` + t=<seg>s); as demais
     * ficam com o link interno (detalhe rolado até o parágrafo).
     *
     * @param  array<string, mixed>  $hit
     * @return array<string, mixed>
     */
    private function linkDoYoutube(array $hit, TranscriptionJob $job): array
    {
        $url = (string) $job->source_url;
        $ehYoutube = strcasecmp((string) $job->platform, 'youtube') === 0
            || preg_match('~^https?://([a-z0-9-]+\.)?(youtube\.com|youtu\.be)/~i', $url) === 1;

        if (! $ehYoutube || $hit['start_seconds'] === null || ! preg_match('~^https?://~i', $url)) {
            return $hit;
        }

        $base = preg_replace('/([?&])t=[^&#]*&?/', '$1', explode('#', $url)[0]);
        $base = rtrim((string) $base, '?&');
        $hit['link'] = $base.(str_contains($base, '?') ? '&' : '?').'t='.(int) floor($hit['start_seconds']).'s';

        return $hit;
    }

    /** @return array<string, mixed> */
    private function hit(object $l, string $query): array
    {
        $inicio = $l->start_seconds !== null ? (float) $l->start_seconds : null;
        $link = "/painel/transcricoes/{$l->job_id}?";
        if ($inicio !== null) {
            $link .= 't='.(int) floor($inicio).'&';
        }
        $link .= 'q='.rawurlencode($query);

        return [
            'chunk_id' => (int) $l->id,
            'chunk_index' => (int) $l->chunk_index,
            'start_seconds' => $inicio,
            'end_seconds' => $l->end_seconds !== null ? (float) $l->end_seconds : null,
            'snippet' => $this->snippet($l->snippet, (string) $l->content),
            'score' => round((float) $l->score, 6),
            'link' => $link,
        ];
    }

    /**
     * XSS: o texto da transcrição é conteúdo de terceiros. Escapa tudo e só depois
     * devolve <mark> no lugar dos marcadores privados que o ts_headline inseriu.
     */
    private function snippet(?string $headline, string $content): string
    {
        // Sem headline (trigram / só vetor): começo do trecho, sem destaque.
        $bruto = $headline !== null && $headline !== ''
            ? $headline
            : mb_strimwidth($content, 0, 240, '…');

        // Um marcador que já venha no conteúdo original não pode virar <mark>.
        if ($headline === null || $headline === '') {
            $bruto = str_replace([self::MARK_OPEN, self::MARK_CLOSE], '', $bruto);
        }

        $escapado = htmlspecialchars($bruto, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');

        return str_replace([self::MARK_OPEN, self::MARK_CLOSE], ['<mark>', '</mark>'], $escapado);
    }

    private function headlineOpts(): string
    {
        return 'StartSel='.self::MARK_OPEN.', StopSel='.self::MARK_CLOSE
            .', MaxFragments=1, MaxWords=35, MinWords=15';
    }

    private function temTabela(): bool
    {
        return DB::selectOne(
            "SELECT 1 AS ok FROM information_schema.columns
             WHERE table_schema = current_schema() AND table_name = 'transcript_chunks' AND column_name = 'search_vector'"
        ) !== null;
    }

    private function temColunaEmbedding(): bool
    {
        return $this->temEmbedding ??= DB::selectOne(
            "SELECT 1 AS ok FROM information_schema.columns
             WHERE table_schema = current_schema() AND table_name = 'transcript_chunks' AND column_name = 'embedding'"
        ) !== null;
    }
}
