import { useState, useEffect } from 'react';
import { router } from '@inertiajs/react';
import { toast } from 'sonner';
import {
    Sparkles,
    Play,
    RotateCcw,
    Palette,
    Type,
    Layers,
    Subtitles,
    Save,
    Smartphone,
    Monitor,
    Upload,
    Image as ImageIcon,
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Field, FieldLabel } from '@/components/ui/field';

export type TemplateConfig = {
    headerTitle?: string;
    headerBadge?: string;
    accentColor?: string;
    bgStyle?: 'blur_dark' | 'blur_intense' | 'gradient_dark';
    subtitleColor?: '#ffffff' | '#facc15' | '#38bdf8';
    ctaText?: string;
};

type Props = {
    channel: {
        id: number;
        slug: string;
        name: string;
        niche: string;
        templateConfig?: TemplateConfig | null;
        hasWatermark?: boolean;
        watermarkUrl?: string | null;
    } | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
};

const COLOR_PRESETS = [
    { label: 'Vermelho Política', value: '#E50914', niche: 'politica' },
    { label: 'Verde Futebol', value: '#10B981', niche: 'futebol' },
    { label: 'Roxo Podcast', value: '#8B5CF6', niche: 'podcast' },
    { label: 'Azul Intenso', value: '#2563EB', niche: 'geral' },
    { label: 'Dourado Âmbar', value: '#F59E0B', niche: 'geral' },
    { label: 'Coral Flame', value: '#FF6A55', niche: 'geral' },
];

