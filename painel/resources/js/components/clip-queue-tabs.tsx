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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { ClipRow } from '@/types/dashboard';

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

function PendingTable({ clips }: { clips: ClipRow[] }) {
    const { selected, toggle, toggleAll, clear } = useSelection();
    const ids = clips.map((c) => c.id);

    if (clips.length === 0) return <EmptyState message="Nenhum clip aguardando aprovação" />;

    return (
        <div>
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
                        {clips.map((clip) => (
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
                                <TableCell className="text-muted-foreground">{clip.destinationChannelName ?? '—'}</TableCell>
                                <TableCell>
                                    <Badge variant="outline">{clip.score ?? '—'}</Badge>
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
}: {
    pendingClips: ClipRow[];
    queuedClips: ClipRow[];
    failures: ClipRow[];
    failedSourceVideoCount: number;
}) {
    return (
        <div className="px-4 lg:px-6">
            <Tabs defaultValue="pending">
                <TabsList>
                    <TabsTrigger value="pending">
                        Fila de aprovação
                        <Badge variant="secondary" className="ml-1.5">
                            {pendingClips.length}
                        </Badge>
                    </TabsTrigger>
                    <TabsTrigger value="queued">
                        Na fila (aguardando cota)
                        <Badge variant="secondary" className="ml-1.5">
                            {queuedClips.length}
                        </Badge>
                    </TabsTrigger>
                    <TabsTrigger value="failures">
                        Últimas falhas
                        <Badge variant="secondary" className="ml-1.5">
                            {failures.length}
                        </Badge>
                    </TabsTrigger>
                </TabsList>
                <TabsContent value="pending" className="mt-4">
                    <PendingTable clips={pendingClips} />
                </TabsContent>
                <TabsContent value="queued" className="mt-4">
                    <QueuedTable clips={queuedClips} />
                </TabsContent>
                <TabsContent value="failures" className="mt-4">
                    <FailuresTable clips={failures} failedSourceVideoCount={failedSourceVideoCount} />
                </TabsContent>
            </Tabs>
        </div>
    );
}
