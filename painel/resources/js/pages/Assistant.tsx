import * as React from 'react';
import { Head, usePage } from '@inertiajs/react';
import {
    BotIcon,
    SendIcon,
    SparklesIcon,
    Trash2Icon,
    CopyIcon,
    CheckIcon,
    RefreshCwIcon,
    ZapIcon,
    TrendingUpIcon,
    ClockIcon,
    DollarSignIcon,
    HelpCircleIcon,
    BarChart3Icon,
    FileTextIcon,
    SlidersHorizontalIcon,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { AppShell } from '@/layouts/app-shell';

type PageProps = {
    auth: { user: { name: string; email: string } | null };
    stats: {
        total_source_channels: number;
        total_dest_channels: number;
        total_source_videos: number;
        total_published_clips: number;
        total_pending_clips: number;
        total_approved_clips: number;
        channels: Array<{ title: string; niche: string; active: boolean; slug: string }>;
    };
    groqModel: string;
};

type Message = {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
};

const SUGGESTIONS = [
    {
        icon: ZapIcon,
        title: 'Fórmula MBL & Missão',
        prompt: 'Como funciona a fórmula dos canais de cortes virais de política (ex: MBL, Missão, Kim Kataguiri)? Me explique a estrutura exata do gancho inicial, legendas e fechamento para replicar no meu canal.',
        tag: 'Política Viral',
    },
    {
        icon: BarChart3Icon,
        title: 'Diagnóstico de Métricas',
        prompt: 'Tenho um vídeo de corte com 1.200 views, 55% de retenção e 4.2% de CTR, mas parou de ser entregue. O que o algoritmo do YouTube está interpretando e o que devo ajustar no próximo?',
        tag: 'YouTube Studio',
    },
    {
        icon: DollarSignIcon,
        title: 'Estimativa de Ganhos',
        prompt: 'Qual a estimativa de faturamento para 200.000 visualizações no YouTube em vídeos longos vs Shorts no Brasil?',
        tag: 'Monetização',
    },
    {
        icon: ClockIcon,
        title: 'Melhores Horários',
        prompt: 'Quais os melhores horários e frequência diária para postar cortes de futebol e política no YouTube Brasil?',
        tag: 'Algoritmo',
    },
];

export default function Assistant({ stats, groqModel }: PageProps) {
    const { props } = usePage<PageProps>();
    const [messages, setMessages] = React.useState<Message[]>(() => {
        const initialGreeting = `Olá! Sou seu assistente de inteligência e estratégia de conteúdo com **LLaMA 3.3 70B** (via Groq). 

Estou conectado ao contexto do seu painel:
- **${stats.total_dest_channels}** canal(is) de destino no YouTube
- **${stats.total_source_channels}** canais fontes monitorados
- **${stats.total_published_clips}** clipes já publicados

Como posso te ajudar hoje? Você pode me passar suas métricas do **YouTube Studio** (CTR, Retenção, Views) para diagnóstico, pedir análises de canais concorrentes (ex: MBL, Missão, Futebol) ou tirar dúvidas sobre monetização!`;

        return [
            {
                id: 'init-1',
                role: 'assistant',
                content: initialGreeting,
                timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
            },
        ];
    });

    const [input, setInput] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const [copiedId, setCopiedId] = React.useState<string | null>(null);
    const [diagOpen, setDiagOpen] = React.useState(false);

    // Estado do Diagnóstico do YouTube Studio
    const [diagForm, setDiagForm] = React.useState({
        videoType: 'shorts',
        niche: 'politica',
        views: '',
        retention: '',
        ctr: '',
        duration: '',
        problem: 'O vídeo parou de receber impressões após as primeiras 24 horas',
    });

    const messagesEndRef = React.useRef<HTMLDivElement>(null);
    const textareaRef = React.useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    React.useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    // Verifica se veio prompt pela URL (?prompt=...)
    React.useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const urlPrompt = params.get('prompt');
        if (urlPrompt && urlPrompt.trim()) {
            handleSend(urlPrompt);
            // Limpa query string sem recarregar a página
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }, []);

    const handleSend = async (textToSend?: string) => {
        const query = (textToSend || input).trim();
        if (!query || loading) return;

        const userMsg: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: query,
            timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
        };

        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        setInput('');
        setLoading(true);

        try {
            // Prepara histórico recente (excluindo saudação inicial)
            const history = updatedMessages
                .filter((m) => m.id !== 'init-1')
                .slice(-6)
                .map((m) => ({ role: m.role, content: m.content }));

            const response = await fetch('/painel/assistente/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement)?.content || '',
                    'Accept': 'application/json',
                },
                body: JSON.stringify({
                    message: query,
                    history: history.slice(0, -1), // histórico anterior
                }),
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(data.error || 'Falha na resposta do assistente');
            }

            const botMsg: Message = {
                id: `bot-${Date.now()}`,
                role: 'assistant',
                content: data.response || 'Sem resposta gerada.',
                timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
            };

            setMessages((prev) => [...prev, botMsg]);
        } catch (err: any) {
            const errorMsg: Message = {
                id: `err-${Date.now()}`,
                role: 'assistant',
                content: `⚠️ **Erro ao consultar a IA:** ${err.message || 'Verifique se a GROQ_API_KEY está configurada no .env'}`,
                timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
            };
            setMessages((prev) => [...prev, errorMsg]);
        } finally {
            setLoading(false);
            setTimeout(() => textareaRef.current?.focus(), 50);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const copyToClipboard = (id: string, text: string) => {
        navigator.clipboard.writeText(text);
        setCopiedId(id);
        setTimeout(() => setCopiedId(null), 2000);
    };

    const clearChat = () => {
        setMessages([
            {
                id: 'init-restart',
                role: 'assistant',
                content: 'Conversa limpa! O que você gostaria de analisar agora?',
                timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
            },
        ]);
    };

    const submitDiagnosis = (e: React.FormEvent) => {
        e.preventDefault();
        const prompt = `[DIAGNÓSTICO YOUTUBE STUDIO]
- Formato: ${diagForm.videoType === 'shorts' ? 'YouTube Shorts (Vertical)' : 'Vídeo Longo (Horizontal)'}
- Nicho/Assunto: ${diagForm.niche}
- Visualizações: ${diagForm.views ? diagForm.views : 'Não informado'}
- % de Retenção / Duração Média: ${diagForm.retention ? diagForm.retention : 'Não informado'}
- Taxa de Cliques (CTR): ${diagForm.ctr ? diagForm.ctr : 'Não informado'}
- Duração do Vídeo: ${diagForm.duration ? diagForm.duration : 'Não informado'}
- Situação / Pergunta: ${diagForm.problem}

Analise esses números como um estrategista sênior do algoritmo do YouTube:
1. Diagnóstico do Algoritmo: O que esses dados indicam sobre a retenção e entrega?
2. Identificação de Gargalos: Onde o vídeo perdeu alcance (Thumbnail/CTR, Gancho nos primeiros 3s ou Ritmo)?
3. Plano de Ação Imediato: 3 passos práticos para aplicar no próximo corte/vídeo para aumentar visualizações e inscritos.`;

        setDiagOpen(false);
        handleSend(prompt);
    };

    return (
        <>
            <Head title="Assistente IA (LLaMA)" />
            <AppShell
                title="Assistente IA de Conteúdo"
                user={props.auth.user}
                description="Consultoria ao vivo com LLaMA 3.3 70B (Groq) para estratégia, retenção, monetização e YouTube Analytics."
                withToaster={false}
            >
                <div className="flex flex-col gap-4 max-w-5xl mx-auto w-full pb-8">
                    {/* Header Banner com Status do Modelo e Ações Rápidas */}
                    <div className="rounded-xl border border-primary/20 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 shadow-xs">
                        <div className="flex items-center gap-3">
                            <div className="size-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
                                <SparklesIcon className="size-5" />
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <h2 className="font-semibold text-foreground text-sm md:text-base">LLaMA 3.3 70B Versatile</h2>
                                    <Badge variant="outline" className="text-[11px] font-mono border-emerald-500/40 text-emerald-500 bg-emerald-500/10">
                                        Gratuito (Groq Cloud)
                                    </Badge>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Respostas rápidas em tempo real com dados contextualizados do seu canal de cortes.
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 self-end md:self-auto">
                            {/* Modal de Diagnóstico do YouTube Studio */}
                            <Dialog open={diagOpen} onOpenChange={setDiagOpen}>
                                <DialogTrigger asChild>
                                    <Button
                                        size="sm"
                                        style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)', color: '#fff' }}
                                        className="h-8 text-xs shadow-xs hover:brightness-105"
                                    >
                                        <BarChart3Icon className="size-3.5 mr-1.5" />
                                        Diagnóstico YouTube Studio
                                    </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-lg">
                                    <DialogHeader>
                                        <DialogTitle className="font-display font-bold flex items-center gap-2">
                                            <BarChart3Icon className="size-5 text-primary" />
                                            Diagnosticar Métricas do YouTube
                                        </DialogTitle>
                                        <DialogDescription className="text-xs">
                                            Insira os dados do seu vídeo obtidos no <strong>YouTube Studio (Analytics)</strong> para que o LLaMA analise a retenção, CTR e recomende melhorias imediatas.
                                        </DialogDescription>
                                    </DialogHeader>
                                    <form onSubmit={submitDiagnosis} className="space-y-3.5 text-xs">
                                        <div className="grid grid-cols-2 gap-3">
                                            <Field>
                                                <FieldLabel className="text-xs">Formato</FieldLabel>
                                                <select
                                                    value={diagForm.videoType}
                                                    onChange={(e) => setDiagForm({ ...diagForm, videoType: e.target.value })}
                                                    className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs shadow-xs"
                                                >
                                                    <option value="shorts">📱 YouTube Shorts (Vertical)</option>
                                                    <option value="long">🎬 Vídeo Longo (Horizontal)</option>
                                                </select>
                                            </Field>
                                            <Field>
                                                <FieldLabel className="text-xs">Nicho / Tema</FieldLabel>
                                                <select
                                                    value={diagForm.niche}
                                                    onChange={(e) => setDiagForm({ ...diagForm, niche: e.target.value })}
                                                    className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs shadow-xs"
                                                >
                                                    <option value="politica">🏛️ Política / Debates</option>
                                                    <option value="futebol">⚽ Futebol / Esportes</option>
                                                    <option value="podcast">🎙️ Podcast / Entrevistas</option>
                                                    <option value="geral">🌐 Outro Nicho</option>
                                                </select>
                                            </Field>
                                        </div>

                                        <div className="grid grid-cols-3 gap-2.5">
                                            <Field>
                                                <FieldLabel className="text-xs">Visualizações</FieldLabel>
                                                <Input
                                                    placeholder="Ex: 2.400"
                                                    value={diagForm.views}
                                                    onChange={(e) => setDiagForm({ ...diagForm, views: e.target.value })}
                                                    className="h-8 text-xs"
                                                />
                                            </Field>
                                            <Field>
                                                <FieldLabel className="text-xs">Retenção (%)</FieldLabel>
                                                <Input
                                                    placeholder="Ex: 58% ou 0:42"
                                                    value={diagForm.retention}
                                                    onChange={(e) => setDiagForm({ ...diagForm, retention: e.target.value })}
                                                    className="h-8 text-xs"
                                                />
                                            </Field>
                                            <Field>
                                                <FieldLabel className="text-xs">CTR / Cliques (%)</FieldLabel>
                                                <Input
                                                    placeholder="Ex: 4.8%"
                                                    value={diagForm.ctr}
                                                    onChange={(e) => setDiagForm({ ...diagForm, ctr: e.target.value })}
                                                    className="h-8 text-xs"
                                                />
                                            </Field>
                                        </div>

                                        <Field>
                                            <FieldLabel className="text-xs">Principal Dúvida ou Problema Observado</FieldLabel>
                                            <Textarea
                                                placeholder="Ex: O vídeo teve 1.500 visualizações na primeira hora e depois o YouTube parou completamente de entregar..."
                                                value={diagForm.problem}
                                                onChange={(e) => setDiagForm({ ...diagForm, problem: e.target.value })}
                                                rows={2}
                                                className="text-xs resize-none"
                                            />
                                        </Field>

                                        <DialogFooter className="pt-2">
                                            <Button type="button" variant="outline" size="sm" onClick={() => setDiagOpen(false)}>
                                                Cancelar
                                            </Button>
                                            <Button
                                                type="submit"
                                                size="sm"
                                                style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)', color: '#fff' }}
                                            >
                                                🧠 Analisar Métricas com IA
                                            </Button>
                                        </DialogFooter>
                                    </form>
                                </DialogContent>
                            </Dialog>

                            <Button
                                variant="outline"
                                size="sm"
                                onClick={clearChat}
                                className="h-8 text-xs text-muted-foreground hover:text-foreground"
                            >
                                <Trash2Icon className="size-3.5 mr-1.5" />
                                Limpar
                            </Button>
                        </div>
                    </div>

                    {/* Sugestões Rápidas */}
                    {messages.length <= 2 && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
                            {SUGGESTIONS.map((sug, i) => (
                                <Card
                                    key={i}
                                    onClick={() => handleSend(sug.prompt)}
                                    className="cursor-pointer border-border/80 hover:border-primary/50 hover:bg-card/80 transition-all shadow-2xs hover:shadow-xs group"
                                >
                                    <CardHeader className="p-3 pb-2 flex flex-row items-center justify-between space-y-0">
                                        <sug.icon className="size-4 text-primary group-hover:scale-110 transition-transform" />
                                        <Badge variant="secondary" className="text-[10px] font-medium py-0 px-1.5">
                                            {sug.tag}
                                        </Badge>
                                    </CardHeader>
                                    <CardContent className="p-3 pt-0">
                                        <CardTitle className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors">
                                            {sug.title}
                                        </CardTitle>
                                        <CardDescription className="text-[11px] line-clamp-2 mt-1">
                                            {sug.prompt}
                                        </CardDescription>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {/* Área de Mensagens */}
                    <Card className="border-border/80 bg-card/60 flex flex-col min-h-[480px] max-h-[650px] shadow-sm">
                        <div className="flex-1 p-4 md:p-6 overflow-y-auto space-y-4">
                            {messages.map((msg) => {
                                const isUser = msg.role === 'user';
                                return (
                                    <div
                                        key={msg.id}
                                        className={`flex gap-3 max-w-[88%] md:max-w-[80%] ${
                                            isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
                                        }`}
                                    >
                                        <div
                                            className={`size-8 shrink-0 rounded-full flex items-center justify-center text-xs font-bold shadow-xs ${
                                                isUser
                                                    ? 'bg-primary text-primary-foreground'
                                                    : 'bg-muted border border-border text-foreground'
                                            }`}
                                        >
                                            {isUser ? <UserIcon className="size-4" /> : <BotIcon className="size-4 text-primary" />}
                                        </div>
                                        <div className="flex flex-col gap-1">
                                            <div
                                                className={`rounded-2xl px-4 py-3 text-[13.5px] leading-relaxed relative group ${
                                                    isUser
                                                        ? 'bg-primary text-primary-foreground rounded-tr-xs'
                                                        : 'bg-muted/80 border border-border/70 text-foreground rounded-tl-xs'
                                                }`}
                                            >
                                                <div className="whitespace-pre-wrap break-words">{msg.content}</div>

                                                {!isUser && (
                                                    <button
                                                        onClick={() => copyToClipboard(msg.id, msg.content)}
                                                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity size-7 rounded-md bg-background/80 hover:bg-background border border-border/80 flex items-center justify-center text-muted-foreground hover:text-foreground"
                                                        title="Copiar resposta"
                                                    >
                                                        {copiedId === msg.id ? (
                                                            <CheckIcon className="size-3.5 text-emerald-500" />
                                                        ) : (
                                                            <CopyIcon className="size-3.5" />
                                                        )}
                                                    </button>
                                                )}
                                            </div>
                                            <span
                                                className={`text-[10.5px] text-muted-foreground px-1 ${
                                                    isUser ? 'text-right' : 'text-left'
                                                }`}
                                            >
                                                {msg.timestamp}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}

                            {loading && (
                                <div className="flex gap-3 max-w-[80%] mr-auto">
                                    <div className="size-8 shrink-0 rounded-full bg-muted border border-border flex items-center justify-center">
                                        <BotIcon className="size-4 text-primary animate-pulse" />
                                    </div>
                                    <div className="rounded-2xl rounded-tl-xs px-4 py-3 bg-muted/80 border border-border/70 text-muted-foreground flex items-center gap-2 text-xs">
                                        <RefreshCwIcon className="size-3.5 animate-spin text-primary" />
                                        <span>LLaMA 3.3 está pensando...</span>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Box */}
                        <div className="p-3 md:p-4 border-t border-border bg-card/90 rounded-b-xl flex flex-col gap-2">
                            <div className="relative flex items-end gap-2">
                                <Textarea
                                    ref={textareaRef}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Faça uma pergunta sobre estratégia, ideias de cortes, horários ou monetização... (Enter para enviar)"
                                    rows={2}
                                    disabled={loading}
                                    className="min-h-[60px] max-h-[140px] resize-none pr-12 text-[13.5px] bg-background/90 rounded-xl"
                                />
                                <Button
                                    onClick={() => handleSend()}
                                    disabled={loading || !input.trim()}
                                    size="icon"
                                    className="absolute right-2.5 bottom-2.5 size-8.5 rounded-lg shadow-xs"
                                >
                                    <SendIcon className="size-4" />
                                </Button>
                            </div>
                            <div className="flex items-center justify-between text-[11px] text-muted-foreground px-1">
                                <span>Pressione <kbd className="font-mono bg-muted px-1 rounded-sm border border-border">Enter</kbd> para enviar, <kbd className="font-mono bg-muted px-1 rounded-sm border border-border">Shift+Enter</kbd> para nova linha</span>
                                <span className="hidden sm:inline">IA especializada em YouTube & Estratégia de Conteúdo</span>
                            </div>
                        </div>
                    </Card>
                </div>
            </AppShell>
        </>
    );
}
