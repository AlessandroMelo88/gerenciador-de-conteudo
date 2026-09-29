import { useState, useEffect } from 'react';
import { Head, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';
import { Sparkles, UploadCloud, Download, Film, AudioWaveform, Pause, Play } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { AppShell } from '@/layouts/app-shell';

type PageProps = {
    auth?: { user: { name: string; email: string } | null };
    flash?: { success: string | null; error: string | null };
};

export default function ProcessVideo() {
    const { props } = usePage<PageProps>();
    const auth = props?.auth;
    const flash = props?.flash;
    const { data, setData, post, processing, reset } = useForm({
        format: 'curto',
        urls: '',
    });

    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime] = useState('0:12');

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
                user={auth?.user ?? null}
                description="Enfileira URLs ou arquivos na fila normal do pipeline."
            >
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                    {/* FORMULÁRIO DE ENFILEIRAMENTO */}
                    <div className="flex flex-col gap-5 rounded-3xl border border-border bg-card p-6 shadow-xs">
                        <div className="flex items-center gap-1.5 text-[11px] font-bold tracking-wider text-muted-foreground uppercase">
                            <Film className="h-3.5 w-3.5 text-[#FF6A55]" /> FONTE
                        </div>

                        <form onSubmit={submit} className="flex flex-col gap-5">
                            {/* Seleção de Formato em Cards conforme Print 5 */}
                            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                <button
                                    type="button"
                                    onClick={() => setData('format', 'curto')}
                                    className={`flex items-start gap-3 rounded-2xl border p-4 text-left transition-all ${
                                        data.format === 'curto'
                                            ? 'border-[#FF6A55] bg-[#FF6A55]/5 ring-1 ring-[#FF6A55]'
                                            : 'border-border bg-card hover:border-border/80'
                                    }`}
                                >
                                    <div
                                        className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
                                            data.format === 'curto' ? 'border-[#FF6A55]' : 'border-muted-foreground'
                                        }`}
                                    >
                                        {data.format === 'curto' && (
                                            <div className="h-2 w-2 rounded-full bg-[#FF6A55]" />
                                        )}
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-foreground">Curto</span>
                                        <p className="mt-0.5 text-xs text-muted-foreground">
                                            Shorts — vários momentos de 15s a 3min, vertical
                                        </p>
                                    </div>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setData('format', 'longo')}
                                    className={`flex items-start gap-3 rounded-2xl border p-4 text-left transition-all ${
                                        data.format === 'longo'
                                            ? 'border-[#FF6A55] bg-[#FF6A55]/5 ring-1 ring-[#FF6A55]'
                                            : 'border-border bg-card hover:border-border/80'
                                    }`}
                                >
                                    <div
                                        className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
                                            data.format === 'longo' ? 'border-[#FF6A55]' : 'border-muted-foreground'
                                        }`}
                                    >
                                        {data.format === 'longo' && (
                                            <div className="h-2 w-2 rounded-full bg-[#FF6A55]" />
                                        )}
                                    </div>
                                    <div className="flex flex-1 flex-col">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-bold text-foreground">Longo</span>
                                            <span className="rounded bg-amber-500/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-amber-500">
                                                Enquadramento 9:16
                                            </span>
                                        </div>
                                        <p className="mt-0.5 text-xs text-muted-foreground">
                                            Segmento longo (10–20min) enquadrado em vertical 9:16 com blur
                                        </p>
                                    </div>
                                </button>
                            </div>

                            {/* URLs do YouTube */}
                            <div className="flex flex-col gap-2">
                                <label htmlFor="youtube-urls" className="text-xs font-semibold text-foreground">
                                    URLs do YouTube (uma por linha)
                                </label>
                                <textarea
                                    id="youtube-urls"
                                    value={data.urls}
                                    onChange={(e) => setData('urls', e.target.value)}
                                    rows={4}
                                    placeholder="https://www.youtube.com/watch?v=...&#10;https://www.youtube.com/watch?v=..."
                                    className="w-full rounded-2xl border border-border bg-muted/10 p-3.5 font-mono text-xs text-foreground focus:ring-1 focus:ring-primary focus:outline-none"
                                    required
                                />
                            </div>

                            {/* Dropzone de Arquivos Locais conforme Print 5 */}
                            <div className="flex cursor-pointer flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-border bg-muted/5 p-6 text-center transition-colors hover:border-[#FF6A55]/50">
                                <UploadCloud className="h-7 w-7 text-muted-foreground" />
                                <div className="text-xs font-semibold text-foreground">
                                    Ou arraste um arquivo de vídeo
                                </div>
                                <span className="text-[11px] text-muted-foreground">
                                    MP4, MOV ou MKV até 4 GB — não consome cota da API
                                </span>
                            </div>

                            {/* Botões de Ação */}
                            <div className="flex items-center gap-3 pt-2">
                                <Button
                                    type="submit"
                                    disabled={processing}
                                    className="flex-1 rounded-xl shadow-sm hover:brightness-105"
                                    style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)', color: '#fff' }}
                                >
                                    <Sparkles className="mr-1.5 h-4 w-4" /> Enfileirar no Pipeline
                                </Button>
                                <Button type="button" variant="outline" className="rounded-xl text-xs">
                                    Só transcrever (local)
                                </Button>
                            </div>
                        </form>
                    </div>

                    {/* WAVEFORM & TRANSCRIÇÃO INTERATIVA */}
                    <div className="flex flex-col gap-5 rounded-3xl border border-border bg-card p-6 shadow-xs">
                        <div className="flex items-center justify-between">
                            <h2 className="flex items-center gap-2 font-display text-base font-bold text-foreground">
                                <AudioWaveform className="h-4 w-4 text-emerald-500" />
                                Transcrição & Waveform
                            </h2>
                            <span className="font-mono text-xs text-muted-foreground">{currentTime} / 0:45</span>
                        </div>

                        {/* Player de Onda de Áudio Simulado */}
                        <div className="flex flex-col gap-3 rounded-2xl border border-border bg-muted/40 p-4">
                            <div className="flex items-center gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsPlaying(!isPlaying)}
                                    className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground shadow-sm transition-transform hover:scale-105"
                                >
                                    {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="ml-0.5 h-4 w-4" />}
                                </button>
                                <div className="flex h-10 flex-1 items-center gap-1 overflow-hidden px-2">
                                    {Array.from({ length: 36 }).map((_, i) => {
                                        const heights = [
                                            30, 60, 90, 45, 80, 100, 70, 40, 65, 85, 95, 50, 75, 80, 60, 40, 85, 100,
                                            70, 50, 65, 80, 95, 45, 60, 75, 90, 55, 40, 70, 85, 60, 45, 80, 90, 35,
                                        ];
                                        const isHighlighted = i >= 8 && i <= 22;
                                        return (
                                            <div
                                                key={i}
                                                className={`flex-1 rounded-full transition-all ${
                                                    isHighlighted ? 'bg-[#FF6A55]' : 'bg-muted-foreground/30'
                                                }`}
                                                style={{ height: `${heights[i % heights.length]}%` }}
                                            />
                                        );
                                    })}
                                </div>
                            </div>
                            <div className="flex items-center justify-between font-mono text-[11px] text-muted-foreground">
                                <span>0:00</span>
                                <span className="font-semibold text-[#FF6A55]">✨ Trecho de Ouro IA: 0:12 – 0:38</span>
                                <span>0:45</span>
                            </div>
                        </div>

                        {/* Stream de Legendas Transcritas */}
                        <div className="flex flex-1 flex-col gap-2">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-semibold text-foreground">Segmentos Transcritos</span>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 text-xs text-muted-foreground hover:text-foreground"
                                >
                                    <Download className="mr-1 h-3.5 w-3.5" /> Baixar .srt
                                </Button>
                            </div>

                            <div className="max-h-[220px] space-y-2 overflow-y-auto rounded-2xl border border-border bg-muted/20 p-3.5 font-mono text-xs">
                                <div className="rounded-xl border border-border/80 bg-card p-2.5">
                                    <span className="text-[10.5px] text-muted-foreground">00:00 → 00:08</span>
                                    <p className="mt-0.5 text-foreground">
                                        "Nós precisamos entender o impacto dessa nova decisão jurídica no cenário
                                        eleitoral."
                                    </p>
                                </div>
                                <div className="rounded-xl border border-[#FF6A55]/30 bg-[#FF6A55]/10 p-2.5">
                                    <span className="text-[10.5px] font-bold text-[#FF6A55]">
                                        00:12 → 00:24 (Selecionado)
                                    </span>
                                    <p className="mt-0.5 font-semibold text-foreground">
                                        "O STF tomou uma postura que gerou um desequilíbrio sem precedentes nas redes
                                        sociais."
                                    </p>
                                </div>
                                <div className="rounded-xl border border-border/80 bg-card p-2.5">
                                    <span className="text-[10.5px] text-muted-foreground">00:25 → 00:38</span>
                                    <p className="mt-0.5 text-foreground">
                                        "E isso afeta diretamente quem depende do engajamento orgânico para se comunicar
                                        com os eleitores."
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </AppShell>
        </>
    );
}
