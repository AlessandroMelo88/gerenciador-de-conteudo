import { useState } from 'react';
import { router } from '@inertiajs/react';
import type { FormDataConvertible } from '@inertiajs/core';
import { toast } from 'sonner';
import { Check, Play, Eye, Trash2, AlertTriangle, RefreshCw } from 'lucide-react';

import { Checkbox } from '@/components/ui/checkbox';
import { ConfirmButton } from '@/components/confirm-button';
import { ClipPreviewModal } from '@/components/clip-preview-modal';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ActiveWindowTable } from '@/components/active-window-table';
import type { ClipRow, ActiveWindowVideo } from '@/types/dashboard';

function post(url: string, data: Record<string, FormDataConvertible | number[]> = {}) {
    router.post(url, data, {
        preserveScroll: true,
        onSuccess: (page) => {
            const flash = page.props.flash as { success?: string | null; error?: string | null };
            if (flash?.success) toast.success(flash.success);
            if (flash?.error) toast.error(flash.error);
        },
    });
}

function FormatBadge({ format }: { format: ClipRow['format'] }) {
    if (format === 'longo') {
        return (
            <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/40 bg-gradient-to-r from-amber-500/20 via-orange-500/20 to-pink-500/20 px-2 py-0.5 text-[10.5px] font-bold text-amber-700 shadow-xs dark:text-amber-300">
                ✨ Longo
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-950 px-2 py-0.5 text-[10.5px] font-semibold text-white dark:bg-black dark:text-zinc-100">
            📱 Curto
        </span>
    );
}

function EmptyState({ message }: { message: string }) {
    return (
        <div className="flex items-center justify-center rounded-2xl border border-dashed border-border bg-card/40 py-12 text-sm text-muted-foreground">
            {message}
        </div>
    );
}

function useSelection(items: ClipRow[] = []) {
    const [selected, setSelected] = useState<number[]>([]);
    const [lastSelectedId, setLastSelectedId] = useState<number | null>(null);

    const toggle = (id: number, shiftKey = false) => {
        setSelected((prev) => {
            const isCurrentlySelected = prev.includes(id);

            if (shiftKey && lastSelectedId !== null && items.length > 0) {
                const lastIdx = items.findIndex((x) => x.id === lastSelectedId);
                const currIdx = items.findIndex((x) => x.id === id);

                if (lastIdx !== -1 && currIdx !== -1) {
                    const start = Math.min(lastIdx, currIdx);
                    const end = Math.max(lastIdx, currIdx);
                    const range = items.slice(start, end + 1).map((x) => x.id);

                    return Array.from(new Set([...prev, ...range]));
                }
            }

            return isCurrentlySelected ? prev.filter((x) => x !== id) : [...prev, id];
        });

        setLastSelectedId(id);
    };

    const toggleAll = (ids: number[]) => {
        setSelected((prev) => (prev.length === ids.length ? [] : ids));
        setLastSelectedId(null);
    };

    const clear = () => {
        setSelected([]);
        setLastSelectedId(null);
    };

    return { selected, toggle, toggleAll, clear };
}

function NicheBadge({ niche, channelName }: { niche?: string | null; channelName?: string | null }) {
    const n = (niche ?? '').toLowerCase();
    const ch = (channelName ?? '').toLowerCase();

    if (n === 'politica' || ch.includes('política') || ch.includes('politica')) {
        return (
            <span className="inline-flex items-center gap-1 rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-[11px] font-semibold text-purple-600 dark:text-purple-400">
                🏛️ {channelName ?? 'Política'}
            </span>
        );
    }
    if (n === 'podcast' || ch.includes('podcast')) {
        return (
            <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] font-semibold text-amber-600 dark:text-amber-400">
                🎙️ {channelName ?? 'Podcast'}
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
            ⚽ {channelName ?? 'Futebol'}
        </span>
    );
}

function ScoreBadge({ score }: { score: number | null }) {
    if (score === null || score === undefined) return <span className="text-muted-foreground">—</span>;

    if (score >= 9) {
        return (
            <span className="inline-flex items-center gap-1 rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs font-bold text-red-500 dark:text-red-400">
                🔥 {score}/10
            </span>
        );
    }
    if (score >= 8) {
        return (
            <span className="inline-flex items-center gap-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                ⭐ {score}/10
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 rounded-lg border border-zinc-500/30 bg-zinc-500/10 px-2.5 py-1 text-xs font-medium text-zinc-400">
            {score}/10
        </span>
    );
}

function PendingTable({ clips }: { clips: ClipRow[] }) {
    const [subTab, setSubTab] = useState<'todos' | 'futebol' | 'politica' | 'podcast'>('todos');
    const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
    const [previewingId, setPreviewingId] = useState<number | null>(null);
    const [modalClip, setModalClip] = useState<ClipRow | null>(null);

    const counts = {
        todos: clips.length,
        futebol: clips.filter((c) => {
            const n = (c.niche ?? '').toLowerCase();
            const ch = (c.destinationChannelName ?? '').toLowerCase();
            return n === 'futebol' || (!n.includes('politica') && !n.includes('podcast') && !ch.includes('política'));
        }).length,
        politica: clips.filter((c) => {
            const n = (c.niche ?? '').toLowerCase();
            const ch = (c.destinationChannelName ?? '').toLowerCase();
            return n === 'politica' || ch.includes('política') || ch.includes('politica');
        }).length,
        podcast: clips.filter((c) => {
            const n = (c.niche ?? '').toLowerCase();
            const ch = (c.destinationChannelName ?? '').toLowerCase();
            return n === 'podcast' || ch.includes('podcast');
        }).length,
    };

    const filteredClips = clips.filter((c) => {
        if (subTab === 'todos') return true;
        const n = (c.niche ?? '').toLowerCase();
        const ch = (c.destinationChannelName ?? '').toLowerCase();
        if (subTab === 'politica') return n === 'politica' || ch.includes('política') || ch.includes('politica');
        if (subTab === 'podcast') return n === 'podcast' || ch.includes('podcast');
        return n === 'futebol' || (!n.includes('politica') && !n.includes('podcast') && !ch.includes('política'));
    });

    const ids = filteredClips.map((c) => c.id);
    const { selected, toggle, toggleAll, clear } = useSelection(filteredClips);

    if (clips.length === 0) return <EmptyState message="Nenhum clip aguardando aprovação" />;

    return (
        <div className="flex flex-col gap-4">
            {/* Top Header of the Queue */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                    <h2 className="font-display text-base font-bold text-foreground">Fila de aprovação</h2>
                    <span className="rounded-lg border border-border bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground">
                        {clips.length} aguardando
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    {ids.length > 0 && (
                        <ConfirmButton
                            variant="outline"
                            size="sm"
                            className="h-8 rounded-lg text-xs font-medium"
                            description={`Aprovar todos os ${ids.length} clipes visíveis?`}
                            onConfirm={() => {
                                post('/painel/clips/bulk-approve', { ids });
                                clear();
                            }}
                        >
                            <Check className="mr-1 h-3.5 w-3.5 text-emerald-500" /> Aprovar todos
                        </ConfirmButton>
                    )}

                    <div className="flex overflow-hidden rounded-lg border bg-card p-0.5">
                        <button
                            type="button"
                            onClick={() => setViewMode('grid')}
                            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                                viewMode === 'grid'
                                    ? 'bg-primary text-primary-foreground shadow-sm'
                                    : 'text-muted-foreground hover:text-foreground'
                            }`}
                            title="Modo Quadro (Cards)"
                        >
                            ⊞ Quadro
                        </button>
                        <button
                            type="button"
                            onClick={() => setViewMode('list')}
                            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                                viewMode === 'list'
                                    ? 'bg-primary text-primary-foreground shadow-sm'
                                    : 'text-muted-foreground hover:text-foreground'
                            }`}
                            title="Modo Tabela (Lista)"
                        >
                            ☰ Tabela
                        </button>
                    </div>
                </div>
            </div>

            {/* Subtabs de nicho */}
            <div className="flex w-fit flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-1.5">
                <button
                    type="button"
                    onClick={() => setSubTab('todos')}
                    className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                        subTab === 'todos'
                            ? 'bg-zinc-900 text-white shadow-sm dark:bg-white dark:text-zinc-900'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>Todos</span>
                    <span className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[10px]">{counts.todos}</span>
                </button>
                <button
                    type="button"
                    onClick={() => setSubTab('futebol')}
                    className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                        subTab === 'futebol'
                            ? 'bg-emerald-600 text-white shadow-sm'
                            : 'text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400'
                    }`}
                >
                    <span>⚽ Futebol</span>
                    <span className="rounded-md bg-emerald-500/20 px-1.5 py-0.5 font-mono text-[10px]">
                        {counts.futebol}
                    </span>
                </button>
                <button
                    type="button"
                    onClick={() => setSubTab('politica')}
                    className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                        subTab === 'politica'
                            ? 'bg-purple-600 text-white shadow-sm'
                            : 'text-purple-600 hover:bg-purple-500/10 dark:text-purple-400'
                    }`}
                >
                    <span>🏛️ Política</span>
                    <span className="rounded-md bg-purple-500/20 px-1.5 py-0.5 font-mono text-[10px]">
                        {counts.politica}
                    </span>
                </button>
                {counts.podcast > 0 && (
                    <button
                        type="button"
                        onClick={() => setSubTab('podcast')}
                        className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                            subTab === 'podcast'
                                ? 'bg-amber-600 text-white shadow-sm'
                                : 'text-amber-600 hover:bg-amber-500/10 dark:text-amber-400'
                        }`}
                    >
                        <span>🎙️ Podcast</span>
                        <span className="rounded-md bg-amber-500/20 px-1.5 py-0.5 font-mono text-[10px]">
                            {counts.podcast}
                        </span>
                    </button>
                )}
            </div>

            {/* Ações em lote caso haja selecionados */}
            {selected.length > 0 && (
                <div className="flex items-center gap-2 rounded-xl border border-border bg-card p-2.5">
                    <span className="mr-2 font-mono text-xs text-muted-foreground">
                        {selected.length} selecionado(s)
                    </span>
                    <ConfirmButton
                        variant="default"
                        size="sm"
                        className="h-8 rounded-lg bg-emerald-600 px-3 text-xs text-white hover:bg-emerald-500"
                        description={`Aprovar os ${selected.length} clips selecionados?`}
                        onConfirm={() => {
                            post('/painel/clips/bulk-approve', { ids: selected });
                            clear();
                        }}
                    >
                        Aprovar selecionados ({selected.length})
                    </ConfirmButton>
                    <ConfirmButton
                        variant="destructive"
                        size="sm"
                        className="h-8 rounded-lg px-3 text-xs"
                        description={`Rejeitar os ${selected.length} clips selecionados? O MP4 será removido.`}
                        onConfirm={() => {
                            post('/painel/clips/bulk-reject', { ids: selected });
                            clear();
                        }}
                    >
                        Rejeitar selecionados ({selected.length})
                    </ConfirmButton>
                </div>
            )}

            {viewMode === 'grid' ? (
                /* MODO QUADRO / CARDS */
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
                    {filteredClips.map((clip) => {
                        const isPol =
                            (clip.niche ?? '').toLowerCase().includes('politica') ||
                            (clip.destinationChannelName ?? '').toLowerCase().includes('política');
                        const bgGradient = isPol
                            ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)'
                            : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';

                        return (
                            <article
                                key={clip.id}
                                className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-xs transition-all hover:border-primary/40"
                            >
                                <div
                                    className="relative aspect-video cursor-pointer overflow-hidden bg-zinc-950"
                                    style={{ background: bgGradient }}
                                    onClick={() => setModalClip(clip)}
                                >
                                    {clip.hasThumbnailFile && clip.thumbnailUrl ? (
                                        <img
                                            src={clip.thumbnailUrl}
                                            alt={clip.title}
                                            className="absolute inset-0 h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                                            loading="lazy"
                                        />
                                    ) : null}
                                    <div className="pointer-events-none absolute inset-0 bg-black/20 transition-colors group-hover:bg-black/40" />
                                    <div className="absolute inset-0 grid place-items-center">
                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setModalClip(clip);
                                            }}
                                            className="grid h-12 w-12 place-items-center rounded-full border border-white/20 bg-black/60 text-white shadow-lg backdrop-blur-md transition-transform group-hover:scale-110"
                                            title="Abrir preview e capa oficial"
                                        >
                                            <Play className="ml-0.5 h-5 w-5 fill-white" />
                                        </button>
                                    </div>
                                    <span className="absolute top-2.5 left-2.5 z-10 rounded-md border border-white/10 bg-black/60 px-2 py-0.5 text-[11px] font-semibold text-white backdrop-blur-md">
                                        {isPol ? '🏛️ Fatos & Debates' : '⚽ Futebol'}
                                    </span>
                                    <span className="absolute top-2.5 right-2.5 z-10">
                                        <FormatBadge format={clip.format} />
                                    </span>
                                    <span className="absolute bottom-2.5 left-2.5 z-10 rounded-md border border-white/10 bg-black/60 px-2 py-0.5 font-mono text-[11px] text-white backdrop-blur-md">
                                        {clip.trecho}
                                    </span>
                                    <span className="absolute right-2.5 bottom-2.5 z-10">
                                        <ScoreBadge score={clip.score} />
                                    </span>
                                </div>

                                {previewingId === clip.id && (
                                    <div className="border-b border-border bg-black/90 p-3">
                                        <video
                                            controls
                                            autoPlay
                                            className="max-h-[220px] w-full rounded-lg"
                                            src={clip.previewUrl}
                                        />
                                    </div>
                                )}

                                <div className="flex flex-1 flex-col gap-3 p-4">
                                    <div className="flex items-start gap-2">
                                        <Checkbox
                                            checked={selected.includes(clip.id)}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                toggle(clip.id, e.shiftKey);
                                            }}
                                            className="mt-1"
                                        />
                                        <div
                                            className="line-clamp-2 text-sm leading-snug font-semibold tracking-tight text-foreground"
                                            title={clip.title}
                                        >
                                            {clip.title}
                                        </div>
                                    </div>

                                    <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                                        <span className="rounded border border-border px-1.5 py-0.5 font-mono">
                                            #{clip.id}
                                        </span>
                                        <span className="truncate">
                                            {clip.destinationChannelName ?? 'Canal Destino'}
                                        </span>
                                    </div>

                                    <div className="flex-1" />

                                    <div className="flex items-center gap-2 border-t border-border/60 pt-2">
                                        <button
                                            type="button"
                                            onClick={() => setModalClip(clip)}
                                            className="inline-flex h-8 shrink-0 items-center justify-center gap-1 rounded-lg border border-zinc-700 bg-zinc-800 px-2.5 text-xs font-semibold text-zinc-300 transition-colors hover:bg-zinc-700 hover:text-white"
                                            title="Abrir preview no celular (9:16) ou computador (16:9)"
                                        >
                                            <Eye className="h-3.5 w-3.5 text-sky-400" />
                                            <span>Preview</span>
                                        </button>
                                        <ConfirmButton
                                            variant="outline"
                                            size="sm"
                                            className="h-8 flex-1 rounded-lg border-emerald-500/30 px-4 text-xs font-semibold text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400"
                                            description={`Aprovar clip #${clip.id} para publicação?`}
                                            onConfirm={() => post(`/painel/clips/${clip.id}/approve`)}
                                        >
                                            Aprovar
                                        </ConfirmButton>
                                        <ConfirmButton
                                            variant="destructive"
                                            size="sm"
                                            className="h-8 rounded-lg px-3 text-xs"
                                            description={`Rejeitar clip #${clip.id}? O MP4 será removido do disco.`}
                                            onConfirm={() => post(`/painel/clips/${clip.id}/reject`)}
                                        >
                                            Rejeitar
                                        </ConfirmButton>
                                    </div>
                                </div>
                            </article>
                        );
                    })}
                </div>
            ) : (
                /* MODO TABELA LIMPO E SEM REDUNDÂNCIA */
                <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-xs">
                    <Table className="w-full text-xs">
                        <TableHeader className="border-b border-border bg-muted/40">
                            <TableRow>
                                <TableHead className="w-8 pl-4">
                                    <Checkbox
                                        checked={selected.length > 0 && selected.length === ids.length}
                                        onCheckedChange={() => toggleAll(ids)}
                                    />
                                </TableHead>
                                <TableHead className="px-4 py-3 text-[11px] font-bold tracking-wider text-muted-foreground uppercase">
                                    CLIPE
                                </TableHead>
                                <TableHead className="px-4 py-3 text-[11px] font-bold tracking-wider text-muted-foreground uppercase">
                                    VÍDEO FONTE
                                </TableHead>
                                <TableHead className="px-4 py-3 text-[11px] font-bold tracking-wider text-muted-foreground uppercase">
                                    TRECHO
                                </TableHead>
                                <TableHead className="px-4 py-3 text-[11px] font-bold tracking-wider text-muted-foreground uppercase">
                                    DESTINO
                                </TableHead>
                                <TableHead className="px-4 py-3 text-[11px] font-bold tracking-wider text-muted-foreground uppercase">
                                    SCORE
                                </TableHead>
                                <TableHead className="px-4 py-3 pr-5 text-right text-[11px] font-bold tracking-wider text-muted-foreground uppercase">
                                    AÇÕES
                                </TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredClips.map((clip) => {
                                const isPol =
                                    (clip.niche ?? '').toLowerCase().includes('politica') ||
                                    (clip.destinationChannelName ?? '').toLowerCase().includes('política');
                                const bgGradient = isPol
                                    ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)'
                                    : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';

                                return (
                                    <TableRow key={clip.id} className="border-b border-border/60 hover:bg-muted/30">
                                        <TableCell className="pl-4">
                                            <Checkbox
                                                checked={selected.includes(clip.id)}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    toggle(clip.id, e.shiftKey);
                                                }}
                                            />
                                        </TableCell>

                                        {/* Coluna CLIPE: Capa + Título + Badges (Nicho e Formato) */}
                                        <TableCell className="max-w-[360px] px-4 py-3">
                                            <div className="flex items-start gap-3">
                                                <div
                                                    className="relative grid h-9 w-14 shrink-0 cursor-pointer place-items-center overflow-hidden rounded-lg border border-border bg-zinc-900 text-white shadow-xs transition-opacity hover:opacity-90"
                                                    style={{ background: bgGradient }}
                                                    onClick={() => setModalClip(clip)}
                                                    title="Clique para abrir o preview e ver a capa"
                                                >
                                                    {clip.hasThumbnailFile && clip.thumbnailUrl ? (
                                                        <img
                                                            src={clip.thumbnailUrl}
                                                            alt={clip.title}
                                                            className="h-full w-full object-cover"
                                                            loading="lazy"
                                                        />
                                                    ) : (
                                                        <Play className="ml-0.5 h-3.5 w-3.5 fill-white" />
                                                    )}
                                                </div>
                                                <div className="min-w-0 flex-1">
                                                    <div
                                                        className="line-clamp-1 text-sm font-semibold tracking-tight text-foreground"
                                                        title={clip.title}
                                                    >
                                                        {clip.title}
                                                    </div>
                                                    <div className="mt-1 flex items-center gap-2">
                                                        <NicheBadge
                                                            niche={clip.niche}
                                                            channelName={clip.destinationChannelName}
                                                        />
                                                        <FormatBadge format={clip.format} />
                                                        <button
                                                            type="button"
                                                            onClick={() =>
                                                                setPreviewingId(
                                                                    previewingId === clip.id ? null : clip.id,
                                                                )
                                                            }
                                                            className="ml-1 text-[11px] font-medium text-amber-500 underline hover:text-amber-400"
                                                        >
                                                            {previewingId === clip.id ? 'Fechar vídeo' : 'Vídeo rápido'}
                                                        </button>
                                                        <button
                                                            type="button"
                                                            onClick={() => setModalClip(clip)}
                                                            className="ml-1 inline-flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-[11px] font-semibold text-zinc-300 shadow-xs transition-all hover:bg-zinc-700 hover:text-white"
                                                            title="Abrir preview no celular (9:16) ou computador (16:9)"
                                                        >
                                                            <Eye className="h-3 w-3 text-sky-400" />
                                                            <span>Preview Completo</span>
                                                        </button>
                                                    </div>

                                                    {previewingId === clip.id && (
                                                        <div className="mt-2 rounded-lg bg-black/90 p-2">
                                                            <video
                                                                controls
                                                                autoPlay
                                                                className="w-[260px] rounded"
                                                                src={clip.previewUrl}
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </TableCell>

                                        {/* Coluna VÍDEO FONTE */}
                                        <TableCell className="max-w-[180px] px-4 py-3">
                                            <div
                                                className="truncate text-xs font-medium text-foreground"
                                                title={clip.sourceVideoTitle ?? ''}
                                            >
                                                {clip.sourceVideoTitle ?? '—'}
                                            </div>
                                            <div className="truncate text-[11px] text-muted-foreground">
                                                {clip.sourceChannelName ?? 'Canal Fonte'}
                                            </div>
                                        </TableCell>

                                        {/* Coluna TRECHO */}
                                        <TableCell className="px-4 py-3 font-mono text-xs whitespace-nowrap text-muted-foreground">
                                            {clip.trecho}
                                        </TableCell>

                                        {/* Coluna DESTINO */}
                                        <TableCell className="px-4 py-3 text-xs font-medium whitespace-nowrap text-foreground">
                                            {clip.destinationChannelName ?? '—'}
                                        </TableCell>

                                        {/* Coluna SCORE */}
                                        <TableCell className="px-4 py-3 whitespace-nowrap">
                                            <ScoreBadge score={clip.score} />
                                        </TableCell>

                                        {/* Coluna AÇÕES */}
                                        <TableCell className="px-4 py-3 pr-5 text-right whitespace-nowrap">
                                            <div className="flex items-center justify-end gap-2">
                                                <ConfirmButton
                                                    variant="outline"
                                                    size="sm"
                                                    className="h-8 rounded-lg border-emerald-500/30 px-3 text-xs font-semibold text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400"
                                                    description={`Aprovar clip #${clip.id} para publicação?`}
                                                    onConfirm={() => post(`/painel/clips/${clip.id}/approve`)}
                                                >
                                                    Aprovar
                                                </ConfirmButton>

                                                <ConfirmButton
                                                    variant="destructive"
                                                    size="sm"
                                                    className="h-8 rounded-lg px-3 text-xs"
                                                    description={`Rejeitar clip #${clip.id}? O MP4 será removido do disco.`}
                                                    onConfirm={() => post(`/painel/clips/${clip.id}/reject`)}
                                                >
                                                    Rejeitar
                                                </ConfirmButton>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </div>
            )}

            {/* MODAL DE PREVIEW CELULAR (9:16) E DESKTOP (16:9) */}
            <ClipPreviewModal
                clip={modalClip}
                isOpen={!!modalClip}
                onClose={() => setModalClip(null)}
                onApprove={(id) => post(`/painel/clips/${id}/approve`)}
                onReject={(id) => post(`/painel/clips/${id}/reject`)}
            />
        </div>
    );
}

