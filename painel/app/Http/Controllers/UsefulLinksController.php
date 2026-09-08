<?php

namespace App\Http\Controllers;

use Inertia\Inertia;
use Inertia\Response;

class UsefulLinksController extends Controller
{
    /**
     * Exibe a página com links úteis, calculadoras de ganhos e ferramentas.
     */
    public function index(): Response
    {
        $categories = [
            [
                'name' => 'Calculadoras de Ganhos e Monetização',
                'description' => 'Ferramentas para calcular e projetar ganhos por visualizações (CPM/RPM).',
                'links' => [
                    [
                        'title' => 'Social Blade Money Calculator',
                        'url' => 'https://socialblade.com/youtube/youtube-money-calculator',
                        'description' => 'Calculadora clássica de estimativa de ganhos diários/mensais com base em visualizações e faixas de CPM.',
                        'badge' => 'Mais Popular',
                        'tag' => 'Ganhos',
                    ],
                    [
                        'title' => 'Influencer Marketing Hub Calculator',
                        'url' => 'https://influencermarketinghub.com/youtube-money-calculator',
                        'description' => 'Calculadora com ajuste dinâmico de taxa de cliques (CTR) e estimativa de ganhos por vídeo ou canal.',
                        'badge' => 'Completo',
                        'tag' => 'Ganhos',
                    ],
                    [
                        'title' => 'NoxInfluencer Estimator',
                        'url' => 'https://www.noxinfluencer.com/youtube-tools/youtube-money-calculator',
                        'description' => 'Estimativas detalhadas de valor por vídeo, patrocínio e receita estimada por canal.',
                        'badge' => 'Analytics',
                        'tag' => 'Ganhos',
                    ],
                ],
            ],
            [
                'name' => 'YouTube & Google AdSense',
                'description' => 'Acesso rápido às ferramentas oficiais do Google para gerenciar canais e pagamentos.',
                'links' => [
                    [
                        'title' => 'YouTube Studio Analytics',
                        'url' => 'https://studio.youtube.com',
                        'description' => 'Painel oficial do YouTube para acompanhar retenção de público, visualizações em tempo real e CTR.',
                        'badge' => 'Oficial',
                        'tag' => 'YouTube',
                    ],
                    [
                        'title' => 'Google AdSense',
                        'url' => 'https://adsense.google.com',
                        'description' => 'Gerenciamento de pagamentos, extrato de ganhos e vínculo da conta financeira (alessandrobm1988@gmail.com).',
                        'badge' => 'Financeiro',
                        'tag' => 'Google',
                    ],
                    [
                        'title' => 'Google Cloud Console (APIs & OAuth)',
                        'url' => 'https://console.cloud.google.com/apis/credentials',
                        'description' => 'Gerenciamento de credenciais OAuth 2.0 e cotas das APIs do YouTube Data e Analytics.',
                        'badge' => 'Dev',
                        'tag' => 'APIs',
                    ],
                ],
            ],
            [
                'name' => 'Inteligência Artificial & APIs',
                'description' => 'Consoles e documentação dos modelos de IA integrados no pipeline.',
                'links' => [
                    [
                        'title' => 'Groq Cloud Console',
                        'url' => 'https://console.groq.com',
                        'description' => 'Console da Groq para gerenciar chaves de API, limites de requisições e monitorar uso do LLaMA e Whisper.',
                        'badge' => 'Gratuito',
                        'tag' => 'IA',
                    ],
                    [
                        'title' => 'Anthropic Claude Console',
                        'url' => 'https://console.anthropic.com',
                        'description' => 'Painel de desenvolvedor da Anthropic para Claude 3.5 Sonnet e Claude Haiku.',
                        'badge' => 'IA',
                        'tag' => 'IA',
                    ],
                ],
            ],
            [
                'name' => 'Diretrizes & Boas Práticas',
                'description' => 'Documentação oficial para evitar desmonetização e bloqueios de direitos autorais.',
                'links' => [
                    [
                        'title' => 'Diretrizes de Conteúdo Reutilizado do YouTube',
                        'url' => 'https://support.google.com/youtube/answer/1311392',
                        'description' => 'Regras essenciais sobre o que é permitido em canais de cortes e como agregar valor original para monetizar.',
                        'badge' => 'Importante',
                        'tag' => 'Regras',
                    ],
                    [
                        'title' => 'Políticas de Monetização do YouTube Shorts',
                        'url' => 'https://support.google.com/youtube/answer/12504220',
                        'description' => 'Como funciona a divisão do pool de receita publicitária e requisitos de qualificação do Shorts.',
                        'badge' => 'Shorts',
                        'tag' => 'Regras',
                    ],
                ],
            ],
        ];

        return Inertia::render('UsefulLinks', [
            'categories' => $categories,
        ]);
    }
}
