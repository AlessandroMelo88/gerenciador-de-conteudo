<?php

namespace App\Http\Controllers;

use App\Models\DestinationChannel;
use App\Models\GeneratedClip;
use App\Models\SourceChannel;
use App\Models\SourceVideo;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Inertia\Inertia;
use Inertia\Response;

class AssistantController extends Controller
{
    /**
     * Exibe a tela do Assistente IA (LLaMA 3.3).
     */
    public function index(): Response
    {
        $stats = [
            'total_source_channels' => SourceChannel::count(),
            'total_dest_channels' => DestinationChannel::count(),
            'total_source_videos' => SourceVideo::count(),
            'total_published_clips' => GeneratedClip::where('status', 'published')->count(),
            'total_pending_clips' => GeneratedClip::whereIn('status', ['pending', 'pending_cut'])->count(),
            'total_approved_clips' => GeneratedClip::where('status', 'approved')->count(),
            'channels' => DestinationChannel::select('title', 'niche', 'active', 'slug')->get(),
        ];

        return Inertia::render('Assistant', [
            'stats' => $stats,
            'groqModel' => config('services.groq.model', 'llama-3.3-70b-versatile'),
        ]);
    }

    /**
     * Processa a pergunta do operador enviando para a Groq Cloud (LLaMA 3.3 70B).
     */
    public function chat(Request $request): JsonResponse
    {
        $request->validate([
            'message' => 'required|string|max:4000',
            'history' => 'nullable|array',
            'history.*.role' => 'required_with:history|in:user,assistant',
            'history.*.content' => 'required_with:history|string',
        ]);

        $apiKey = config('services.groq.key');
        if (! $apiKey) {
            $apiKey = env('GROQ_API_KEY');
        }

        if (! $apiKey) {
            return response()->json([
                'error' => 'Chave da API Groq (GROQ_API_KEY) não configurada no ambiente.',
            ], 422);
        }

        // Compila contexto do canal para enriquecer as respostas da IA
        $destChannels = DestinationChannel::all();
        $sourceChannels = SourceChannel::limit(15)->get();
        $recentClips = GeneratedClip::with(['sourceVideo', 'destinationChannel'])
            ->where('status', 'published')
            ->latest('published_at')
            ->limit(5)
            ->get();

        $channelsSummary = $destChannels->map(function ($ch) {
            return "- {$ch->title} (Nicho: {$ch->niche}, Slug: {$ch->slug}, Ativo: " . ($ch->active ? 'Sim' : 'Não') . ')';
        })->implode("\n");

        $sourcesSummary = $sourceChannels->map(function ($sc) {
            return "- {$sc->title} (Nicho: {$sc->target_niche})";
        })->implode("\n");

        $recentClipsSummary = $recentClips->map(function ($clip) {
            $title = $clip->custom_title ?: $clip->sourceVideo?->title ?: 'Sem título';
            $channel = $clip->destinationChannel?->title ?: 'Geral';
            return "- '{$title}' no canal {$channel} (Publicado em: {$clip->published_at})";
        })->implode("\n");

        $systemPrompt = <<<PROMPT
Você é o assistente oficial de estratégia de conteúdo e inteligência do sistema 'Canal de Cortes'.
Seu objetivo é ajudar o criador a maximizar visualizações, retenção, inscritos e faturamento no YouTube (especialmente com YouTube Shorts e Vídeos Longos nos nichos de Futebol e Política).

Você tem acesso ao estado atual do sistema do operador:
[CANAIS DESTINO NO YOUTUBE]:
{$channelsSummary}

[CANAIS FONTE MONITORADOS]:
{$sourcesSummary}

[ÚLTIMOS CLIPES PUBLICADOS]:
{$recentClipsSummary}

DIRETRIZES DE ESPECIALISTA:
1. Métricas e Monetização:
   - YouTube Shorts: RPM médio no Brasil é de \$0.02 a \$0.06 por 1.000 visualizações (foco em volume e ganho de inscritos rápidos).
   - Vídeos Longos (7 a 20 min): RPM médio no Brasil é de \$1.50 a \$3.50+ por 1.000 visualizações (foco em receita sustentável e tempo de exibição).
   - AdSense: O e-mail do AdSense pode ser centralizado para múltiplos canais, enquanto a autenticação de API e canais individuais fica na conta do canal.
2. Melhores Práticas de Cortes:
   - Primeiros 3 segundos (O Gancho / Hook): Deve iniciar diretamente na frase mais polêmica, reveladora ou no auge da emoção. Evitar introduções longas.
   - Enquadramento vertical (9:16) com fundo desfocado e legendas dinâmicas de alto contraste.
   - Horários de pico no Brasil: Futebol (11h30-13h30 e 18h30-22h00, especialmente pós-jogos); Política (07h00-09h00, 12h00-14h00 e 19h00-22h00).
3. Seja sempre direto, prático, encorajador e objetivo. Use formatação markdown limpa (tópicos, negrito e tabelas quando útil). Responda sempre em Português do Brasil.
PROMPT;

        $messages = [
            ['role' => 'system', 'content' => $systemPrompt],
        ];

        // Adiciona histórico da conversa (últimas 6 mensagens para manter contexto sem estourar limites)
        if ($request->has('history') && is_array($request->history)) {
            $history = array_slice($request->history, -6);
            foreach ($history as $msg) {
                $messages[] = [
                    'role' => $msg['role'],
                    'content' => $msg['content'],
                ];
            }
        }

        $messages[] = [
            'role' => 'user',
            'content' => $request->message,
        ];

        try {
            $response = Http::withHeaders([
                'Authorization' => "Bearer {$apiKey}",
                'Content-Type' => 'application/json',
            ])->timeout(45)->post('https://api.groq.com/openai/v1/chat/completions', [
                'model' => config('services.groq.model', 'llama-3.3-70b-versatile'),
                'messages' => $messages,
                'temperature' => 0.7,
                'max_tokens' => 2048,
            ]);

            if ($response->failed()) {
                Log::error('Groq API Error: ' . $response->body());
                return response()->json([
                    'error' => 'Erro ao comunicar com a Groq API: ' . ($response->json('error.message') ?: $response->status()),
                ], 500);
            }

            $content = $response->json('choices.0.message.content');

            return response()->json([
                'response' => $content,
            ]);
        } catch (\Exception $e) {
            Log::error('AssistantController Exception: ' . $e->getMessage());
            return response()->json([
                'error' => 'Erro interno ao processar a pergunta: ' . $e->getMessage(),
            ], 500);
        }
    }
}
