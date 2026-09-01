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

    const toggle = (id: number) =>
        setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    const toggleAll = () =>
        setSelected((prev) => (prev.length === videos.data.length ? [] : videos.data.map((v) => v.id)));

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
                actions={<PurgeOldDialog />}
            >
                <VideoSummaryCards storage={storage} downloadWindow={downloadWindow} />

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
                                className="w-64"
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
                                <SelectTrigger className="w-48">
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
                                <span className="text-sm text-muted-foreground">Só sem uso (seguro apagar)</span>
                            </div>
                        </div>

                        {selected.length > 0 && (
                            <div className="flex items-center gap-2">
                                <ConfirmButton
                                    variant="destructive"
                                    size="sm"
                                    description={`Apagar os arquivos brutos dos ${selected.length} vídeo(s) selecionado(s)? Os cortes já gerados NÃO são afetados.`}
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
                                    Copiar URLs selecionadas
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                        const ids = videos.data
                                            .filter((v) => selected.includes(v.id))
                                            .map((v) => v.youtubeVideoId)
                                            .join('\n');
                                        copyToClipboard(ids, `${selected.length} ID(s) copiado(s)`);
                                    }}
                                >
                                    Copiar IDs selecionados
                                </Button>
                            </div>
                        )}

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
                                                        onCheckedChange={() => toggle(v.id)}
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
