<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use RuntimeException;

class ClipProcessorClient
{
    public function __construct(
        protected ?string $baseUrl = null,
        protected ?string $token = null,
    ) {
        $this->baseUrl ??= config('services.clip_processor.url');
        $this->token ??= config('services.clip_processor.token');
    }

    /**
     * @return array{channel_id: string, channel_name: string, channel_handle: string}
     *
     * @throws RuntimeException ao falhar (yt-dlp ou HTTP 4xx/5xx).
     */
    public function resolveChannel(string $url): array
    {
        $response = Http::timeout(30)
            ->withHeader('X-Internal-Token', (string) $this->token)
            ->post($this->baseUrl.'/internal/resolve-channel', ['url' => $url]);

        if ($response->status() === 422) {
            throw new RuntimeException('Não consegui resolver esse canal. Verifique a URL.');
        }

        if (! $response->successful()) {
            throw new RuntimeException('Erro interno ao chamar o clip-processor: HTTP '.$response->status());
        }

        $data = $response->json();

        return [
            'channel_id' => (string) ($data['channel_id'] ?? ''),
            'channel_name' => (string) ($data['channel_name'] ?? ''),
            'channel_handle' => (string) ($data['channel_handle'] ?? ''),
        ];
    }

    /** @return int exit code (0=ok, 1=clip não existe, 2=status inválido). */
    public function rejectClip(int $clipId): int
    {
        $response = Http::timeout(15)
            ->withHeader('X-Internal-Token', (string) $this->token)
            ->post($this->baseUrl.'/internal/reject-clip', ['clip_id' => $clipId]);

        if (! $response->successful()) {
            throw new RuntimeException('Erro ao rejeitar clip: HTTP '.$response->status());
        }

        return (int) $response->json('exit_code', 1);
    }

    /**
     * Enfileira URL do YouTube para processamento pelo pipeline.
     *
     * @param  string  $format  'curto' (shorts, padrão) ou 'longo' (segmento único 10-20min)
     * @return int exit_code (0=ok, 2=URL inválida, 3=metadata yt-dlp falhou)
     *
     * @throws RuntimeException em erro HTTP 5xx ou timeout.
     */
    public function processUrl(string $url, string $format = 'curto'): int
    {
        $response = Http::timeout(30)
            ->withHeader('X-Internal-Token', (string) $this->token)
            ->post($this->baseUrl.'/internal/process-url', ['url' => $url, 'format' => $format]);

        if (! $response->successful()) {
            throw new RuntimeException('Erro ao processar URL: HTTP '.$response->status());
        }

        return (int) $response->json('exit_code', 3);
    }

    /**
     * Limpa arquivos locais seguros, arquiva a transcrição e preserva as linhas
     * da fonte e dos clips no PostgreSQL.
     *
     * @return array{deleted: bool, transcript_archived: bool, freed_bytes: int}
     *
     * @throws RuntimeException ao falhar (vídeo não existe, em uso, ou erro HTTP).
     */
    public function deleteSourceVideo(int $sourceVideoId): array
    {
        $response = Http::timeout(15)
            ->withHeader('X-Internal-Token', (string) $this->token)
            ->post($this->baseUrl.'/internal/delete-source-video', ['source_video_id' => $sourceVideoId]);

        if ($response->status() === 422) {
            throw new RuntimeException((string) $response->json('error', 'Não consegui apagar esse arquivo.'));
        }

        if (! $response->successful()) {
            throw new RuntimeException('Erro interno ao chamar o clip-processor: HTTP '.$response->status());
        }

        return [
            'deleted' => (bool) $response->json('deleted', false),
            'transcript_archived' => (bool) $response->json('transcript_archived', false),
            'freed_bytes' => (int) $response->json('freed_bytes', 0),
        ];
    }

    /**
     * Remove arquivos locais antigos e preserva as linhas e transcrições no banco.
     *
     * @return array{deleted_rows: int, retained_rows: int, cleaned_videos: int, transcripts_archived: int, skipped_rows: int, freed_bytes: int}
     *
     * @throws RuntimeException em erro HTTP.
     */
    public function purgeOldVideos(string $beforeDate): array
    {
        $response = Http::timeout(60)
            ->withHeader('X-Internal-Token', (string) $this->token)
            ->post($this->baseUrl.'/internal/purge-old-videos', ['before_date' => $beforeDate]);

        if (! $response->successful()) {
            throw new RuntimeException('Erro ao limpar vídeos antigos: HTTP '.$response->status());
        }

        return [
            'deleted_rows' => (int) $response->json('deleted_rows', 0),
            'retained_rows' => (int) $response->json('retained_rows', 0),
            'cleaned_videos' => (int) $response->json('cleaned_videos', 0),
            'transcripts_archived' => (int) $response->json('transcripts_archived', 0),
            'skipped_rows' => (int) $response->json('skipped_rows', 0),
            'freed_bytes' => (int) $response->json('freed_bytes', 0),
        ];
    }

    public function pauseVideo(int $sourceVideoId): array
    {
        return $this->queueAction("/internal/videos/{$sourceVideoId}/pause");
    }

    public function resumeVideo(int $sourceVideoId): array
    {
        return $this->queueAction("/internal/videos/{$sourceVideoId}/resume");
    }

    public function prioritizeVideo(int $sourceVideoId): array
    {
        return $this->queueAction("/internal/videos/{$sourceVideoId}/prioritize");
    }

    /** @param  list<int>  $ids */
    public function reorderVideos(array $ids): array
    {
        $response = Http::timeout(15)
            ->withHeader('X-Internal-Token', (string) $this->token)
            ->post($this->baseUrl.'/internal/videos/reorder', ['ids' => array_values($ids)]);

        if ($response->status() === 422) {
            throw new RuntimeException((string) $response->json('error', 'Não consegui reordenar.'));
        }

        if (! $response->successful()) {
            throw new RuntimeException('Erro ao reordenar vídeos: HTTP '.$response->status());
        }

        return $response->json() ?? [];
    }

    /** @return array<string, mixed> */
    private function queueAction(string $path): array
    {
        $response = Http::timeout(15)
            ->withHeader('X-Internal-Token', (string) $this->token)
            ->post($this->baseUrl.$path);

        if ($response->status() === 422) {
            throw new RuntimeException((string) $response->json('error', 'Ação de fila rejeitada.'));
        }

        if (! $response->successful()) {
            throw new RuntimeException('Erro na fila do clip-processor: HTTP '.$response->status());
        }

        return $response->json() ?? [];
    }

    /**
     * Dispara um ciclo imediato de publicação de clipes no clip-processor.
     */
    public function publishNow(): bool
    {
        try {
            $response = Http::timeout(5)
                ->withHeader('X-Internal-Token', (string) $this->token)
                ->post($this->baseUrl.'/internal/publish-now');

            return $response->successful();
        } catch (\Throwable $e) {
            Log::warning('Falha ao disparar publicação imediata: '.$e->getMessage());

            return false;
        }
    }
}
