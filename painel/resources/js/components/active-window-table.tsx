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
import { GripVerticalIcon, PauseIcon, PlayIcon, ArrowUpIcon } from 'lucide-react';

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

function ScoreBadge({ score }: { score: number | null }) {
    if (score === null) {
        return <Badge variant="secondary">—</Badge>;
    }
    return <Badge variant={score >= 7 ? 'default' : 'destructive'}>{score}</Badge>;
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
        <div className="flex flex-wrap items-center gap-1">
            {video.paused ? (
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => postAction(`/painel/videos/${video.id}/resume`)}
                >
                    <PlayIcon className="size-3.5" />
                    Retomar
                </Button>
            ) : (
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => postAction(`/painel/videos/${video.id}/pause`)}
                >
                    <PauseIcon className="size-3.5" />
                    Pausar
                </Button>
            )}
            <Button
                variant="outline"
                size="sm"
                onClick={() => postAction(`/painel/videos/${video.id}/prioritize`)}
            >
                <ArrowUpIcon className="size-3.5" />
                Priorizar
            </Button>
            {video.canDelete ? (
                <ConfirmButton
                    variant="destructive"
                    size="sm"
                    description={`Apagar o arquivo bruto de "${video.title}"? Os clips já cortados NÃO são afetados; libera vaga na janela.`}
                    onConfirm={() => postAction(`/painel/videos/${video.id}/delete`)}
                >
                    Apagar
                </ConfirmButton>
            ) : (
                <Button variant="destructive" size="sm" disabled title="Arquivo em uso ou clips ainda precisam do bruto">
                    Apagar
                </Button>
            )}
        </div>
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
    onToggleSelect: () => void;
    dragHandle?: ReactNode;
}) {
    return (
        <>
            <TableCell className="w-8">
                <Checkbox
                    checked={isSelected}
                    disabled={!video.canDelete}
                    onCheckedChange={onToggleSelect}
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
            <TableCell className="text-muted-foreground">{video.sourceChannelName ?? '—'}</TableCell>
            <TableCell>
                <Badge variant={video.format === 'longo' ? 'default' : 'secondary'}>
                    {video.format === 'longo' ? 'Longo' : 'Curto'}
                </Badge>
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
            <TableCell className="text-muted-foreground">{video.publishedAt ?? '—'}</TableCell>
            <TableCell>
                <ScoreBadge score={video.score} />
            </TableCell>
            <TableCell className="text-muted-foreground">{video.clipCount}</TableCell>
            <TableCell>
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
    onToggleSelect: () => void;
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
                onToggleSelect={onToggleSelect}
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
    onToggleSelect: (id: number) => void;
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
                <TableHead>Publicado</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Clips</TableHead>
                <TableHead>Ações</TableHead>
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
                                    onToggleSelect={() => onToggleSelect(video.id)}
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
                                    onToggleSelect={() => onToggleSelect(video.id)}
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
    const { selected, toggle, toggleAll, clear } = useSelection();
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
