import { useState } from 'react';
import { Head, router, usePage } from '@inertiajs/react';
import { toast } from 'sonner';
import {
    ArrowUpIcon,
    CalendarIcon,
    CheckCircle2Icon,
    ShieldAlertIcon,
    SparklesIcon,
    Trash2Icon,
} from 'lucide-react';

import { ConfirmButton } from '@/components/confirm-button';
import { VideoSummaryCards, StorageMetrics, DownloadWindowMetrics } from '@/components/video-summary-cards';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { AppShell } from '@/layouts/app-shell';

type SourceVideoRow = {
    id: number;
    title: string;
    channelName: string | null;
    status: string;
    statusLabel: string;
    youtubeVideoId: string;
    hasLocalFile: boolean;
    canDelete?: boolean;
    uso: string;
    publishedAt: string | null;
    updatedAt: string | null;
};

type PageProps = {
    videos: {
        data: SourceVideoRow[];
        currentPage: number;
        lastPage: number;
        total: number;
        perPage: number;
    };
    filters: {
        tab: string;
        status: string | null;
        seguro_apagar: boolean;
        published_from: string | null;
        published_until: string | null;
        search: string | null;
        per_page: number;
    };
    statusOptions: Record<string, string>;
    storage?: StorageMetrics;
    downloadWindow?: DownloadWindowMetrics;
    auth: { user: { name: string; email: string } | null };
};

const STATUS_BADGE: Record<string, string> = {
    published: 'default',
    failed: 'destructive',
    downloading: 'secondary',
    transcribing: 'secondary',
    selecting: 'secondary',
    cutting: 'secondary',
    publishing: 'secondary',
    downloaded: 'outline',
};

const USO_BADGE: Record<string, string> = {
    'Falhou — pode apagar': 'destructive',
    'Sem uso — pode apagar': 'destructive',
    Publicado: 'default',
    'Em uso': 'secondary',
};

function applyFilters(patch: Record<string, unknown>, current: PageProps['filters']) {
    router.get(
        '/painel/videos',
        { ...current, ...patch },
        { preserveState: true, preserveScroll: true, replace: true },
    );
}

