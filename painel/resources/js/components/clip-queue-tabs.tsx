import { useState } from 'react';
import { router } from '@inertiajs/react';
import type { FormDataConvertible } from '@inertiajs/core';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ConfirmButton } from '@/components/confirm-button';
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
    return <Badge variant={format === 'longo' ? 'default' : 'secondary'}>{format === 'longo' ? 'Longo' : 'Curto'}</Badge>;
}

function TitleCell({ clip }: { clip: ClipRow }) {
    const [open, setOpen] = useState(false);

    return (
        <div className="max-w-[220px]">
            <span className="block truncate" title={clip.title}>
                {clip.title}
            </span>
            <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="mt-0.5 text-xs text-amber-500 underline hover:text-amber-400"
            >
                {open ? 'Ocultar clip' : 'Ver clip'}
            </button>
            {open && (
                <video controls preload="metadata" className="mt-1.5 w-[200px] rounded" src={clip.previewUrl} />
            )}
        </div>
    );
}

function EmptyState({ message }: { message: string }) {
    return <div className="flex items-center justify-center rounded-lg border border-dashed py-12 text-sm text-muted-foreground">{message}</div>;
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
            <span className="inline-flex items-center gap-1 rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-xs font-semibold text-purple-600 dark:text-purple-400">
                🏛️ {channelName ?? 'Política'}
            </span>
        );
    }
    if (n === 'podcast' || ch.includes('podcast')) {
        return (
            <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
                🎙️ {channelName ?? 'Podcast'}
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
            ⚽ {channelName ?? 'Futebol'}
        </span>
    );
}

