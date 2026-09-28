<?php

namespace App\Services;

use GuzzleHttp\Psr7\Uri;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\UriInterface;
use RuntimeException;

/**
 * Copy de venda para uma oferta a partir da página do produto/afiliado.
 *
 * Mesmas regras do affiliate-worker (copywriter.py), com foco em conversão.
 * Ordem (regra do projeto: todo caminho de IA nasce com fallback Groq):
 * Anthropic → Groq. Se as duas falharem, lança exceção — o operador escreve na mão.
 */
class OfferCopywriter
{
    public const ANTHROPIC_MODEL = 'claude-haiku-4-5';

    public const MAX_CTA = 60;

    public const MAX_COPY_SHORT = 280;

    private const PAGE_TEXT_LIMIT = 4000;

    private const RULES = 'Você é copywriter de resposta direta e escreve divulgação de ofertas de afiliado em português do Brasil. '
        .'Boas práticas de venda: abra com o benefício ou a dor que o produto resolve (não com a descrição técnica); '
        .'fale com o leitor em segunda pessoa; transforme característica em benefício concreto; '
        .'use prova ou diferencial só se aparecer nos dados; termine com uma chamada para ação clara e única. '
        .'No texto longo, siga a estrutura AIDA (atenção, interesse, desejo, ação) em 2 a 4 parágrafos curtos. '
        .'Regras obrigatórias: '
        .'1) Use somente os dados fornecidos. Não invente preço, desconto, frete, brinde, prazo, estoque ou escassez. '
        .'2) Não prometa resultado nem afirme ganho de renda, saúde, emagrecimento ou cura garantidos. '
        .'3) Não inclua links, URLs nem encurtadores (o link rastreável é anexado depois). '
        .'4) No máximo 2 hashtags, sem caixa alta gritada, no máximo 2 emojis no texto curto. '
        .'5) No texto longo, termine avisando que é link de afiliado. '
        .'Formato: responda APENAS um objeto JSON com as chaves "cta_text" (chamada curta, até 60 caracteres), '
        .'"copy_short" (até 280 caracteres, para Telegram ou comentário fixado) e '
        .'"copy_long" (2 a 4 parágrafos separados por linha em branco, para descrição de vídeo ou blog).';

    private const NICHE_TONE = [
        'futebol' => 'Tom: de torcedor para torcedor, direto, animado, sem exagero.',
        'politica' => 'Tom: sóbrio e informativo. Sem posicionamento partidário, sem atacar ou elogiar políticos, partidos ou ideologias.',
    ];

    /**
     * @return array{cta_text: string, copy_short: string, copy_long: string, provider: string}
     */
    public function generate(string $url, ?string $title = null, ?string $niche = null): array
    {
        $page = $this->fetchPage($url);

        if ($page === null && blank($title)) {
            throw new RuntimeException('Não consegui ler a página. Preencha o título e tente de novo.');
        }

        $system = self::RULES.' '.(self::NICHE_TONE[strtolower((string) $niche)] ?? 'Tom: claro, honesto e objetivo.');
        $user = $this->userPrompt($title, $niche, $page);

        foreach (['anthropic', 'groq'] as $provider) {
            try {
                $text = $provider === 'anthropic' ? $this->viaAnthropic($system, $user) : $this->viaGroq($system, $user);

                return [...$this->normalize($this->parseJson($text)), 'provider' => $provider];
            } catch (\Throwable $e) {
                Log::warning("offer-copy: {$provider} falhou: ".$e->getMessage());
            }
        }

        throw new RuntimeException('A IA não respondeu (Anthropic e Groq falharam). Tente de novo em instantes.');
    }

    /** @return array{title: ?string, description: ?string, price: ?string, text: string}|null */
    public function fetchPage(string $url): ?array
    {
        try {
            $this->assertPublicUrl(new Uri($url));

            $response = Http::timeout(10)
                ->withHeaders([
                    'User-Agent' => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36',
                    'Accept-Language' => 'pt-BR,pt;q=0.9',
                ])
                ->withOptions(['allow_redirects' => [
                    'max' => 5,
                    'protocols' => ['http', 'https'],
                    // Link de afiliado é redirect; cada salto passa pela mesma checagem (SSRF).
                    'on_redirect' => fn (RequestInterface $req, $res, UriInterface $uri) => $this->assertPublicUrl($uri),
                ]])
                ->get($url);
        } catch (\Throwable $e) {
            Log::info('offer-copy: página não lida: '.$e->getMessage());

            return null;
        }

        if (! $response->successful() || ! str_contains(strtolower($response->header('Content-Type')), 'html')) {
            return null;
        }

        return $this->extract($response->body());
    }

    /** @return array{title: ?string, description: ?string, price: ?string, text: string} */
    public function extract(string $html): array
    {
        $dom = new \DOMDocument;
        libxml_use_internal_errors(true);
        $dom->loadHTML('<?xml encoding="UTF-8">'.$html, LIBXML_NONET);
        libxml_clear_errors();
        $xpath = new \DOMXPath($dom);

        $meta = function (string $attr, string $name) use ($xpath): ?string {
            $node = $xpath->query("//meta[@{$attr}='{$name}']/@content")->item(0);

            return $node ? trim($node->nodeValue) : null;
        };

        foreach ($xpath->query('//script|//style|//noscript|//svg|//nav|//footer') as $node) {
            $node->parentNode?->removeChild($node);
        }

        $body = $dom->getElementsByTagName('body')->item(0);
        $text = trim((string) preg_replace('/\s+/u', ' ', $body?->textContent ?? ''));

        return [
            'title' => $meta('property', 'og:title') ?: trim((string) $dom->getElementsByTagName('title')->item(0)?->textContent) ?: null,
            'description' => $meta('property', 'og:description') ?: $meta('name', 'description'),
            'price' => $meta('property', 'product:price:amount') ?: $meta('property', 'og:price:amount'),
            'text' => mb_substr($text, 0, self::PAGE_TEXT_LIMIT),
        ];
    }

