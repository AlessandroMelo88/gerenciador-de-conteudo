<?php

namespace App\Services;

use GuzzleHttp\Promise\FulfilledPromise;
use GuzzleHttp\Promise\PromiseInterface;
use GuzzleHttp\Psr7\Response as Psr7Response;
use Illuminate\Support\Facades\Http;
use Psr\Http\Message\ResponseInterface;
use Telegram\Bot\HttpClients\HttpClientInterface;

/**
 * Telegram SDK HTTP handler that delegates to Laravel's Http facade.
 *
 * Substitui o GuzzleHttpClient padrão do SDK para que Http::fake() funcione
 * nos testes Feature (TelegramWebhookTest, TelegramCommandsTest, PipelineEventTest).
 * Permite usar Http::assertSent() / Http::assertSentCount() para verificar
 * chamadas à API do Telegram — sendMessage, replyWithMessage, etc.
 */
class TelegramHttpClientHandler implements HttpClientInterface
{
    protected int $timeOut = 30;

    protected int $connectTimeOut = 10;

    public function send(
        string $url,
        string $method,
        array $headers = [],
        array $options = [],
        bool $isAsyncRequest = false
    ): ResponseInterface|PromiseInterface|null {
        $pending = Http::withHeaders($headers)->timeout($this->timeOut);

        if (strtoupper($method) === 'POST') {
            // SDK normaliza params via normalizeParams() → wraps em ['form_params' => $params]
            // para chamadas de texto/comandos (sendMessage, replyWithMessage, etc.)
            $formData = $options['form_params'] ?? [];
            $response = $pending->asForm()->post($url, $formData);
        } else {
            $response = $pending->get($url, $options['query'] ?? []);
        }

        $psr7 = new Psr7Response(
            $response->status(),
            ['Content-Type' => 'application/json'],
            $response->body(),
        );

        return $isAsyncRequest ? new FulfilledPromise($psr7) : $psr7;
    }

    public function getTimeOut(): int
    {
        return $this->timeOut;
    }

    public function setTimeOut(int $timeOut): static
    {
        $this->timeOut = $timeOut;

        return $this;
    }

    public function getConnectTimeOut(): int
    {
        return $this->connectTimeOut;
    }

    public function setConnectTimeOut(int $connectTimeOut): static
    {
        $this->connectTimeOut = $connectTimeOut;

        return $this;
    }
}
