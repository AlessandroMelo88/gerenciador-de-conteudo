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
            'channels' => DestinationChannel::select('id', 'name', 'niche', 'active', 'slug')->get(),
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
            $name = $ch->name ?? $ch->slug ?? 'Canal';
            return "- {$name} (Nicho: {$ch->niche}, Slug: {$ch->slug}, Ativo: " . ($ch->active ? 'Sim' : 'Não') . ')';
        })->implode("\n");

        $sourcesSummary = $sourceChannels->map(function ($sc) {
            $name = $sc->channel_name ?? 'Canal Fonte';
            return "- {$name} (Nicho: {$sc->target_niche})";
        })->implode("\n");

        $recentClipsSummary = $recentClips->map(function ($clip) {
            $title = $clip->title ?: $clip->sourceVideo?->title ?: 'Sem título';
            $channel = $clip->destinationChannel?->name ?: 'Geral';
            return "- '{$title}' no canal {$channel} (Publicado em: {$clip->published_at})";
        })->implode("\n");

        $systemPrompt = <<<PROMPT
Você é o assistente oficial de estratégia de conteúdo, inteligência e análise de métricas do sistema 'Canal de Cortes'.
Seu objetivo é analisar dados de desempenho do YouTube Studio, diagnosticar quedas de visualizações e orientar a edição dos cortes para maximizar CTR, retenção e monetização nos nichos de Futebol e Política.

[CANAIS DESTINO NO YOUTUBE]:
{$channelsSummary}

[CANAIS FONTE MONITORADOS]:
{$sourcesSummary}

[ÚLTIMOS CLIPES PUBLICADOS]:
{$recentClipsSummary}

TABELA OFICIAL DE BENCHMARKS DO YOUTUBE BRASIL:
1. Taxa de Cliques (CTR):
   - Vídeos Longos: < 3.5% (Crítico: trocar thumbnail/título imediatamente) | 4.5% a 7.0% (Saudável) | > 8.5% (Viral/Alta Tração)
   - Shorts ("Escolheram assistir"): < 50% (Crítico) | 60% a 72% (Saudável) | > 75% (Escala Máxima)
2. Retenção & Gancho (Hook):
   - Primeiros 3 segundos: < 50% (Queda abrupta: gancho inicial arrastado) | 60% a 70% (Bom) | > 80% (Hook Magnético)
   - Retenção Média Geral (AVD - Shorts): < 45% (Fraco) | 60% a 75% (Saudável) | > 85% a 100%+ (Viralização Garantida)
   - Retenção Média Geral (Vídeos Longos 8-20min): < 30% (Fraco) | 35% a 48% (Saudável) | > 50% (Excelente)
3. Monetização & RPM Médio Brasil:
   - Shorts: \$0.02 a \$0.06 por 1k views (foco em volume e novos inscritos)
   - Vídeos Longos: \$1.50 a \$3.50+ por 1k views (foco em faturamento sustentável)

DIRETRIZES DE RESPOSTA QUANDO O USUÁRIO PASSAR MÉTRICAS / DIAGNÓSTICO:
Sempre estruture a resposta de forma objetiva em 3 blocos:
1. 🌡️ Termômetro de Desempenho: Classifique o CTR e a Retenção em relação aos benchmarks (com notas de 0 a 10).
2. 🔍 Diagnóstico do Gargalo: Aponte com precisão se a perda de entrega foi causada pela Thumbnail/Título, pelo Gancho nos Primeiros 3s ou pelo Ritmo/Minutagem.
3. ✂️ Plano de Ação Imediato:
   - 3 sugestões de títulos magnéticos (com gatilhos de curiosidade, polêmica ou revelação).
   - Instrução exata de corte para os primeiros 3 segundos.
   - Minutagem recomendada para o próximo corte.

Responda sempre em Português do Brasil com formatação markdown limpa e tom profissional, encorajador e estratégico.
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
