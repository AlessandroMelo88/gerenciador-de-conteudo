import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { router } from '@inertiajs/react';
import { toast } from 'sonner';
import {
    DndContext,
    KeyboardSensor,
    PointerSensor,
    closestCenter,
    type DragEndEvent,
    useSensor,
    useSensors,
} from '@dnd-kit/core';
import {
    SortableContext,
    arrayMove,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVerticalIcon, PauseIcon, PlayIcon, ArrowUpIcon, MoreVerticalIcon, TrashIcon } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ConfirmButton } from '@/components/confirm-button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Progress } from '@/components/ui/progress';
import type { ActiveWindowVideo } from '@/types/dashboard';
import { cn } from '@/lib/utils';

const STATUS_LABEL: Record<string, string> = {
    pending: 'Pendente',
    downloading: 'Baixando',
    downloaded: 'Baixado',
    transcribing: 'Transcrevendo',
    selecting: 'Selecionando',
    cutting: 'Cortando',
    publishing: 'Publicando',
    published: 'Publicado',
    failed: 'Falha',
};

function ScoreBadge({ score }: { score: number | null | undefined }) {
    if (score === null || score === undefined) {
        return <span className="text-muted-foreground">—</span>;
    }

    if (score >= 9) {
        return (
            <span className="inline-flex items-center gap-1 rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs font-bold text-red-500 dark:text-red-400 shadow-xs">
                🔥 {score}/10
            </span>
        );
    }
    if (score >= 8) {
        return (
            <span className="inline-flex items-center gap-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400 shadow-xs">
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

function NicheBadge({ niche, channelName }: { niche?: string | null; channelName?: string | null }) {
    const n = (niche ?? '').toLowerCase();
    const ch = (channelName ?? '').toLowerCase();

    if (n === 'politica' || ch.includes('política') || ch.includes('politica')) {
        return (
            <span className="inline-flex items-center gap-1 rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-[11px] font-semibold text-purple-600 dark:text-purple-400">
                🏛️ {channelName ?? 'Cortes da Política'}
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
            ⚽ {channelName ?? 'Futebol em Cortes'}
        </span>
    );
}

function FormatBadge({ format }: { format?: string | null }) {
    const isLongo = format === 'longo';
    if (isLongo) {
        return (
            <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/40 bg-gradient-to-r from-amber-500/15 to-orange-500/15 px-2 py-0.5 text-[11px] font-bold text-amber-500 dark:text-amber-400 shadow-xs">
                ✨ Longo
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-800/80 px-2 py-0.5 text-[11px] font-semibold text-zinc-300">
            📱 Curto
        </span>
    );
}

function useSelection(items: ActiveWindowVideo[]) {
    const [selected, setSelected] = useState<number[]>([]);
    const [lastSelectedId, setLastSelectedId] = useState<number | null>(null);

    const toggle = (id: number, shiftKey = false) => {
        setSelected((prev) => {
            const isCurrentlySelected = prev.includes(id);

            if (shiftKey && lastSelectedId !== null) {
                const lastIdx = items.findIndex((x) => x.id === lastSelectedId);
                const currIdx = items.findIndex((x) => x.id === id);

                if (lastIdx !== -1 && currIdx !== -1) {
                    const start = Math.min(lastIdx, currIdx);
                    const end = Math.max(lastIdx, currIdx);
                    const range = items
                        .slice(start, end + 1)
                        .filter((v) => v.canDelete)
                        .map((v) => v.id);

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

function postAction(url: string, data: Record<string, unknown> = {}) {
    router.post(url, data, {
        preserveScroll: true,
        onSuccess: (page) => {
            const flash = page.props.flash as { success?: string | null; error?: string | null };
            if (flash?.success) toast.success(flash.success);
            if (flash?.error) toast.error(flash.error);
        },
    });
}

function VideoActions({ video }: { video: ActiveWindowVideo }) {
    return (
        <AlertDialog>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="size-8" title="Ações">
                        <MoreVerticalIcon className="size-4" />
                        <span className="sr-only">Ações</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-40">
                    {video.paused ? (
                        <DropdownMenuItem onClick={() => postAction(`/painel/videos/${video.id}/resume`)}>
                            <PlayIcon className="mr-2 size-4" />
                            Retomar
                        </DropdownMenuItem>
                    ) : (
                        <DropdownMenuItem onClick={() => postAction(`/painel/videos/${video.id}/pause`)}>
                            <PauseIcon className="mr-2 size-4" />
                            Pausar
                        </DropdownMenuItem>
                    )}
                    <DropdownMenuItem onClick={() => postAction(`/painel/videos/${video.id}/prioritize`)}>
                        <ArrowUpIcon className="mr-2 size-4" />
                        Priorizar
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    {video.canDelete ? (
                        <AlertDialogTrigger asChild>
                            <DropdownMenuItem variant="destructive" onSelect={(e) => e.preventDefault()}>
                                <TrashIcon className="mr-2 size-4" />
                                Apagar
                            </DropdownMenuItem>
                        </AlertDialogTrigger>
                    ) : (
                        <DropdownMenuItem variant="destructive" disabled title="Arquivo em uso ou clips ainda precisam do bruto">
                            <TrashIcon className="mr-2 size-4" />
                            Apagar
                        </DropdownMenuItem>
                    )}
                </DropdownMenuContent>
            </DropdownMenu>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Tem certeza?</AlertDialogTitle>
                    <AlertDialogDescription>
                        Apagar o arquivo bruto de "{video.title}"? Os clips já cortados NÃO são afetados; libera vaga na janela.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                    <AlertDialogAction onClick={() => postAction(`/painel/videos/${video.id}/delete`)}>
                        Confirmar
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}

function VideoCells({
    video,
    isSelected,
    onToggleSelect,
    dragHandle,
}: {
    video: ActiveWindowVideo;
    isSelected: boolean;
    onToggleSelect: (shiftKey: boolean) => void;
    dragHandle?: ReactNode;
}) {
    return (
        <>
            <TableCell className="w-8">
                <Checkbox
                    checked={isSelected}
                    disabled={!video.canDelete}
                    onClick={(e) => {
                        e.stopPropagation();
                        onToggleSelect(e.shiftKey);
                    }}
                    title={!video.canDelete ? 'Arquivo em uso ou clips ainda precisam do bruto' : undefined}
                />
            </TableCell>
            <TableCell className="w-8">{dragHandle}</TableCell>
            <TableCell className="max-w-[280px] truncate" title={video.title}>
                <span className="flex items-center gap-2">
                    {video.title}
                    {video.paused && <Badge variant="outline">Pausado</Badge>}
                    {video.priority > 0 && (
                        <Badge variant="secondary" className="tabular-nums">
                            P{video.priority}
                        </Badge>
                    )}
                </span>
            </TableCell>
            <TableCell>
                <div className="flex flex-col gap-1 py-0.5 min-w-[130px]">
                    <span className="font-semibold text-xs text-foreground truncate max-w-[190px]" title={video.sourceChannelName ?? undefined}>
                        {video.sourceChannelName ?? '—'}
                    </span>
                    <div>
                        <NicheBadge niche={video.niche} channelName={video.destinationChannelName} />
                    </div>
                </div>
            </TableCell>
            <TableCell>
                <FormatBadge format={video.format} />
            </TableCell>
            <TableCell>
                <span
                    className={cn(
                        'text-muted-foreground',
                        video.processing && !video.paused && 'font-medium text-foreground',
                    )}
                >
                    {STATUS_LABEL[video.status] ?? video.status}
                </span>
            </TableCell>
            <TableCell>
                <div className="flex items-center gap-2 min-w-[110px]">
                    <Progress value={video.progress ?? 0} className="h-1.5 flex-1" />
                    <span className="text-xs text-muted-foreground tabular-nums w-8 text-right font-medium">
                        {video.progress ?? 0}%
                    </span>
                </div>
            </TableCell>
            <TableCell className="text-muted-foreground">{video.publishedAt ?? '—'}</TableCell>
            <TableCell>
                <ScoreBadge score={video.score} />
            </TableCell>
            <TableCell className="text-muted-foreground">{video.clipCount}</TableCell>
            <TableCell className="text-right">
                <VideoActions video={video} />
            </TableCell>
        </>
    );
}

function SortableRow({
    video,
    isSelected,
    onToggleSelect,
}: {
    video: ActiveWindowVideo;
    isSelected: boolean;
    onToggleSelect: (id: number, shiftKey: boolean) => void;
}) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id: video.id,
    });

    return (
        <TableRow
            ref={setNodeRef}
            style={{ transform: CSS.Transform.toString(transform), transition }}
            className={cn(isDragging && 'bg-muted/50', video.paused && 'opacity-70')}
        >
            <VideoCells
                video={video}
                isSelected={isSelected}
                onToggleSelect={(shiftKey) => onToggleSelect(video.id, shiftKey)}
                dragHandle={
                    <button
                        type="button"
                        className="cursor-grab touch-none text-muted-foreground hover:text-foreground active:cursor-grabbing"
                        aria-label="Arrastar para reordenar"
                        {...attributes}
                        {...listeners}
                    >
                        <GripVerticalIcon className="size-4" />
                    </button>
                }
            />
        </TableRow>
    );
}

function VideoTable({
    videos,
    sortable,
    onReorder,
    selected,
    onToggleSelect,
}: {
    videos: ActiveWindowVideo[];
    sortable?: boolean;
    onReorder?: (ids: number[]) => void;
    selected: number[];
    onToggleSelect: (id: number, shiftKey: boolean) => void;
}) {
    const [items, setItems] = useState(videos);
    useEffect(() => setItems(videos), [videos]);

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
        useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
    );

    function handleDragEnd(event: DragEndEvent) {
        const { active, over } = event;
        if (!over || active.id === over.id) return;
        const oldIndex = items.findIndex((v) => v.id === active.id);
        const newIndex = items.findIndex((v) => v.id === over.id);
        if (oldIndex < 0 || newIndex < 0) return;
        const next = arrayMove(items, oldIndex, newIndex);
        setItems(next);
        onReorder?.(next.map((v) => v.id));
    }

    const header = (
        <TableHeader>
            <TableRow>
                <TableHead className="w-8" />
                <TableHead className="w-8" />
                <TableHead>Título</TableHead>
                <TableHead>Canal</TableHead>
                <TableHead>Formato</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[120px]">Progresso</TableHead>
                <TableHead>Publicado</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Clips</TableHead>
                <TableHead className="w-12 text-right">Ações</TableHead>
            </TableRow>
        </TableHeader>
    );

    if (!sortable) {
        return (
            <div className="overflow-x-auto rounded-lg border">
                <Table>
                    {header}
                    <TableBody>
                        {items.map((video) => (
                            <TableRow
                                key={video.id}
                                className={cn(
                                    video.processing && 'bg-primary/5',
                                    video.paused && 'opacity-70',
                                )}
                            >
                                <VideoCells
                                    video={video}
                                    isSelected={selected.includes(video.id)}
                                    onToggleSelect={(shiftKey) => onToggleSelect(video.id, shiftKey)}
                                    dragHandle={<span className="inline-block w-4" />}
                                />
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        );
    }

    return (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <div className="overflow-x-auto rounded-lg border">
                <Table>
                    {header}
                    <SortableContext items={items.map((v) => v.id)} strategy={verticalListSortingStrategy}>
                        <TableBody>
                            {items.map((video) => (
                                <SortableRow
                                    key={video.id}
                                    video={video}
                                    isSelected={selected.includes(video.id)}
                                    onToggleSelect={onToggleSelect}
                                />
                            ))}
                        </TableBody>
                    </SortableContext>
                </Table>
            </div>
        </DndContext>
    );
}

export function ActiveWindowTable({ videos }: { videos: ActiveWindowVideo[] }) {
    const { selected, toggle, toggleAll, clear } = useSelection(videos);
    const curtoCount = videos.filter((v) => v.format === 'curto').length;
    const longoCount = videos.filter((v) => v.format === 'longo').length;
    const processing = useMemo(() => videos.filter((v) => v.processing && !v.paused), [videos]);
    const idle = useMemo(() => videos.filter((v) => !v.processing || v.paused), [videos]);
    const deletableIds = useMemo(() => videos.filter((v) => v.canDelete).map((v) => v.id), [videos]);

    useEffect(() => {
        if (videos.length === 0) return;
        const interval = setInterval(() => {
            router.reload({ only: ['activeWindow', 'overview', 'quota'] });
        }, 20000);
        return () => clearInterval(interval);
    }, [videos.length]);

    if (videos.length === 0) {
        return (
            <div className="flex items-center justify-center rounded-lg border border-dashed py-12 text-sm text-muted-foreground">
                Nenhum vídeo baixado agora — a janela está vazia, o próximo ciclo (até 20 min) repõe.
            </div>
        );
    }

    function persistReorder(ids: number[]) {
        // Mantém processando no topo da ordem persistida juntos com ociosos.
        const processingIds = processing.map((v) => v.id);
        router.post(
            '/painel/videos/reorder',
            { ids: [...processingIds, ...ids] },
            { preserveScroll: true },
        );
    }

    const defaultTab = processing.length > 0 ? 'processing' : 'idle';

    return (
        <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
                {videos.length} vídeo(s) com arquivo em disco agora ({curtoCount} curto / {longoCount} longo).
                Arraste pra reordenar a fila ociosa; pause para segurar; priorizar sobe na seleção do próximo
                ciclo.
            </p>

            <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => toggleAll(deletableIds)}>
                    Marcar/desmarcar todos
                </Button>
                <ConfirmButton
                    variant="destructive"
                    size="sm"
                    disabled={selected.length === 0}
                    description={`Apagar o arquivo bruto de ${selected.length} vídeo(s) selecionado(s)? Os clips já cortados NÃO são afetados; libera vagas na janela.`}
                    onConfirm={() => {
                        postAction('/painel/videos/bulk-delete', { ids: selected });
                        clear();
                    }}
                >
                    Apagar selecionados ({selected.length})
                </ConfirmButton>
            </div>

            <Tabs key={defaultTab} defaultValue={defaultTab}>
                <TabsList>
                    <TabsTrigger value="processing">Processando agora {processing.length}</TabsTrigger>
                    <TabsTrigger value="idle">Na janela (ociosos / pausados) {idle.length}</TabsTrigger>
                </TabsList>

                <TabsContent value="processing" className="mt-4">
                    {processing.length === 0 ? (
                        <p className="rounded-lg border border-dashed px-4 py-6 text-sm text-muted-foreground">
                            Nenhum vídeo processando agora.
                        </p>
                    ) : (
                        <VideoTable
                            videos={processing}
                            selected={selected}
                            onToggleSelect={toggle}
                        />
                    )}
                </TabsContent>

                <TabsContent value="idle" className="mt-4">
                    {idle.length === 0 ? (
                        <p className="rounded-lg border border-dashed px-4 py-6 text-sm text-muted-foreground">
                            Todos os vídeos da janela estão em processamento.
                        </p>
                    ) : (
                        <VideoTable
                            videos={idle}
                            sortable
                            onReorder={persistReorder}
                            selected={selected}
                            onToggleSelect={toggle}
                        />
                    )}
                </TabsContent>
            </Tabs>
        </div>
    );
}
