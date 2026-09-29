import * as React from 'react';
import { Head, usePage } from '@inertiajs/react';
import {
    BotIcon,
    UserIcon,
    SendIcon,
    SparklesIcon,
    Trash2Icon,
    CopyIcon,
    CheckIcon,
    RefreshCwIcon,
    ZapIcon,
    ClockIcon,
    DollarSignIcon,
    BarChart3Icon,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
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
        channels: Array<{ id?: number; name?: string; title?: string; niche: string; active: boolean; slug: string }>;
    };
};

type Message = {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
};

const SUGGESTIONS = [
    {
        icon: BarChart3Icon,
        title: '⚽ Métricas Futebol em Cortes',
        prompt: `[ANÁLISE DE MÉTRICAS - FUTEBOL EM CORTES]
- Formato: YouTube Shorts
- CTR (Escolheram assistir): 58%
- Retenção Média (AVD): 44%
- Retenção nos primeiros 3s: 52%
- Tema do Vídeo: Lance polêmico de arbitragem no clássico
- Título Atual: Juiz errou feio no lance polêmico ontem

Com base nos benchmarks de futebol no Brasil:
1. Qual é o principal gargalo (Capa/Título ou Gancho dos 3s)?
2. Dê 3 opções de títulos com alto gatilho de curiosidade (CTR > 75%).
3. O que devo cortar nos primeiros 3 segundos para a retenção passar de 70%?`,
        tag: 'Futebol',
    },
    {
        icon: ZapIcon,
        title: '🏛️ Métricas Cortes da Política',
        prompt: `[ANÁLISE DE MÉTRICAS - CORTES DA POLÍTICA]
- Formato: Vídeo Longo (12 min)
- CTR (Taxa de Cliques): 4.1%
- Retenção Média (AVD): 34%
- Retenção nos primeiros 3s: 62%
- Tema do Vídeo: Debate acalorado sobre decisão do STF
- Título Atual: Deputado confronta ministro ao vivo no plenário

Com base nos benchmarks de política no Brasil (estilo MBL / Missão):
1. Onde está o gargalo principal (Capa/Título vs Meio do Vídeo)?
2. Dê 3 opções de títulos no padrão viral de confronto.
3. Qual a minutagem ideal para esse corte?`,
        tag: 'Política',
    },
    {
        icon: DollarSignIcon,
        title: '💰 Calculadora de Ganhos',
        prompt: 'Qual a estimativa de faturamento para 200.000 visualizações no YouTube em vídeos longos vs Shorts no Brasil?',
        tag: 'Monetização',
    },
    {
        icon: ClockIcon,
        title: '⏰ Melhores Horários',
        prompt: 'Quais os melhores horários e frequência diária para postar cortes de futebol e política no YouTube Brasil?',
        tag: 'Algoritmo',
    },
];

