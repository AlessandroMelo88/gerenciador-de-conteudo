<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
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
     * Apaga o arquivo bruto (.mp4) de um source_video no disco do clip-processor
     * e zera local_path no banco. Não mexe em status/generated_clips.
     *
     * @return array{deleted: bool, freed_bytes: int}
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
            'freed_bytes' => (int) $response->json('freed_bytes', 0),
        ];
    }

    /**
     * Limpa vídeos fonte publicados antes de `$beforeDate` (formato 'Y-m-d'):
     * apaga a linha inteira dos que nunca foram processados (sem clips), e libera
     * o arquivo bruto dos que já geraram clips mas não precisam mais dele.
     *
     * @return array{deleted_rows: int, freed_bytes: int}
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
            'freed_bytes' => (int) $response->json('freed_bytes', 0),
        ];
    }

    /**
     * Inicia uma transcrição local (whisper-cpp) de uma URL do YouTube no clip-processor.
     * Timeout curto porque o endpoint só cria o job e dispara a thread de background —
     * não espera o whisper terminar.
     *
     * @return array{job_id: int}
     *
     * @throws RuntimeException em erro HTTP.
     */
    public function transcribe(string $url): array
    {
        $response = Http::timeout(15)
            ->withHeader('X-Internal-Token', (string) $this->token)
            ->post($this->baseUrl.'/internal/transcribe', ['url' => $url]);

        if (! $response->successful()) {
            throw new RuntimeException('Erro ao iniciar transcrição: HTTP '.$response->status());
        }

        return ['job_id' => (int) $response->json('job_id', 0)];
    }
}