function ScoreBadge({ score }: { score: number | null }) {
    if (score === null || score === undefined) return <span className="text-muted-foreground">—</span>;

    if (score >= 9) {
        return (
            <span className="inline-flex items-center gap-1 rounded-md border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-xs font-bold text-red-500 dark:text-red-400">
                🔥 {score}/10
            </span>
        );
    }
    if (score >= 8) {
        return (
            <span className="inline-flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                ⭐ {score}/10
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 rounded-md border border-zinc-500/30 bg-zinc-500/10 px-2 py-0.5 text-xs font-medium text-zinc-400">
            {score}/10
        </span>
    );
}

function PendingTable({ clips }: { clips: ClipRow[] }) {
    const [subTab, setSubTab] = useState<'todos' | 'futebol' | 'politica' | 'podcast'>('todos');
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
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
        <div>
            {/* Subtabs de nicho + Toggle Grid/List */}
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-1.5 w-fit">
                    <button
                        type="button"
                        onClick={() => setSubTab('todos')}
                        className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                            subTab === 'todos'
                                ? 'bg-primary text-primary-foreground shadow-sm'
                                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                        }`}
                    >
                        <span>Todos</span>
                        <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
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

                {/* Alternador de Modo Quadro (Grid) e Modo Tabela (List) */}
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

            <div className="mb-3 flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => toggleAll(ids)}>
                    Marcar/desmarcar todos
                </Button>
                <ConfirmButton
                    variant="default"
                    size="sm"
                    disabled={selected.length === 0}
                    description={`Aprovar ${selected.length} clip(s) selecionado(s)?`}
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
                    disabled={selected.length === 0}
                    description={`Rejeitar ${selected.length} clip(s) selecionado(s)? Os MP4s serão removidos.`}
                    onConfirm={() => {
                        post('/painel/clips/bulk-reject', { ids: selected });
                        clear();
                    }}
                >
                    Rejeitar selecionados ({selected.length})
                </ConfirmButton>
            </div>

            {/* RENDERIZAÇÃO DO MODO QUADRO OU TABELA */}
            {viewMode === 'grid' ? (
                <div className="grid gap-5 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                    {filteredClips.map((clip) => {
                        const isPol = (clip.niche ?? '').toLowerCase() === 'politica' || (clip.destinationChannelName ?? '').toLowerCase().includes('política');
                        const bgGradient = isPol ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)' : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';

                        return (
                            <article
                                key={clip.id}
                                className="group rounded-2xl border border-border bg-card overflow-hidden flex flex-col hover:border-primary/40 transition-all shadow-xs"
                            >
                                <div className="relative aspect-video overflow-hidden" style={{ background: bgGradient }}>
                                    <div className="absolute inset-0 grid place-items-center">
                                        <div className="w-12 h-12 rounded-full bg-black/50 backdrop-blur-md border border-white/20 grid place-items-center text-white group-hover:scale-105 transition-transform">
                                            ▶
                                        </div>
                                    </div>
                                    <span className="absolute left-2.5 top-2.5">
                                        <NicheBadge niche={clip.niche} channelName={clip.destinationChannelName} />
                                    </span>
                                    <span className="absolute right-2.5 top-2.5 font-mono text-[11px] px-2 py-1 rounded-lg bg-black/60 text-white backdrop-blur-md border border-white/10">
                                        {clip.format === 'longo' ? 'Longo' : 'Curto'}
                                    </span>
                                    <span className="absolute right-2.5 bottom-2.5">
                                        <ScoreBadge score={clip.score} />
                                    </span>
                                    <span className="absolute left-2.5 bottom-2.5 font-mono text-[10.5px] px-2 py-0.5 rounded-md bg-black/60 text-white backdrop-blur-md border border-white/10">
                                        {clip.trecho}
                                    </span>
                                </div>
                                <div className="p-4 flex flex-col gap-3 flex-1">
                                    <div className="flex items-start gap-2">
                                        <Checkbox
                                            checked={selected.includes(clip.id)}
                                            onCheckedChange={() => toggle(clip.id)}
                                            className="mt-1"
                                        />
                                        <div className="font-semibold text-sm leading-snug tracking-tight text-foreground line-clamp-2">
                                            {clip.title}
                                        </div>
                                    </div>
                                    <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                                        <span className="font-mono px-1.5 py-0.5 rounded border border-border">
                                            #{clip.id}
                                        </span>
                                        <span className="truncate">{clip.sourceChannelName ?? 'Canal Fonte'}</span>
                                    </div>
                                    <div className="flex-1" />
                                    <div className="flex items-center gap-2 pt-2 border-t border-border/60">
                                        <ConfirmButton
                                            variant="default"
                                            size="sm"
                                            className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                                            description={`Aprovar clip #${clip.id}?`}
                                            onConfirm={() => post(`/painel/clips/${clip.id}/approve`)}
                                        >
                                            Aprovar
                                        </ConfirmButton>
                                        <ConfirmButton
                                            variant="destructive"
                                            size="sm"
                                            description={`Rejeitar clip #${clip.id}? O MP4 será removido.`}
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
                <div className="overflow-x-auto rounded-lg border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-8" />
                            <TableHead>ID</TableHead>
                            <TableHead>Título</TableHead>
                            <TableHead>Vídeo fonte</TableHead>
                            <TableHead>Trecho</TableHead>
                            <TableHead>Canal fonte</TableHead>
                            <TableHead>Formato</TableHead>
                            <TableHead>Destino</TableHead>
                            <TableHead>Score</TableHead>
                            <TableHead>Ações</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filteredClips.map((clip) => (
                            <TableRow key={clip.id}>
                                <TableCell>
                                    <Checkbox checked={selected.includes(clip.id)} onCheckedChange={() => toggle(clip.id)} />
                                </TableCell>
                                <TableCell className="text-muted-foreground">{clip.id}</TableCell>
                                <TableCell>
                                    <TitleCell clip={clip} />
                                </TableCell>
                                <TableCell className="max-w-[140px] truncate text-muted-foreground" title={clip.sourceVideoTitle ?? ''}>
                                    {clip.sourceVideoTitle ?? '—'}
                                </TableCell>
                                <TableCell className="text-muted-foreground">{clip.trecho}</TableCell>
                                <TableCell className="text-muted-foreground">{clip.sourceChannelName ?? '—'}</TableCell>
                                <TableCell>
                                    <FormatBadge format={clip.format} />
                                </TableCell>
                                <TableCell>
                                    <NicheBadge niche={clip.niche} channelName={clip.destinationChannelName} />
                                </TableCell>
                                <TableCell>
                                    <ScoreBadge score={clip.score} />
                                </TableCell>
                                <TableCell>
                                    <div className="flex flex-col items-start gap-1">
                                        <ConfirmButton
                                            variant="outline"
                                            size="sm"
                                            description={`Aprovar clip #${clip.id}?`}
                                            onConfirm={() => post(`/painel/clips/${clip.id}/approve`)}
                                        >
                                            Aprovar
                                        </ConfirmButton>
                                        <ConfirmButton
                                            variant="destructive"
                                            size="sm"
                                            description={`Rejeitar clip #${clip.id}? O MP4 será removido do disco.`}
                                            onConfirm={() => post(`/painel/clips/${clip.id}/reject`)}
                                        >
                                            Rejeitar
                                        </ConfirmButton>
                                    </div>
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

function QueuedTable({ clips }: { clips: ClipRow[] }) {
    const { selected, toggle, toggleAll, clear } = useSelection();
    const ids = clips.map((c) => c.id);

    if (clips.length === 0) return <EmptyState message="Nenhum clip aprovado aguardando publicação" />;

    return (
        <div>
            <p className="mb-3 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3 py-2 text-sm text-blue-200">
                Publica automaticamente em ordem (mais antigo primeiro), respeitando o limite diário de uploads. Se
                não fizer nada, a fila segue sozinha. Use &quot;Rejeitar&quot; só se a notícia ficou velha/irrelevante.
            </p>
            <div className="mb-3 flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => toggleAll(ids)}>
                    Marcar/desmarcar todos
                </Button>
                <ConfirmButton
                    variant="destructive"
                    size="sm"
                    disabled={selected.length === 0}
                    description={`Rejeitar ${selected.length} clip(s) selecionado(s)? Os MP4s serão removidos.`}
                    onConfirm={() => {
                        post('/painel/clips/bulk-reject', { ids: selected });
                        clear();
                    }}
                >
                    Rejeitar selecionados ({selected.length})
                </ConfirmButton>
            </div>
            <div className="overflow-x-auto rounded-lg border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-8" />
                            <TableHead>Pos.</TableHead>
                            <TableHead>ID</TableHead>
                            <TableHead>Título</TableHead>
                            <TableHead>Vídeo fonte</TableHead>
                            <TableHead>Trecho</TableHead>
                            <TableHead>Canal fonte</TableHead>
                            <TableHead>Formato</TableHead>
                            <TableHead>Destino</TableHead>
                            <TableHead>Score</TableHead>
                            <TableHead>Aprovado</TableHead>
                            <TableHead>Ações</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {clips.map((clip, index) => (
                            <TableRow key={clip.id}>
                                <TableCell>
                                    <Checkbox checked={selected.includes(clip.id)} onCheckedChange={() => toggle(clip.id)} />
                                </TableCell>
                                <TableCell className="text-muted-foreground">#{index + 1}</TableCell>
                                <TableCell className="text-muted-foreground">{clip.id}</TableCell>
                                <TableCell>
                                    <TitleCell clip={clip} />
                                </TableCell>
                                <TableCell className="max-w-[140px] truncate text-muted-foreground" title={clip.sourceVideoTitle ?? ''}>
                                    {clip.sourceVideoTitle ?? '—'}
                                </TableCell>
                                <TableCell className="text-muted-foreground">{clip.trecho}</TableCell>
                                <TableCell className="text-muted-foreground">{clip.sourceChannelName ?? '—'}</TableCell>
                                <TableCell>
                                    <FormatBadge format={clip.format} />
                                </TableCell>
                                <TableCell className="text-muted-foreground">{clip.destinationChannelName ?? '—'}</TableCell>
                                <TableCell>
                                    <Badge variant="outline">{clip.score ?? '—'}</Badge>
                                </TableCell>
                                <TableCell className="text-muted-foreground">{clip.createdAt}</TableCell>
                                <TableCell>
                                    <ConfirmButton
                                        variant="destructive"
                                        size="sm"
                                        description={`Rejeitar clip #${clip.id}? O MP4 será removido do disco e ele sai da fila.`}
                                        onConfirm={() => post(`/painel/clips/${clip.id}/reject`)}
                                    >
                                        Rejeitar
                                    </ConfirmButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}

function FailuresTable({ clips, failedSourceVideoCount }: { clips: ClipRow[]; failedSourceVideoCount: number }) {
    if (clips.length === 0) return <EmptyState message="Nenhuma falha registrada" />;

    return (
        <div>
            {failedSourceVideoCount > 0 && (
                <p className="mb-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                    Vídeos fonte com falha: <strong>{failedSourceVideoCount}</strong>
                </p>
            )}
            <div className="overflow-x-auto rounded-lg border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>ID</TableHead>
                            <TableHead>Título</TableHead>
                            <TableHead>Destino</TableHead>
                            <TableHead>Quando</TableHead>
                            <TableHead>Ações</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {clips.map((clip) => (
                            <TableRow key={clip.id}>
                                <TableCell className="text-muted-foreground">{clip.id}</TableCell>
                                <TableCell className="max-w-[260px]">
                                    <span className="block truncate" title={clip.title}>
                                        {clip.title}
                                    </span>
                                    {clip.uploadError && (
                                        <span
                                            className="mt-0.5 block truncate text-xs text-red-400"
                                            title={clip.uploadError}
                                        >
                                            {clip.uploadError}
                                        </span>
                                    )}
                                </TableCell>
                                <TableCell className="text-muted-foreground">{clip.destinationChannelName ?? '—'}</TableCell>
                                <TableCell className="text-muted-foreground">{clip.updatedAt}</TableCell>
                                <TableCell>
                                    <ConfirmButton
                                        variant="outline"
                                        size="sm"
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
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>🎯 Fila de aprovação</span>
                    <span className="rounded-md bg-muted px-2 py-0.5 text-[10.5px] font-mono">
                        {pendingClips.length}
                    </span>
                </button>

                <button
                    type="button"
                    onClick={() => setMainTab('active_window')}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                        mainTab === 'active_window'
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>⚡ Processados / Janela Ativa</span>
                    <span className="rounded-md bg-muted px-2 py-0.5 text-[10.5px] font-mono">
                        {activeWindow.length}
                    </span>
                </button>

                <button
                    type="button"
                    onClick={() => setMainTab('queued')}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                        mainTab === 'queued'
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>🚀 Prontos para subir</span>
                    <span className="rounded-md bg-muted px-2 py-0.5 text-[10.5px] font-mono">
                        {queuedClips.length}
                    </span>
                </button>

                <button
                    type="button"
                    onClick={() => setMainTab('failures')}
                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                        mainTab === 'failures'
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }`}
                >
                    <span>⚠️ Falhas recentes</span>
                    <span className="rounded-md bg-muted px-2 py-0.5 text-[10.5px] font-mono">
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
