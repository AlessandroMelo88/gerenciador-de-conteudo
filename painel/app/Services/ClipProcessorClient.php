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
}
