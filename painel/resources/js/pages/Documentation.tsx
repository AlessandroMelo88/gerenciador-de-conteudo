import { Head, usePage } from '@inertiajs/react';
import { SparklesIcon } from 'lucide-react';

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { AppShell } from '@/layouts/app-shell';

type PageProps = {
    auth: { user: { name: string; email: string } | null };
};

const CHAIN = [
    'Descobre vídeo novo (RSS)',
    'Baixa',
    'Transcreve',
    'IA seleciona momentos',
    'Corta + legenda + marca d\'água',
];

export default function Documentation() {
    const { props } = usePage<PageProps>();

    return (
        <>
            <Head title="Documentação" />
            <AppShell
                title="Documentação do Painel"
                user={props.auth.user}
                description="Como o pipeline funciona e o que cada tela do painel faz."
                withToaster={false}
            >
                <div className="flex flex-col gap-4 max-w-5xl mx-auto w-full pb-8">
                    <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 shadow-xs">
                        <div className="mb-2 flex items-center gap-2 font-medium text-amber-200">
                            <SparklesIcon className="size-4" />
                            Como o pipeline funciona, resumido
                        </div>
                        <p className="mb-3 text-sm text-muted-foreground">
                            Se você não mexer em nada, o sistema publica sozinho, em loop:
                        </p>
                        <div className="flex flex-wrap items-center gap-1.5 text-sm">
                            {CHAIN.map((step) => (
                                <span key={step} className="flex items-center gap-1.5">
                                    <Badge variant="secondary">{step}</Badge>
                                    <span className="text-muted-foreground">→</span>
                                </span>
                            ))}
                            <Badge className="bg-amber-500 text-amber-950">Fila de aprovação</Badge>
                            <span className="text-muted-foreground">→</span>
                            <Badge className="bg-emerald-500 text-emerald-950">Publica (cota diária)</Badge>
                        </div>
                        <p className="mt-3 text-sm text-muted-foreground">
                            As seções abaixo explicam cada tela do painel. Clique no título de cada uma pra
                            abrir/fechar.
                        </p>
                    </div>

                    <Accordion type="multiple" className="w-full space-y-2">
                        <AccordionItem value="assistente-ia" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                            <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                🤖 Assistente IA & Diagnóstico de Métricas (YouTube Studio)
                            </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-3 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            O <strong className="text-foreground">Assistente IA</strong> é uma consultoria estratégica ao vivo alimentada por <strong>LLaMA 3.3 70B</strong> (via Groq Cloud, com inferência gratuita ultrarrápida), integrada com os dados reais dos seus canais e clipes.
                                        </p>

                                        <h4 className="font-bold text-foreground text-sm flex items-center gap-1.5 mt-3">
                                            📊 As 4 Métricas Essenciais do YouTube Studio para Passar para a IA:
                                        </h4>
                                        <p>
                                            No seu painel do <strong>YouTube Studio (studio.youtube.com)</strong>, acesse a aba <em>Estatísticas (Analytics)</em> do vídeo ou canal. São estas 4 métricas que determinam se o algoritmo entrega ou bloqueia seu alcance:
                                        </p>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-2 not-prose">
                                            <div className="p-3 rounded-lg border border-border bg-muted/40">
                                                <div className="font-bold text-foreground text-xs">1. Taxa de Cliques (CTR)</div>
                                                <div className="text-[11px] text-muted-foreground mt-0.5">
                                                    Mede o poder do Título e da Capa (Thumbnail).
                                                </div>
                                                <div className="text-[11px] mt-1 text-emerald-500 font-mono">
                                                    Ideal: 5% a 10%+ (Abaixo de 4% o YouTube freia impressões)
                                                </div>
                                            </div>
                                            <div className="p-3 rounded-lg border border-border bg-muted/40">
                                                <div className="font-bold text-foreground text-xs">2. % de Retenção / Duração Média</div>
                                                <div className="text-[11px] text-muted-foreground mt-0.5">
                                                    Quanto tempo as pessoas assistem sem abandonar o vídeo.
                                                </div>
                                                <div className="text-[11px] mt-1 text-emerald-500 font-mono">
                                                    Longos: 40% a 55%+ | Shorts: 75% a 90%+
                                                </div>
                                            </div>
                                            <div className="p-3 rounded-lg border border-border bg-muted/40">
                                                <div className="font-bold text-foreground text-xs">3. Assistiram vs. Pularam (Swiped Away)</div>
                                                <div className="text-[11px] text-muted-foreground mt-0.5">
                                                    Exclusivo de Shorts. % de pessoas que não passaram reto nos primeiros 3s.
                                                </div>
                                                <div className="text-[11px] mt-1 text-emerald-500 font-mono">
                                                    Ideal: Mínimo de 70% a 80% escolhendo assistir
                                                </div>
                                            </div>
                                            <div className="p-3 rounded-lg border border-border bg-muted/40">
                                                <div className="font-bold text-foreground text-xs">4. Velocidade nas Primeiras 24h-48h</div>
                                                <div className="text-[11px] text-muted-foreground mt-0.5">
                                                    Consumo imediato por inscritos ou público inicial.
                                                </div>
                                                <div className="text-[11px] mt-1 text-emerald-500 font-mono">
                                                    Define se o vídeo entra na esteira de recomendação externa
                                                </div>
                                            </div>
                                        </div>

                                        <h4 className="font-bold text-foreground text-sm mt-3">
                                            🛠️ Como Usar a Ferramenta de Diagnóstico no Painel:
                                        </h4>
                                        <ol className="list-decimal pl-4 space-y-1">
                                            <li>Acesse o menu <strong>Assistente IA</strong> e clique no botão <strong>📊 Diagnóstico YouTube Studio</strong> no topo.</li>
                                            <li>Selecione o formato (<em>Shorts Vertical</em> ou <em>Vídeo Longo Horizontal</em>) e o nicho (<em>Política</em>, <em>Futebol</em>, etc.).</li>
                                            <li>Preencha as visualizações, a retenção % e o CTR obtidos no YouTube Studio.</li>
                                            <li>Digite a dúvida ou sintoma (ex: <em>&quot;O vídeo teve 1.500 views na primeira hora e parou de entregar&quot;</em>) e clique em <strong>Analisar Métricas</strong>.</li>
                                            <li>A IA entregará um diagnóstico com o gargalo exato (Hook nos 3 primeiros segundos, Thumbnail/CTR ou Ritmo) e um plano de ação para o próximo vídeo.</li>
                                        </ol>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            {/* 2. ESTRATÉGIA DE CORTES DE POLÍTICA (MBL / MISSÃO) */}
                            <AccordionItem value="politica-viral" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                                <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                    🏛️ Estratégia de Cortes de Política (Fórmula MBL, Missão e Debates)
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-3 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            O robô de cortes conta com um modelo de seleção especializado no nicho de <strong className="text-foreground">Política</strong>, calibrado para a fórmula de alto engajamento usada pelos canais mais virais do Brasil (ex: canais de cortes do MBL, Missão, Kim Kataguiri, Arthur do Val e sabatinas eleitorais).
                                        </p>

                                        <h4 className="font-bold text-foreground text-sm">Os 4 Pilares da Fórmula de Alta Retenção:</h4>
                                        <div className="space-y-2">
                                            <div className="p-3 rounded-lg border border-purple-500/20 bg-purple-500/5">
                                                <strong className="text-purple-400">1. Gancho Inicial Agressivo (0 a 5 segundos):</strong>
                                                <p className="mt-1 text-xs">
                                                    O corte não tem saudações, introduções ou enrolação. Ele começa diretamente na pergunta mais ácida, na declaração chocante ou no início de uma resposta contundente.
                                                </p>
                                            </div>
                                            <div className="p-3 rounded-lg border border-purple-500/20 bg-purple-500/5">
                                                <strong className="text-purple-400">2. Conflito & Refutação (&quot;Jantada&quot;):</strong>
                                                <p className="mt-1 text-xs">
                                                    A IA busca ativamente momentos onde uma narrativa é quebrada, contradições são expostas ou há embate direto de ideias com forte carga emocional.
                                                </p>
                                            </div>
                                            <div className="p-3 rounded-lg border border-purple-500/20 bg-purple-500/5">
                                                <strong className="text-purple-400">3. Raciocínio Fechado & Fechamento Seco no Ápice:</strong>
                                                <p className="mt-1 text-xs">
                                                    O corte possui começo, meio e fim da ideia, mas termina imediatamente após o golpe argumentativo final, sem sobras. Isso maximiza o loop e incentiva comentários.
                                                </p>
                                            </div>
                                            <div className="p-3 rounded-lg border border-purple-500/20 bg-purple-500/5">
                                                <strong className="text-purple-400">4. Formato Visual 9:16 Otimizado:</strong>
                                                <p className="mt-1 text-xs">
                                                    Enquadramento vertical com fundo desfocado em tempo real, legendas dinâmicas de alto contraste (amarelo/branco) e espaço para manchete no topo.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            {/* 3. CANAIS FONTE & BENCHMARK */}
                            <AccordionItem value="canais-fonte" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                                <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                    📡 Canais Fonte & Análise de Concorrentes (Benchmark)
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-3 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            Canais do YouTube monitorados automaticamente pelo robô para download de matéria-prima bruta. Você também pode cadastrar canais de inspiração e concorrência para análise estratégica.
                                        </p>
                                        <ul>
                                            <li>
                                                <strong>Como cadastrar:</strong> Clique em <em>+ Novo Canal Fonte</em> e insira o <code>@handle</code> (ex: <code>@mblivre</code>, <code>@cortesdomissao</code>, <code>@geglobo</code>), URL completa ou Channel ID (<code>UC...</code>), selecionando o nicho correspondente.
                                            </li>
                                            <li>
                                                <strong>Botão 🧠 Analisar IA:</strong> Presente em cada canal cadastrado. Ao clicar, o Assistente IA abre automaticamente uma auditoria dissecando títulos virais, ganchos de abertura e padrões de edição para você modelar.
                                            </li>
                                            <li>
                                                <strong>Ativo / Bloquear (Blacklist):</strong> O switch &quot;Ativo&quot; pausa novos downloads sem apagar o canal. &quot;Bloquear&quot; ignora qualquer conteúdo futuro desse canal.
                                            </li>
                                            <li>
                                                <strong>Balanceamento de Nichos:</strong> O robô alterna os downloads para não sobrecarregar apenas um nicho (garantindo volume equilibrado entre futebol, política e podcasts).
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            {/* 4. DASHBOARD */}
                            <AccordionItem value="dashboard" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                                <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                    📊 Dashboard & Fila de Publicação
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-2 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            Tela de comando central — visão em tempo real da produção e fila de decisão:
                                        </p>
                                        <ul>
                                            <li>
                                                <strong>Cota de Uploads</strong> — uploads diários realizados por canal destino versus o limite diário da API do YouTube.
                                            </li>
                                            <li>
                                                <strong>Fila de Aprovação</strong> — clipes cortados, legendados e prontos com thumbnail para você aprovar, editar título ou descartar com 1 clique.
                                            </li>
                                            <li>
                                                <strong>Na Fila (Aguardando Cota)</strong> — clipes aprovados que serão postados automaticamente pelo robô respeitando a janela de publicação.
                                            </li>
                                            <li>
                                                <strong>Visualizador Integrado (Preview)</strong> — player que reproduz o clipe cortado no formato vertical 9:16 ou widescreen 16:9 direto no navegador.
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            {/* 5. CANAIS DESTINO & TEMPLATES */}
                            <AccordionItem value="canais-destino" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                                <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                    📺 Canais Destino & Estúdio de Templates (9:16)
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-2 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            Canais do YouTube onde os cortes finais aprovados são publicados.
                                        </p>
                                        <ul>
                                            <li>
                                                <strong>YouTube Channel ID:</strong> Identificador oficial do canal que inicia com <code>UC...</code>.
                                            </li>
                                            <li>
                                                <strong>Estúdio de Templates 9:16:</strong> Personalização visual por canal: cor de destaque, cor das legendas, textos de chamada para inscrição (CTA), logotipo e marca d&apos;água que são queimados diretamente no vídeo.
                                            </li>
                                            <li>
                                                <strong>Autorização OAuth:</strong> Autenticação segura com a API do Google para permitir uploads automatizados na cota diária.
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            {/* 6. VÍDEOS & GERENCIAMENTO DE DISCO */}
                            <AccordionItem value="videos" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                                <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                    🎬 Vídeos & Gerenciamento de Disco
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-2 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            Histórico de todos os vídeos brutos baixados da internet para alimentar o pipeline:
                                        </p>
                                        <ul>
                                            <li>
                                                <strong>Cards de Armazenamento:</strong> Exibem o espaço livre em disco no servidor e a ocupação da janela de download.
                                            </li>
                                            <li>
                                                <strong>Filtro &quot;Seguro Apagar&quot;:</strong> Identifica vídeos brutos que já geraram cortes finais ou foram concluídos, liberando espaço em disco sem risco.
                                            </li>
                                            <li>
                                                <strong>Limpeza Automatizada:</strong> Opções de exclusão de arquivos brutos por período ou em lote para manter o SSD sempre saudável.
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            {/* 7. LINKS ÚTEIS & MONETIZAÇÃO */}
                            <AccordionItem value="links-uteis" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                                <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                    🔗 Links Úteis & Calculadora de Ganhos YouTube
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-3 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            Hub central de ferramentas externas essenciais para monitoramento e monetização:
                                        </p>
                                        <ul>
                                            <li>
                                                <strong>Calculadora de Faturamento em Tempo Real:</strong> Simula os ganhos em Dólar (USD) e Reais (BRL) baseado nas visualizações e no RPM médio do Brasil:
                                                <ul className="list-disc pl-4 mt-1 text-xs">
                                                    <li><em>YouTube Shorts:</em> RPM de $0.02 a $0.06 por 1.000 visualizações (foco em volume e atração rápida de inscritos).</li>
                                                    <li><em>Vídeos Longos (7 a 20 min):</em> RPM de $1.50 a $3.50+ por 1.000 visualizações (foco em alta receita publicitária e retenção).</li>
                                                </ul>
                                            </li>
                                            <li>
                                                <strong>Atalhos Diretos:</strong> Acesso rápido com 1 clique para <em>Social Blade</em>, <em>Influencer Marketing Hub</em>, <em>YouTube Studio</em>, <em>Google AdSense</em> e <em>Groq Cloud Console</em>.
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            {/* 8. PROCESSAR VÍDEO & TRANSCRIÇÃO */}
                            <AccordionItem value="processar-video" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                                <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                    ⚡ Processar Vídeo Manual & Transcrição Local
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-2 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            Recursos para envio pontual e transcrição de áudio:
                                        </p>
                                        <ul>
                                            <li>
                                                <strong>Processar Vídeo:</strong> Permite colar qualquer link do YouTube e escolher se o corte deve ser curto (Shorts 9:16) ou longo (16:9), entrando imediatamente no fluxo de download e corte por IA.
                                            </li>
                                            <li>
                                                <strong>Transcrição Local:</strong> Permite fazer upload de arquivos de áudio/vídeo para transcrição automática com whisper local, com visualização do texto e exportação de legendas (.SRT ou .JSON).
                                            </li>
                                        </ul>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>

                            {/* 9. MONITORAMENTO, SENTRY & WATCHDOG PROATIVO */}
                            <AccordionItem value="monitoramento-watchdog" className="border border-border/80 rounded-xl px-4 bg-card/40 shadow-2xs">
                                <AccordionTrigger className="font-semibold text-foreground text-sm hover:text-primary">
                                    🛡️ Monitoramento, Sentry & Watchdog Proativo
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="prose prose-sm prose-invert max-w-none space-y-3 pt-2 text-xs md:text-[13px] leading-relaxed text-muted-foreground">
                                        <p>
                                            O sistema conta com uma infraestrutura de <strong className="text-foreground">observabilidade em duas camadas</strong> para garantir que nenhuma falha interrompa a postagem diária nos seus canais:
                                        </p>

                                        <div className="my-3 overflow-hidden rounded-xl border border-border/80 bg-zinc-950/70 p-2 md:p-3 shadow-md not-prose flex flex-col items-center justify-center">
                                            <img
                                                src="/images/arquitetura_monitoramento_watchdog.jpg"
                                                alt="Arquitetura de Monitoramento Proativo, Sentry e Watchdog"
                                                className="w-full max-w-4xl max-h-[460px] object-contain rounded-lg shadow-inner"
                                                loading="lazy"
                                            />
                                            <p className="mt-2 text-center text-[11px] text-muted-foreground/80">
                                                Diagrama da infraestrutura de observabilidade proativa (Sentry + Watchdog + Hub Laravel)
                                            </p>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-2 not-prose">
                                            <div className="p-3 rounded-lg border border-red-500/20 bg-red-500/5">
                                                <div className="font-bold text-red-400 text-xs">Camada 1: Sentry (Crashes & Código)</div>
                                                <div className="text-[11px] text-muted-foreground mt-1">
                                                    Captura exceções de baixo nível, erros 500 no PHP/Laravel e falhas imprevistas em chamadas às APIs do YouTube e Groq, notificando o operador instantaneamente.
                                                </div>
                                            </div>
                                            <div className="p-3 rounded-lg border border-amber-500/20 bg-amber-500/5">
                                                <div className="font-bold text-amber-400 text-xs">Camada 2: Watchdog Proativo (watchdog.py)</div>
                                                <div className="text-[11px] text-muted-foreground mt-1">
                                                    Monitor inteligente executado a cada 30 min. Detecta deadlocks de regras de negócio silenciosos e executa rotinas de auto-cura automáticas.
                                                </div>
                                            </div>
                                        </div>

                                        <h4 className="font-bold text-foreground text-sm mt-3">
                                            🔍 O que o Watchdog monitora ativamente:
                                        </h4>
                                        <ul className="space-y-1">
                                            <li>
                                                <strong>Auto-Cura de Clipes Fantasmas:</strong> Identifica clipes aprovados sem arquivo .mp4 físico no disco, marcando-os como falhos e destravando imediatamente as vagas da janela de download.
                                            </li>
                                            <li>
                                                <strong>Deadlock da Janela de Download:</strong> Alerta imediatamente se as 7 vagas estiverem 100% ocupadas por mais de 2 horas sem nenhum progresso.
                                            </li>
                                            <li>
                                                <strong>Fila de Aprovação Vazia:</strong> Avisa se não houver clipes novos gerados há mais de 6 horas durante o horário diurno (08h às 23h).
                                            </li>
                                            <li>
                                                <strong>Validação de Tokens OAuth:</strong> Verifica antes da janela nobre de postagem se os canais ativos possuem autorização válida.
                                            </li>
                                            <li>
                                                <strong>Armazenamento SSD:</strong> Dispara aviso quando o disco do servidor estiver com menos de 5 GB livres ou mais de 85% de uso.
                                            </li>
                                        </ul>

                                        <h4 className="font-bold text-foreground text-sm mt-3">
                                            📲 Notificações no Telegram & E-mail:
                                        </h4>
                                        <p>
                                            Qualquer anomalia crítica dispara um alerta com link direto para o painel de resolução no seu <strong>Telegram</strong> e no seu <strong>E-mail</strong> cadastrado.
                                        </p>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>
                        </Accordion>
                </div>
            </AppShell>
        </>
    );
}