function PurgeOldDialog() {
    const [open, setOpen] = useState(false);
    const defaultDate = new Date(Date.now() - 3 * 86400000).toISOString().slice(0, 10);
    const [beforeDate, setBeforeDate] = useState(defaultDate);

    const setQuickDays = (days: number) => {
        const d = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
        setBeforeDate(d);
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" className="gap-1.5 border-destructive/30 text-destructive hover:bg-destructive/10">
                    <Trash2Icon className="h-4 w-4" />
                    Limpar vídeos antigos
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
                <DialogHeader className="gap-1">
                    <DialogTitle className="flex items-center gap-2 text-lg font-semibold">
                        <SparklesIcon className="h-5 w-5 text-primary" />
                        Limpeza de Vídeos Antigos
                    </DialogTitle>
                </DialogHeader>

                <div className="space-y-3 py-1">
                    <div className="rounded-lg border bg-card p-3 space-y-2 text-xs">
                        <div className="flex items-start gap-2">
                            <ShieldAlertIcon className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                            <div>
                                <span className="font-medium text-foreground">O que será limpo:</span>
                                <p className="text-muted-foreground mt-0.5">
                                    Apaga do banco matérias antigas sem clips e libera do HD o vídeo bruto (.mp4) de vídeos antigos já processados.
                                </p>
                            </div>
                        </div>
                        <div className="flex items-start gap-2 pt-1 border-t">
                            <CheckCircle2Icon className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                            <div>
                                <span className="font-medium text-foreground">O que permanece seguro:</span>
                                <p className="text-muted-foreground mt-0.5">
                                    Clips gerados, edições e histórico de postagens no YouTube permanecem 100% salvos.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <FieldLabel className="text-xs">Atalhos de data de corte:</FieldLabel>
                        <div className="flex gap-1.5">
                            <Button variant="outline" size="sm" type="button" className="h-7 text-xs flex-1" onClick={() => setQuickDays(3)}>
                                Há 3 dias
                            </Button>
                            <Button variant="outline" size="sm" type="button" className="h-7 text-xs flex-1" onClick={() => setQuickDays(7)}>
                                Há 7 dias
                            </Button>
                            <Button variant="outline" size="sm" type="button" className="h-7 text-xs flex-1" onClick={() => setQuickDays(30)}>
                                Há 30 dias
                            </Button>
                        </div>
                    </div>

                    <Field>
                        <FieldLabel htmlFor="before_date" className="text-xs font-medium">Apagar registros anteriores a:</FieldLabel>
                        <Input
                            id="before_date"
                            type="date"
                            value={beforeDate}
                            max={new Date().toISOString().slice(0, 10)}
                            onChange={(e) => setBeforeDate(e.target.value)}
                        />
                    </Field>
                </div>

                <DialogFooter className="gap-2">
                    <Button variant="outline" size="sm" onClick={() => setOpen(false)}>
                        Cancelar
                    </Button>
                    <ConfirmButton
                        variant="destructive"
                        size="sm"
                        description={`Confirma a exclusão de registros e arquivos de mídia anteriores a ${beforeDate}?`}
                        onConfirm={() => {
                            router.post(
                                '/painel/videos/purge-old',
                                { before_date: beforeDate },
                                { onSuccess: () => setOpen(false) },
                            );
                        }}
                    >
                        Executar Limpeza
                    </ConfirmButton>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

export default function SourceVideos() {
    const { props } = usePage<PageProps>();
    const { videos, filters, statusOptions, storage, downloadWindow, auth } = props;
    const [selected, setSelected] = useState<number[]>([]);
    const [lastSelectedId, setLastSelectedId] = useState<number | null>(null);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

    const toggle = (id: number, shiftKey = false) => {
        setSelected((prev) => {
            const isCurrentlySelected = prev.includes(id);

            if (shiftKey && lastSelectedId !== null) {
                const lastIdx = videos.data.findIndex((x) => x.id === lastSelectedId);
                const currIdx = videos.data.findIndex((x) => x.id === id);

                if (lastIdx !== -1 && currIdx !== -1) {
                    const start = Math.min(lastIdx, currIdx);
                    const end = Math.max(lastIdx, currIdx);
                    const range = videos.data
                        .slice(start, end + 1)
                        .filter((v) => v.canDelete ?? v.hasLocalFile)
                        .map((v) => v.id);

                    return Array.from(new Set([...prev, ...range]));
                }
            }

            return isCurrentlySelected ? prev.filter((x) => x !== id) : [...prev, id];
        });

        setLastSelectedId(id);
    };

    const toggleAll = () => {
        const selectable = videos.data.filter((v) => v.canDelete ?? v.hasLocalFile).map((v) => v.id);
        setSelected((prev) => (prev.length === selectable.length ? [] : selectable));
        setLastSelectedId(null);
    };

    function copyToClipboard(text: string, message: string) {
        navigator.clipboard.writeText(text).catch(() => {});
        toast.success(message);
    }

    return (
        <>
            <Head title="Vídeos" />
            <AppShell
                title="Vídeos"
                user={auth.user}
                description={`Lista de todo vídeo bruto (fonte) já baixado ou tentado pelo pipeline — não são os clips finais, são a matéria-prima. ${videos.total} vídeo(s).`}
                actions={
                    <div className="flex items-center gap-2">
                        <div className="flex rounded-lg border bg-card p-0.5 overflow-hidden">
                            <button
                                type="button"
                                onClick={() => setViewMode('grid')}
                                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                                    viewMode === 'grid'
                                        ? 'bg-primary text-primary-foreground shadow-sm'
                                        : 'text-muted-foreground hover:text-foreground'
                                }`}
                                title="Modo Quadro"
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
                                title="Modo Tabela"
                            >
                                ☰ Tabela
                            </button>
                        </div>
                        <PurgeOldDialog />
                    </div>
                }
            >
                <VideoSummaryCards storage={storage} downloadWindow={downloadWindow} />

                <div className="flex flex-wrap items-center justify-between gap-3">
                    <Tabs
                        value={filters.tab}
                        onValueChange={(tab) => applyFilters({ tab }, filters)}
                    >
                        <TabsList>
                            <TabsTrigger value="ativos">Ativos</TabsTrigger>
                            <TabsTrigger value="falharam">Falharam</TabsTrigger>
                            <TabsTrigger value="todos">Todos</TabsTrigger>
                        </TabsList>
                    </Tabs>

                    <div className="flex flex-wrap items-center gap-3">
                        <Input
                            placeholder="Buscar título ou canal…"
                            defaultValue={filters.search ?? ''}
                            className="w-56 text-xs h-9"
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    applyFilters({ search: (e.target as HTMLInputElement).value }, filters);
                                }
                            }}
                        />
                        <Select
                            value={filters.status ?? 'all'}
                            onValueChange={(v) => applyFilters({ status: v === 'all' ? null : v }, filters)}
                        >
                            <SelectTrigger className="w-40 text-xs h-9">
                                <SelectValue placeholder="Status" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Todos os status</SelectItem>
                                {Object.entries(statusOptions).map(([value, label]) => (
                                    <SelectItem key={value} value={value}>
                                        {label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <div className="flex items-center gap-2">
                            <Switch
                                checked={filters.seguro_apagar}
                                onCheckedChange={(v) => applyFilters({ seguro_apagar: v }, filters)}
                            />
                            <span className="text-xs text-muted-foreground">Só sem uso</span>
                        </div>
                    </div>
                </div>

                {selected.length > 0 && (
                    <div className="flex items-center gap-2">
                        <ConfirmButton
                            variant="destructive"
                            size="sm"
                            description={`Apagar os arquivos brutos dos ${selected.length} vídeo(s) selecionado(s)?`}
                            onConfirm={() => {
                                router.post(
                                    '/painel/videos/bulk-delete-files',
                                    { ids: selected },
                                    { preserveScroll: true, onSuccess: () => setSelected([]) },
                                );
                            }}
                        >
                            Apagar arquivos selecionados ({selected.length})
                        </ConfirmButton>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                                const urls = videos.data
                                    .filter((v) => selected.includes(v.id))
                                    .map((v) => `https://youtube.com/watch?v=${v.youtubeVideoId}`)
                                    .join('\n');
                                copyToClipboard(urls, `${selected.length} URL(s) copiada(s)`);
                            }}
                        >
                            Copiar URLs
                        </Button>
                    </div>
                )}

                {viewMode === 'grid' ? (
                    <div className="grid gap-5 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                        {videos.data.map((v) => {
                            const isPol = (v.channelName ?? '').toLowerCase().includes('pingos') || (v.channelName ?? '').toLowerCase().includes('politica') || (v.channelName ?? '').toLowerCase().includes('band') || (v.channelName ?? '').toLowerCase().includes('antagonista');
                            const bgGradient = isPol ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)' : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';

                            return (
                                <article
                                    key={v.id}
                                    className="group rounded-2xl border border-border bg-card overflow-hidden flex flex-col hover:border-primary/40 transition-all shadow-xs"
                                >
                                    <div className="relative aspect-video overflow-hidden" style={{ background: bgGradient }}>
                                        <div className="absolute inset-0 grid place-items-center">
                                            <a
                                                href={`https://youtube.com/watch?v=${v.youtubeVideoId}`}
                                                target="_blank"
                                                rel="noreferrer"
                                                className="w-12 h-12 rounded-full bg-black/50 backdrop-blur-md border border-white/20 grid place-items-center text-white group-hover:scale-105 transition-transform"
                                            >
                                                ▶
                                            </a>
                                        </div>
                                        <span className="absolute left-2.5 top-2.5 font-semibold text-[11px] px-2 py-0.5 rounded-md bg-black/60 text-white backdrop-blur-md border border-white/10">
                                            {isPol ? '🏛️ Política' : '⚽ Futebol'}
                                        </span>
                                        <span className="absolute right-2.5 top-2.5 font-mono text-[11px] px-2 py-0.5 rounded-md bg-black/60 text-white backdrop-blur-md border border-white/10">
                                            {v.statusLabel}
                                        </span>
                                    </div>
                                    <div className="p-4 flex flex-col gap-3 flex-1">
                                        <div className="flex items-start gap-2">
                                            {(v.canDelete ?? v.hasLocalFile) && (
                                                <Checkbox
                                                    checked={selected.includes(v.id)}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        toggle(v.id, e.shiftKey);
                                                    }}
                                                    className="mt-1"
                                                />
                                            )}
                                            <div className="font-semibold text-sm leading-snug tracking-tight text-foreground line-clamp-2" title={v.title}>
                                                {v.title}
                                            </div>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                                            <span className="font-mono px-1.5 py-0.5 rounded border border-border">
                                                #{v.id}
                                            </span>
                                            <span className="truncate">{v.channelName ?? 'Canal Fonte'}</span>
                                        </div>
                                        <div className="flex-1" />
                                        <div className="flex items-center gap-2 pt-2 border-t border-border/60">
                                            <a
                                                href={`https://youtube.com/watch?v=${v.youtubeVideoId}`}
                                                target="_blank"
                                                rel="noreferrer"
                                                className="inline-flex h-8 items-center justify-center rounded-lg border border-border px-3 text-xs font-medium text-foreground hover:bg-muted"
                                            >
                                                Ver no YouTube
                                            </a>
                                            <div className="flex-1" />
                                            {(v.canDelete ?? v.hasLocalFile) && (
                                                <ConfirmButton
                                                    variant="destructive"
                                                    size="sm"
                                                    className="h-8 px-2.5 text-xs"
                                                    description={`Apagar arquivo bruto do vídeo #${v.id}?`}
                                                    onConfirm={() => {
                                                        router.post(`/painel/videos/${v.id}/delete-file`, {}, { preserveScroll: true });
                                                    }}
                                                >
                                                    Apagar arquivo
                                                </ConfirmButton>
                                            )}
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
                                        <TableHead className="w-8">
                                            <Checkbox
                                                checked={selected.length > 0 && selected.length === videos.data.length}
                                                onCheckedChange={toggleAll}
                                            />
                                        </TableHead>
                                        <TableHead>ID</TableHead>
                                        <TableHead>Título</TableHead>
                                        <TableHead>Canal</TableHead>
                                        <TableHead>Data do Vídeo</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>YouTube ID</TableHead>
                                        <TableHead>Arquivo local</TableHead>
                                        <TableHead>Uso</TableHead>
                                        <TableHead>Atualizado</TableHead>
                                        <TableHead>Ações</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {videos.data.map((v) => (
                                        <TableRow key={v.id}>
                                            <TableCell>
                                                {(v.canDelete ?? v.hasLocalFile) && (
                                                    <Checkbox
                                                        checked={selected.includes(v.id)}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            toggle(v.id, e.shiftKey);
                                                        }}
                                                    />
                                                )}
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">{v.id}</TableCell>
                                            <TableCell className="max-w-[300px] truncate" title={v.title}>
                                                {v.title}
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">{v.channelName ?? '—'}</TableCell>
                                            <TableCell className="text-muted-foreground whitespace-nowrap text-xs">
                                                {v.publishedAt ? (
                                                    <span className="flex items-center gap-1.5">
                                                        <CalendarIcon className="h-3.5 w-3.5 text-muted-foreground/70" />
                                                        {v.publishedAt}
                                                    </span>
                                                ) : (
                                                    '—'
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant={(STATUS_BADGE[v.status] as never) ?? 'secondary'}>
                                                    {v.statusLabel}
                                                </Badge>
                                            </TableCell>
                                            <TableCell
                                                className="cursor-pointer font-mono text-xs text-primary"
                                                onClick={() => copyToClipboard(v.youtubeVideoId, 'ID copiado!')}
                                            >
                                                {v.youtubeVideoId}
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant={v.hasLocalFile ? 'outline' : 'secondary'}>
                                                    {v.hasLocalFile ? 'Sim' : 'Não'}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant={(USO_BADGE[v.uso] as never) ?? 'secondary'}>{v.uso}</Badge>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">{v.updatedAt}</TableCell>
                                            <TableCell>
                                                <div className="flex gap-1.5 items-center">
                                                    <Button variant="ghost" size="sm" asChild>
                                                        <a
                                                            href={`https://youtube.com/watch?v=${v.youtubeVideoId}`}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                        >
                                                            YouTube
                                                        </a>
                                                    </Button>
                                                    {v.status === 'pending' && (
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="text-amber-500 hover:text-amber-600 hover:bg-amber-500/10 gap-1 text-xs"
                                                            onClick={() =>
                                                                router.post(
                                                                    `/painel/videos/${v.id}/prioritize`,
                                                                    {},
                                                                    {
                                                                        preserveScroll: true,
                                                                        onSuccess: () => toast.success(`Vídeo #${v.id} priorizado na fila!`),
                                                                    },
                                                                )
                                                            }
                                                        >
                                                            <ArrowUpIcon className="h-3.5 w-3.5" />
                                                            Priorizar
                                                        </Button>
                                                    )}
                                                    {(v.canDelete ?? v.hasLocalFile) && (
                                                        <ConfirmButton
                                                            variant="destructive"
                                                            size="sm"
                                                            description="Apaga o vídeo bruto (.mp4), clips gerados em disco e thumbnails para liberar espaço no HD. Essa ação não pode ser desfeita."
                                                            onConfirm={() =>
                                                                router.post(
                                                                    `/painel/videos/${v.id}/delete-file`,
                                                                    {},
                                                                    { preserveScroll: true },
                                                                )
                                                            }
                                                        >
                                                            Apagar
                                                        </ConfirmButton>
                                                    )}
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}

                        <div className="flex items-center justify-between">
                            <p className="text-sm text-muted-foreground">
                                Página {videos.currentPage} de {videos.lastPage} — {videos.total} vídeo(s)
                            </p>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={videos.currentPage <= 1}
                                    onClick={() => applyFilters({ page: videos.currentPage - 1 }, filters)}
                                >
                                    Anterior
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={videos.currentPage >= videos.lastPage}
                                    onClick={() => applyFilters({ page: videos.currentPage + 1 }, filters)}
                                >
                                    Próxima
                                </Button>
                            </div>
                        </div>
            </AppShell>
        </>
    );
}
