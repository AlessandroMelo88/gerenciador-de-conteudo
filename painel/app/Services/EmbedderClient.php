<?php

namespace App\Services;

use App\Exceptions\EmbedderException;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\RequestException;
use Illuminate\Support\Facades\Http;

/**
 * Cliente do sidecar de embeddings (POST {url}/embed, Bearer). Só embute a consulta
 * do usuário; os chunks são embutidos pelo indexador Python.
 */
class EmbedderClient
{
    public function __construct(
        protected ?string $baseUrl = null,
        protected ?string $token = null,
        protected ?int $timeout = null,
    ) {
        $this->baseUrl ??= (string) config('services.embedder.url');
        $this->token ??= config('services.embedder.token');
        $this->timeout ??= (int) config('services.embedder.timeout', 3);
    }

    /**
     * @return list<float> vetor L2-normalizado da consulta
     *
     * @throws EmbedderException em qualquer falha — quem chama decide degradar.
     */
    public function embedQuery(string $text): array
    {
        if ($this->baseUrl === '') {
            throw new EmbedderException('EMBEDDER_URL não configurada.');
        }

        try {
            $response = Http::withToken((string) $this->token)
                ->acceptJson()
                ->timeout($this->timeout)
                ->post(rtrim($this->baseUrl, '/').'/embed', ['texts' => [$text], 'kind' => 'query'])
                ->throw();
        } catch (ConnectionException|RequestException $e) {
            throw new EmbedderException('Embedder indisponível: '.$e->getMessage(), 0, $e);
        }

        $vector = $response->json('vectors.0');

        if (! is_array($vector) || $vector === [] || ! array_is_list($vector)) {
            throw new EmbedderException('Resposta do embedder sem vetor.');
        }

        foreach ($vector as $v) {
            if (! is_int($v) && ! is_float($v)) {
                throw new EmbedderException('Vetor do embedder inválido.');
            }
        }

        return array_map('floatval', $vector);
    }
}
