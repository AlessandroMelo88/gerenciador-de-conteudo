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
    failedCount?: number;
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

function PaginationControls({
    currentPage,
    lastPage,
    total,
    perPage,
    onPageChange,
    onPerPageChange,
}: {
    currentPage: number;
    lastPage: number;
    total: number;
    perPage: number;
    onPageChange: (page: number) => void;
    onPerPageChange: (perPage: number) => void;
}) {
    const getPageNumbers = () => {
        if (lastPage <= 7) {
            return Array.from({ length: lastPage }, (_, i) => i + 1);
        }
        if (currentPage <= 4) {
            return [1, 2, 3, 4, 5, '...', lastPage];
        }
        if (currentPage >= lastPage - 3) {
            return [1, '...', lastPage - 4, lastPage - 3, lastPage - 2, lastPage - 1, lastPage];
        }
        return [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', lastPage];
    };

    return (
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-border">
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span>
                    Página <strong className="text-foreground">{currentPage}</strong> de <strong className="text-foreground">{lastPage}</strong> ({total} vídeos no total)
                </span>
                <div className="flex items-center gap-1.5 ml-2 border-l border-border pl-3">
                    <span>Exibir:</span>
                    <select
                        value={perPage}
                        onChange={(e) => onPerPageChange(Number(e.target.value))}
                        className="bg-card border border-border rounded-md px-2 py-1 text-xs text-foreground cursor-pointer focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                        <option value={15}>15 por pág</option>
                        <option value={20}>20 por pág</option>
                        <option value={30}>30 por pág</option>
                        <option value={50}>50 por pág</option>
                        <option value={100}>100 por pág</option>
                    </select>
                </div>
            </div>

            <div className="flex items-center gap-1">
                <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-2.5 text-xs"
                    disabled={currentPage <= 1}
                    onClick={() => onPageChange(currentPage - 1)}
                >
                    Anterior
                </Button>

                <div className="hidden sm:flex items-center gap-1 mx-1">
                    {getPageNumbers().map((p, idx) =>
                        p === '...' ? (
                            <span key={`ellipsis-${idx}`} className="px-1.5 text-xs text-muted-foreground">
                                …
                            </span>
                        ) : (
                            <Button
                                key={`page-${p}`}
                                variant={p === currentPage ? 'default' : 'outline'}
                                size="sm"
                                className="h-8 w-8 p-0 text-xs font-medium"
                                onClick={() => onPageChange(p as number)}
                            >
                                {p}
                            </Button>
                        ),
                    )}
                </div>

                <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-2.5 text-xs"
                    disabled={currentPage >= lastPage}
                    onClick={() => onPageChange(currentPage + 1)}
                >
                    Próxima
                </Button>
            </div>
        </div>
    );
}

export default function SourceVideos() {
    const { props } = usePage<PageProps>();
    const { videos, filters, statusOptions, failedCount = 0, storage, downloadWindow, auth } = props;
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
                        {failedCount > 0 && (
                            <ConfirmButton
                                variant="destructive"
                                size="sm"
                                className="gap-1.5 h-8 text-xs font-semibold border-destructive/30"
                                description={`Deseja excluir definitivamente todos os ${failedCount} registros de vídeos que falharam no download ou processamento?`}
                                onConfirm={() =>
                                    router.post(
                                        '/painel/videos/purge-failed',
                                        {},
                                        {
                                            preserveScroll: true,
                                            onSuccess: () => toast.success('Registros de falhas removidos com sucesso!'),
                                        },
                                    )
                                }
                            >
                                <Trash2Icon className="h-3.5 w-3.5" />
                                Limpar {failedCount} falhas
                            </ConfirmButton>
                        )}
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
                            <TabsTrigger value="falharam" className="relative">
                                Falharam
                                {failedCount > 0 && (
                                    <span className="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-destructive text-destructive-foreground">
                                        {failedCount}
                                    </span>
                                )}
                            </TabsTrigger>
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
                    <div className="flex flex-wrap items-center gap-2">
                        <ConfirmButton
                            variant="destructive"
                            size="sm"
                            description={`Excluir definitivamente os ${selected.length} registro(s) do banco de dados e arquivos locais? Esta ação não pode ser desfeita.`}
                            onConfirm={() => {
                                router.post(
                                    '/painel/videos/bulk-destroy-records',
                                    { ids: selected },
                                    { preserveScroll: true, onSuccess: () => setSelected([]) },
                                );
                            }}
                        >
                            <Trash2Icon className="h-3.5 w-3.5 mr-1" />
                            Excluir do Banco ({selected.length})
                        </ConfirmButton>
                        <ConfirmButton
                            variant="outline"
                            size="sm"
                            className="text-destructive border-destructive/30 hover:bg-destructive/10"
                            description={`Apagar somente os arquivos brutos dos ${selected.length} vídeo(s) selecionado(s) para liberar HD?`}
                            onConfirm={() => {
                                router.post(
                                    '/painel/videos/bulk-delete-files',
                                    { ids: selected },
                                    { preserveScroll: true, onSuccess: () => setSelected([]) },
                                );
                            }}
                        >
                            Apagar só arquivos ({selected.length})
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
                                                <div className="flex items-center gap-1">
                                                    {v.hasLocalFile && (
                                                        <ConfirmButton
                                                            variant="outline"
                                                            size="sm"
                                                            className="h-8 px-2 text-[11px] text-destructive border-destructive/30 hover:bg-destructive/10"
                                                            description={`Apagar arquivo bruto (.mp4) do vídeo #${v.id} para liberar HD?`}
                                                            onConfirm={() => {
                                                                router.post(`/painel/videos/${v.id}/delete-file`, {}, { preserveScroll: true });
                                                            }}
                                                        >
                                                            Arquivo
                                                        </ConfirmButton>
                                                    )}
                                                    <ConfirmButton
                                                        variant="destructive"
                                                        size="sm"
                                                        className="h-8 px-2 text-[11px] gap-1"
                                                        description={`Excluir definitivamente o registro do vídeo #${v.id} do banco de dados?`}
                                                        onConfirm={() => {
                                                            router.post(`/painel/videos/${v.id}/destroy-record`, {}, { preserveScroll: true });
                                                        }}
                                                    >
                                                        <Trash2Icon className="h-3 w-3" />
                                                        Excluir
                                                    </ConfirmButton>
                                                </div>
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
                                                        <div className="flex items-center gap-1">
                                                            {v.hasLocalFile && (
                                                                <ConfirmButton
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="text-xs h-7 text-destructive border-destructive/30 hover:bg-destructive/10"
                                                                    description="Apaga o arquivo de vídeo bruto (.mp4) para liberar espaço no HD. O registro permanece no histórico."
                                                                    onConfirm={() =>
                                                                        router.post(
                                                                            `/painel/videos/${v.id}/delete-file`,
                                                                            {},
                                                                            { preserveScroll: true },
                                                                        )
                                                                    }
                                                                >
                                                                    Arquivo
                                                                </ConfirmButton>
                                                            )}
                                                            <ConfirmButton
                                                                variant="destructive"
                                                                size="sm"
                                                                className="text-xs h-7 gap-1"
                                                                description="Exclui definitivamente este vídeo e todos os seus clips do banco de dados e arquivos locais. Essa ação não pode ser desfeita."
                                                                onConfirm={() =>
                                                                    router.post(
                                                                        `/painel/videos/${v.id}/destroy-record`,
                                                                        {},
                                                                        { preserveScroll: true },
                                                                    )
                                                                }
                                                            >
                                                                <Trash2Icon className="h-3 w-3" />
                                                                Excluir
                                                            </ConfirmButton>
                                                        </div>
                                                    )}
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}

                    <PaginationControls
                        currentPage={videos.currentPage}
                        lastPage={videos.lastPage}
                        total={videos.total}
                        perPage={videos.perPage}
                        onPageChange={(page) => applyFilters({ page }, filters)}
                        onPerPageChange={(per_page) => applyFilters({ per_page, page: 1 }, filters)}
                    />
            </AppShell>
        </>
    );
}
