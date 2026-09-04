import { useState } from 'react';
import { router } from '@inertiajs/react';
import type { FormDataConvertible } from '@inertiajs/core';
import { toast } from 'sonner';
import { Check, Play, X, Eye } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ConfirmButton } from '@/components/confirm-button';
import { ClipPreviewModal } from '@/components/clip-preview-modal';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
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
            <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/40 bg-gradient-to-r from-amber-500/20 via-orange-500/20 to-pink-500/20 px-2 py-0.5 text-[10.5px] font-bold text-amber-700 dark:text-amber-300 shadow-xs">
                ✨ Longo
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 rounded-md bg-zinc-950 text-white dark:bg-black dark:text-zinc-100 border border-zinc-800 px-2 py-0.5 text-[10.5px] font-semibold">
            📱 Curto
        </span>
    );
}

function EmptyState({ message }: { message: string }) {
    return (
        <div className="flex items-center justify-center rounded-2xl border border-dashed border-border py-12 text-sm text-muted-foreground bg-card/40">
            {message}
        </div>
    );
}

function useSelection() {
    const [selected, setSelected] = useState<number[]>([]);

    const toggle = (id: number) =>
        setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

    const toggleAll = (ids: number[]) =>
        setSelected((prev) => (prev.length === ids.length ? [] : ids));

    const clear = () => setSelected([]);

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
    const { selected, toggle, toggleAll, clear } = useSelection();

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

    if (clips.length === 0) return <EmptyState message="Nenhum clip aguardando aprovação" />;

    return (
        <div className="flex flex-col gap-4">
            {/* Top Header of the Queue */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                    <h2 className="font-display text-base font-bold text-foreground">Fila de aprovação</h2>
                    <span className="text-xs font-mono px-2 py-0.5 rounded-lg bg-muted text-muted-foreground border border-border">
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
                            <Check className="w-3.5 h-3.5 mr-1 text-emerald-500" /> Aprovar todos
                        </ConfirmButton>
                    )}

                    <div className="flex rounded-lg border bg-card p-0.5 overflow-hidden">
                        <button
                            type="button"
                            onClick={() => setViewMode('grid')}
                            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
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
                            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
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
            <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-1.5 w-fit">
                <button
                    type="button"
                    onClick={() => setSubTab('todos')}
                    className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                        subTab === 'todos'
                            ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>Todos</span>
                    <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-mono">
                        {counts.todos}
                    </span>
                </button>
                <button
                    type="button"
                    onClick={() => setSubTab('futebol')}
                    className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                        subTab === 'futebol'
                            ? 'bg-emerald-600 text-white shadow-sm'
                            : 'text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10'
                    }`}
                >
                    <span>⚽ Futebol</span>
                    <span className="rounded-md bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-mono">
                        {counts.futebol}
                    </span>
                </button>
                <button
                    type="button"
                    onClick={() => setSubTab('politica')}
                    className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                        subTab === 'politica'
                            ? 'bg-purple-600 text-white shadow-sm'
                            : 'text-purple-600 dark:text-purple-400 hover:bg-purple-500/10'
                    }`}
                >
                    <span>🏛️ Política</span>
                    <span className="rounded-md bg-purple-500/20 px-1.5 py-0.5 text-[10px] font-mono">
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
                                : 'text-amber-600 dark:text-amber-400 hover:bg-amber-500/10'
                        }`}
                    >
                        <span>🎙️ Podcast</span>
                        <span className="rounded-md bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-mono">
                            {counts.podcast}
                        </span>
                    </button>
                )}
            </div>

            {/* Ações em lote caso haja selecionados */}
            {selected.length > 0 && (
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-card border border-border">
                    <span className="text-xs text-muted-foreground font-mono mr-2">
                        {selected.length} selecionado(s)
                    </span>
                    <ConfirmButton
                        variant="default"
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs h-8 px-3 rounded-lg"
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
                        className="text-xs h-8 px-3 rounded-lg"
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
                <div className="grid gap-6 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                    {filteredClips.map((clip) => {
                        const isPol = (clip.niche ?? '').toLowerCase().includes('politica') || (clip.destinationChannelName ?? '').toLowerCase().includes('política');
                        const bgGradient = isPol ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)' : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';

                        return (
                            <article
                                key={clip.id}
                                className="group rounded-2xl border border-border bg-card overflow-hidden flex flex-col hover:border-primary/40 transition-all shadow-xs"
                            >
                                <div className="relative aspect-video overflow-hidden" style={{ background: bgGradient }}>
                                    <div className="absolute inset-0 grid place-items-center">
                                        <button
                                            type="button"
                                            onClick={() => setModalClip(clip)}
                                            className="w-12 h-12 rounded-full bg-black/50 backdrop-blur-md border border-white/20 grid place-items-center text-white group-hover:scale-105 transition-transform"
                                            title="Abrir preview no celular (9:16) ou computador (16:9)"
                                        >
                                            <Play className="w-5 h-5 ml-0.5 fill-white" />
                                        </button>
                                    </div>
                                    <span className="absolute left-2.5 top-2.5 font-semibold text-[11px] px-2 py-0.5 rounded-md bg-black/60 text-white backdrop-blur-md border border-white/10">
                                        {isPol ? '🏛️ Política' : '⚽ Futebol'}
                                    </span>
                                    <span className="absolute right-2.5 top-2.5">
                                        <FormatBadge format={clip.format} />
                                    </span>
                                    <span className="absolute left-2.5 bottom-2.5 font-mono text-[11px] px-2 py-0.5 rounded-md bg-black/60 text-white backdrop-blur-md border border-white/10">
                                        {clip.trecho}
                                    </span>
                                    <span className="absolute right-2.5 bottom-2.5">
                                        <ScoreBadge score={clip.score} />
                                    </span>
                                </div>

                                {previewingId === clip.id && (
                                    <div className="p-3 bg-black/90 border-b border-border">
                                        <video controls autoPlay className="w-full rounded-lg max-h-[220px]" src={clip.previewUrl} />
                                    </div>
                                )}

                                <div className="p-4 flex flex-col gap-3 flex-1">
                                    <div className="flex items-start gap-2">
                                        <Checkbox
                                            checked={selected.includes(clip.id)}
                                            onCheckedChange={() => toggle(clip.id)}
                                            className="mt-1"
                                        />
                                        <div className="font-semibold text-sm leading-snug tracking-tight text-foreground line-clamp-2" title={clip.title}>
                                            {clip.title}
                                        </div>
                                    </div>

                                    <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                                        <span className="font-mono px-1.5 py-0.5 rounded border border-border">#{clip.id}</span>
                                        <span className="truncate">{clip.destinationChannelName ?? 'Canal Destino'}</span>
                                    </div>

                                    <div className="flex-1" />

                                    <div className="flex items-center gap-2 pt-2 border-t border-border/60">
                                        <button
                                            type="button"
                                            onClick={() => setModalClip(clip)}
                                            className="inline-flex items-center justify-center gap-1 text-xs font-semibold text-zinc-300 hover:text-white px-2.5 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 transition-colors shrink-0"
                                            title="Abrir preview no celular (9:16) ou computador (16:9)"
                                        >
                                            <Eye className="w-3.5 h-3.5 text-sky-400" />
                                            <span>Preview</span>
                                        </button>
                                        <ConfirmButton
                                            variant="outline"
                                            size="sm"
                                            className="text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 border-emerald-500/30 font-semibold text-xs h-8 px-4 rounded-lg flex-1"
                                            description={`Aprovar clip #${clip.id} para publicação?`}
                                            onConfirm={() => post(`/painel/clips/${clip.id}/approve`)}
                                        >
                                            Aprovar
                                        </ConfirmButton>
                                        <ConfirmButton
                                            variant="destructive"
                                            size="sm"
                                            className="text-xs h-8 px-3 rounded-lg"
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
                <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-xs">
                    <Table className="w-full text-xs">
                        <TableHeader className="bg-muted/40 border-b border-border">
                            <TableRow>
                                <TableHead className="w-8 pl-4">
                                    <Checkbox
                                        checked={selected.length > 0 && selected.length === ids.length}
                                        onCheckedChange={() => toggleAll(ids)}
                                    />
                                </TableHead>
                                <TableHead className="px-4 py-3 font-bold text-[11px] tracking-wider text-muted-foreground uppercase">
                                    CLIPE
                                </TableHead>
                                <TableHead className="px-4 py-3 font-bold text-[11px] tracking-wider text-muted-foreground uppercase">
                                    VÍDEO FONTE
                                </TableHead>
                                <TableHead className="px-4 py-3 font-bold text-[11px] tracking-wider text-muted-foreground uppercase">
                                    TRECHO
                                </TableHead>
                                <TableHead className="px-4 py-3 font-bold text-[11px] tracking-wider text-muted-foreground uppercase">
                                    DESTINO
                                </TableHead>
                                <TableHead className="px-4 py-3 font-bold text-[11px] tracking-wider text-muted-foreground uppercase">
                                    SCORE
                                </TableHead>
                                <TableHead className="px-4 py-3 font-bold text-[11px] tracking-wider text-muted-foreground uppercase text-right pr-5">
                                    AÇÕES
                                </TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredClips.map((clip) => {
                                const isPol = (clip.niche ?? '').toLowerCase().includes('politica') || (clip.destinationChannelName ?? '').toLowerCase().includes('política');
                                const bgGradient = isPol ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)' : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';

                                return (
                                    <TableRow key={clip.id} className="hover:bg-muted/30 border-b border-border/60">
                                        <TableCell className="pl-4">
                                            <Checkbox
                                                checked={selected.includes(clip.id)}
                                                onCheckedChange={() => toggle(clip.id)}
                                            />
                                        </TableCell>

                                        {/* Coluna CLIPE: Thumbnail + Título + Badges (Nicho e Formato) */}
                                        <TableCell className="px-4 py-3 max-w-[360px]">
                                            <div className="flex items-start gap-3">
                                                <div
                                                    className="w-12 h-9 rounded-lg shrink-0 grid place-items-center text-white shadow-xs cursor-pointer hover:opacity-90 transition-opacity"
                                                    style={{ background: bgGradient }}
                                                    onClick={() => setModalClip(clip)}
                                                    title="Clique para ver o preview no celular (9:16) ou computador (16:9)"
                                                >
                                                    <Play className="w-3.5 h-3.5 ml-0.5 fill-white" />
                                                </div>
                                                <div className="min-w-0 flex-1">
                                                    <div className="font-semibold text-sm text-foreground tracking-tight line-clamp-1" title={clip.title}>
                                                        {clip.title}
                                                    </div>
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <NicheBadge niche={clip.niche} channelName={clip.destinationChannelName} />
                                                        <FormatBadge format={clip.format} />
                                                        <button
                                                            type="button"
                                                            onClick={() => setPreviewingId(previewingId === clip.id ? null : clip.id)}
                                                            className="text-[11px] text-amber-500 underline hover:text-amber-400 font-medium ml-1"
                                                        >
                                                            {previewingId === clip.id ? 'Fechar vídeo' : 'Vídeo rápido'}
                                                        </button>
                                                        <button
                                                            type="button"
                                                            onClick={() => setModalClip(clip)}
                                                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-zinc-300 hover:text-white px-2 py-0.5 rounded-md bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 transition-all shadow-xs ml-1"
                                                            title="Abrir preview no celular (9:16) ou computador (16:9)"
                                                        >
                                                            <Eye className="w-3 h-3 text-sky-400" />
                                                            <span>Preview Completo</span>
                                                        </button>
                                                    </div>

                                                    {previewingId === clip.id && (
                                                        <div className="mt-2 p-2 bg-black/90 rounded-lg">
                                                            <video controls autoPlay className="w-[260px] rounded" src={clip.previewUrl} />
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </TableCell>

                                        {/* Coluna VÍDEO FONTE */}
                                        <TableCell className="px-4 py-3 max-w-[180px]">
                                            <div className="text-xs text-foreground font-medium truncate" title={clip.sourceVideoTitle ?? ''}>
                                                {clip.sourceVideoTitle ?? '—'}
                                            </div>
                                            <div className="text-[11px] text-muted-foreground truncate">
                                                {clip.sourceChannelName ?? 'Canal Fonte'}
                                            </div>
                                        </TableCell>

                                        {/* Coluna TRECHO */}
                                        <TableCell className="px-4 py-3 font-mono text-xs text-muted-foreground whitespace-nowrap">
                                            {clip.trecho}
                                        </TableCell>

                                        {/* Coluna DESTINO */}
                                        <TableCell className="px-4 py-3 text-xs font-medium text-foreground whitespace-nowrap">
                                            {clip.destinationChannelName ?? '—'}
                                        </TableCell>

                                        {/* Coluna SCORE */}
                                        <TableCell className="px-4 py-3 whitespace-nowrap">
                                            <ScoreBadge score={clip.score} />
                                        </TableCell>

                                        {/* Coluna AÇÕES */}
                                        <TableCell className="px-4 py-3 text-right pr-5 whitespace-nowrap">
                                            <div className="flex items-center justify-end gap-2">
                                                <ConfirmButton
                                                    variant="outline"
                                                    size="sm"
                                                    className="text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 border-emerald-500/30 font-semibold text-xs h-8 px-3 rounded-lg"
                                                    description={`Aprovar clip #${clip.id} para publicação?`}
                                                    onConfirm={() => post(`/painel/clips/${clip.id}/approve`)}
                                                >
                                                    Aprovar
                                                </ConfirmButton>

                                                <ConfirmButton
                                                    variant="destructive"
                                                    size="sm"
                                                    className="text-xs h-8 px-3 rounded-lg"
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
        <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-xs">
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
                            <TableCell className="px-5 py-3 font-medium text-foreground max-w-[300px] truncate">{clip.title}</TableCell>
                            <TableCell className="px-5 py-3">
                                <NicheBadge niche={clip.niche} channelName={clip.destinationChannelName} />
                            </TableCell>
                            <TableCell className="px-5 py-3">
                                <FormatBadge format={clip.format} />
                            </TableCell>
                            <TableCell className="px-5 py-3">
                                <ScoreBadge score={clip.score} />
                            </TableCell>
                            <TableCell className="px-5 py-3 text-muted-foreground font-mono text-[11px]">{clip.createdAt}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}

function FailuresTable({
    clips,
    failedSourceVideoCount,
}: {
    clips: ClipRow[];
    failedSourceVideoCount: number;
}) {
    if (clips.length === 0 && failedSourceVideoCount === 0) {
        return <EmptyState message="Nenhuma falha recente no pipeline" />;
    }

    return (
        <div className="flex flex-col gap-4">
            {failedSourceVideoCount > 0 && (
                <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive flex items-center justify-between text-xs">
                    <span>⚠️ {failedSourceVideoCount} vídeo(s) fonte falharam no download ou processamento.</span>
                    <a href="/painel/videos?tab=falharam" className="underline font-semibold">
                        Ver falhas em Vídeos →
                    </a>
                </div>
            )}

            {clips.length > 0 && (
                <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-xs">
                    <Table className="w-full text-xs">
                        <TableHeader className="bg-muted/40">
                            <TableRow>
                                <TableHead className="px-5 py-3 font-semibold">ID</TableHead>
                                <TableHead className="px-5 py-3 font-semibold">Título & Erro</TableHead>
                                <TableHead className="px-5 py-3 font-semibold">Canal Destino</TableHead>
                                <TableHead className="px-5 py-3 font-semibold">Data</TableHead>
                                <TableHead className="px-5 py-3 font-semibold text-right">Ação</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {clips.map((clip) => (
                                <TableRow key={clip.id} className="hover:bg-muted/30">
                                    <TableCell className="px-5 py-3 font-mono text-muted-foreground">#{clip.id}</TableCell>
                                    <TableCell className="px-5 py-3 max-w-[350px]">
                                        <div className="font-medium text-foreground">{clip.title}</div>
                                        {clip.uploadError && (
                                            <span className="text-[11px] text-destructive block truncate mt-0.5" title={clip.uploadError}>
                                                {clip.uploadError}
                                            </span>
                                        )}
                                    </TableCell>
                                    <TableCell className="px-5 py-3">
                                        <NicheBadge niche={clip.niche} channelName={clip.destinationChannelName} />
                                    </TableCell>
                                    <TableCell className="px-5 py-3 text-muted-foreground font-mono text-[11px]">{clip.updatedAt}</TableCell>
                                    <TableCell className="px-5 py-3 text-right">
                                        <ConfirmButton
                                            variant="outline"
                                            size="sm"
                                            className="h-8 text-xs rounded-lg"
                                            description={`Reenviar clip #${clip.id} para reprocessamento?`}
                                            onConfirm={() => post(`/painel/clips/${clip.id}/reprocess`)}
                                        >
                                            Reprocessar
                                        </ConfirmButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
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
            <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-2xl border border-border bg-card w-fit">
                <button
                    type="button"
                    onClick={() => setMainTab('pending')}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                        mainTab === 'pending'
                            ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>🎯 Fila de aprovação</span>
                    <span
                        className={`rounded-md px-2 py-0.5 text-[10.5px] font-mono font-bold transition-colors ${
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
                            ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>⚡ Processados / Janela Ativa</span>
                    <span
                        className={`rounded-md px-2 py-0.5 text-[10.5px] font-mono font-bold transition-colors ${
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
                            ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>🚀 Prontos para subir</span>
                    <span
                        className={`rounded-md px-2 py-0.5 text-[10.5px] font-mono font-bold transition-colors ${
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
                            ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>⚠️ Falhas recentes</span>
                    <span
                        className={`rounded-md px-2 py-0.5 text-[10.5px] font-mono font-bold transition-colors ${
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
            {mainTab === 'failures' && <FailuresTable clips={failures} failedSourceVideoCount={failedSourceVideoCount} />}
        </div>
    );
}
