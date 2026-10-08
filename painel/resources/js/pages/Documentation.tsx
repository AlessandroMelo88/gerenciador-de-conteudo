import { useState, useMemo } from 'react';
import { Head, usePage } from '@inertiajs/react';
import {
    Sparkles,
    Key,
    Shield,
    Tv,
    Bot,
    Play,
    Copy,
    Check,
    ExternalLink,
    AlertTriangle,
    CheckCircle2,
    ArrowRight,
    Terminal,
    Layers,
    Search,
    Mail,
    FileText,
    RefreshCw,
    Clock,
    TrendingUp,
    HardDrive,
    Send,
    Info,
    ChevronRight,
    Flame,
    BookOpen,
    Video,
    Trophy,
    Landmark,
    Mic,
} from 'lucide-react';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AppShell } from '@/layouts/app-shell';

function YoutubeIcon(props: React.SVGProps<SVGSVGElement>) {
    return (
        <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>
    );
}

type PageProps = {
    auth: { user: { name: string; email: string } | null };
};

const CHAIN = [
    { label: 'Descobre vídeo (RSS)', desc: 'A cada 20 min varre os canais fonte ativos' },
    { label: 'Baixa Vídeo', desc: 'Reserva vaga na janela (máx 16 vídeos)' },
    { label: 'Transcreve Áudio', desc: 'Groq Cloud LLaMA/Whisper + Whisper C++ local' },
    { label: 'IA Seleciona Momentos', desc: 'LLaMA 3.3 70B extrai trechos virais com gancho' },
    { label: 'Renderiza Vídeo (FFmpeg)', desc: '9:16 vertical + fundo dinâmico + legendas + watermark' },
    { label: 'Fila de Decisão', desc: 'Aprovação humana ou postagem automática' },
    { label: 'Publica no YouTube', desc: 'Respeita cotas diárias e janelas 12h-14h e 19h-22h' },
];

function CopyButton({ code }: { code: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        toast.success('Comando copiado para a área de transferência');
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/80 hover:bg-muted text-[11px] font-mono text-muted-foreground hover:text-foreground transition-colors border border-border/70 shrink-0"
            title="Copiar comando"
        >
            {copied ? (
                <>
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                    <span className="text-emerald-500 font-medium">Copiado!</span>
                </>
            ) : (
                <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copiar</span>
                </>
            )}
        </button>
    );
}

function CodeBlock({ code, title }: { code: string; title?: string }) {
    return (
        <div className="rounded-xl border border-border/80 bg-zinc-950/80 overflow-hidden font-mono text-xs my-2.5 shadow-sm">
            {title && (
                <div className="flex items-center justify-between px-3.5 py-2 border-b border-border/60 bg-muted/20 text-[11px] text-muted-foreground">
                    <span className="flex items-center gap-1.5 font-medium">
                        <Terminal className="w-3.5 h-3.5 text-primary" />
                        {title}
                    </span>
                    <CopyButton code={code} />
                </div>
            )}
            <div className="p-3.5 overflow-x-auto flex items-start justify-between gap-3 text-zinc-200 text-[12px] leading-relaxed">
                <pre className="whitespace-pre">{code}</pre>
                {!title && <CopyButton code={code} />}
            </div>
        </div>
    );
}