    private function assertPublicUrl(UriInterface $uri): void
    {
        if (! in_array(strtolower($uri->getScheme()), ['http', 'https'], true)) {
            throw new RuntimeException('esquema não permitido');
        }

        $ips = $this->resolveHost($uri->getHost());
        if ($ips === []) {
            throw new RuntimeException('host não resolve');
        }

        foreach ($ips as $ip) {
            if (! filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) {
                throw new RuntimeException('endereço interno bloqueado');
            }
        }
    }

    /** @return list<string> */
    protected function resolveHost(string $host): array
    {
        return gethostbynamel($host) ?: [];
    }

    private function userPrompt(?string $title, ?string $niche, ?array $page): string
    {
        $lines = ['Nicho: '.($niche ?: '-')];
        if (filled($title)) {
            $lines[] = "Produto (informado pelo operador): {$title}";
        }
        if ($page) {
            if ($page['title']) {
                $lines[] = "Título da página: {$page['title']}";
            }
            if ($page['description']) {
                $lines[] = "Descrição da página: {$page['description']}";
            }
            $lines[] = $page['price'] ? "Preço na página: {$page['price']}" : 'Preço: não informado (não mencione preço)';
            if ($page['text'] !== '') {
                $lines[] = "Texto da página (trecho):\n{$page['text']}";
            }
        } else {
            $lines[] = 'Página não disponível. Preço: não informado (não mencione preço).';
        }
        $lines[] = 'Gere o JSON pedido.';

        return implode("\n", $lines);
    }

    private function viaAnthropic(string $system, string $user): string
    {
        $key = config('services.anthropic.key');
        if (blank($key)) {
            throw new RuntimeException('ANTHROPIC_API_KEY não definido');
        }

        $response = Http::timeout(45)
            ->withHeaders(['x-api-key' => $key, 'anthropic-version' => '2023-06-01'])
            ->post('https://api.anthropic.com/v1/messages', [
                'model' => self::ANTHROPIC_MODEL,
                'max_tokens' => 1024,
                'system' => $system,
                'messages' => [['role' => 'user', 'content' => $user]],
            ])
            ->throw();

        $block = collect($response->json('content', []))->firstWhere('type', 'text');

        return (string) ($block['text'] ?? '');
    }

    private function viaGroq(string $system, string $user): string
    {
        $key = config('services.groq.key');
        if (blank($key)) {
            throw new RuntimeException('GROQ_API_KEY não definido');
        }

        $response = Http::timeout(45)
            ->withToken($key)
            ->post('https://api.groq.com/openai/v1/chat/completions', [
                'model' => config('services.groq.model'),
                'messages' => [
                    ['role' => 'system', 'content' => $system],
                    ['role' => 'user', 'content' => $user],
                ],
                // Sem response_format: o modo JSON da Groq rejeita a geração inteira (400) por
                // qualquer desvio; o parseJson abaixo já tolera texto em volta do objeto.
                'temperature' => 0.5,
                'max_tokens' => 2048,
            ])
            ->throw();

        return (string) $response->json('choices.0.message.content', '');
    }

    /** Parse defensivo: tolera cercas ```json, bloco <think> e texto em volta do objeto. */
    private function parseJson(string $text): array
    {
        $clean = trim((string) preg_replace('/<think>.*?<\/think>/s', '', $text));
        $clean = trim((string) preg_replace('/^```(?:json)?\s*|\s*```$/', '', $clean));
        $data = json_decode($clean, true);

        if (! is_array($data)) {
            $start = strpos($clean, '{');
            $end = strrpos($clean, '}');
            $data = ($start !== false && $end > $start) ? json_decode(substr($clean, $start, $end - $start + 1), true) : null;
        }

        if (! is_array($data)) {
            throw new RuntimeException('resposta sem JSON válido');
        }

        return $data;
    }

    /** @return array{cta_text: string, copy_short: string, copy_long: string} */
    private function normalize(array $data): array
    {
        $out = [];
        foreach (['cta_text', 'copy_short', 'copy_long'] as $key) {
            $value = is_string($data[$key] ?? null) ? $this->stripUrls($data[$key]) : '';
            if ($value === '') {
                throw new RuntimeException("campo ausente: {$key}");
            }
            $out[$key] = $value;
        }

        $out['cta_text'] = $this->truncate($out['cta_text'], self::MAX_CTA);
        $out['copy_short'] = $this->truncate($out['copy_short'], self::MAX_COPY_SHORT);

        return $out;
    }

    private function stripUrls(string $text): string
    {
        $text = (string) preg_replace('~(https?://\S+|www\.\S+)~i', '', $text);

        return trim((string) preg_replace('/[ \t]{2,}/', ' ', $text));
    }

    private function truncate(string $text, int $limit): string
    {
        if (mb_strlen($text) <= $limit) {
            return $text;
        }
        $cut = rtrim(mb_substr($text, 0, $limit - 1));
        $space = mb_strrpos($cut, ' ');

        return rtrim($space ? mb_substr($cut, 0, $space) : $cut, ' ,;:.-').'…';
    }
}
