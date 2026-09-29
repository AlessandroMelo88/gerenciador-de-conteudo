import { useState, useEffect } from 'react';
import { X, Smartphone, Monitor, Play, CheckCircle2, ThumbsUp, Share2, Bookmark, Check, Flame } from 'lucide-react';
import type { ClipRow } from '@/types/dashboard';
import { Button } from '@/components/ui/button';

interface ClipPreviewModalProps {
    clip: ClipRow | null;
    isOpen: boolean;
    onClose: () => void;
    onApprove: (id: number) => void;
    onReject: (id: number) => void;
}

export function ClipPreviewModal({ clip, isOpen, onClose, onApprove, onReject }: ClipPreviewModalProps) {
    const [device, setDevice] = useState<'mobile' | 'desktop'>('mobile');
    const [desktopTab, setDesktopTab] = useState<'video' | 'cover'>('cover');

    useEffect(() => {
        if (clip) {
            setDevice(clip.format === 'longo' ? 'desktop' : 'mobile');
            setDesktopTab('cover');
        }
    }, [clip?.id, clip?.format]);

    if (!isOpen || !clip) return null;

    const isPol =
        (clip.niche ?? '').toLowerCase().includes('politica') ||
        (clip.destinationChannelName ?? '').toLowerCase().includes('política') ||
        (clip.destinationChannelName ?? '').toLowerCase().includes('fatos');
    const isFut =
        (clip.niche ?? '').toLowerCase().includes('futebol') ||
        (clip.destinationChannelName ?? '').toLowerCase().includes('futebol');

    const tmpl = clip.destinationTemplate || {};
    const channelName =
        clip.destinationChannelName || (isPol ? 'Fatos & Debates' : isFut ? 'Futebol em Cortes' : 'Canal de Cortes');
    const headerTitle = tmpl.headerTitle || channelName.toUpperCase();
    const headerBadge =
        tmpl.headerBadge || (isPol ? '🔴 FATOS & DEBATES' : isFut ? '⚽ LANCE DECISIVO' : '🎙️ CORTES EXCLUSIVOS');
    const accentColor = tmpl.accentColor || (isPol ? '#0284c7' : isFut ? '#10B981' : '#8B5CF6');
    const subtitleColor = tmpl.subtitleColor || '#facc15';
    const ctaText = tmpl.ctaText || 'INSCREVA-SE NO CANAL';
    const isLongo = clip.format === 'longo';
    const isCurto = !isLongo;

    return (
        <div className="fixed inset-0 z-50 flex animate-in items-center justify-center bg-black/80 p-3 backdrop-blur-md duration-200 fade-in sm:p-5">
            <div className="relative flex max-h-[94vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 text-zinc-100 shadow-2xl">
                {/* TOPO DO MODAL */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 bg-zinc-900/60 px-5 py-3.5">
                    <div className="flex min-w-0 items-center gap-3">
                        <div
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-black text-white shadow-sm"
                            style={{ backgroundColor: accentColor }}
                        >
                            {channelName.charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                            <div className="flex items-center gap-2">
                                <h3 className="truncate text-sm font-semibold text-white">{clip.title}</h3>
                                {isLongo ? (
                                    <span className="shrink-0 rounded border border-amber-500/30 bg-amber-500/20 px-2 py-0.5 text-[10.5px] font-bold text-amber-300">
                                        ✨ Longo (16:9)
                                    </span>
                                ) : (
                                    <span className="shrink-0 rounded border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-[10.5px] font-semibold text-zinc-300">
                                        📱 Curto
                                    </span>
                                )}
                            </div>
                            <p className="truncate text-xs text-zinc-400">
                                Canal: <strong className="text-zinc-200">{channelName}</strong> • Trecho:{' '}
                                <span className="font-mono text-zinc-300">{clip.trecho}</span>
                            </p>
                        </div>
                    </div>

                    {/* SELETOR DE DISPOSITIVO (CELULAR VS DESKTOP) */}
                    <div className="flex shrink-0 items-center gap-2">
                        <div className="flex items-center rounded-xl border border-zinc-800 bg-zinc-900 p-1">
                            <button
                                type="button"
                                onClick={() => setDevice('mobile')}
                                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
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
                                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                                    device === 'desktop'
                                        ? 'border border-zinc-700 bg-zinc-800 text-white shadow-sm'
                                        : 'text-zinc-400 hover:text-white'
                                }`}
                            >
                                <Monitor className="h-3.5 w-3.5" />
                                <span>Desktop / YouTube (16:9)</span>
                            </button>
                        </div>

                        <button
                            type="button"
                            onClick={onClose}
                            className="rounded-lg p-1.5 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
                            title="Fechar modal"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    </div>
                </div>

                {/* CORPO DO PREVIEW */}
                <div className="flex flex-1 flex-col items-center justify-start overflow-y-auto bg-zinc-950/70 p-3 sm:justify-center sm:p-5">
                    {device === 'mobile' ? (
                        /* SIMULADOR CELULAR SMARTPHONE 9:16 (SEM CORTES) */
                        <div className="relative flex aspect-[9/16] max-h-[72vh] w-[320px] flex-col justify-between overflow-hidden rounded-[38px] border-4 border-zinc-700 bg-zinc-900 p-3 shadow-2xl sm:w-[350px]">
                            {/* Câmera / Ilha Superior */}
                            <div className="absolute top-3.5 left-1/2 z-30 h-4 w-28 -translate-x-1/2 rounded-full bg-zinc-800 shadow-inner" />

                            {/* Canvas do Smartphone */}
                            <div className="relative z-10 flex h-full w-full flex-col items-center justify-center overflow-hidden rounded-[26px] bg-black">
                                {clip.hasVideoFile ? (
                                    /* O vídeo (seja Longo enquadrado ou Shorts) preenche 100% da tela do celular sem cortar */
                                    <video
                                        controls
                                        autoPlay
                                        playsInline
                                        className="h-full w-full rounded-[26px] object-cover"
                                        src={clip.previewUrl}
                                        poster={clip.hasThumbnailFile ? clip.thumbnailUrl : undefined}
                                    />
                                ) : (
                                    /* Mockup simulado caso o arquivo de vídeo ainda não exista em disco */
                                    <div className="relative flex h-full w-full flex-col justify-between bg-zinc-950 p-3.5">
                                        <div
                                            className="absolute inset-0 bg-cover bg-center opacity-30 blur-lg"
                                            style={{
                                                backgroundImage: clip.hasThumbnailFile
                                                    ? `url(${clip.thumbnailUrl})`
                                                    : isPol
                                                      ? 'radial-gradient(circle, #7f1d1d 0%, #090a0f 100%)'
                                                      : 'radial-gradient(circle, #064e3b 0%, #090a0f 100%)',
                                            }}
                                        />
                                        {/* Topo */}
                                        <div className="relative z-10 pt-5 text-center">
                                            <span
                                                className="rounded-full px-2.5 py-0.5 text-[10px] font-bold text-white uppercase shadow-sm"
                                                style={{ backgroundColor: accentColor }}
                                            >
                                                {headerBadge}
                                            </span>
                                            <h4 className="mt-1 text-xs font-bold text-white drop-shadow">
                                                {headerTitle}
                                            </h4>
                                        </div>
                                        {/* Centro: ocupa todo o espaço útil vertical entre topo e botão */}
                                        <div className="group relative z-10 my-2.5 flex w-full flex-1 flex-col items-center justify-center overflow-hidden rounded-2xl border-2 border-white/20 bg-black/75 shadow-2xl">
                                            {clip.hasThumbnailFile ? (
                                                <img
                                                    src={clip.thumbnailUrl}
                                                    alt={clip.title || 'Preview do vídeo'}
                                                    className="h-full w-full object-cover"
                                                />
                                            ) : (
                                                <div className="flex flex-col items-center justify-center p-4 text-center">
                                                    <div
                                                        className="mb-2 flex h-12 w-12 items-center justify-center rounded-full text-white shadow-lg backdrop-blur-md"
                                                        style={{ backgroundColor: `${accentColor}EE` }}
                                                    >
                                                        <Play className="ml-0.5 h-6 w-6 fill-white" />
                                                    </div>
                                                    <p className="line-clamp-3 px-2 text-xs leading-snug font-bold text-zinc-200">
                                                        {clip.title}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                        {/* Legenda simulada acima do botão */}
                                        <div className="relative z-10 mb-2 px-2 text-center">
                                            <span
                                                className="inline-block rounded bg-black/80 px-2.5 py-1 text-[10.5px] font-extrabold shadow drop-shadow-md"
                                                style={{ color: subtitleColor }}
                                            >
                                                "Golaço e lance espetacular!"
                                            </span>
                                        </div>
                                        {/* Rodapé: Botão Inscreva-se seguro sem sobreposição */}
                                        <div className="relative z-10 pb-2 text-center">
                                            <div
                                                className="w-full rounded-xl py-2.5 text-center text-xs font-black tracking-wider text-white uppercase shadow-lg transition-transform"
                                                style={{ backgroundColor: accentColor }}
                                            >
                                                {ctaText}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Logo do Canal no Canto Superior Direito (Celular) */}
                                {clip.destinationChannelWatermarkUrl && (
                                    <div className="pointer-events-none absolute top-4 right-4 z-30 drop-shadow-md">
                                        <img
                                            src={clip.destinationChannelWatermarkUrl}
                                            alt={channelName}
                                            className="h-8 w-8 rounded-full border border-white/40 bg-black/40 object-cover p-0.5 shadow-lg backdrop-blur-xs"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : isCurto ? (
                        /* DESKTOP: YOUTUBE SHORTS (PLAYER VERTICAL 9:16 COM BOTÕES LATERAIS DO YOUTUBE) */
                        <div className="flex items-end gap-4 py-2">
                            <div className="relative aspect-[9/16] w-[320px] overflow-hidden rounded-2xl border border-zinc-800 bg-black shadow-2xl sm:w-[350px]">
                                {clip.hasVideoFile ? (
                                    <video
                                        controls
                                        autoPlay
                                        playsInline
                                        className="h-full w-full object-cover"
                                        src={clip.previewUrl}
                                        poster={clip.hasThumbnailFile ? clip.thumbnailUrl : undefined}
                                    />
                                ) : (
                                    <div className="flex h-full w-full flex-col items-center justify-center bg-zinc-900 p-4 text-center">
                                        <Play className="mb-2 h-12 w-12 text-white" />
                                        <p className="text-xs text-white">{clip.title}</p>
                                    </div>
                                )}

                                {/* Logo no Canto Superior Direito do Shorts */}
                                {clip.destinationChannelWatermarkUrl && (
                                    <div className="pointer-events-none absolute top-3.5 right-3.5 z-30 drop-shadow-md">
                                        <img
                                            src={clip.destinationChannelWatermarkUrl}
                                            alt={channelName}
                                            className="h-8 w-8 rounded-full border border-white/40 bg-black/40 object-cover p-0.5 shadow-lg backdrop-blur-xs"
                                        />
                                    </div>
                                )}

                                {/* Overlay inferior do Shorts (Canal + Título) */}
                                <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-4">
                                    <div className="pointer-events-auto mb-1.5 flex items-center gap-2">
                                        <div
                                            className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white"
                                            style={{ backgroundColor: accentColor }}
                                        >
                                            {channelName.charAt(0).toUpperCase()}
                                        </div>
                                        <span className="text-xs font-semibold text-white">{channelName}</span>
                                        <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-black">
                                            Inscrever-se
                                        </span>
                                    </div>
                                    <p className="line-clamp-2 text-xs leading-snug font-semibold text-white drop-shadow">
                                        {clip.title}
                                    </p>
                                </div>
                            </div>

                            {/* Barra lateral direita clássica do YouTube Shorts no PC */}
                            <div className="flex flex-col items-center gap-4 pb-4">
                                <div className="flex flex-col items-center gap-1">
                                    <div className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border border-zinc-700 bg-zinc-800/90 text-white shadow transition-colors hover:bg-zinc-700">
                                        <ThumbsUp className="h-4 w-4" />
                                    </div>
                                    <span className="text-[10px] font-semibold text-zinc-400">12K</span>
                                </div>
                                <div className="flex flex-col items-center gap-1">
                                    <div className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border border-zinc-700 bg-zinc-800/90 text-white shadow transition-colors hover:bg-zinc-700">
                                        <Share2 className="h-4 w-4" />
                                    </div>
                                    <span className="text-[10px] font-semibold text-zinc-400">Compartilhar</span>
                                </div>
                                <div className="flex flex-col items-center gap-1">
                                    <div className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border border-zinc-700 bg-zinc-800/90 text-white shadow transition-colors hover:bg-zinc-700">
                                        <Bookmark className="h-4 w-4" />
                                    </div>
                                    <span className="text-[10px] font-semibold text-zinc-400">Salvar</span>
                                </div>
                            </div>
                        </div>
                    ) : (
                        /* DESKTOP: YOUTUBE VÍDEO LONGO (PLAYER WIDESCREEN 16:9 COM MOLDURA/BACKGROUND OFICIAL) */
                        <div className="flex w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 shadow-2xl">
                            {/* Barra do Navegador */}
                            <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950/90 px-4 py-2 font-mono text-xs text-zinc-400">
                                <div className="flex items-center gap-2">
                                    <div className="flex items-center gap-1.5">
                                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500/80" />
                                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-yellow-500/80" />
                                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500/80" />
                                    </div>
                                    <span className="ml-2 truncate text-zinc-500">
                                        youtube.com/watch?v={clip.id} — Vídeo Longo Oficial (16:9)
                                    </span>
                                </div>
                                <div className="flex items-center gap-1 rounded-lg border border-zinc-800 bg-zinc-900 p-1 font-sans">
                                    <button
                                        type="button"
                                        onClick={() => setDesktopTab('cover')}
                                        className={`rounded px-2.5 py-1 text-xs font-semibold transition-all ${
                                            desktopTab === 'cover'
                                                ? 'bg-amber-500 font-bold text-black shadow-sm'
                                                : 'text-zinc-400 hover:text-white'
                                        }`}
                                    >
                                        🖼️ Capa
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setDesktopTab('video')}
                                        className={`rounded px-2.5 py-1 text-xs font-semibold transition-all ${
                                            desktopTab === 'video'
                                                ? 'border border-zinc-700 bg-zinc-800 text-white shadow-sm'
                                                : 'text-zinc-400 hover:text-white'
                                        }`}
                                    >
                                        ▶️ Assistir Vídeo
                                    </button>
                                </div>
                            </div>

                            {/* Container Widescreen 16:9 */}
                            <div className="relative mx-auto flex aspect-video max-h-[48vh] w-full items-center justify-center overflow-hidden bg-zinc-950 select-none">
                                {desktopTab === 'cover' ? (
                                    /* Aba Capa: Exibe a Capa Oficial 1280x720 em tela cheia 16:9 do YouTube */
                                    <div className="relative flex h-full w-full items-center justify-center bg-zinc-950">
                                        {clip.hasThumbnailFile ? (
                                            <img
                                                src={clip.thumbnailUrl}
                                                alt="Capa Oficial 16:9 do YouTube"
                                                className="h-full w-full bg-black object-contain"
                                            />
                                        ) : (
                                            <div className="p-6 text-center">
                                                <Play className="mx-auto mb-2 h-12 w-12 text-white opacity-60" />
                                                <h4 className="px-4 text-sm font-bold text-white">{clip.title}</h4>
                                                <p className="mt-1 text-xs text-zinc-500">Capa em processamento</p>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    /* Aba Vídeo: Player de Reprodução do Vídeo Longo 16:9 */
                                    <div className="relative flex h-full w-full items-center justify-center bg-zinc-950">
                                        {clip.hasVideoFile ? (
                                            <video
                                                controls
                                                autoPlay
                                                playsInline
                                                className="h-full w-full bg-black object-contain"
                                                src={clip.previewUrl}
                                                poster={clip.hasThumbnailFile ? clip.thumbnailUrl : undefined}
                                            />
                                        ) : (
                                            <div className="relative flex h-full w-full items-center justify-center overflow-hidden bg-zinc-950">
                                                <img
                                                    src={
                                                        clip.destinationChannelBackgroundUrl ||
                                                        (isPol
                                                            ? '/storage/branding/background-fatos-e-debates.png'
                                                            : isFut
                                                              ? '/storage/branding/background-futebol-em-cortes.png'
                                                              : '/storage/branding/background-podcast-cortes.png')
                                                    }
                                                    alt={`Background ${channelName}`}
                                                    className="absolute inset-0 z-0 h-full w-full object-cover"
                                                    onError={(e) => {
                                                        e.currentTarget.style.display = 'none';
                                                    }}
                                                />
                                                <div className="relative z-10 rounded-2xl border border-white/10 bg-black/60 p-6 text-center backdrop-blur-sm">
                                                    <Play className="mx-auto mb-2 h-12 w-12 text-white opacity-75" />
                                                    <h4 className="px-4 text-sm font-bold text-white">{clip.title}</h4>
                                                    <p className="mt-1 text-xs text-zinc-400">Vídeo em processamento</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                <span className="absolute right-3 bottom-2.5 z-20 rounded border border-white/10 bg-black/80 px-2 py-0.5 font-mono text-[11px] font-semibold text-white">
                                    {clip.trecho}
                                </span>
                            </div>

                            {/* Detalhes do Vídeo no Desktop (Estilo YouTube) */}
                            <div className="flex flex-col gap-4 p-5">
                                <h2 className="text-base leading-snug font-bold text-white sm:text-lg">{clip.title}</h2>

                                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
                                    {/* Canal */}
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="flex h-10 w-10 items-center justify-center rounded-full text-sm font-black text-white shadow-md"
                                            style={{ backgroundColor: accentColor }}
                                        >
                                            {channelName.charAt(0).toUpperCase()}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-1.5 text-sm font-bold text-white">
                                                <span>{channelName}</span>
                                                <CheckCircle2 className="h-4 w-4 text-zinc-400" />
                                            </div>
                                            <span className="text-[11px] text-zinc-400">Cortes Oficiais • YouTube</span>
                                        </div>
                                        <button
                                            type="button"
                                            className="ml-2 rounded-full bg-white px-4 py-1.5 text-xs font-bold text-black transition-colors hover:bg-zinc-200"
                                        >
                                            Inscrever-se
                                        </button>
                                    </div>

                                    {/* Botões de Ação do YouTube */}
                                    <div className="flex items-center gap-1.5 text-xs text-zinc-300">
                                        <div className="flex items-center overflow-hidden rounded-full border border-zinc-700/60 bg-zinc-800">
                                            <button
                                                type="button"
                                                className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-zinc-700"
                                            >
                                                <ThumbsUp className="h-3.5 w-3.5" /> <span>Gostei</span>
                                            </button>
                                        </div>
                                        <button
                                            type="button"
                                            className="flex items-center gap-1.5 rounded-full border border-zinc-700/60 bg-zinc-800 px-3 py-1.5 hover:bg-zinc-700"
                                        >
                                            <Share2 className="h-3.5 w-3.5" /> <span>Compartilhar</span>
                                        </button>
                                        <button
                                            type="button"
                                            className="flex items-center gap-1.5 rounded-full border border-zinc-700/60 bg-zinc-800 px-3 py-1.5 hover:bg-zinc-700"
                                        >
                                            <Bookmark className="h-3.5 w-3.5" /> <span>Salvar</span>
                                        </button>
                                    </div>
                                </div>

                                {/* Caixa de Descrição do YouTube */}
                                <div className="flex flex-col gap-2 rounded-xl border border-zinc-700/50 bg-zinc-800/60 p-3.5 text-xs">
                                    <div className="flex items-center gap-2 font-semibold text-zinc-300">
                                        <span>Fila de Publicação</span>
                                        <span>•</span>
                                        <span className="font-mono font-bold text-amber-400">
                                            Score: {clip.score ?? '—'}/10
                                        </span>
                                        <span>•</span>
                                        <span className="text-zinc-400">
                                            Vídeo Fonte: {clip.sourceVideoTitle || 'Original'}
                                        </span>
                                    </div>
                                    <p className="leading-relaxed text-zinc-300">
                                        {clip.description ||
                                            `Cortes dos principais debates e momentos mais marcantes. Acompanhe os melhores trechos do canal ${channelName}.`}
                                    </p>
                                    <div className="flex flex-wrap gap-1.5 pt-1 font-mono text-[11px] text-sky-400">
                                        <span>#{clip.niche ?? 'cortes'}</span>
                                        <span>#cortes</span>
                                        <span>#youtube</span>
                                        <span>#brasil</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* RODAPÉ DO MODAL: AÇÕES RÁPIDAS */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-zinc-800 bg-zinc-900/80 px-5 py-3.5">
                    <div className="flex items-center gap-2 text-xs text-zinc-400">
                        <Flame className="h-4 w-4 text-orange-500" />
                        <span>
                            Score: <strong className="text-white">{clip.score ?? '—'}/10</strong>
                        </span>
                        <span className="text-zinc-600">|</span>
                        <span>
                            Canal Fonte: <strong className="text-zinc-300">{clip.sourceChannelName ?? '—'}</strong>
                        </span>
                    </div>

                    <div className="flex items-center gap-2">
                        <Button
                            variant="destructive"
                            size="sm"
                            className="h-8 rounded-lg text-xs"
                            onClick={() => {
                                onReject(clip.id);
                                onClose();
                            }}
                        >
                            Rejeitar
                        </Button>
                        <Button
                            variant="default"
                            size="sm"
                            className="h-8 rounded-lg bg-emerald-600 text-xs font-semibold text-white hover:bg-emerald-500"
                            onClick={() => {
                                onApprove(clip.id);
                                onClose();
                            }}
                        >
                            <Check className="mr-1 h-3.5 w-3.5" />
                            Aprovar para Publicação
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
