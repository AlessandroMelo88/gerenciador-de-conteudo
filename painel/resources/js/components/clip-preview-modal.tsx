import { useState } from 'react';
import {
    X,
    Smartphone,
    Monitor,
    Play,
    CheckCircle2,
    ThumbsUp,
    Share2,
    Bookmark,
    Check,
    Flame,
} from 'lucide-react';
import type { ClipRow } from '@/types/dashboard';
import { Button } from '@/components/ui/button';

interface ClipPreviewModalProps {
    clip: ClipRow | null;
    isOpen: boolean;
    onClose: () => void;
    onApprove: (id: number) => void;
    onReject: (id: number) => void;
}

export function ClipPreviewModal({
    clip,
    isOpen,
    onClose,
    onApprove,
    onReject,
}: ClipPreviewModalProps) {
    const [device, setDevice] = useState<'mobile' | 'desktop'>('mobile');
    const [desktopTab, setDesktopTab] = useState<'video' | 'cover'>('cover');

    if (!isOpen || !clip) return null;

    const isPol =
        (clip.niche ?? '').toLowerCase().includes('politica') ||
        (clip.destinationChannelName ?? '').toLowerCase().includes('política');
    const isFut =
        (clip.niche ?? '').toLowerCase().includes('futebol') ||
        (clip.destinationChannelName ?? '').toLowerCase().includes('futebol');

    const tmpl = clip.destinationTemplate || {};
    const channelName = clip.destinationChannelName || (isPol ? 'Cortes da Política' : isFut ? 'Futebol em Cortes' : 'Canal de Cortes');
    const headerTitle = tmpl.headerTitle || channelName.toUpperCase();
    const headerBadge = tmpl.headerBadge || (isPol ? '🔴 DEBATE AO VIVO' : isFut ? '⚽ LANCE DECISIVO' : '🎙️ CORTES EXCLUSIVOS');
    const accentColor = tmpl.accentColor || (isPol ? '#E50914' : isFut ? '#10B981' : '#8B5CF6');
    const subtitleColor = tmpl.subtitleColor || '#facc15';
    const ctaText = tmpl.ctaText || 'INSCREVA-SE NO CANAL';
    const isLongo = clip.format === 'longo';
    const isCurto = !isLongo;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
            <div className="relative flex flex-col w-full max-w-5xl max-h-[94vh] bg-zinc-950 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden text-zinc-100">
                {/* TOPO DO MODAL */}
                <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 border-b border-zinc-800/80 bg-zinc-900/60">
                    <div className="flex items-center gap-3 min-w-0">
                        <div
                            className="w-8 h-8 rounded-lg flex items-center justify-center font-black text-xs text-white shrink-0 shadow-sm"
                            style={{ backgroundColor: accentColor }}
                        >
                            {channelName.charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                            <div className="flex items-center gap-2">
                                <h3 className="font-semibold text-sm truncate text-white">{clip.title}</h3>
                                {isLongo ? (
                                    <span className="shrink-0 px-2 py-0.5 rounded text-[10.5px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                        ✨ Longo (9:16)
                                    </span>
                                ) : (
                                    <span className="shrink-0 px-2 py-0.5 rounded text-[10.5px] font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700">
                                        📱 Curto
                                    </span>
                                )}
                            </div>
                            <p className="text-xs text-zinc-400 truncate">
                                Canal: <strong className="text-zinc-200">{channelName}</strong> • Trecho: <span className="font-mono text-zinc-300">{clip.trecho}</span>
                            </p>
                        </div>
                    </div>

                    {/* SELETOR DE DISPOSITIVO (CELULAR VS DESKTOP) */}
                    <div className="flex items-center gap-2 shrink-0">
                        <div className="flex items-center p-1 rounded-xl bg-zinc-900 border border-zinc-800">
                            <button
                                type="button"
                                onClick={() => setDevice('mobile')}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
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
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                    device === 'desktop'
                                        ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700'
                                        : 'text-zinc-400 hover:text-white'
                                }`}
                            >
                                <Monitor className="w-3.5 h-3.5" />
                                <span>Desktop / YouTube (16:9)</span>
                            </button>
                        </div>

                        <button
                            type="button"
                            onClick={onClose}
                            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
                            title="Fechar modal"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* CORPO DO PREVIEW */}
                <div className="flex-1 overflow-y-auto p-4 sm:p-6 flex items-center justify-center bg-zinc-950/70">
                    {device === 'mobile' ? (
                        /* SIMULADOR CELULAR SMARTPHONE 9:16 (SEM CORTES) */
                        <div className="relative w-[320px] sm:w-[350px] aspect-[9/16] max-h-[72vh] rounded-[38px] p-3 bg-zinc-900 border-4 border-zinc-700 shadow-2xl flex flex-col justify-between overflow-hidden">
                            {/* Câmera / Ilha Superior */}
                            <div className="absolute top-3.5 left-1/2 -translate-x-1/2 w-28 h-4 bg-zinc-800 rounded-full z-30 shadow-inner" />

                            {/* Canvas do Smartphone */}
                            <div className="relative w-full h-full rounded-[26px] overflow-hidden bg-black z-10 flex flex-col items-center justify-center">
                                {clip.hasVideoFile ? (
                                    /* O vídeo (seja Longo enquadrado ou Shorts) preenche 100% da tela do celular sem cortar */
                                    <video
                                        controls
                                        autoPlay
                                        playsInline
                                        className="w-full h-full object-cover rounded-[26px]"
                                        src={clip.previewUrl}
                                        poster={clip.hasThumbnailFile ? clip.thumbnailUrl : undefined}
                                    />
                                ) : (
                                    /* Mockup simulado caso o arquivo de vídeo ainda não exista em disco */
                                    <div className="relative w-full h-full flex flex-col justify-between p-4 bg-zinc-950">
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
                                        <div className="relative z-10 pt-7 text-center">
                                            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold text-white uppercase" style={{ backgroundColor: accentColor }}>
                                                {headerBadge}
                                            </span>
                                            <h4 className="font-bold text-xs text-white mt-1">{headerTitle}</h4>
                                        </div>
                                        {/* Centro */}
                                        <div className="relative z-10 my-auto p-4 rounded-xl bg-black/60 border border-white/10 text-center">
                                            <Play className="w-8 h-8 text-white mx-auto mb-2" />
                                            <p className="text-xs text-zinc-300 font-semibold">{clip.title}</p>
                                        </div>
                                        {/* Rodapé */}
                                        <div className="relative z-10 pb-4 text-center">
                                            <div className="w-full py-2 rounded-xl text-center font-bold text-xs text-white uppercase" style={{ backgroundColor: accentColor }}>
                                                {ctaText}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Logo do Canal no Canto Superior Direito (Celular) */}
                                {clip.destinationChannelWatermarkUrl && (
                                    <div className="absolute top-4 right-4 z-30 pointer-events-none drop-shadow-md">
                                        <img
                                            src={clip.destinationChannelWatermarkUrl}
                                            alt={channelName}
                                            className="w-8 h-8 rounded-full object-cover border border-white/40 shadow-lg bg-black/40 backdrop-blur-xs p-0.5"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : isCurto ? (
                        /* DESKTOP: YOUTUBE SHORTS (PLAYER VERTICAL 9:16 COM BOTÕES LATERAIS DO YOUTUBE) */
                            <div className="flex items-end gap-4 py-2">
                                <div className="relative w-[320px] sm:w-[350px] aspect-[9/16] rounded-2xl overflow-hidden bg-black border border-zinc-800 shadow-2xl">
                                    {clip.hasVideoFile ? (
                                        <video
                                            controls
                                            autoPlay
                                            playsInline
                                            className="w-full h-full object-cover"
                                            src={clip.previewUrl}
                                            poster={clip.hasThumbnailFile ? clip.thumbnailUrl : undefined}
                                        />
                                    ) : (
                                        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-zinc-900">
                                            <Play className="w-12 h-12 text-white mb-2" />
                                            <p className="text-xs text-white">{clip.title}</p>
                                        </div>
                                    )}

                                    {/* Logo no Canto Superior Direito do Shorts */}
                                    {clip.destinationChannelWatermarkUrl && (
                                        <div className="absolute top-3.5 right-3.5 z-30 pointer-events-none drop-shadow-md">
                                            <img
                                                src={clip.destinationChannelWatermarkUrl}
                                                alt={channelName}
                                                className="w-8 h-8 rounded-full object-cover border border-white/40 shadow-lg bg-black/40 backdrop-blur-xs p-0.5"
                                            />
                                        </div>
                                    )}

                                    {/* Overlay inferior do Shorts (Canal + Título) */}
                                    <div className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/90 via-black/40 to-transparent pointer-events-none">
                                        <div className="flex items-center gap-2 mb-1.5 pointer-events-auto">
                                            <div className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs text-white" style={{ backgroundColor: accentColor }}>
                                                {channelName.charAt(0).toUpperCase()}
                                            </div>
                                            <span className="font-semibold text-xs text-white">{channelName}</span>
                                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold text-black bg-white">Inscrever-se</span>
                                        </div>
                                        <p className="text-xs font-semibold text-white line-clamp-2 leading-snug drop-shadow">
                                            {clip.title}
                                        </p>
                                    </div>
                                </div>

                                {/* Barra lateral direita clássica do YouTube Shorts no PC */}
                                <div className="flex flex-col items-center gap-4 pb-4">
                                    <div className="flex flex-col items-center gap-1">
                                        <div className="w-10 h-10 rounded-full bg-zinc-800/90 border border-zinc-700 flex items-center justify-center text-white hover:bg-zinc-700 cursor-pointer transition-colors shadow">
                                            <ThumbsUp className="w-4 h-4" />
                                        </div>
                                        <span className="text-[10px] text-zinc-400 font-semibold">12K</span>
                                    </div>
                                    <div className="flex flex-col items-center gap-1">
                                        <div className="w-10 h-10 rounded-full bg-zinc-800/90 border border-zinc-700 flex items-center justify-center text-white hover:bg-zinc-700 cursor-pointer transition-colors shadow">
                                            <Share2 className="w-4 h-4" />
                                        </div>
                                        <span className="text-[10px] text-zinc-400 font-semibold">Compartilhar</span>
                                    </div>
                                    <div className="flex flex-col items-center gap-1">
                                        <div className="w-10 h-10 rounded-full bg-zinc-800/90 border border-zinc-700 flex items-center justify-center text-white hover:bg-zinc-700 cursor-pointer transition-colors shadow">
                                            <Bookmark className="w-4 h-4" />
                                        </div>
                                        <span className="text-[10px] text-zinc-400 font-semibold">Salvar</span>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            /* DESKTOP: YOUTUBE VÍDEO LONGO (PLAYER WIDESCREEN 16:9 + CAPA OFICIAL) */
                            <div className="w-full max-w-3xl flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900 shadow-2xl overflow-hidden">
                                {/* Barra do Navegador */}
                                <div className="flex items-center justify-between px-4 py-2 bg-zinc-950/90 border-b border-zinc-800 text-xs text-zinc-400 font-mono">
                                    <div className="flex items-center gap-2">
                                        <div className="flex items-center gap-1.5">
                                            <span className="w-2.5 h-2.5 rounded-full bg-red-500/80 inline-block" />
                                            <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80 inline-block" />
                                            <span className="w-2.5 h-2.5 rounded-full bg-green-500/80 inline-block" />
                                        </div>
                                        <span className="ml-2 truncate text-zinc-500">
                                            youtube.com/watch?v={clip.id} — Vídeo Longo Oficial
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-1 font-sans bg-zinc-900 p-1 rounded-lg border border-zinc-800">
                                        <button
                                            type="button"
                                            onClick={() => setDesktopTab('cover')}
                                            className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                                                desktopTab === 'cover'
                                                    ? 'bg-amber-500 text-black shadow-sm font-bold'
                                                    : 'text-zinc-400 hover:text-white'
                                            }`}
                                        >
                                            🖼️ Capa / Thumbnail
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setDesktopTab('video')}
                                            className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                                                desktopTab === 'video'
                                                    ? 'bg-zinc-800 text-white shadow-sm border border-zinc-700'
                                                    : 'text-zinc-400 hover:text-white'
                                            }`}
                                        >
                                            ▶️ Assistir Vídeo
                                        </button>
                                    </div>
                                </div>

                                {/* Player Widescreen 16:9 com Ambient Mode ou Capa Oficial */}
                                <div className="relative w-full aspect-video bg-zinc-950 flex items-center justify-center overflow-hidden">
                                    {/* Fundo com Ambient Lighting para preencher widescreen suavemente */}
                                    {clip.hasThumbnailFile && (
                                        <div
                                            className="absolute inset-0 bg-cover bg-center scale-110 blur-2xl opacity-40 pointer-events-none"
                                            style={{ backgroundImage: `url(${clip.thumbnailUrl})` }}
                                        />
                                    )}

                                    {desktopTab === 'cover' ? (
                                        /* Exibição da Capa Oficial 16:9 com palavras chamativas */
                                        <div className="relative z-10 w-full h-full flex items-center justify-center bg-black">
                                            {clip.hasThumbnailFile ? (
                                                <img
                                                    src={clip.thumbnailUrl}
                                                    alt="Capa Oficial 16:9 do YouTube"
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className="text-center p-6">
                                                    <Play className="w-12 h-12 text-white mx-auto mb-2" />
                                                    <h4 className="text-base font-bold text-white">{clip.title}</h4>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        /* Reprodução do Vídeo */
                                        clip.hasVideoFile ? (
                                            <video
                                                controls
                                                autoPlay
                                                className="relative z-10 max-w-full max-h-full object-contain rounded-lg shadow-2xl"
                                                src={clip.previewUrl}
                                                poster={clip.hasThumbnailFile ? clip.thumbnailUrl : undefined}
                                            />
                                        ) : (
                                            <div className="relative z-10 w-full h-full flex flex-col items-center justify-center">
                                                <div className="text-center p-6">
                                                    <Play className="w-12 h-12 text-white mx-auto mb-2" />
                                                    <h4 className="text-base font-bold text-white">{clip.title}</h4>
                                                </div>
                                            </div>
                                        )
                                    )}

                                    <span className="absolute right-3 bottom-3 px-2 py-0.5 rounded bg-black/80 text-[11px] font-mono font-semibold text-white border border-white/10 z-20">
                                        {clip.trecho}
                                    </span>

                                    {/* Marca d'água / Logo Oficial do Canal no Canto Superior Direito */}
                                    <div className="absolute top-4 right-4 z-30 pointer-events-none drop-shadow-xl flex items-center">
                                        {clip.destinationChannelWatermarkUrl ? (
                                            <img
                                                src={clip.destinationChannelWatermarkUrl}
                                                alt={channelName}
                                                className="w-10 h-10 sm:w-12 sm:h-12 rounded-full object-cover border-2 border-white/40 shadow-2xl bg-black/40 backdrop-blur-xs p-0.5"
                                            />
                                        ) : (
                                            <div
                                                className="w-9 h-9 rounded-full flex items-center justify-center font-black text-xs text-white border-2 border-white/30 shadow-lg"
                                                style={{ backgroundColor: accentColor }}
                                            >
                                                {channelName.charAt(0).toUpperCase()}
                                            </div>
                                        )}
                                    </div>
                                </div>

                            {/* Detalhes do Vídeo no Desktop (Estilo YouTube) */}
                            <div className="p-5 flex flex-col gap-4">
                                <h2 className="text-base sm:text-lg font-bold text-white leading-snug">
                                    {clip.title}
                                </h2>

                                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-zinc-800/80">
                                    {/* Canal */}
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-10 h-10 rounded-full flex items-center justify-center font-black text-sm text-white shadow-md"
                                            style={{ backgroundColor: accentColor }}
                                        >
                                            {channelName.charAt(0).toUpperCase()}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-1.5 font-bold text-sm text-white">
                                                <span>{channelName}</span>
                                                <CheckCircle2 className="w-4 h-4 text-zinc-400" />
                                            </div>
                                            <span className="text-[11px] text-zinc-400">
                                                Cortes Oficiais • YouTube
                                            </span>
                                        </div>
                                        <button
                                            type="button"
                                            className="ml-2 px-4 py-1.5 rounded-full text-xs font-bold text-black bg-white hover:bg-zinc-200 transition-colors"
                                        >
                                            Inscrever-se
                                        </button>
                                    </div>

                                    {/* Botões de Ação do YouTube */}
                                    <div className="flex items-center gap-1.5 text-xs text-zinc-300">
                                        <div className="flex items-center rounded-full bg-zinc-800 border border-zinc-700/60 overflow-hidden">
                                            <button type="button" className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-zinc-700">
                                                <ThumbsUp className="w-3.5 h-3.5" /> <span>Gostei</span>
                                            </button>
                                        </div>
                                        <button type="button" className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700/60 hover:bg-zinc-700">
                                            <Share2 className="w-3.5 h-3.5" /> <span>Compartilhar</span>
                                        </button>
                                        <button type="button" className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-800 border border-zinc-700/60 hover:bg-zinc-700">
                                            <Bookmark className="w-3.5 h-3.5" /> <span>Salvar</span>
                                        </button>
                                    </div>
                                </div>

                                {/* Caixa de Descrição do YouTube */}
                                <div className="p-3.5 rounded-xl bg-zinc-800/60 border border-zinc-700/50 text-xs flex flex-col gap-2">
                                    <div className="flex items-center gap-2 font-semibold text-zinc-300">
                                        <span>Fila de Publicação</span>
                                        <span>•</span>
                                        <span className="font-mono text-amber-400 font-bold">Score: {clip.score ?? '—'}/10</span>
                                        <span>•</span>
                                        <span className="text-zinc-400">Vídeo Fonte: {clip.sourceVideoTitle || 'Original'}</span>
                                    </div>
                                    <p className="text-zinc-300 leading-relaxed">
                                        {clip.description ||
                                            `Cortes dos principais debates e momentos mais marcantes. Acompanhe os melhores trechos do canal ${channelName}.`}
                                    </p>
                                    <div className="flex flex-wrap gap-1.5 pt-1 text-sky-400 font-mono text-[11px]">
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
                <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 border-t border-zinc-800 bg-zinc-900/80">
                    <div className="flex items-center gap-2 text-xs text-zinc-400">
                        <Flame className="w-4 h-4 text-orange-500" />
                        <span>Score: <strong className="text-white">{clip.score ?? '—'}/10</strong></span>
                        <span className="text-zinc-600">|</span>
                        <span>Canal Fonte: <strong className="text-zinc-300">{clip.sourceChannelName ?? '—'}</strong></span>
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
                            className="h-8 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white"
                            onClick={() => {
                                onApprove(clip.id);
                                onClose();
                            }}
                        >
                            <Check className="w-3.5 h-3.5 mr-1" />
                            Aprovar para Publicação
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