function QueuedTable({ clips }: { clips: ClipRow[] }) {
    if (clips.length === 0) {
        return <EmptyState message="Nenhum clip aprovado aguardando cota no momento" />;
    }

    return (
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-xs">
            <Table className="w-full text-xs">
                <TableHeader className="bg-muted/40">
                    <TableRow>
                        <TableHead className="px-5 py-3 font-semibold">ID</TableHead>
                        <TableHead className="px-5 py-3 font-semibold">Título</TableHead>
                        <TableHead className="px-5 py-3 font-semibold">Canal Destino</TableHead>
                        <TableHead className="px-5 py-3 font-semibold">Formato</TableHead>
                        <TableHead className="px-5 py-3 font-semibold">Score</TableHead>
                        <TableHead className="px-5 py-3 font-semibold">Aprovado em</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {clips.map((clip) => (
                        <TableRow key={clip.id} className="hover:bg-muted/30">
                            <TableCell className="px-5 py-3 font-mono text-muted-foreground">#{clip.id}</TableCell>
                            <TableCell className="max-w-[300px] truncate px-5 py-3 font-medium text-foreground">
                                {clip.title}
                            </TableCell>
                            <TableCell className="px-5 py-3">
                                <NicheBadge niche={clip.niche} channelName={clip.destinationChannelName} />
                            </TableCell>
                            <TableCell className="px-5 py-3">
                                <FormatBadge format={clip.format} />
                            </TableCell>
                            <TableCell className="px-5 py-3">
                                <ScoreBadge score={clip.score} />
                            </TableCell>
                            <TableCell className="px-5 py-3 font-mono text-[11px] text-muted-foreground">
                                {clip.createdAt}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}

function FailuresTable({ clips, failedSourceVideoCount }: { clips: ClipRow[]; failedSourceVideoCount: number }) {
    if (clips.length === 0 && failedSourceVideoCount === 0) {
        return <EmptyState message="Nenhuma falha recente no pipeline" />;
    }

    return (
        <div className="flex flex-col gap-4">
            {failedSourceVideoCount > 0 && (
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-destructive/20 bg-destructive/10 p-4 text-xs text-destructive">
                    <div className="flex items-center gap-2">
                        <span>⚠️ {failedSourceVideoCount} vídeo(s) fonte falharam no download ou processamento.</span>
                        <a href="/painel/videos?tab=falharam" className="ml-1 font-semibold underline">
                            Ver detalhes →
                        </a>
                    </div>
                    <ConfirmButton
                        variant="destructive"
                        size="sm"
                        className="h-8 gap-1.5 text-xs font-semibold shadow-xs"
                        description={`Apagar arquivos locais dos ${failedSourceVideoCount} vídeos com falha? Os registros e transcrições serão mantidos.`}
                        onConfirm={() => post('/painel/videos/purge-failed')}
                    >
                        <Trash2 className="h-3.5 w-3.5" />
                        Limpar arquivos de {failedSourceVideoCount} vídeos falhados
                    </ConfirmButton>
                </div>
            )}

            {clips.length > 0 && (
                <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-muted-foreground">
                            {clips.length} clip(s) com falha recente
                        </span>
                        <ConfirmButton
                            variant="outline"
                            size="sm"
                            className="h-7 gap-1.5 border-destructive/30 text-xs text-destructive hover:bg-destructive/10"
                            description={`Apagar somente os arquivos dos ${clips.length} clips com falha? Os registros e vínculos serão mantidos.`}
                            onConfirm={() => post('/painel/clips/purge-failed')}
                        >
                            <Trash2 className="h-3.5 w-3.5" />
                            Limpar arquivos de clips falhados
                        </ConfirmButton>
                    </div>

                    <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-xs">
                        <Table className="w-full text-xs">
                            <TableHeader className="bg-muted/40">
                                <TableRow>
                                    <TableHead className="w-16 px-5 py-3 font-semibold">ID</TableHead>
                                    <TableHead className="px-5 py-3 font-semibold">Vídeo & Detalhes da Falha</TableHead>
                                    <TableHead className="w-44 px-5 py-3 font-semibold">Canal Destino</TableHead>
                                    <TableHead className="w-32 px-5 py-3 font-semibold">Data</TableHead>
                                    <TableHead className="w-40 px-5 py-3 text-right font-semibold">Ações</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {clips.map((clip) => {
                                    const clipTitle =
                                        clip.title ||
                                        (clip.sourceVideoTitle
                                            ? `Corte de: ${clip.sourceVideoTitle}`
                                            : `Clip #${clip.id}`);
                                    const hasDistinctSource = Boolean(
                                        clip.sourceVideoTitle &&
                                        clip.title &&
                                        clip.title !== clip.sourceVideoTitle &&
                                        !clip.title.includes(clip.sourceVideoTitle),
                                    );

                                    return (
                                        <TableRow key={clip.id} className="hover:bg-muted/30">
                                            <TableCell className="px-5 py-4 align-top font-mono font-semibold text-muted-foreground">
                                                #{clip.id}
                                            </TableCell>
                                            <TableCell className="px-5 py-4 align-top">
                                                <div className="flex max-w-3xl flex-col gap-2">
                                                    <div>
                                                        <div
                                                            className="text-[13px] leading-snug font-semibold text-foreground"
                                                            title={clipTitle}
                                                        >
                                                            {clipTitle}
                                                        </div>
                                                        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                                                            {hasDistinctSource && (
                                                                <span
                                                                    title={clip.sourceVideoTitle ?? ''}
                                                                    className="max-w-md truncate"
                                                                >
                                                                    🎬{' '}
                                                                    <span className="font-medium text-foreground/70">
                                                                        Fonte:
                                                                    </span>{' '}
                                                                    {clip.sourceVideoTitle}
                                                                </span>
                                                            )}
                                                            {clip.trecho && (
                                                                <span className="rounded border border-border/40 bg-muted/60 px-1.5 py-0.5 font-mono text-[10.5px] text-muted-foreground">
                                                                    ⏱️ Trecho: {clip.trecho}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Box de Diagnóstico do Erro com quebra de linha garantida */}
                                                    <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
                                                        <div className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold tracking-wider text-destructive uppercase">
                                                            <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-destructive" />
                                                            <span>Diagnóstico da Falha</span>
                                                        </div>
                                                        <div className="rounded-lg border border-destructive/15 bg-destructive/5 p-2 font-mono text-[11.5px] leading-relaxed break-words text-destructive/95">
                                                            {clip.uploadError ||
                                                                'Falha no corte ou processamento do vídeo'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell className="px-5 py-4 align-top">
                                                <div className="pt-0.5">
                                                    <NicheBadge
                                                        niche={clip.niche}
                                                        channelName={clip.destinationChannelName}
                                                    />
                                                </div>
                                            </TableCell>
                                            <TableCell className="px-5 py-4 align-top font-mono text-[11px] whitespace-nowrap text-muted-foreground">
                                                <div className="pt-1">{clip.updatedAt}</div>
                                            </TableCell>
                                            <TableCell className="px-5 py-4 text-right align-top">
                                                <div className="flex items-center justify-end gap-1.5 pt-0.5">
                                                    <ConfirmButton
                                                        variant="outline"
                                                        size="sm"
                                                        className="h-8 gap-1 rounded-lg border-primary/40 text-xs font-semibold shadow-xs hover:bg-primary/10 hover:text-primary"
                                                        description={`Reenviar clip #${clip.id} para reprocessamento? Ele voltará para a fila de corte.`}
                                                        onConfirm={() => post(`/painel/clips/${clip.id}/reprocess`)}
                                                    >
                                                        <RefreshCw className="h-3.5 w-3.5" />
                                                        Reprocessar
                                                    </ConfirmButton>
                                                    <ConfirmButton
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 w-8 rounded-lg p-0 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                                                        description={`Excluir o clip #${clip.id} definitivamente do banco?`}
                                                        onConfirm={() => post(`/painel/clips/${clip.id}/delete`)}
                                                    >
                                                        <Trash2 className="h-3.5 w-3.5" />
                                                    </ConfirmButton>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    </div>
                </div>
            )}
        </div>
    );
}

export function ClipQueueTabs({
    pendingClips,
    queuedClips,
    failures,
    failedSourceVideoCount,
    activeWindow = [],
}: {
    pendingClips: ClipRow[];
    queuedClips: ClipRow[];
    failures: ClipRow[];
    failedSourceVideoCount: number;
    activeWindow?: ActiveWindowVideo[];
}) {
    const [mainTab, setMainTab] = useState<'pending' | 'active_window' | 'queued' | 'failures'>('pending');

    return (
        <div className="flex flex-col gap-5">
            {/* ABAS PAI UNIFORMES */}
            <div className="flex w-fit flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-1.5">
                <button
                    type="button"
                    onClick={() => setMainTab('pending')}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                        mainTab === 'pending'
                            ? 'bg-zinc-900 text-white shadow-sm dark:bg-white dark:text-zinc-900'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>🎯 Fila de aprovação</span>
                    <span
                        className={`rounded-md px-2 py-0.5 font-mono text-[10.5px] font-bold transition-colors ${
                            mainTab === 'pending'
                                ? 'bg-white/20 text-white dark:bg-zinc-900/15 dark:text-zinc-900'
                                : 'bg-muted text-muted-foreground'
                        }`}
                    >
                        {pendingClips.length}
                    </span>
                </button>

                <button
                    type="button"
                    onClick={() => setMainTab('active_window')}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                        mainTab === 'active_window'
                            ? 'bg-zinc-900 text-white shadow-sm dark:bg-white dark:text-zinc-900'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>⚡ Processados / Janela Ativa</span>
                    <span
                        className={`rounded-md px-2 py-0.5 font-mono text-[10.5px] font-bold transition-colors ${
                            mainTab === 'active_window'
                                ? 'bg-white/20 text-white dark:bg-zinc-900/15 dark:text-zinc-900'
                                : 'bg-muted text-muted-foreground'
                        }`}
                    >
                        {activeWindow.length}
                    </span>
                </button>

                <button
                    type="button"
                    onClick={() => setMainTab('queued')}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                        mainTab === 'queued'
                            ? 'bg-zinc-900 text-white shadow-sm dark:bg-white dark:text-zinc-900'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>🚀 Prontos para subir</span>
                    <span
                        className={`rounded-md px-2 py-0.5 font-mono text-[10.5px] font-bold transition-colors ${
                            mainTab === 'queued'
                                ? 'bg-white/20 text-white dark:bg-zinc-900/15 dark:text-zinc-900'
                                : 'bg-muted text-muted-foreground'
                        }`}
                    >
                        {queuedClips.length}
                    </span>
                </button>

                <button
                    type="button"
                    onClick={() => setMainTab('failures')}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                        mainTab === 'failures'
                            ? 'bg-zinc-900 text-white shadow-sm dark:bg-white dark:text-zinc-900'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>⚠️ Falhas recentes</span>
                    <span
                        className={`rounded-md px-2 py-0.5 font-mono text-[10.5px] font-bold transition-colors ${
                            mainTab === 'failures'
                                ? 'bg-white/20 text-white dark:bg-zinc-900/15 dark:text-zinc-900'
                                : 'bg-muted text-muted-foreground'
                        }`}
                    >
                        {failures.length}
                    </span>
                </button>
            </div>

            {/* CONTEÚDO DAS ABAS */}
            {mainTab === 'pending' && <PendingTable clips={pendingClips} />}
            {mainTab === 'active_window' && (
                <div className="rounded-2xl border border-border bg-card p-5">
                    <div className="mb-4">
                        <h2 className="font-display text-sm font-bold tracking-tight text-foreground">
                            Vídeos em Processamento / Baixados em Disco
                        </h2>
                        <p className="text-xs text-muted-foreground">
                            Matéria-prima bruta sendo baixada, transcrita pelo Whisper e selecionada pelo LLaMA.
                        </p>
                    </div>
                    <ActiveWindowTable videos={activeWindow} />
                </div>
            )}
            {mainTab === 'queued' && <QueuedTable clips={queuedClips} />}
            {mainTab === 'failures' && (
                <FailuresTable clips={failures} failedSourceVideoCount={failedSourceVideoCount} />
            )}
        </div>
    );
}