export default function Documentation() {
    const { props } = usePage<PageProps>();
    const [activeTab, setActiveTab] = useState<'guia-canal' | 'pipeline' | 'telas' | 'estrategia' | 'monitoramento' | 'comandos'>('guia-canal');
    const [searchQuery, setSearchQuery] = useState('');

    const tabs = [
        { id: 'guia-canal', label: 'Criar & Automatizar Canal', icon: YoutubeIcon, badge: 'Passo a Passo' },
        { id: 'pipeline', label: 'Pipeline & Automação', icon: Layers, badge: '20 min loop' },
        { id: 'telas', label: 'Manual das Telas', icon: Tv, badge: 'Guia do Painel' },
        { id: 'estrategia', label: 'Estratégia & IA', icon: Bot, badge: 'LLaMA 3.3' },
        { id: 'monitoramento', label: 'Observabilidade & Watchdog', icon: Shield, badge: 'Auto-cura' },
        { id: 'comandos', label: 'Comandos & Runbook', icon: Terminal, badge: 'Operação' },
    ] as const;

    const filteredTabs = useMemo(() => {
        if (!searchQuery.trim()) return tabs;
        const q = searchQuery.toLowerCase();
        return tabs.filter((t) => t.label.toLowerCase().includes(q) || t.badge.toLowerCase().includes(q));
    }, [searchQuery]);

    return (
        <>
            <Head title="Documentação do Sistema" />
            <AppShell
                title="Central de Documentação & Runbook"
                user={props.auth.user}
                description="Manual operacional completo: criação de canais no YouTube, credenciais OAuth, arquitetura do pipeline autônomo, regras de IA e observabilidade."
                withToaster={false}
            >
                <div className="flex flex-col gap-6 max-w-6xl mx-auto w-full pb-16">
                    {/* Banner Superior com Ciclo do Pipeline */}
                    <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-background to-card p-5 md:p-6 shadow-sm">
                        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                            <div className="flex items-center gap-2.5 font-bold text-amber-300 text-base">
                                <Sparkles className="w-5 h-5 text-amber-400" />
                                <span>Fluxo Autônomo de Produção (Pipeline 24/7)</span>
                            </div>
                            <span className="text-xs text-muted-foreground bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full font-mono">
                                Ciclos automáticos a cada 20 min
                            </span>
                        </div>
                        <p className="text-xs md:text-sm text-muted-foreground leading-relaxed mb-4">
                            O Canal de Cortes opera de forma 100% autônoma e descentralizada. Sem intervenção manual, os vídeos brutos são descobertos, baixados, transcritos, lapidados por IA e publicados nos canais de destino nas janelas ideais:
                        </p>

                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-2">
                            {CHAIN.map((step, idx) => (
                                <div
                                    key={step.label}
                                    className="p-2.5 rounded-xl border border-border/80 bg-card/60 flex flex-col justify-between gap-1 shadow-2xs relative group hover:border-amber-500/40 transition-colors"
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="text-[10px] font-mono font-bold text-amber-500">#{idx + 1}</span>
                                        {idx < CHAIN.length - 1 && (
                                            <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/40 hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-10" />
                                        )}
                                    </div>
                                    <div className="font-semibold text-[11px] text-foreground leading-tight">{step.label}</div>
                                    <div className="text-[9.5px] text-muted-foreground leading-tight line-clamp-2">{step.desc}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Barra de Navegação por Categorias e Busca */}
                    <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
                        {/* Seletor de Abas Estilo Pills */}
                        <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-2xl border border-border bg-card shadow-xs">
                            {tabs.map((tab) => {
                                const Icon = tab.icon;
                                const isActive = activeTab === tab.id;
                                return (
                                    <button
                                        key={tab.id}
                                        type="button"
                                        onClick={() => setActiveTab(tab.id)}
                                        className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all ${
                                            isActive
                                                ? 'bg-primary text-primary-foreground shadow-sm'
                                                : 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'
                                        }`}
                                    >
                                        <Icon className="w-3.5 h-3.5 shrink-0" />
                                        <span>{tab.label}</span>
                                        <span
                                            className={`rounded-md px-1.5 py-0.2 text-[10px] font-mono hidden sm:inline-block ${
                                                isActive ? 'bg-primary-foreground/20 text-primary-foreground' : 'bg-muted text-muted-foreground'
                                            }`}
                                        >
                                            {tab.badge}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>

                        {/* Busca rápida */}
                        <div className="relative w-full md:w-64">
                            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                            <Input
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Filtrar tópicos..."
                                className="h-10 pl-9 pr-3 rounded-xl text-xs bg-card"
                            />
                        </div>
                    </div>

                    {/* ========================================================================= */}
                    {/* ABA 1: GUIA PASSO A PASSO PARA CRIAR & AUTOMATIZAR CANAL NO YOUTUBE      */}
                    {/* ========================================================================= */}
                    {activeTab === 'guia-canal' && (
                        <div className="space-y-6">
                            {/* Card de Boas-Vindas ao Guia */}
                            <div className="rounded-2xl border border-primary/20 bg-primary/5 p-5 md:p-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                                        <YoutubeIcon className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-lg text-foreground">
                                            Guia Completo: Criar, Autenticar e Automatizar um Canal no YouTube
                                        </h3>
                                        <p className="text-xs text-muted-foreground">
                                            Siga este roteiro detalhado do zero até a publicação 100% autônoma pelo pipeline.
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                                    <div className="p-3 rounded-xl border border-border/80 bg-card/60">
                                        <span className="font-semibold text-foreground flex items-center gap-1.5">
                                            <Mail className="w-3.5 h-3.5 text-primary" /> Multi-Contas Google
                                        </span>
                                        <p className="text-[11px] text-muted-foreground mt-1">
                                            Suporta canais na conta <strong>Money Intel</strong> (ex: Fatos & Debates e Futebol em Cortes) e na conta <strong>Alessandro BM</strong> (<span className="font-mono text-zinc-300">alessandrobm1988@gmail.com</span>).
                                        </p>
                                    </div>
                                    <div className="p-3 rounded-xl border border-border/80 bg-card/60">
                                        <span className="font-semibold text-foreground flex items-center gap-1.5">
                                            <Key className="w-3.5 h-3.5 text-amber-500" /> Token OAuth Isolado
                                        </span>
                                        <p className="text-[11px] text-muted-foreground mt-1">
                                            Cada canal possui seu arquivo <code className="font-mono">token-&#123;slug&#125;.json</code> próprio com <em>refresh token</em> permanente e cota diária independente.
                                        </p>
                                    </div>
                                    <div className="p-3 rounded-xl border border-border/80 bg-card/60">
                                        <span className="font-semibold text-foreground flex items-center gap-1.5">
                                            <Shield className="w-3.5 h-3.5 text-emerald-500" /> Guard Anti-Erro (Bug 18)
                                        </span>
                                        <p className="text-[11px] text-muted-foreground mt-1">
                                            Validação automática pós-consentimento: o sistema recusa salvar tokens que apontem para contas pessoais em vez da Conta de Marca.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Alerta Importante sobre o Canal Placeholder "Podcast Cortes" */}
                            <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-xs">
                                <div className="flex items-center gap-2 font-bold text-blue-400 mb-1">
                                    <Info className="w-4 h-4" />
                                    <span>Esclarecimento: Por que o canal &quot;Podcast Cortes&quot; aparece no painel?</span>
                                </div>
                                <p className="text-muted-foreground leading-relaxed">
                                    O canal <strong>Podcast Cortes</strong> foi criado originalmente pelo arquivo de semente inicial (<code className="font-mono">BaselineSeeder.php</code>) apenas como um <strong>modelo placeholder</strong> de demonstração para o nicho de podcasts (<code className="font-mono">UC_PLACEHOLDER_PODCAST</code>, pausado e com 0 clipes). Ele não possui token OAuth nem canal real no YouTube. Você pode <strong>excluí-lo com 1 clique</strong> no ícone de lixeira em <em>Canais Destino</em> ou substituí-lo configurando o seu novo canal oficial.
                                </p>
                            </div>

                            {/* ETAPA 1 */}
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-xl bg-primary text-primary-foreground font-bold text-xs">
                                        1
                                    </span>
                                    <div>
                                        <h4 className="font-bold text-base text-foreground">
                                            Criar o Canal no YouTube (Recomendado: Conta de Marca)
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            Configuração inicial do canal e ativação de recursos avançados
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 text-xs md:text-[13px] text-muted-foreground leading-relaxed pl-2 md:pl-11">
                                    <ol className="list-decimal pl-4 space-y-2">
                                        <li>
                                            Acesse o <a href="https://www.youtube.com" target="_blank" rel="noreferrer" className="text-primary underline">YouTube</a> logado na conta Google desejada (ex: <code className="font-mono">alessandrobm1988@gmail.com</code>).
                                        </li>
                                        <li>
                                            Clique na sua foto de perfil &gt; <strong>Configurações</strong> &gt; <strong>Adicionar ou gerenciar seus canais</strong> &gt; <strong>Criar um canal</strong>.
                                            <p className="mt-1 text-[11px] text-amber-500/90 font-medium">
                                                💡 Recomendação: Criar como <strong>Conta de Marca</strong> permite múltiplos administradores, nome de canal flexível e isolamento da sua conta pessoal do Google.
                                            </p>
                                        </li>
                                        <li>
                                            Defina o nome do canal (ex: <em>Cortes do Alessandro</em> ou <em>Podcast em Cortes</em>), o identificador único (<code className="font-mono">@handle</code>) e adicione avatar e imagem de capa.
                                        </li>
                                        <li>
                                            <strong>Obter o YouTube Channel ID oficial (UC...):</strong>
                                            <ul className="list-disc pl-4 mt-1 space-y-1 text-xs">
                                                <li>Acesse <a href="https://studio.youtube.com" target="_blank" rel="noreferrer" className="text-primary underline">studio.youtube.com</a> no canal criado.</li>
                                                <li>No menu lateral esquerdo, clique em <strong>Configurações</strong> &gt; <strong>Canal</strong> &gt; <strong>Configurações avançadas</strong>.</li>
                                                <li>Role até o final e clique em <em>Configurações de canal do YouTube</em> (ou acesse diretamente <a href="https://www.youtube.com/account_advanced" target="_blank" rel="noreferrer" className="text-primary underline">youtube.com/account_advanced</a>).</li>
                                                <li>Copie o <strong>ID do canal</strong> (sempre inicia com <code className="font-mono text-foreground font-semibold">UC...</code>, exatamente 24 caracteres). Guarde esse ID.</li>
                                            </ul>
                                        </li>
                                        <li>
                                            <strong>Crucial: Ativar Recursos Intermediários via SMS:</strong>
                                            <ul className="list-disc pl-4 mt-1 space-y-1 text-xs">
                                                <li>Em <code className="font-mono">studio.youtube.com</code> &gt; <strong>Configurações</strong> &gt; <strong>Canal</strong> &gt; <strong>Qualificação para recursos</strong>.</li>
                                                <li>Ative os <strong>Recursos intermediários</strong> confirmando seu número de telefone celular por código SMS.</li>
                                                <li className="text-amber-500">
                                                    ⚠️ <strong>Por que isso é obrigatório:</strong> Canais sem verificação de telefone são bloqueados pela API do YouTube com <em>Erro 403 Forbidden</em> ao tentar aplicar capas (thumbnails personalizadas) e têm todos os uploads forçados para o modo Privado.
                                                </li>
                                            </ul>
                                        </li>
                                    </ol>
                                </div>
                            </div>

                            {/* ETAPA 2 */}
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-xl bg-primary text-primary-foreground font-bold text-xs">
                                        2
                                    </span>
                                    <div>
                                        <h4 className="font-bold text-base text-foreground">
                                            Configurar o Google Cloud Console & YouTube Data API
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            Habilitar as APIs do YouTube e configurar a tela de consentimento OAuth
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 text-xs md:text-[13px] text-muted-foreground leading-relaxed pl-2 md:pl-11">
                                    <ol className="list-decimal pl-4 space-y-2">
                                        <li>
                                            Acesse o <a href="https://console.cloud.google.com" target="_blank" rel="noreferrer" className="text-primary underline">Google Cloud Console</a> na conta Google do canal.
                                        </li>
                                        <li>
                                            Selecione um projeto existente (ex: <code className="font-mono">canal-de-cortes-499720</code>) ou clique em <strong>Novo Projeto</strong> (ex: <code className="font-mono">canaldecortes-alessandro</code>).
                                        </li>
                                        <li>
                                            Acesse <strong>APIs e Serviços &gt; Biblioteca</strong> e ative as duas APIs essenciais:
                                            <ul className="list-disc pl-4 mt-1 space-y-1">
                                                <li><strong className="text-foreground">YouTube Data API v3</strong> — necessária para o envio automático de vídeos, tags, títulos e miniaturas.</li>
                                                <li><strong className="text-foreground">YouTube Analytics API</strong> — necessária para coleta diária de métricas de retenção e visualização por clipe (SPEC-001).</li>
                                            </ul>
                                        </li>
                                        <li>
                                            Acesse <strong>APIs e Serviços &gt; Tela de consentimento OAuth</strong> (OAuth consent screen):
                                            <ul className="list-disc pl-4 mt-1 space-y-1">
                                                <li>Escolha <strong>Externo (External)</strong> e clique em <em>Criar</em>.</li>
                                                <li>Preencha o <em>Nome do app</em> (ex: <code>Canal de Cortes AutoUploader</code>), o e-mail de suporte e o e-mail do desenvolvedor.</li>
                                                <li>Na tela de <strong>Escopos (Scopes)</strong>, adicione os 3 escopos obrigatórios:
                                                    <div className="p-2.5 my-1.5 rounded-lg border border-border/80 bg-zinc-950 font-mono text-[11px] text-zinc-300 space-y-1">
                                                        <div>https://www.googleapis.com/auth/youtube.upload</div>
                                                        <div>https://www.googleapis.com/auth/youtube.force-ssl</div>
                                                        <div>https://www.googleapis.com/auth/yt-analytics.readonly</div>
                                                    </div>
                                                    <span className="text-[11px] text-amber-500">
                                                        * O escopo <code>youtube.force-ssl</code> é fundamental para permitir que o script valide a identidade do canal antes de subir qualquer vídeo.
                                                    </span>
                                                </li>
                                                <li>Em <strong>Usuários de Teste (Test users)</strong>: adicione o seu e-mail Google (ex: <code className="font-mono">alessandrobm1988@gmail.com</code>).</li>
                                                <li>
                                                    <em>Dica Pro:</em> Para evitar que o token expire a cada 7 dias no modo &quot;Testing&quot;, você pode clicar no botão <strong>Publicar App (Publish App)</strong> na tela de consentimento. Como o app é de uso pessoal, não há custo nem burocracia.
                                                </li>
                                            </ul>
                                        </li>
                                    </ol>
                                </div>
                            </div>

                            {/* ETAPA 3 */}
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-xl bg-primary text-primary-foreground font-bold text-xs">
                                        3
                                    </span>
                                    <div>
                                        <h4 className="font-bold text-base text-foreground">
                                            Criar Credenciais OAuth (Desktop App) e Baixar client_secret.json
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            Gerar o par de chaves de autenticação do Google Cloud
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 text-xs md:text-[13px] text-muted-foreground leading-relaxed pl-2 md:pl-11">
                                    <ol className="list-decimal pl-4 space-y-2">
                                        <li>
                                            No Google Cloud Console, acesse <strong>APIs e Serviços &gt; Credenciais</strong>.
                                        </li>
                                        <li>
                                            Clique em <strong>+ Criar Credenciais &gt; ID do cliente OAuth</strong>.
                                        </li>
                                        <li>
                                            No campo <em>Tipo de aplicativo</em>, selecione obrigatoriamente: <strong>App para computador (Desktop application)</strong>.
                                        </li>
                                        <li>
                                            Dê um nome (ex: <code>Canal de Cortes Local Client</code>) e clique em <em>Criar</em>.
                                        </li>
                                        <li>
                                            Clique no botão de <strong>Download do JSON</strong> (ou ícone de seta para baixo).
                                        </li>
                                        <li>
                                            Renomeie o arquivo baixado para <code className="font-mono text-foreground font-bold">client_secret.json</code> e salve no diretório <code className="font-mono">youtube/</code> da raiz do projeto:
                                        </li>
                                    </ol>
                                    <CodeBlock
                                        title="Localização do arquivo client_secret.json"
                                        code="mv ~/Downloads/client_secret_*.json /Users/alessandrobm1/develop/server/wordpress/canaldecortes/youtube/client_secret.json"
                                    />
                                </div>
                            </div>

                            {/* ETAPA 4 */}
                            <div className="rounded-2xl border border-amber-500/30 bg-card p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-xl bg-amber-500 text-amber-950 font-bold text-xs">
                                        4
                                    </span>
                                    <div>
                                        <h4 className="font-bold text-base text-foreground flex items-center gap-2">
                                            Gerar o Token OAuth com Guard de Identidade
                                            <Badge variant="outline" className="border-amber-500/40 text-amber-400 text-[10px]">Prevenção do Bug 18</Badge>
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            Geração do token com verificação automática do canal
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 text-xs md:text-[13px] text-muted-foreground leading-relaxed pl-2 md:pl-11">
                                    <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 my-2">
                                        <div className="flex items-center gap-2 font-bold text-red-400 text-xs mb-1">
                                            <AlertTriangle className="w-4 h-4 shrink-0" />
                                            <span>ALERTA CRÍTICO: Escolha da Conta no Navegador (Lição do Bug 18)</span>
                                        </div>
                                        <p className="text-[12px] leading-relaxed text-red-200/90">
                                            Quando a janela do navegador abrir para você autorizar o login no Google, <strong>escolha a CONTA DE MARCA do canal</strong>, e NUNCA a sua conta pessoal! Em outubro de 2026, foi escolhida a conta pessoal &quot;Alessandro Melo&quot; e 4 dias de cortes foram postados privados no canal pessoal em vez do canal de futebol. O script agora confere automaticamente e aborta se o canal retornado não bater com o esperado.
                                        </p>
                                    </div>

                                    <p>
                                        Execute o comando na raiz do projeto informando o slug desejado e o Channel ID esperado:
                                    </p>

                                    <CodeBlock
                                        title="Comando para gerar o token do novo canal"
                                        code="cd /Users/alessandrobm1/develop/server/wordpress/canaldecortes
.venv/bin/python youtube/generate_token_channel.py --channel novo-canal-slug --expect-channel-id UCxxxxxxxxxxxxxxxxxxxx"
                                    />

                                    <p>
                                        Ou adicione o mapeamento em <code className="font-mono">youtube/generate_token_channel.py</code> e use o atalho do Makefile:
                                    </p>

                                    <CodeBlock
                                        title="Atalho via Makefile"
                                        code="make token-youtube CANAL=novo-canal-slug"
                                    />

                                    <p>
                                        O script salvará o arquivo de credenciais permanente em:
                                        <br />
                                        <code className="font-mono text-emerald-400 font-semibold">youtube/token-&#123;slug&#125;.json</code>.
                                    </p>
                                </div>
                            </div>

                            {/* ETAPA 5 */}
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-xl bg-primary text-primary-foreground font-bold text-xs">
                                        5
                                    </span>
                                    <div>
                                        <h4 className="font-bold text-base text-foreground">
                                            Cadastrar o Canal na Tela &quot;Canais Destino&quot; do Painel
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            Registrar metadados, e-mail vinculado, formato e template visual 9:16
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 text-xs md:text-[13px] text-muted-foreground leading-relaxed pl-2 md:pl-11">
                                    <ol className="list-decimal pl-4 space-y-2">
                                        <li>
                                            Acesse o menu <strong>Canais Destino</strong> no painel e clique no botão <span className="font-semibold text-primary">+ Novo Canal Destino</span>.
                                        </li>
                                        <li>
                                            Preencha os campos com atenção:
                                            <ul className="list-disc pl-4 mt-1 space-y-1 text-xs">
                                                <li><strong>Nome do Canal:</strong> Nome público do canal (ex: <em>Cortes do Alessandro</em>).</li>
                                                <li><strong>Slug (identificador único):</strong> Deve ser <strong>exatamente o mesmo slug</strong> usado no arquivo do token (ex: se o arquivo for <code>token-alessandro-cortes.json</code>, o slug é <code>alessandro-cortes</code>).</li>
                                                <li><strong>Nicho:</strong> Selecione <em>Futebol</em>, <em>Política</em> ou <em>Podcast</em> (o nicho determina quais vídeos brutos de <em>Canais Fonte</em> alimentarão este canal).</li>
                                                <li><strong>YouTube Channel ID:</strong> O ID oficial <code className="font-mono">UC...</code> obtido no passo 1.</li>
                                                <li><strong className="text-foreground">Conta Google / E-mail do Canal:</strong> O e-mail da conta Google dona do canal (ex: <code className="font-mono">alessandrobm1988@gmail.com</code> ou a conta Money Intel correspondente). Esse campo permite saber com clareza em qual conta os acessos estão vinculados.</li>
                                                <li><strong>Formato dos Vídeos:</strong> <em>Automático</em>, <em>Só Shorts</em> (corta apenas trechos verticais 9:16) ou <em>Shorts + vídeo longo</em>.</li>
                                                <li><strong>Privacidade padrão no YouTube:</strong> <em>Privado</em> (sobe como privado para conferência manual) ou <em>Público</em> (vai ao ar diretamente após a aprovação).</li>
                                            </ul>
                                        </li>
                                        <li>
                                            Clique em <strong>Criar Canal</strong>. Assim que salvo, o card exibirá o badge verde <Badge variant="outline" className="text-emerald-500 border-emerald-500/20">OAuth autorizado</Badge> se o arquivo de token estiver presente na pasta <code className="font-mono">youtube/</code>.
                                        </li>
                                        <li>
                                            <strong>Estúdio de Template 9:16 & Marca d&apos;água:</strong>
                                            <p className="mt-1">
                                                No card do canal criado, clique em <strong>✨ Template 9:16</strong> para ajustar:
                                            </p>
                                            <ul className="list-disc pl-4 mt-1 space-y-1 text-xs">
                                                <li>Manchete superior e cor de destaque (Accent Color).</li>
                                                <li>Estilo de fundo (fundo desfocado dinâmico ou cores sólidas).</li>
                                                <li>Cor e tamanho das legendas automáticas animadas.</li>
                                                <li>Texto de chamada para inscrição (CTA).</li>
                                                <li>Upload da <strong>Marca d&apos;água (Watermark PNG transparente)</strong> que será queimada no vídeo pelo FFmpeg.</li>
                                            </ul>
                                        </li>
                                    </ol>
                                </div>
                            </div>

                            {/* ETAPA 6 */}
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-xl bg-primary text-primary-foreground font-bold text-xs">
                                        6
                                    </span>
                                    <div>
                                        <h4 className="font-bold text-base text-foreground">
                                            Vincular Canais Fonte (Abastecimento Automático de Vídeos)
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            Como o pipeline sabe de onde baixar os vídeos para alimentar este canal
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 text-xs md:text-[13px] text-muted-foreground leading-relaxed pl-2 md:pl-11">
                                    <p>
                                        O roteamento de vídeos brutos para os canais de destino é feito <strong>por nicho</strong> (<code className="font-mono">source_channels.target_niche = destination_channels.niche</code>).
                                    </p>
                                    <ol className="list-decimal pl-4 space-y-1.5">
                                        <li>Acesse a tela <strong>Canais Fonte</strong> no menu lateral.</li>
                                        <li>Clique em <strong>+ Novo Canal Fonte</strong>.</li>
                                        <li>Insira o <code className="font-mono">@handle</code> do canal de referência (ex: <code className="font-mono">@flowpodcast</code>, <code className="font-mono">@geglobo</code>, <code className="font-mono">@mblivre</code>) ou a URL completa do canal no YouTube.</li>
                                        <li>Selecione o <strong>mesmo nicho</strong> do seu canal de destino.</li>
                                        <li>Garanta que o switch <em>Ativo</em> esteja ligado. A partir deste momento, qualquer vídeo novo postado por esse canal fonte será detectado pelo RSS poller a cada 20 minutos e entrará na esteira de corte para o seu canal!</li>
                                    </ol>
                                </div>
                            </div>

                            {/* ETAPA 7 */}
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-xl bg-primary text-primary-foreground font-bold text-xs">
                                        7
                                    </span>
                                    <div>
                                        <h4 className="font-bold text-base text-foreground">
                                            Sincronizar o Token em Produção (VPS Oracle Cloud)
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            Copiar o arquivo de token para o servidor oficial que roda o daemon 24/7
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 text-xs md:text-[13px] text-muted-foreground leading-relaxed pl-2 md:pl-11">
                                    <p>
                                        Para que o robô em produção na nuvem consiga publicar os vídeos no novo canal, envie o arquivo de token gerado via SCP:
                                    </p>
                                    <CodeBlock
                                        title="Copiar token para a VPS Oracle de produção"
                                        code="scp -i ~/.ssh/oracle-a1-2026-09-16.key youtube/token-novo-canal-slug.json ubuntu@129.80.236.185:/home/ubuntu/canaldecortes/youtube/"
                                    />
                                    <p>
                                        Para reiniciar o container e garantir que as credenciais foram lidas imediatamente:
                                    </p>
                                    <CodeBlock
                                        title="Reiniciar o clip-processor em produção"
                                        code="ssh -i ~/.ssh/oracle-a1-2026-09-16.key ubuntu@129.80.236.185 'cd /home/ubuntu/canaldecortes && docker compose restart clip-processor'"
                                    />
                                </div>
                            </div>

                            {/* ETAPA 8 */}
                            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center justify-center w-8 h-8 rounded-xl bg-emerald-500 text-emerald-950 font-bold text-xs">
                                        8
                                    </span>
                                    <div>
                                        <h4 className="font-bold text-base text-foreground">
                                            Fila de Aprovação, Cotas Diárias & Publicação Automática
                                        </h4>
                                        <p className="text-xs text-muted-foreground">
                                            Como o sistema publica e respeita as cotas do YouTube
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 text-xs md:text-[13px] text-muted-foreground leading-relaxed pl-2 md:pl-11">
                                    <ul className="list-disc pl-4 space-y-2">
                                        <li>
                                            <strong>Fila de Aprovação (Dashboard):</strong> Todos os clipes cortados, legendados e com thumbnail gerada aparecem na tela principal. Você pode dar play, assistir ao vídeo em 9:16, editar o título gerado pela IA ou aprovar com 1 clique.
                                        </li>
                                        <li>
                                            <strong>Janelas Nobres de Publicação:</strong> O publicador automático (<code className="font-mono">publisher.py</code>) opera com janela horária estratégica para o Brasil:
                                            <div className="flex items-center gap-2 my-1">
                                                <Badge variant="secondary" className="font-mono">12h às 14h (Almoço)</Badge>
                                                <span className="text-muted-foreground">&</span>
                                                <Badge variant="secondary" className="font-mono">19h às 22h (Horário Nobre Noturno)</Badge>
                                            </div>
                                        </li>
                                        <li>
                                            <strong>Cotas Diárias e Anti-Flood:</strong> Cada canal destino possui sua própria cota gerenciada no Redis (padrão de segurança de 2 a 10 uploads/dia para não esgotar as 10.000 unidades da API do YouTube).
                                        </li>
                                        <li>
                                            <strong>Revezamento por Canal Fonte:</strong> O sistema alterna entre os canais de origem para garantir que nenhum canal monopolize a esteira de postagem do dia.
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ========================================================================= */}
                    {/* ABA 2: PIPELINE & FLUXO AUTÔNOMO                                         */}
                    {/* ========================================================================= */}
                    {activeTab === 'pipeline' && (
                        <div className="space-y-6">
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <div className="flex items-center gap-2.5 font-bold text-base text-foreground">
                                    <Layers className="w-5 h-5 text-primary" />
                                    <span>Arquitetura da Esteira (Daemon Python + Scheduler APScheduler)</span>
                                </div>
                                <p className="text-xs md:text-sm text-muted-foreground leading-relaxed">
                                    O motor do projeto roda no container <code className="font-mono">clip-processor</code>, executado pelo agendador em <code className="font-mono">clip-processor/src/main.py</code> no fuso de São Paulo (<code className="font-mono">America/Sao_Paulo</code>). A esteira é dividida em dois ciclos independentes:
                                </p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                                    <div className="p-4 rounded-xl border border-border/80 bg-muted/30 space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="font-bold text-xs text-foreground flex items-center gap-1.5">
                                                <RefreshCw className="w-4 h-4 text-primary" /> 1. Ciclo de Ingestão (ingest_cycle)
                                            </span>
                                            <Badge variant="secondary" className="font-mono text-[10px]">A cada 20 min</Badge>
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Executa <strong>RSS Polling</strong> em todos os canais fonte ativos &gt; Encontra vagas na janela de download (máx 16 vídeos no total) &gt; Baixa o vídeo com <code className="font-mono">yt-dlp</code> &gt; Extrai áudio &gt; Transcreve pelo Groq Cloud LLaMA/Whisper &gt; IA (LLaMA 3.3) seleciona os melhores momentos virais &gt; FFmpeg renderiza os clipes verticais 9:16 com legendas e marca d&apos;água.
                                        </p>
                                    </div>

                                    <div className="p-4 rounded-xl border border-border/80 bg-muted/30 space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="font-bold text-xs text-foreground flex items-center gap-1.5">
                                                <Send className="w-4 h-4 text-emerald-500" /> 2. Ciclo de Publicação (publish_cycle)
                                            </span>
                                            <Badge variant="secondary" className="font-mono text-[10px]">A cada 20 min</Badge>
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Verifica se a hora atual está dentro das janelas de postagem (12h-14h ou 19h-22h) &gt; Confere cota diária do canal no Redis &gt; Valida o token OAuth com o guard de segurança do canal destino &gt; Realiza upload resumível do clipe para o YouTube &gt; Seta a miniatura (thumbnail) &gt; Registra a métrica no banco de dados.
                                        </p>
                                    </div>
                                </div>

                                <div className="rounded-xl border border-border bg-card p-4 space-y-2 text-xs">
                                    <h5 className="font-bold text-foreground">Regras Fundamentais de Operação do Pipeline:</h5>
                                    <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                                        <li><strong>Janela de Download Concorrente:</strong> Limitada em 16 vídeos ativos simultâneos no disco para evitar esgotamento de SSD (10 para o nicho de Futebol + 6 para o nicho de Política).</li>
                                        <li><strong>Round-Robin por Canal Fonte:</strong> Vídeos são intercalados para que canais com muitos vídeos não furem a fila nem monopolizem os uploads.</li>
                                        <li><strong>Reserva de Vagas para Vídeo Longo:</strong> Quando um vídeo longo está pronto na fila, o sistema reserva slots diários para ele antes de consumir todas as vagas com Shorts.</li>
                                        <li><strong>Fallbacks Automáticos:</strong> Se a API do Groq estiver temporariamente indisponível, o sistema recorre ao motor Whisper local C++ para não paralisar o pipeline.</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ========================================================================= */}
                    {/* ABA 3: MANUAL DAS TELAS DO PAINEL                                        */}
                    {/* ========================================================================= */}
                    {activeTab === 'telas' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="rounded-2xl border border-border bg-card p-5 space-y-2">
                                <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                                    📊 Dashboard & Fila de Publicação
                                </h4>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Centro de comando diário. Exibe os contadores de uploads do dia vs limite da API, a fila de aprovação humana com player integrado 9:16 para preview, e a lista de vídeos aprovados agendados para a próxima janela de postagem.
                                </p>
                            </div>

                            <div className="rounded-2xl border border-border bg-card p-5 space-y-2">
                                <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                                    📺 Canais Destino & Estúdio de Templates
                                </h4>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Gerenciamento dos canais do YouTube que recebem as publicações. Permite configurar o Channel ID (<code className="font-mono">UC...</code>), o e-mail Google vinculado, status da autorização OAuth, cotas diárias, e personalizar o estúdio 9:16 (cores, legendas, CTA e marca d&apos;água).
                                </p>
                            </div>

                            <div className="rounded-2xl border border-border bg-card p-5 space-y-2">
                                <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                                    📡 Canais Fonte & Benchmark de Concorrentes
                                </h4>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Canais do YouTube monitorados pelo robô via RSS para captura de vídeos brutos. Inclui o botão <strong>🧠 Analisar IA</strong> para dissecar concorrentes (ganchos, frequência e títulos virais com LLaMA 3.3).
                                </p>
                            </div>

                            <div className="rounded-2xl border border-border bg-card p-5 space-y-2">
                                <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                                    🎬 Vídeos & Gerenciamento de Disco
                                </h4>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Visão do armazenamento SSD da máquina, vídeos brutos baixados e status de processamento. O filtro <em>&quot;Seguro Apagar&quot;</em> lista vídeos que já geraram cortes com segurança, permitindo liberar espaço sem risco de perder arquivos pendentes.
                                </p>
                            </div>

                            <div className="rounded-2xl border border-border bg-card p-5 space-y-2">
                                <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                                    ⚡ Processar Vídeo Manual
                                </h4>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Permite colar qualquer URL do YouTube avulsa e escolher o formato de corte (Shorts 9:16 ou Longo 16:9), enviando o vídeo imediatamente para a fila de corte prioritária sem esperar o ciclo do RSS.
                                </p>
                            </div>

                            <div className="rounded-2xl border border-border bg-card p-5 space-y-2">
                                <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                                    🎙️ Transcrições & Base de Conhecimento
                                </h4>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Transcreve qualquer vídeo ou áudio colado (YouTube, TikTok, Instagram, Vimeo). O texto completo fica indexado no PostgreSQL com busca vetorial e opções de download em formatos <code className="font-mono">.md</code>, <code className="font-mono">.txt</code> ou legendas <code className="font-mono">.srt</code>.
                                </p>
                            </div>

                            <div className="rounded-2xl border border-border bg-card p-5 space-y-2 md:col-span-2">
                                <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                                    🔗 Links Úteis, Calculadora de Ganhos & AdSense
                                </h4>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Hub central com calculadora de receita integrada baseada no RPM do Brasil (Shorts vs Vídeos Longos), simulando faturamento mensal em Dólar e Reais, além de atalhos diretos para YouTube Studio, Google Cloud Console e Google AdSense.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* ========================================================================= */}
                    {/* ABA 4: ESTRATÉGIA DE CONTEÚDO & IA                                       */}
                    {/* ========================================================================= */}
                    {activeTab === 'estrategia' && (
                        <div className="space-y-6">
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <h4 className="font-bold text-base text-foreground flex items-center gap-2">
                                    <Bot className="w-5 h-5 text-purple-400" />
                                    As 4 Métricas Essenciais do YouTube Studio para Passar para a IA
                                </h4>
                                <p className="text-xs md:text-sm text-muted-foreground leading-relaxed">
                                    Na ferramenta de <strong>Diagnóstico YouTube Studio</strong> (dentro do menu <em>Assistente IA</em>), o modelo LLaMA 3.3 70B correlaciona estas 4 métricas oficiais para apontar o gargalo exato do canal:
                                </p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-2">
                                    <div className="p-3.5 rounded-xl border border-border bg-muted/40 space-y-1">
                                        <div className="font-bold text-foreground text-xs">1. Taxa de Cliques (CTR %)</div>
                                        <div className="text-[11px] text-muted-foreground">Mede a atratividade da Capa (Thumbnail) e do Título.</div>
                                        <div className="text-[11px] font-mono text-emerald-500 font-semibold">Ideal: 5% a 10%+ (Abaixo de 4% o YouTube freia as impressões)</div>
                                    </div>

                                    <div className="p-3.5 rounded-xl border border-border bg-muted/40 space-y-1">
                                        <div className="font-bold text-foreground text-xs">2. % de Retenção / Duração Média</div>
                                        <div className="text-[11px] text-muted-foreground">Quanto tempo o público assiste antes de sair do vídeo.</div>
                                        <div className="text-[11px] font-mono text-emerald-500 font-semibold">Longos: 40% a 55%+ | Shorts: 75% a 90%+</div>
                                    </div>

                                    <div className="p-3.5 rounded-xl border border-border bg-muted/40 space-y-1">
                                        <div className="font-bold text-foreground text-xs">3. Assistiram vs. Pularam (Swiped Away)</div>
                                        <div className="text-[11px] text-muted-foreground">Exclusivo de Shorts. % de pessoas que não passaram reto nos primeiros 3s.</div>
                                        <div className="text-[11px] font-mono text-emerald-500 font-semibold">Ideal: Mínimo de 70% a 85% escolhendo assistir</div>
                                    </div>

                                    <div className="p-3.5 rounded-xl border border-border bg-muted/40 space-y-1">
                                        <div className="font-bold text-foreground text-xs">4. Velocidade nas Primeiras 24h-48h</div>
                                        <div className="text-[11px] text-muted-foreground">Tração inicial por inscritos e consumo imediato.</div>
                                        <div className="text-[11px] font-mono text-emerald-500 font-semibold">Define se o vídeo entra na esteira de recomendação externa</div>
                                    </div>
                                </div>
                            </div>

                            {/* Fórmula de Política MBL / Missão */}
                            <div className="rounded-2xl border border-purple-500/20 bg-purple-500/5 p-5 md:p-6 space-y-4">
                                <h4 className="font-bold text-base text-foreground flex items-center gap-2">
                                    <Landmark className="w-5 h-5 text-purple-400" />
                                    Fórmula dos Cortes Virais de Política (MBL, Missão e Debates)
                                </h4>
                                <p className="text-xs md:text-sm text-muted-foreground leading-relaxed">
                                    O motor de seleção da IA em <code className="font-mono">selector.py</code> foi calibrado com base nos canais de maior engajamento político do Brasil:
                                </p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                                    <div className="p-3 rounded-xl border border-purple-500/20 bg-card/60 space-y-1">
                                        <strong className="text-purple-300">1. Gancho Inicial Agressivo (0 a 5s):</strong>
                                        <p className="text-muted-foreground text-[11.5px]">
                                            O clipe não possui saudações, introduções ou enrolação. Começa diretamente na pergunta ácida, na revelação chocante ou no início de uma resposta contundente.
                                        </p>
                                    </div>
                                    <div className="p-3 rounded-xl border border-purple-500/20 bg-card/60 space-y-1">
                                        <strong className="text-purple-300">2. Conflito & Refutação (&quot;Jantada&quot;):</strong>
                                        <p className="text-muted-foreground text-[11.5px]">
                                            A IA rastreia momentos em que narrativas são expostas, hipocrisias são mostradas ou argumentos são quebrados com dados e firmeza.
                                        </p>
                                    </div>
                                    <div className="p-3 rounded-xl border border-purple-500/20 bg-card/60 space-y-1">
                                        <strong className="text-purple-300">3. Raciocínio Fechado & Término no Ápice:</strong>
                                        <p className="text-muted-foreground text-[11.5px]">
                                            O clipe fecha no clímax do golpe argumentativo. Sem sobras pós-desfecho, o que maximiza o replay e incentiva discussões nos comentários.
                                        </p>
                                    </div>
                                    <div className="p-3 rounded-xl border border-purple-500/20 bg-card/60 space-y-1">
                                        <strong className="text-purple-300">4. Formato Visual 9:16 Otimizado:</strong>
                                        <p className="text-muted-foreground text-[11.5px]">
                                            Enquadramento vertical com fundo desfocado em tempo real, legendas dinâmicas de alto contraste e manchete chamativa no topo.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ========================================================================= */}
                    {/* ABA 5: OBSERVABILIDADE & MONITORAMENTO (WATCHDOG)                         */}
                    {/* ========================================================================= */}
                    {activeTab === 'monitoramento' && (
                        <div className="space-y-6">
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <h4 className="font-bold text-base text-foreground flex items-center gap-2">
                                    <Shield className="w-5 h-5 text-emerald-500" />
                                    Infraestrutura de Observabilidade em 3 Camadas
                                </h4>
                                <p className="text-xs md:text-sm text-muted-foreground leading-relaxed">
                                    Para garantir 100% de confiabilidade e impedir interrupções silenciosas nas postagens diárias, o sistema conta com observabilidade proativa em 3 camadas complementares:
                                </p>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 my-2">
                                    <div className="p-3.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 space-y-1.5">
                                        <div className="font-bold text-emerald-400 text-xs">Camada 1: Better Stack</div>
                                        <p className="text-[11px] text-muted-foreground">
                                            Monitoramento externo de uptime HTTPS 24/7, heartbeats dos cronjobs/daemons e checagem de expiração de certificados SSL.
                                        </p>
                                    </div>

                                    <div className="p-3.5 rounded-xl border border-red-500/20 bg-red-500/5 space-y-1.5">
                                        <div className="font-bold text-red-400 text-xs">Camada 2: Sentry</div>
                                        <p className="text-[11px] text-muted-foreground">
                                            Rastreamento de exceções no PHP/Laravel e falhas imprevistas em chamadas às APIs do YouTube e Groq, alertando o operador instantaneamente.
                                        </p>
                                    </div>

                                    <div className="p-3.5 rounded-xl border border-amber-500/20 bg-amber-500/5 space-y-1.5">
                                        <div className="font-bold text-amber-400 text-xs">Camada 3: Watchdog Proativo</div>
                                        <p className="text-[11px] text-muted-foreground">
                                            Monitor interno executado a cada 30 min. Detecta deadlocks de regras de negócio silenciosos e executa rotinas de auto-cura automáticas.
                                        </p>
                                    </div>
                                </div>

                                <div className="my-3 overflow-hidden rounded-xl border border-border/80 bg-zinc-950/70 p-3 shadow-md flex flex-col items-center justify-center">
                                    <img
                                        src="/images/arquitetura_monitoramento_watchdog.jpg"
                                        alt="Arquitetura de Monitoramento Proativo, Better Stack, Sentry e Watchdog"
                                        className="w-full max-w-4xl max-h-[440px] object-contain rounded-lg shadow-inner"
                                        loading="lazy"
                                    />
                                    <p className="mt-2 text-center text-[11px] text-muted-foreground/80">
                                        Diagrama da infraestrutura de observabilidade proativa (Better Stack + Sentry + Watchdog + Hub Laravel)
                                    </p>
                                </div>

                                <div className="space-y-2 text-xs text-muted-foreground">
                                    <h5 className="font-bold text-foreground">Rotinas Automáticas do Watchdog Proativo:</h5>
                                    <ul className="list-disc pl-4 space-y-1">
                                        <li><strong>Auto-Cura de Clipes Fantasmas:</strong> Identifica clipes aprovados sem arquivo físico no SSD, marcando-os como falhos e destravando as vagas da janela de download.</li>
                                        <li><strong>Deadlock da Janela de Download:</strong> Alerta se todas as 16 vagas estiverem ocupadas por mais de 2 horas sem nenhum progresso.</li>
                                        <li><strong>Fila de Aprovação Vazia:</strong> Notifica no Telegram se nenhum clipe novo for gerado durante o dia (08h às 23h).</li>
                                        <li><strong>Validação Prévia de Tokens OAuth:</strong> Testa as credenciais dos canais ativos antes das janelas de postagem para evitar uploads falhos.</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ========================================================================= */}
                    {/* ABA 6: COMANDOS & RUNBOOK                                                */}
                    {/* ========================================================================= */}
                    {activeTab === 'comandos' && (
                        <div className="space-y-6">
                            <div className="rounded-2xl border border-border bg-card p-5 md:p-6 space-y-4">
                                <h4 className="font-bold text-base text-foreground flex items-center gap-2">
                                    <Terminal className="w-5 h-5 text-primary" />
                                    Comandos Operacionais & Atalhos Rápidos
                                </h4>
                                <p className="text-xs md:text-sm text-muted-foreground leading-relaxed">
                                    Guia rápido de comandos executados no host ou no servidor de produção:
                                </p>

                                <div className="space-y-4">
                                    <div>
                                        <div className="font-semibold text-xs text-foreground mb-1">
                                            1. Gerar Token OAuth do YouTube para Canal Destino
                                        </div>
                                        <CodeBlock
                                            title="Geração de token no host local"
                                            code="make token-youtube CANAL=futebol-em-cortes
# Ou especificando o ID esperado para validação rigorosa:
.venv/bin/python youtube/generate_token_channel.py --channel futebol-em-cortes --expect-channel-id UCcyeBQFAkUNeDJbBM7JJqLw"
                                        />
                                    </div>

                                    <div>
                                        <div className="font-semibold text-xs text-foreground mb-1">
                                            2. Verificar Saúde e Logs dos Containers Docker
                                        </div>
                                        <CodeBlock
                                            title="Checar status dos serviços"
                                            code="docker compose ps clip-processor postgres redis php nginx
docker compose logs --tail=100 -f clip-processor"
                                        />
                                    </div>

                                    <div>
                                        <div className="font-semibold text-xs text-foreground mb-1">
                                            3. Reiniciar o Processador de Clipes com Segurança
                                        </div>
                                        <p className="text-[11px] text-muted-foreground mb-1">
                                            Antes de reiniciar, verifique se não há uploads em trânsito (<code className="font-mono">publishing</code>):
                                        </p>
                                        <CodeBlock
                                            title="Verificar trânsito e reiniciar"
                                            code="docker exec postgres psql -U clips_user -d clips_automation -c &quot;SELECT status, COUNT(*) FROM generated_clips WHERE status IN ('cutting','publishing') GROUP BY status;&quot;
# Se zero, reiniciar à vontade:
docker compose restart clip-processor"
                                        />
                                    </div>

                                    <div>
                                        <div className="font-semibold text-xs text-foreground mb-1">
                                            4. Rodar Migrações do Banco de Dados no Painel
                                        </div>
                                        <CodeBlock
                                            title="Executar migrations pendentes"
                                            code="docker exec php bash -c &quot;cd /var/www/html/painel && php artisan migrate&quot;"
                                        />
                                    </div>

                                    <div>
                                        <div className="font-semibold text-xs text-foreground mb-1">
                                            5. Rodar Testes Automatizados e Linters
                                        </div>
                                        <CodeBlock
                                            title="Suíte de testes locais"
                                            code="make test-python   # Pytest no clip-processor
make lint-python   # Ruff linter
cd painel && npm run build  # Compilar assets do painel"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </AppShell>
        </>
    );
}
