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
    Tv, 
    Check, 
    Save,
    Flame,
    Trophy,
    Landmark,
    Mic,
    Smartphone,
    Monitor,
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
    if (!channel) return null;

    const isPolitica = (channel.niche || '').toLowerCase().includes('pol');
    const isFutebol = (channel.niche || '').toLowerCase().includes('fut');

    // Defaults baseados no nicho
    const defaultTitle = channel.name.toUpperCase();
    const defaultBadge = isPolitica ? '🔴 DEBATE AO VIVO' : (isFutebol ? '⚽ LANCE DECISIVO' : '🎙️ CORTES EXCLUSIVOS');
    const defaultAccent = isPolitica ? '#E50914' : (isFutebol ? '#10B981' : '#8B5CF6');

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
    }, [channel, open]);

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
            }
        );
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl p-0 overflow-hidden bg-zinc-950 border border-white/10 text-zinc-100 sm:rounded-2xl max-h-[92vh] flex flex-col">
                {/* Header */}
                <DialogHeader className="p-6 border-b border-white/10 bg-zinc-900/50 flex-row items-center justify-between space-y-0">
                    <div className="flex items-center gap-3">
                        <div 
                            className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg transition-colors"
                            style={{ backgroundColor: accentColor }}
                        >
                            <Sparkles className="w-5 h-5" />
                        </div>
                        <div>
                            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
                                Estúdio de Template 9:16 — {channel.name}
                            </DialogTitle>
                            <p className="text-xs text-zinc-400 mt-0.5">
                                Configure o enquadramento vertical, títulos, cores e legendas usados nos cortes deste canal.
                            </p>
                        </div>
                    </div>
                    <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={handleResetDefaults}
                        className="text-xs text-zinc-400 hover:text-white flex items-center gap-1.5"
                    >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Padrão do Nicho
                    </Button>
                </DialogHeader>

                {/* Body: 2 Columns */}
                <div className="flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-12 gap-6 p-6">
                    {/* CONTROLES (Lado Esquerdo - 7 cols) */}
                    <div className="md:col-span-7 flex flex-col gap-5 pr-2">
                        {/* Seção: Topo */}
                        <div className="space-y-3 p-4 rounded-xl bg-zinc-900/40 border border-white/5">
                            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                                <Type className="w-3.5 h-3.5 text-[#FF6A55]" />
                                Identidade do Topo
                            </div>

                            <Field>
                                <FieldLabel className="text-xs font-medium text-zinc-300">Título Principal (Header)</FieldLabel>
                                <Input
                                    value={headerTitle}
                                    onChange={(e) => setHeaderTitle(e.target.value)}
                                    placeholder="Ex: POLÍTICA EM CORTES"
                                    className="bg-zinc-900/80 border-white/10 text-white font-semibold text-sm"
                                />
                            </Field>

                            <Field>
                                <FieldLabel className="text-xs font-medium text-zinc-300">Selo / Badge Superior</FieldLabel>
                                <Input
                                    value={headerBadge}
                                    onChange={(e) => setHeaderBadge(e.target.value)}
                                    placeholder="Ex: 🔴 DEBATE AO VIVO"
                                    className="bg-zinc-900/80 border-white/10 text-white text-xs"
                                />
                            </Field>
                        </div>

                        {/* Seção: Paleta e Cores */}
                        <div className="space-y-3 p-4 rounded-xl bg-zinc-900/40 border border-white/5">
                            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                                <Palette className="w-3.5 h-3.5 text-[#FF6A55]" />
                                Cor do Tema & Destaque
                            </div>

                            <div className="flex flex-wrap gap-2 pt-1">
                                {COLOR_PRESETS.map((preset) => (
                                    <button
                                        key={preset.value}
                                        type="button"
                                        onClick={() => setAccentColor(preset.value)}
                                        className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 border transition-all ${
                                            accentColor.toLowerCase() === preset.value.toLowerCase()
                                                ? 'border-white text-white shadow-md bg-white/10 scale-105'
                                                : 'border-white/10 text-zinc-400 hover:border-white/30 bg-zinc-900/50'
                                        }`}
                                    >
                                        <div 
                                            className="w-3 h-3 rounded-full border border-black/30"
                                            style={{ backgroundColor: preset.value }}
                                        />
                                        {preset.label}
                                    </button>
                                ))}
                            </div>

                            <div className="flex items-center gap-3 pt-2">
                                <span className="text-xs text-zinc-400">Cor Personalizada:</span>
                                <div className="flex items-center gap-2 bg-zinc-900/80 px-2.5 py-1 rounded-lg border border-white/10">
                                    <input 
                                        type="color" 
                                        value={accentColor} 
                                        onChange={(e) => setAccentColor(e.target.value)}
                                        className="w-6 h-6 rounded cursor-pointer bg-transparent border-0" 
                                    />
                                    <span className="font-mono text-xs uppercase text-zinc-200">{accentColor}</span>
                                </div>
                            </div>
                        </div>

                        {/* Seção: Fundo & Blur */}
                        <div className="space-y-3 p-4 rounded-xl bg-zinc-900/40 border border-white/5">
                            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                                <Layers className="w-3.5 h-3.5 text-[#FF6A55]" />
                                Fundo de Enquadramento (FFmpeg)
                            </div>

                            <div className="grid grid-cols-3 gap-2">
                                <button
                                    type="button"
                                    onClick={() => setBgStyle('blur_dark')}
                                    className={`p-3 rounded-xl border text-left flex flex-col gap-1 transition-all ${
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
                                    className={`p-3 rounded-xl border text-left flex flex-col gap-1 transition-all ${
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
                                    className={`p-3 rounded-xl border text-left flex flex-col gap-1 transition-all ${
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
                        <div className="space-y-3 p-4 rounded-xl bg-zinc-900/40 border border-white/5">
                            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                                <Subtitles className="w-3.5 h-3.5 text-[#FF6A55]" />
                                Legendas e Chamada (Rodapé)
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <FieldLabel className="text-xs font-medium text-zinc-300 mb-1.5 block">Cor da Legenda Dinâmica</FieldLabel>
                                    <div className="flex gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setSubtitleColor('#facc15')}
                                            className={`flex-1 py-1.5 px-3 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                                                subtitleColor === '#facc15'
                                                    ? 'border-yellow-400 bg-yellow-400/10 text-yellow-400 ring-1 ring-yellow-400'
                                                    : 'border-white/10 text-zinc-400 hover:border-white/20'
                                            }`}
                                        >
                                            <div className="w-3 h-3 rounded-full bg-yellow-400" />
                                            Amarelo Ouro
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setSubtitleColor('#ffffff')}
                                            className={`flex-1 py-1.5 px-3 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                                                subtitleColor === '#ffffff'
                                                    ? 'border-white bg-white/10 text-white ring-1 ring-white'
                                                    : 'border-white/10 text-zinc-400 hover:border-white/20'
                                            }`}
                                        >
                                            <div className="w-3 h-3 rounded-full bg-white" />
                                            Branco Puro
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <FieldLabel className="text-xs font-medium text-zinc-300 mb-1.5 block">Texto do Botão / CTA</FieldLabel>
                                    <Input
                                        value={ctaText}
                                        onChange={(e) => setCtaText(e.target.value)}
                                        placeholder="Ex: INSCREVA-SE NO CANAL"
                                        className="bg-zinc-900/80 border-white/10 text-white text-xs"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* PREVIEW DO CELULAR / DESKTOP EM TEMPO REAL (Lado Direito - 5 cols) */}
                    <div className="md:col-span-5 flex flex-col items-center justify-center bg-zinc-900/30 rounded-2xl p-5 border border-white/5 relative">
                        {/* Seletor de visualização */}
                        <div className="flex items-center p-1 rounded-xl bg-zinc-900 border border-white/10 mb-4">
                            <button
                                type="button"
                                onClick={() => setDevice('mobile')}
                                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                                    device === 'mobile'
                                        ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700'
                                        : 'text-zinc-400 hover:text-white'
                                }`}
                            >
                                <Smartphone className="w-3.5 h-3.5" />
                                <span>Celular (9:16)</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => setDevice('desktop')}
                                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                                    device === 'desktop'
                                        ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700'
                                        : 'text-zinc-400 hover:text-white'
                                }`}
                            >
                                <Monitor className="w-3.5 h-3.5" />
                                <span>Desktop (16:9)</span>
                            </button>
                        </div>

                        {device === 'mobile' ? (
                            /* MOCKUP DO CELULAR */
                            <div 
                                className="relative w-[260px] h-[460px] rounded-[36px] p-2.5 shadow-2xl border-4 border-zinc-800 flex flex-col overflow-hidden select-none"
                                style={{
                                    backgroundColor: '#090a0f',
                                    boxShadow: `0 20px 50px rgba(0,0,0,0.8), 0 0 35px ${accentColor}25`,
                                }}
                            >
                                {/* Câmera / Notch do Celular */}
                                <div className="absolute top-3 left-1/2 -translate-x-1/2 w-16 h-3.5 bg-zinc-800 rounded-full z-30" />

                                {/* Fundo Simulado (Blur / Gradiente) */}
                                <div className="absolute inset-0 z-0 overflow-hidden">
                                    {bgStyle === 'gradient_dark' ? (
                                        <div 
                                            className="w-full h-full"
                                            style={{
                                                background: `radial-gradient(circle at 50% 30%, ${accentColor}35 0%, #0d1117 70%)`
                                            }}
                                        />
                                    ) : (
                                        <div className="w-full h-full relative">
                                            <div 
                                                className="absolute inset-0 bg-cover bg-center scale-125"
                                                style={{
                                                    backgroundImage: 'url("https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?q=80&w=800&auto=format&fit=crop")',
                                                    filter: bgStyle === 'blur_intense' ? 'blur(16px) brightness(0.6)' : 'blur(10px) brightness(0.55)',
                                                }}
                                            />
                                            <div 
                                                className="absolute inset-0"
                                                style={{
                                                    background: `linear-gradient(to bottom, rgba(10,12,16,0.7) 0%, transparent 35%, transparent 65%, rgba(10,12,16,0.9) 100%)`
                                                }}
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Conteúdo Sobreposto (9:16 Canvas) */}
                                <div className="relative z-10 w-full h-full flex flex-col justify-between pt-6 pb-2 px-1">
                                    {/* TOPO: Logo e Título */}
                                    <div className="flex flex-col items-center text-center gap-1.5 px-2">
                                        <div 
                                            className="px-2.5 py-0.5 rounded-full text-[9px] font-extrabold uppercase tracking-wider text-white shadow-sm flex items-center gap-1"
                                            style={{ backgroundColor: accentColor }}
                                        >
                                            {headerBadge || 'AO VIVO'}
                                        </div>
                                        <div className="text-[13px] font-black uppercase tracking-tight text-white leading-tight drop-shadow-md">
                                            {headerTitle || channel.name}
                                        </div>
                                    </div>

                                    {/* CENTRO: Player 16:9 Centralizado */}
                                    <div className="w-full my-auto px-1">
                                        <div 
                                            className="w-full aspect-video rounded-xl overflow-hidden relative border-2 border-white/20 shadow-2xl flex items-center justify-center group"
                                            style={{
                                                boxShadow: `0 8px 30px rgba(0,0,0,0.8), 0 0 20px ${accentColor}30`,
                                            }}
                                        >
                                            <img 
                                                src="https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?q=80&w=800&auto=format&fit=crop" 
                                                alt="Player 16:9" 
                                                className="w-full h-full object-cover"
                                            />
                                            <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
                                                <div 
                                                    className="w-9 h-9 rounded-full flex items-center justify-center text-white shadow-lg backdrop-blur-md"
                                                    style={{ backgroundColor: `${accentColor}DD` }}
                                                >
                                                    <Play className="w-4 h-4 ml-0.5 fill-white" />
                                                </div>
                                            </div>
                                            <div className="absolute bottom-1.5 right-2 bg-black/70 px-1.5 py-0.5 rounded text-[9px] font-mono text-zinc-200">
                                                05:42
                                            </div>
                                        </div>
                                    </div>

                                    {/* RODAPÉ: Legendas e Chamada */}
                                    <div className="flex flex-col items-center text-center gap-2.5 px-2 pb-1">
                                        {/* Caixa de Legenda */}
                                        <div className="bg-black/80 px-3 py-1.5 rounded-lg border border-white/10 backdrop-blur-sm max-w-[220px]">
                                            <p 
                                                className="text-[10px] font-extrabold leading-tight drop-shadow-[0_1px_2px_rgba(0,0,0,1)]"
                                                style={{ color: subtitleColor }}
                                            >
                                                "Este é o momento mais importante do debate de hoje!"
                                            </p>
                                        </div>

                                        {/* Botão de Inscrição */}
                                        <div 
                                            className="w-full py-1.5 rounded-xl text-[10px] font-extrabold text-white uppercase tracking-wider text-center shadow-lg transition-transform"
                                            style={{ 
                                                backgroundColor: accentColor,
                                                boxShadow: `0 4px 15px ${accentColor}40`
                                            }}
                                        >
                                            {ctaText || 'INSCREVA-SE'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            /* MOCKUP DESKTOP (16:9 NO YOUTUBE) */
                            <div className="w-full max-w-sm rounded-xl border border-zinc-800 bg-zinc-950 overflow-hidden shadow-2xl">
                                <div className="relative aspect-video bg-black flex items-center justify-center">
                                    <img 
                                        src="https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?q=80&w=800&auto=format&fit=crop" 
                                        alt="Player 16:9" 
                                        className="w-full h-full object-cover"
                                    />
                                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded text-[9px] font-bold text-white shadow-md uppercase" style={{ backgroundColor: accentColor }}>
                                        {headerBadge}
                                    </div>
                                    <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
                                        <div className="w-10 h-10 rounded-full flex items-center justify-center text-white shadow-xl" style={{ backgroundColor: accentColor }}>
                                            <Play className="w-4 h-4 ml-0.5 fill-white" />
                                        </div>
                                    </div>
                                    <span className="absolute right-2 bottom-2 bg-black/80 text-[9px] font-mono text-white px-1.5 py-0.5 rounded">
                                        12:30
                                    </span>
                                </div>
                                <div className="p-3 flex flex-col gap-2">
                                    <h5 className="font-bold text-xs text-white line-clamp-2">
                                        {headerTitle} — DEBATE COMPLETO E ANÁLISE DOS PRINCIPAIS FATOS
                                    </h5>
                                    <div className="flex items-center justify-between pt-1 border-t border-zinc-800">
                                        <div className="flex items-center gap-1.5">
                                            <div className="w-5 h-5 rounded-full flex items-center justify-center font-black text-[9px] text-white" style={{ backgroundColor: accentColor }}>
                                                {channel.name.charAt(0).toUpperCase()}
                                            </div>
                                            <span className="text-[11px] font-semibold text-zinc-300">{channel.name}</span>
                                        </div>
                                        <span className="px-2 py-0.5 rounded-full text-[9px] font-bold text-black bg-white">
                                            {ctaText.includes('INSCREV') ? 'Inscrever-se' : ctaText}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <p className="text-[10px] text-zinc-500 mt-3 text-center">
                            Renderizado via FFmpeg em 1080x1920 (Full HD) no celular e 16:9 com thumbnail no desktop.
                        </p>
                    </div>
                </div>

                {/* Footer Actions */}
                <DialogFooter className="p-4 border-t border-white/10 bg-zinc-900/50 flex items-center justify-between sm:justify-between">
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
                            className="bg-[#FF6A55] hover:bg-[#FF6A55]/90 text-white font-bold px-5 flex items-center gap-2"
                        >
                            <Save className="w-4 h-4" />
                            {saving ? 'Salvando...' : 'Salvar Template do Canal'}
                        </Button>
                    </div>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