export default function Assistant({ stats }: PageProps) {
    const { props } = usePage<PageProps>();
    const [messages, setMessages] = React.useState<Message[]>(() => {
        const initialGreeting = `Olá! Sou seu assistente de inteligência e estratégia de conteúdo com **LLaMA 3.3 70B** (via Groq). 

Estou conectado ao contexto do seu painel:
- **${stats.total_dest_channels}** canal(is) de destino no YouTube
- **${stats.total_source_channels}** canais fontes monitorados
- **${stats.total_published_clips}** clipes já publicados

Como posso te ajudar hoje? Você pode clicar em **Diagnóstico YouTube Studio** acima ou usar os cartões abaixo para diagnosticar métricas do **Futebol em Cortes** ou **Cortes da Política**!`;

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
        niche: 'futebol',
        title: '',
        views: '',
        retention: '',
        first3s: '',
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

    const handleSend = React.useCallback(
        async (textToSend?: string) => {
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
                        'X-CSRF-TOKEN':
                            (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement)?.content || '',
                        Accept: 'application/json',
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
            } catch (err: unknown) {
                const errorMsg: Message = {
                    id: `err-${Date.now()}`,
                    role: 'assistant',
                    content: `⚠️ **Erro ao consultar a IA:** ${err instanceof Error ? err.message : 'Verifique se a GROQ_API_KEY está configurada no .env'}`,
                    timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
                };
                setMessages((prev) => [...prev, errorMsg]);
            } finally {
                setLoading(false);
                setTimeout(() => textareaRef.current?.focus(), 50);
            }
        },
        [input, loading, messages],
    );

    // Verifica se veio prompt pela URL (?prompt=...)
    React.useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const urlPrompt = params.get('prompt');
        if (urlPrompt && urlPrompt.trim()) {
            void handleSend(urlPrompt);
            // Limpa query string sem recarregar a página
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }, [handleSend]);

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

    const setPresetDiagnosis = (type: 'futebol' | 'politica') => {
        if (type === 'futebol') {
            setDiagForm({
                videoType: 'shorts',
                niche: 'futebol',
                title: 'Juiz errou feio no lance polêmico ontem',
                views: '3.200',
                retention: '44%',
                first3s: '52%',
                ctr: '58%',
                duration: '0:45',
                problem: 'O vídeo teve pico na primeira hora e parou de ser entregue no feed dos Shorts.',
            });
        } else {
            setDiagForm({
                videoType: 'long',
                niche: 'politica',
                title: 'Deputado confronta ministro ao vivo no plenário',
                views: '1.800',
                retention: '34%',
                first3s: '62%',
                ctr: '4.1%',
                duration: '11:30',
                problem: 'A retenção média caiu no meio do vídeo e o CTR está abaixo de 5%.',
            });
        }
    };

    const submitDiagnosis = (e: React.FormEvent) => {
        e.preventDefault();
        const prompt = `[DIAGNÓSTICO YOUTUBE STUDIO]
- Formato: ${diagForm.videoType === 'shorts' ? 'YouTube Shorts (Vertical)' : 'Vídeo Longo (Horizontal)'}
- Nicho/Assunto: ${diagForm.niche}
- Título Atual: ${diagForm.title ? diagForm.title : 'Não informado'}
- Visualizações: ${diagForm.views ? diagForm.views : 'Não informado'}
- % de Retenção Média (AVD): ${diagForm.retention ? diagForm.retention : 'Não informado'}
- Retenção Primeiros 3s (Hook): ${diagForm.first3s ? diagForm.first3s : 'Não informado'}
- Taxa de Cliques (CTR): ${diagForm.ctr ? diagForm.ctr : 'Não informado'}
- Duração do Vídeo: ${diagForm.duration ? diagForm.duration : 'Não informado'}
- Situação / Pergunta: ${diagForm.problem}

Analise esses números com base nos benchmarks oficiais do YouTube Brasil:
1. 🌡️ Termômetro de Desempenho (Notas 0-10 para CTR e Retenção).
2. 🔍 Diagnóstico do Gargalo (Capa/Título vs Gancho dos 3s vs Minutagem).
3. ✂️ Plano de Ação Imediato (3 novos títulos de alto clique + instrução exata de corte para os primeiros 3 segundos).`;

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
                <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 pb-8">
                    {/* Header Banner com Status do Modelo e Ações Rápidas */}
                    <div className="flex flex-col items-start justify-between gap-3 rounded-xl border border-primary/20 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-4 shadow-xs md:flex-row md:items-center">
                        <div className="flex items-center gap-3">
                            <div className="flex size-10 items-center justify-center rounded-xl bg-primary/20 text-primary">
                                <SparklesIcon className="size-5" />
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <h2 className="text-sm font-semibold text-foreground md:text-base">
                                        LLaMA 3.3 70B Versatile
                                    </h2>
                                    <Badge
                                        variant="outline"
                                        className="border-emerald-500/40 bg-emerald-500/10 font-mono text-[11px] text-emerald-500"
                                    >
                                        Gratuito (Groq Cloud)
                                    </Badge>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Respostas instantâneas contextualizadas com os dados e benchmarks dos seus canais de
                                    cortes.
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
                                        <BarChart3Icon className="mr-1.5 size-3.5" />
                                        Diagnóstico YouTube Studio
                                    </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-lg">
                                    <DialogHeader>
                                        <DialogTitle className="flex items-center gap-2 font-display font-bold">
                                            <BarChart3Icon className="size-5 text-primary" />
                                            Diagnosticar Métricas do YouTube Studio
                                        </DialogTitle>
                                        <DialogDescription className="text-xs">
                                            Insira os dados do vídeo ou clique nos presets rápidos abaixo para o LLaMA
                                            analisar gargalos de retenção e CTR.
                                        </DialogDescription>
                                    </DialogHeader>

                                    {/* Presets Rápidos de 1 Clique */}
                                    <div className="flex items-center gap-2 rounded-lg border border-border/80 bg-muted/60 p-2">
                                        <span className="text-[11px] font-semibold whitespace-nowrap text-muted-foreground">
                                            Preencher rápido:
                                        </span>
                                        <div className="flex flex-wrap gap-1.5">
                                            <button
                                                type="button"
                                                onClick={() => setPresetDiagnosis('futebol')}
                                                className="rounded border border-border/80 bg-background px-2 py-1 text-[11px] font-medium transition-colors hover:border-emerald-500/50 hover:bg-emerald-500/10"
                                            >
                                                ⚽ Futebol em Cortes
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setPresetDiagnosis('politica')}
                                                className="rounded border border-border/80 bg-background px-2 py-1 text-[11px] font-medium transition-colors hover:border-red-500/50 hover:bg-red-500/10"
                                            >
                                                🏛️ Cortes da Política
                                            </button>
                                        </div>
                                    </div>

                                    <form onSubmit={submitDiagnosis} className="space-y-3 text-xs">
                                        <div className="grid grid-cols-2 gap-3">
                                            <Field>
                                                <FieldLabel className="text-xs">Formato</FieldLabel>
                                                <select
                                                    value={diagForm.videoType}
                                                    onChange={(e) =>
                                                        setDiagForm({ ...diagForm, videoType: e.target.value })
                                                    }
                                                    className="h-8 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-xs"
                                                >
                                                    <option value="shorts">📱 YouTube Shorts (Vertical)</option>
                                                    <option value="long">🎬 Vídeo Longo (Horizontal)</option>
                                                </select>
                                            </Field>
                                            <Field>
                                                <FieldLabel className="text-xs">Nicho / Tema</FieldLabel>
                                                <select
                                                    value={diagForm.niche}
                                                    onChange={(e) =>
                                                        setDiagForm({ ...diagForm, niche: e.target.value })
                                                    }
                                                    className="h-8 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-xs"
                                                >
                                                    <option value="futebol">⚽ Futebol / Esportes</option>
                                                    <option value="politica">🏛️ Política / Debates</option>
                                                    <option value="podcast">🎙️ Podcast / Entrevistas</option>
                                                    <option value="geral">🌐 Outro Nicho</option>
                                                </select>
                                            </Field>
                                        </div>

                                        <Field>
                                            <FieldLabel className="text-xs">
                                                Título Atual do Vídeo / Manchete
                                            </FieldLabel>
                                            <Input
                                                placeholder="Ex: Juiz errou feio no lance polêmico ontem"
                                                value={diagForm.title}
                                                onChange={(e) => setDiagForm({ ...diagForm, title: e.target.value })}
                                                className="h-8 text-xs"
                                            />
                                        </Field>

                                        <div className="grid grid-cols-4 gap-2">
                                            <Field>
                                                <FieldLabel className="text-xs">Visualizações</FieldLabel>
                                                <Input
                                                    placeholder="Ex: 3.200"
                                                    value={diagForm.views}
                                                    onChange={(e) =>
                                                        setDiagForm({ ...diagForm, views: e.target.value })
                                                    }
                                                    className="h-8 text-xs"
                                                />
                                            </Field>
                                            <Field>
                                                <FieldLabel className="text-xs">Retenção AVD</FieldLabel>
                                                <Input
                                                    placeholder="Ex: 44%"
                                                    value={diagForm.retention}
                                                    onChange={(e) =>
                                                        setDiagForm({ ...diagForm, retention: e.target.value })
                                                    }
                                                    className="h-8 text-xs"
                                                />
                                            </Field>
                                            <Field>
                                                <FieldLabel className="text-xs">Primeiros 3s</FieldLabel>
                                                <Input
                                                    placeholder="Ex: 52%"
                                                    value={diagForm.first3s}
                                                    onChange={(e) =>
                                                        setDiagForm({ ...diagForm, first3s: e.target.value })
                                                    }
                                                    className="h-8 text-xs"
                                                />
                                            </Field>
                                            <Field>
                                                <FieldLabel className="text-xs">CTR (%)</FieldLabel>
                                                <Input
                                                    placeholder="Ex: 58%"
                                                    value={diagForm.ctr}
                                                    onChange={(e) => setDiagForm({ ...diagForm, ctr: e.target.value })}
                                                    className="h-8 text-xs"
                                                />
                                            </Field>
                                        </div>

                                        <Field>
                                            <FieldLabel className="text-xs">
                                                Principal Dúvida ou Problema Observado
                                            </FieldLabel>
                                            <Textarea
                                                placeholder="Ex: O vídeo teve 1.500 visualizações na primeira hora e depois o YouTube parou completamente de entregar..."
                                                value={diagForm.problem}
                                                onChange={(e) => setDiagForm({ ...diagForm, problem: e.target.value })}
                                                rows={2}
                                                className="resize-none text-xs"
                                            />
                                        </Field>

                                        <DialogFooter className="pt-2">
                                            <Button
                                                type="button"
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setDiagOpen(false)}
                                            >
                                                Cancelar
                                            </Button>
                                            <Button
                                                type="submit"
                                                size="sm"
                                                style={{
                                                    background: 'linear-gradient(160deg,#FF6A55,#E23C33)',
                                                    color: '#fff',
                                                }}
                                            >
                                                🧠 Analisar com LLaMA
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
                                <Trash2Icon className="mr-1.5 size-3.5" />
                                Limpar
                            </Button>
                        </div>
                    </div>

                    {/* Sugestões Rápidas */}
                    {messages.length <= 2 && (
                        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
                            {SUGGESTIONS.map((sug, i) => (
                                <Card
                                    key={i}
                                    onClick={() => handleSend(sug.prompt)}
                                    className="group cursor-pointer border-border/80 shadow-2xs transition-all hover:border-primary/50 hover:bg-card/80 hover:shadow-xs"
                                >
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 p-3 pb-2">
                                        <sug.icon className="size-4 text-primary transition-transform group-hover:scale-110" />
                                        <Badge variant="secondary" className="px-1.5 py-0 text-[10px] font-medium">
                                            {sug.tag}
                                        </Badge>
                                    </CardHeader>
                                    <CardContent className="p-3 pt-0">
                                        <CardTitle className="text-xs font-semibold text-foreground transition-colors group-hover:text-primary">
                                            {sug.title}
                                        </CardTitle>
                                        <CardDescription className="mt-1 line-clamp-2 text-[11px]">
                                            {sug.prompt}
                                        </CardDescription>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {/* Área de Mensagens */}
                    <Card className="flex max-h-[650px] min-h-[480px] flex-col border-border/80 bg-card/60 shadow-sm">
                        <div className="flex-1 space-y-4 overflow-y-auto p-4 md:p-6">
                            {messages.map((msg) => {
                                const isUser = msg.role === 'user';
                                return (
                                    <div
                                        key={msg.id}
                                        className={`flex max-w-[88%] gap-3 md:max-w-[80%] ${
                                            isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
                                        }`}
                                    >
                                        <div
                                            className={`flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-bold shadow-xs ${
                                                isUser
                                                    ? 'bg-primary text-primary-foreground'
                                                    : 'border border-border bg-muted text-foreground'
                                            }`}
                                        >
                                            {isUser ? (
                                                <UserIcon className="size-4" />
                                            ) : (
                                                <BotIcon className="size-4 text-primary" />
                                            )}
                                        </div>
                                        <div className="flex flex-col gap-1">
                                            <div
                                                className={`group relative rounded-2xl px-4 py-3 text-[13.5px] leading-relaxed ${
                                                    isUser
                                                        ? 'rounded-tr-xs bg-primary text-primary-foreground'
                                                        : 'rounded-tl-xs border border-border/70 bg-muted/80 text-foreground'
                                                }`}
                                            >
                                                <div className="break-words whitespace-pre-wrap">{msg.content}</div>

                                                {!isUser && (
                                                    <button
                                                        onClick={() => copyToClipboard(msg.id, msg.content)}
                                                        className="absolute top-2 right-2 flex size-7 items-center justify-center rounded-md border border-border/80 bg-background/80 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 hover:bg-background hover:text-foreground"
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
                                                className={`px-1 text-[10.5px] text-muted-foreground ${
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
                                <div className="mr-auto flex max-w-[80%] gap-3">
                                    <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-border bg-muted">
                                        <BotIcon className="size-4 animate-pulse text-primary" />
                                    </div>
                                    <div className="flex items-center gap-2 rounded-2xl rounded-tl-xs border border-border/70 bg-muted/80 px-4 py-3 text-xs text-muted-foreground">
                                        <RefreshCwIcon className="size-3.5 animate-spin text-primary" />
                                        <span>LLaMA 3.3 está pensando...</span>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Box */}
                        <div className="flex flex-col gap-2 rounded-b-xl border-t border-border bg-card/90 p-3 md:p-4">
                            <div className="relative flex items-end gap-2">
                                <Textarea
                                    ref={textareaRef}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Faça uma pergunta sobre estratégia, ideias de cortes, horários ou monetização... (Enter para enviar)"
                                    rows={2}
                                    disabled={loading}
                                    className="max-h-[140px] min-h-[60px] resize-none rounded-xl bg-background/90 pr-12 text-[13.5px]"
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
                            <div className="flex items-center justify-between px-1 text-[11px] text-muted-foreground">
                                <span>
                                    Pressione{' '}
                                    <kbd className="rounded-sm border border-border bg-muted px-1 font-mono">Enter</kbd>{' '}
                                    para enviar,{' '}
                                    <kbd className="rounded-sm border border-border bg-muted px-1 font-mono">
                                        Shift+Enter
                                    </kbd>{' '}
                                    para nova linha
                                </span>
                                <span className="hidden sm:inline">
                                    IA especializada em YouTube & Estratégia de Conteúdo
                                </span>
                            </div>
                        </div>
                    </Card>
                </div>
            </AppShell>
        </>
    );
}