export function ChannelTemplateModal({ channel, open, onOpenChange }: Props) {
    const channelName = channel?.name ?? '';
    const niche = (channel?.niche ?? '').toLowerCase();
    const isPolitica = niche.includes('pol');
    const isFutebol = niche.includes('fut');

    // Defaults baseados no nicho
    const defaultTitle = channelName.toUpperCase();
    const defaultBadge = isPolitica ? '🔴 DEBATE AO VIVO' : isFutebol ? '⚽ LANCE DECISIVO' : '🎙️ CORTES EXCLUSIVOS';
    const defaultAccent = isPolitica ? '#E50914' : isFutebol ? '#10B981' : '#8B5CF6';

    const [headerTitle, setHeaderTitle] = useState('');
    const [headerBadge, setHeaderBadge] = useState('');
    const [accentColor, setAccentColor] = useState(defaultAccent);
    const [bgStyle, setBgStyle] = useState<'blur_dark' | 'blur_intense' | 'gradient_dark'>('blur_dark');
    const [subtitleColor, setSubtitleColor] = useState<'#ffffff' | '#facc15' | '#38bdf8'>('#facc15');
    const [ctaText, setCtaText] = useState('INSCREVA-SE NO CANAL');
    const [saving, setSaving] = useState(false);
    const [device, setDevice] = useState<'mobile' | 'desktop'>('mobile');

    // Carrega dados existentes do canal quando abre o modal
    useEffect(() => {
        if (channel && open) {
            const cfg = channel.templateConfig || {};
            setHeaderTitle(cfg.headerTitle || defaultTitle);
            setHeaderBadge(cfg.headerBadge || defaultBadge);
            setAccentColor(cfg.accentColor || defaultAccent);
            setBgStyle(cfg.bgStyle || 'blur_dark');
            setSubtitleColor(cfg.subtitleColor || '#facc15');
            setCtaText(cfg.ctaText || 'INSCREVA-SE NO CANAL');
        }
    }, [channel, open, defaultTitle, defaultBadge, defaultAccent]);

    if (!channel) return null;

    const handleResetDefaults = () => {
        setHeaderTitle(defaultTitle);
        setHeaderBadge(defaultBadge);
        setAccentColor(defaultAccent);
        setBgStyle('blur_dark');
        setSubtitleColor('#facc15');
        setCtaText('INSCREVA-SE NO CANAL');
        toast.info('Valores restaurados para o padrão do nicho');
    };

    const handleSave = () => {
        setSaving(true);
        const template_config: TemplateConfig = {
            headerTitle,
            headerBadge,
            accentColor,
            bgStyle,
            subtitleColor,
            ctaText,
        };

        router.put(
            `/painel/canais-destino/${channel.id}`,
            {
                template_config,
            },
            {
                preserveScroll: true,
                onSuccess: () => {
                    setSaving(false);
                    toast.success(`Template do canal ${channel.name} salvo com sucesso!`);
                    onOpenChange(false);
                },
                onError: (err) => {
                    setSaving(false);
                    toast.error('Erro ao salvar template: ' + (Object.values(err)[0] || 'Erro desconhecido'));
                },
            },
        );
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="flex max-h-[92vh] max-w-4xl flex-col overflow-hidden border border-white/10 bg-zinc-950 p-0 text-zinc-100 sm:rounded-2xl">
                {/* Header */}
                <DialogHeader className="flex-row items-center justify-between space-y-0 border-b border-white/10 bg-zinc-900/50 p-6">
                    <div className="flex items-center gap-3">
                        <div
                            className="flex h-10 w-10 items-center justify-center rounded-xl text-white shadow-lg transition-colors"
                            style={{ backgroundColor: accentColor }}
                        >
                            <Sparkles className="h-5 w-5" />
                        </div>
                        <div>
                            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-white">
                                Estúdio de Template 9:16 — {channel.name}
                            </DialogTitle>
                            <p className="mt-0.5 text-xs text-zinc-400">
                                Configure o enquadramento vertical, títulos, cores e legendas usados nos cortes deste
                                canal.
                            </p>
                        </div>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleResetDefaults}
                        className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white"
                    >
                        <RotateCcw className="h-3.5 w-3.5" />
                        Padrão do Nicho
                    </Button>
                </DialogHeader>

                {/* Body: 2 Columns */}
                <div className="grid flex-1 grid-cols-1 gap-6 overflow-y-auto p-6 md:grid-cols-12">
                    {/* CONTROLES (Lado Esquerdo - 7 cols) */}
                    <div className="flex flex-col gap-5 pr-2 md:col-span-7">
                        {/* Seção: Topo */}
                        <div className="space-y-3 rounded-xl border border-white/5 bg-zinc-900/40 p-4">
                            <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-zinc-400 uppercase">
                                <Type className="h-3.5 w-3.5 text-[#FF6A55]" />
                                Identidade do Topo
                            </div>

                            <Field>
                                <FieldLabel className="text-xs font-medium text-zinc-300">
                                    Título Principal (Header)
                                </FieldLabel>
                                <Input
                                    value={headerTitle}
                                    onChange={(e) => setHeaderTitle(e.target.value)}
                                    placeholder="Ex: POLÍTICA EM CORTES"
                                    className="border-white/10 bg-zinc-900/80 text-sm font-semibold text-white"
                                />
                            </Field>

                            <Field>
                                <FieldLabel className="text-xs font-medium text-zinc-300">
                                    Selo / Badge Superior
                                </FieldLabel>
                                <Input
                                    value={headerBadge}
                                    onChange={(e) => setHeaderBadge(e.target.value)}
                                    placeholder="Ex: 🔴 DEBATE AO VIVO"
                                    className="border-white/10 bg-zinc-900/80 text-xs text-white"
                                />
                            </Field>
                        </div>

                        {/* Seção: Paleta e Cores */}
                        <div className="space-y-3 rounded-xl border border-white/5 bg-zinc-900/40 p-4">
                            <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-zinc-400 uppercase">
                                <Palette className="h-3.5 w-3.5 text-[#FF6A55]" />
                                Cor do Tema & Destaque
                            </div>

                            <div className="flex flex-wrap gap-2 pt-1">
                                {COLOR_PRESETS.map((preset) => (
                                    <button
                                        key={preset.value}
                                        type="button"
                                        onClick={() => setAccentColor(preset.value)}
                                        className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
                                            accentColor.toLowerCase() === preset.value.toLowerCase()
                                                ? 'scale-105 border-white bg-white/10 text-white shadow-md'
                                                : 'border-white/10 bg-zinc-900/50 text-zinc-400 hover:border-white/30'
                                        }`}
                                    >
                                        <div
                                            className="h-3 w-3 rounded-full border border-black/30"
                                            style={{ backgroundColor: preset.value }}
                                        />
                                        {preset.label}
                                    </button>
                                ))}
                            </div>

                            <div className="flex items-center gap-3 pt-2">
                                <span className="text-xs text-zinc-400">Cor Personalizada:</span>
                                <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-zinc-900/80 px-2.5 py-1">
                                    <input
                                        type="color"
                                        value={accentColor}
                                        onChange={(e) => setAccentColor(e.target.value)}
                                        className="h-6 w-6 cursor-pointer rounded border-0 bg-transparent"
                                    />
                                    <span className="font-mono text-xs text-zinc-200 uppercase">{accentColor}</span>
                                </div>
                            </div>
                        </div>

                        {/* Seção: Logo / Marca d'Água do Canal */}
                        <div className="space-y-3 rounded-xl border border-white/5 bg-zinc-900/40 p-4">
                            <div className="flex items-center justify-between text-xs font-semibold tracking-wider text-zinc-400 uppercase">
                                <div className="flex items-center gap-2">
                                    <ImageIcon className="h-3.5 w-3.5 text-[#FF6A55]" />
                                    Logo / Marca d'Água do Canal
                                </div>
                                <span className="font-mono text-[10px] text-zinc-500">Canto Sup. Direito</span>
                            </div>

                            <div className="flex items-center gap-4">
                                {channel.hasWatermark && channel.watermarkUrl ? (
                                    <img
                                        src={channel.watermarkUrl}
                                        alt={channel.name}
                                        className="h-14 w-14 shrink-0 rounded-full border-2 border-white/20 bg-black/40 object-cover p-1 shadow-md"
                                    />
                                ) : (
                                    <div className="flex h-14 w-14 shrink-0 flex-col items-center justify-center rounded-full border border-dashed border-white/20 bg-zinc-900/50 text-zinc-500">
                                        <ImageIcon className="h-5 w-5 text-zinc-400" />
                                    </div>
                                )}
                                <div className="flex-1 space-y-1">
                                    <p className="text-xs font-medium text-zinc-300">
                                        {channel.hasWatermark
                                            ? 'Logo do canal configurada'
                                            : 'Nenhuma logo personalizada'}
                                    </p>
                                    <p className="text-[11px] leading-snug text-zinc-400">
                                        Exibida automaticamente no canto superior direito dos vídeos e capas.
                                    </p>
                                    <label className="mt-1 inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-white/10 bg-zinc-800 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-zinc-700">
                                        <Upload className="h-3.5 w-3.5" />
                                        <span>Subir nova Logo (PNG)</span>
                                        <input
                                            type="file"
                                            accept="image/png,image/jpeg"
                                            className="hidden"
                                            onChange={(e) => {
                                                const file = e.target.files?.[0];
                                                if (!file) return;
                                                const fd = new FormData();
                                                fd.append('watermark', file);
                                                router.post(`/painel/canais-destino/${channel.id}/watermark`, fd, {
                                                    preserveScroll: true,
                                                    onSuccess: () => toast.success('Logo atualizada com sucesso!'),
                                                });
                                            }}
                                        />
                                    </label>
                                </div>
                            </div>
                        </div>

                        {/* Seção: Fundo & Blur */}
                        <div className="space-y-3 rounded-xl border border-white/5 bg-zinc-900/40 p-4">
                            <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-zinc-400 uppercase">
                                <Layers className="h-3.5 w-3.5 text-[#FF6A55]" />
                                Fundo de Enquadramento (FFmpeg)
                            </div>

                            <div className="grid grid-cols-3 gap-2">
                                <button
                                    type="button"
                                    onClick={() => setBgStyle('blur_dark')}
                                    className={`flex flex-col gap-1 rounded-xl border p-3 text-left transition-all ${
                                        bgStyle === 'blur_dark'
                                            ? 'border-[#FF6A55] bg-[#FF6A55]/10 text-white'
                                            : 'border-white/10 bg-zinc-900/50 text-zinc-400 hover:border-white/20'
                                    }`}
                                >
                                    <span className="text-xs font-bold text-white">Blur Cinematográfico</span>
                                    <span className="text-[10.5px] leading-tight text-zinc-400">
                                        Vídeo desfocado + 30% escurecido (Padrão)
                                    </span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setBgStyle('blur_intense')}
                                    className={`flex flex-col gap-1 rounded-xl border p-3 text-left transition-all ${
                                        bgStyle === 'blur_intense'
                                            ? 'border-[#FF6A55] bg-[#FF6A55]/10 text-white'
                                            : 'border-white/10 bg-zinc-900/50 text-zinc-400 hover:border-white/20'
                                    }`}
                                >
                                    <span className="text-xs font-bold text-white">Blur Intenso</span>
                                    <span className="text-[10.5px] leading-tight text-zinc-400">
                                        Desfoque profundo no player central
                                    </span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setBgStyle('gradient_dark')}
                                    className={`flex flex-col gap-1 rounded-xl border p-3 text-left transition-all ${
                                        bgStyle === 'gradient_dark'
                                            ? 'border-[#FF6A55] bg-[#FF6A55]/10 text-white'
                                            : 'border-white/10 bg-zinc-900/50 text-zinc-400 hover:border-white/20'
                                    }`}
                                >
                                    <span className="text-xs font-bold text-white">Gradiente Dark</span>
                                    <span className="text-[10.5px] leading-tight text-zinc-400">
                                        Degradê escuro com glow do canal
                                    </span>
                                </button>
                            </div>
                        </div>

                        {/* Seção: Legendas & CTA */}
                        <div className="space-y-3 rounded-xl border border-white/5 bg-zinc-900/40 p-4">
                            <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-zinc-400 uppercase">
                                <Subtitles className="h-3.5 w-3.5 text-[#FF6A55]" />
                                Legendas e Chamada (Rodapé)
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <FieldLabel className="mb-1.5 block text-xs font-medium text-zinc-300">
                                        Cor da Legenda Dinâmica
                                    </FieldLabel>
                                    <div className="flex gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setSubtitleColor('#facc15')}
                                            className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all ${
                                                subtitleColor === '#facc15'
                                                    ? 'border-yellow-400 bg-yellow-400/10 text-yellow-400 ring-1 ring-yellow-400'
                                                    : 'border-white/10 text-zinc-400 hover:border-white/20'
                                            }`}
                                        >
                                            <div className="h-3 w-3 rounded-full bg-yellow-400" />
                                            Amarelo Ouro
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setSubtitleColor('#ffffff')}
                                            className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all ${
                                                subtitleColor === '#ffffff'
                                                    ? 'border-white bg-white/10 text-white ring-1 ring-white'
                                                    : 'border-white/10 text-zinc-400 hover:border-white/20'
                                            }`}
                                        >
                                            <div className="h-3 w-3 rounded-full bg-white" />
                                            Branco Puro
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <FieldLabel className="mb-1.5 block text-xs font-medium text-zinc-300">
                                        Texto do Botão / CTA
                                    </FieldLabel>
                                    <Input
                                        value={ctaText}
                                        onChange={(e) => setCtaText(e.target.value)}
                                        placeholder="Ex: INSCREVA-SE NO CANAL"
                                        className="border-white/10 bg-zinc-900/80 text-xs text-white"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* PREVIEW DO CELULAR / DESKTOP EM TEMPO REAL (Lado Direito - 5 cols) */}
                    <div className="relative flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-zinc-900/30 p-5 md:col-span-5">
                        {/* Seletor de visualização */}
                        <div className="mb-4 flex items-center rounded-xl border border-white/10 bg-zinc-900 p-1">
                            <button
                                type="button"
                                onClick={() => setDevice('mobile')}
                                className={`flex items-center gap-1.5 rounded-lg px-3 py-1 text-xs font-semibold transition-all ${
                                    device === 'mobile'
                                        ? 'border border-zinc-700 bg-zinc-800 text-white shadow-sm'
                                        : 'text-zinc-400 hover:text-white'
                                }`}
                            >
                                <Smartphone className="h-3.5 w-3.5" />
                                <span>Celular (9:16)</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => setDevice('desktop')}
                                className={`flex items-center gap-1.5 rounded-lg px-3 py-1 text-xs font-semibold transition-all ${
                                    device === 'desktop'
                                        ? 'border border-zinc-700 bg-zinc-800 text-white shadow-sm'
                                        : 'text-zinc-400 hover:text-white'
                                }`}
                            >
                                <Monitor className="h-3.5 w-3.5" />
                                <span>Desktop (16:9)</span>
                            </button>
                        </div>

                        {device === 'mobile' ? (
                            /* MOCKUP DO CELULAR */
                            <div
                                className="relative flex h-[460px] w-[260px] flex-col overflow-hidden rounded-[36px] border-4 border-zinc-800 p-2.5 shadow-2xl select-none"
                                style={{
                                    backgroundColor: '#090a0f',
                                    boxShadow: `0 20px 50px rgba(0,0,0,0.8), 0 0 35px ${accentColor}25`,
                                }}
                            >
                                {/* Câmera / Notch do Celular */}
                                <div className="absolute top-3 left-1/2 z-30 h-3.5 w-16 -translate-x-1/2 rounded-full bg-zinc-800" />

                                {/* Fundo Simulado (Blur / Gradiente) */}
                                <div className="absolute inset-0 z-0 overflow-hidden">
                                    {bgStyle === 'gradient_dark' ? (
                                        <div
                                            className="h-full w-full"
                                            style={{
                                                background: `radial-gradient(circle at 50% 30%, ${accentColor}35 0%, #0d1117 70%)`,
                                            }}
                                        />
                                    ) : (
                                        <div className="relative h-full w-full">
                                            <div
                                                className="absolute inset-0 scale-125 bg-cover bg-center"
                                                style={{
                                                    backgroundImage:
                                                        'url("https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?q=80&w=800&auto=format&fit=crop")',
                                                    filter:
                                                        bgStyle === 'blur_intense'
                                                            ? 'blur(16px) brightness(0.6)'
                                                            : 'blur(10px) brightness(0.55)',
                                                }}
                                            />
                                            <div
                                                className="absolute inset-0"
                                                style={{
                                                    background: `linear-gradient(to bottom, rgba(10,12,16,0.7) 0%, transparent 35%, transparent 65%, rgba(10,12,16,0.9) 100%)`,
                                                }}
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Conteúdo Sobreposto (9:16 Canvas) */}
                                <div className="relative z-10 flex h-full w-full flex-col justify-between px-1 pt-6 pb-2">
                                    {/* Logo Oficial do Canal no Canto Superior Direito */}
                                    {channel.hasWatermark && channel.watermarkUrl && (
                                        <div className="pointer-events-none absolute top-2 right-2 z-30 drop-shadow-md">
                                            <img
                                                src={channel.watermarkUrl}
                                                alt={channel.name}
                                                className="h-7 w-7 rounded-full border border-white/40 bg-black/40 object-cover p-0.5 shadow-lg backdrop-blur-xs"
                                            />
                                        </div>
                                    )}

                                    {/* TOPO: Logo e Título */}
                                    <div className="flex flex-col items-center gap-1.5 px-2 text-center">
                                        <div
                                            className="flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[9px] font-extrabold tracking-wider text-white uppercase shadow-sm"
                                            style={{ backgroundColor: accentColor }}
                                        >
                                            {headerBadge || 'AO VIVO'}
                                        </div>
                                        <div className="text-[13px] leading-tight font-black tracking-tight text-white uppercase drop-shadow-md">
                                            {headerTitle || channel.name}
                                        </div>
                                    </div>

                                    {/* CENTRO: Player 16:9 Centralizado */}
                                    <div className="my-auto w-full px-1">
                                        <div
                                            className="group relative flex aspect-video w-full items-center justify-center overflow-hidden rounded-xl border-2 border-white/20 shadow-2xl"
                                            style={{
                                                boxShadow: `0 8px 30px rgba(0,0,0,0.8), 0 0 20px ${accentColor}30`,
                                            }}
                                        >
                                            <img
                                                src="https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?q=80&w=800&auto=format&fit=crop"
                                                alt="Player 16:9"
                                                className="h-full w-full object-cover"
                                            />
                                            <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                                                <div
                                                    className="flex h-9 w-9 items-center justify-center rounded-full text-white shadow-lg backdrop-blur-md"
                                                    style={{ backgroundColor: `${accentColor}DD` }}
                                                >
                                                    <Play className="ml-0.5 h-4 w-4 fill-white" />
                                                </div>
                                            </div>
                                            <div className="absolute right-2 bottom-1.5 rounded bg-black/70 px-1.5 py-0.5 font-mono text-[9px] text-zinc-200">
                                                05:42
                                            </div>
                                        </div>
                                    </div>

                                    {/* RODAPÉ: Legendas e Chamada */}
                                    <div className="flex flex-col items-center gap-2.5 px-2 pb-1 text-center">
                                        {/* Caixa de Legenda */}
                                        <div className="max-w-[220px] rounded-lg border border-white/10 bg-black/80 px-3 py-1.5 backdrop-blur-sm">
                                            <p
                                                className="text-[10px] leading-tight font-extrabold drop-shadow-[0_1px_2px_rgba(0,0,0,1)]"
                                                style={{ color: subtitleColor }}
                                            >
                                                "Este é o momento mais importante do debate de hoje!"
                                            </p>
                                        </div>

                                        {/* Botão de Inscrição */}
                                        <div
                                            className="w-full rounded-xl py-1.5 text-center text-[10px] font-extrabold tracking-wider text-white uppercase shadow-lg transition-transform"
                                            style={{
                                                backgroundColor: accentColor,
                                                boxShadow: `0 4px 15px ${accentColor}40`,
                                            }}
                                        >
                                            {ctaText || 'INSCREVA-SE'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            /* MOCKUP DESKTOP (16:9 NO YOUTUBE) */
                            <div className="w-full max-w-sm overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 shadow-2xl">
                                <div className="relative flex aspect-video items-center justify-center bg-black">
                                    <img
                                        src="https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?q=80&w=800&auto=format&fit=crop"
                                        alt="Player 16:9"
                                        className="h-full w-full object-cover"
                                    />
                                    <div
                                        className="absolute top-2 left-2 rounded px-2 py-0.5 text-[9px] font-bold text-white uppercase shadow-md"
                                        style={{ backgroundColor: accentColor }}
                                    >
                                        {headerBadge}
                                    </div>
                                    <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                                        <div
                                            className="flex h-10 w-10 items-center justify-center rounded-full text-white shadow-xl"
                                            style={{ backgroundColor: accentColor }}
                                        >
                                            <Play className="ml-0.5 h-4 w-4 fill-white" />
                                        </div>
                                    </div>
                                    <span className="absolute right-2 bottom-2 rounded bg-black/80 px-1.5 py-0.5 font-mono text-[9px] text-white">
                                        12:30
                                    </span>
                                </div>
                                <div className="flex flex-col gap-2 p-3">
                                    <h5 className="line-clamp-2 text-xs font-bold text-white">
                                        {headerTitle} — DEBATE COMPLETO E ANÁLISE DOS PRINCIPAIS FATOS
                                    </h5>
                                    <div className="flex items-center justify-between border-t border-zinc-800 pt-1">
                                        <div className="flex items-center gap-1.5">
                                            <div
                                                className="flex h-5 w-5 items-center justify-center rounded-full text-[9px] font-black text-white"
                                                style={{ backgroundColor: accentColor }}
                                            >
                                                {channel.name.charAt(0).toUpperCase()}
                                            </div>
                                            <span className="text-[11px] font-semibold text-zinc-300">
                                                {channel.name}
                                            </span>
                                        </div>
                                        <span className="rounded-full bg-white px-2 py-0.5 text-[9px] font-bold text-black">
                                            {ctaText.includes('INSCREV') ? 'Inscrever-se' : ctaText}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <p className="mt-3 text-center text-[10px] text-zinc-500">
                            Renderizado via FFmpeg em 1080x1920 (Full HD) no celular e 16:9 com capa no desktop.
                        </p>
                    </div>
                </div>

                {/* Footer Actions */}
                <DialogFooter className="flex items-center justify-between border-t border-white/10 bg-zinc-900/50 p-4 sm:justify-between">
                    <div className="text-xs text-zinc-400">
                        Canal ativo: <strong className="text-white">{channel.name}</strong> ({channel.slug})
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="ghost"
                            onClick={() => onOpenChange(false)}
                            className="text-zinc-400 hover:text-white"
                        >
                            Cancelar
                        </Button>
                        <Button
                            onClick={handleSave}
                            disabled={saving}
                            className="flex items-center gap-2 bg-[#FF6A55] px-5 font-bold text-white hover:bg-[#FF6A55]/90"
                        >
                            <Save className="h-4 w-4" />
                            {saving ? 'Salvando...' : 'Salvar Template do Canal'}
                        </Button>
                    </div>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
