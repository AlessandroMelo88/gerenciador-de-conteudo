import { useState, useEffect } from 'react';
import { Head, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';
import { Play, Pause, Sparkles, UploadCloud, Download, Film, Video, AudioWaveform } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { AppShell } from '@/layouts/app-shell';

type PageProps = {
    auth: { user: { name: string; email: string } | null };
    flash: { success: string | null; error: string | null };
};

export default function ProcessVideo() {
    const { props } = usePage<PageProps>();
    const { auth, flash } = props;
    const { data, setData, post, processing, reset } = useForm({
        format: 'curto',
        urls: '',
    });

    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState('0:12');

    useEffect(() => {
        if (flash?.success) toast.success(flash.success);
        if (flash?.error) toast.error(flash.error, { style: { whiteSpace: 'pre-line' } });
    }, [flash?.success, flash?.error]);

    function submit(e: React.FormEvent) {
        e.preventDefault();
        post('/painel/processar-video', {
            preserveScroll: true,
            onSuccess: () => {
                reset('urls');
                toast.success('Vídeo(s) enfileirado(s) para processamento!');
            },
        });
    }

    return (
        <>
            <Head title="Processar Vídeo" />
            <AppShell
                title="Processar Vídeo"
                user={auth.user}
                description="Enfileire URLs do YouTube ou envie arquivos locais para o pipeline de IA (download → transcrição Whisper → seleção LLaMA → corte FFmpeg)."
            >
                <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
                    {/* FORMULÁRIO DE ENFILEIRAMENTO */}
                    <div className="rounded-2xl border border-border bg-card p-6 flex flex-col gap-5 shadow-xs">
                        <h2 className="font-display text-base font-bold text-foreground flex items-center gap-2">
                            <Film className="w-4 h-4 text-[#FF6A55]" />
                            Configurações de Processamento
                        </h2>

                        <form onSubmit={submit} className="flex flex-col gap-5">
                            {/* Seleção de Formato em Cards */}
                            <div className="flex flex-col gap-2">
                                <label className="text-xs font-semibold text-foreground">Formato do Corte</label>
                                <div className="grid grid-cols-2 gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setData('format', 'curto')}
                                        className={`p-4 rounded-xl border text-left flex flex-col gap-1 transition-all ${
                                            data.format === 'curto'
                                                ? 'border-primary bg-primary/10 shadow-xs'
                                                : 'border-border bg-muted/30 hover:border-border/80'
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="font-bold text-sm text-foreground">Curto (9:16)</span>
                                            <span className="text-[10.5px] font-mono px-2 py-0.5 rounded bg-black/10 dark:bg-white/10">
                                                ≤ 60s
                                            </span>
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Shorts vertical com legendas automáticas e marca d'água.
                                        </p>
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() => setData('format', 'longo')}
                                        className={`p-4 rounded-xl border text-left flex flex-col gap-1 transition-all ${
                                            data.format === 'longo'
                                                ? 'border-primary bg-primary/10 shadow-xs'
                                                : 'border-border bg-muted/30 hover:border-border/80'
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="font-bold text-sm text-foreground">Longo (16:9)</span>
                                            <span className="text-[10.5px] font-mono px-2 py-0.5 rounded bg-black/10 dark:bg-white/10">
                                                12–25 min
                                            </span>
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Vídeo completo de debate / podcast mantendo o enquadramento original.
                                        </p>
                                    </button>
                                </div>
                            </div>

                            {/* URLs do YouTube */}
                            <div className="flex flex-col gap-2">
                                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                                    <Video className="w-3.5 h-3.5 text-red-500" />
                                    URLs do YouTube (uma por linha)
                                </label>
                                <textarea
                                    value={data.urls}
                                    onChange={(e) => setData('urls', e.target.value)}
                                    rows={4}
                                    placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/..."
                                    className="w-full rounded-xl border border-border bg-muted/20 p-3 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                                    required
                                />
                            </div>

                            {/* Dropzone de Arquivos Locais */}
                            <div className="rounded-xl border-2 border-dashed border-border p-5 text-center flex flex-col items-center gap-2 hover:border-primary/50 transition-colors cursor-pointer bg-muted/10">
                                <UploadCloud className="w-6 h-6 text-muted-foreground" />
                                <div className="text-xs font-medium text-foreground">
                                    Ou arraste um vídeo MP4/MKV aqui
                                </div>
                                <span className="text-[11px] text-muted-foreground">
                                    Processamento direto no servidor
                                </span>
                            </div>

                            {/* Botões de Ação */}
                            <div className="flex items-center gap-3 pt-2">
                                <Button
                                    type="submit"
                                    disabled={processing}
                                    className="flex-1 shadow-sm hover:brightness-105"
                                    style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)', color: '#fff' }}
                                >
                                    <Sparkles className="w-4 h-4 mr-1.5" /> Enfileirar no Pipeline
                                </Button>
                                <Button type="button" variant="outline" className="text-xs">
                                    Só transcrever (local)
                                </Button>
                            </div>
                        </form>
                    </div>

                    {/* WAVEFORM & TRANSCRIÇÃO INTERATIVA */}
                    <div className="rounded-2xl border border-border bg-card p-6 flex flex-col gap-5 shadow-xs">
                        <div className="flex items-center justify-between">
                            <h2 className="font-display text-base font-bold text-foreground flex items-center gap-2">
                                <AudioWaveform className="w-4 h-4 text-emerald-500" />
                                Transcrição & Waveform
                            </h2>
                            <span className="font-mono text-xs text-muted-foreground">{currentTime} / 0:45</span>
                        </div>

                        {/* Player de Onda de Áudio Simulado */}
                        <div className="rounded-xl border border-border bg-muted/40 p-4 flex flex-col gap-3">
                            <div className="flex items-center gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsPlaying(!isPlaying)}
                                    className="w-10 h-10 rounded-full bg-primary text-primary-foreground grid place-items-center shrink-0 shadow-sm hover:scale-105 transition-transform"
                                >
                                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                                </button>
                                <div className="flex-1 flex items-center gap-1 h-10 overflow-hidden px-2">
                                    {Array.from({ length: 36 }).map((_, i) => {
                                        const heights = [30, 60, 90, 45, 80, 100, 70, 40, 65, 85, 95, 50, 75, 80, 60, 40, 85, 100, 70, 50, 65, 80, 95, 45, 60, 75, 90, 55, 40, 70, 85, 60, 45, 80, 90, 35];
                                        const isHighlighted = i >= 8 && i <= 22;
                                        return (
                                            <div
                                                key={i}
                                                className={`flex-1 rounded-full transition-all ${
                                                    isHighlighted
                                                        ? 'bg-primary'
                                                        : 'bg-muted-foreground/30'
                                                }`}
                                                style={{ height: `${heights[i % heights.length]}%` }}
                                            />
                                        );
                                    })}
                                </div>
                            </div>
                            <div className="flex items-center justify-between text-[11px] text-muted-foreground font-mono">
                                <span>0:00</span>
                                <span className="text-primary font-semibold">✨ Trecho de Ouro IA: 0:12 – 0:38</span>
                                <span>0:45</span>
                            </div>
                        </div>

                        {/* Stream de Legendas Transcritas */}
                        <div className="flex flex-col gap-2 flex-1">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-semibold text-foreground">Segmentos Transcritos</span>
                                <Button variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground hover:text-foreground">
                                    <Download className="w-3.5 h-3.5 mr-1" /> Baixar .srt
                                </Button>
                            </div>

                            <div className="rounded-xl border border-border bg-muted/20 p-3 space-y-2 max-h-[220px] overflow-y-auto text-xs font-mono">
                                <div className="p-2 rounded-lg bg-card border border-border/80">
                                    <span className="text-muted-foreground text-[10.5px]">00:00 → 00:08</span>
                                    <p className="text-foreground mt-0.5">"Nós precisamos entender o impacto dessa nova decisão jurídica no cenário eleitoral."</p>
                                </div>
                                <div className="p-2 rounded-lg bg-primary/10 border border-primary/30">
                                    <span className="text-primary text-[10.5px] font-bold">00:12 → 00:24 (Selecionado)</span>
                                    <p className="text-foreground font-semibold mt-0.5">"O STF tomou uma postura que gerou um desequilíbrio sem precedentes nas redes sociais."</p>
                                </div>
                                <div className="p-2 rounded-lg bg-card border border-border/80">
                                    <span className="text-muted-foreground text-[10.5px]">00:25 → 00:38</span>
                                    <p className="text-foreground mt-0.5">"E isso afeta diretamente quem depende do engajamento orgânico para se comunicar com os eleitores."</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </AppShell>
        </>
    );
}
