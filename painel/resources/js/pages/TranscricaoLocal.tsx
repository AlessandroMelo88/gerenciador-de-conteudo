import { useEffect, useState } from 'react';
import { Head, Link, router, useForm, usePage } from '@inertiajs/react';
import { BookOpenIcon, DownloadIcon, PauseIcon, PencilIcon, PlayIcon, RotateCcwIcon, Trash2Icon } from 'lucide-react';
import { toast } from 'sonner';

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
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import { Field, FieldDescription, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { BuscaTranscricoes } from '@/components/transcricoes/BuscaTranscricoes';
import { AppShell } from '@/layouts/app-shell';

type Status = 'pending' | 'downloading' | 'transcribing' | 'paused' | 'done' | 'failed';

type Job = {
    id: number;
    source_url: string;
    title: string | null;
    platform: string | null;
    duration_seconds: number | null;
    status: Status;
    progress_percent: number;
    srt_path: string | null;
    media_path: string | null;
    media_bytes: number | null;
    error_message: string | null;
    excerpt: string | null;
    created_at: string;
};

type Paginated<T> = {
    data: T[];
    current_page: number;
    last_page: number;
    total: number;
    prev_page_url: string | null;
    next_page_url: string | null;
};

type PageProps = {
    auth?: { user: { name: string; email: string } | null };
    flash?: { success: string | null; error: string | null };
    jobs?: Paginated<Job>;
};

const STATUS_LABELS: Record<Status, string> = {
    pending: 'Na fila do Mac',
    downloading: 'Baixando a aula',
    transcribing: 'Transcrevendo',
    paused: 'Pausada',
    done: 'Concluído',
    failed: 'Falhou',
};

const EM_ANDAMENTO: Status[] = ['pending', 'downloading', 'transcribing'];
const COM_BARRA: Status[] = [...EM_ANDAMENTO, 'paused'];

export function formatarDuracao(segundos: number | null): string | null {
    if (!segundos) return null;
    if (segundos < 60) return `${segundos}s`;
    const h = Math.floor(segundos / 3600);
    const min = Math.floor((segundos % 3600) / 60);
    return h > 0 ? `${h}h${String(min).padStart(2, '0')}min` : `${min}min`;
}

function EditarTituloModal({ job }: { job: Pick<Job, 'id' | 'title' | 'source_url'> }) {
    const [aberto, setAberto] = useState(false);
    const [titulo, setTitulo] = useState(job.title || '');
    const [salvando, setSalvando] = useState(false);

    useEffect(() => {
        setTitulo(job.title || '');
    }, [job.title]);

    function salvar(e: React.FormEvent) {
        e.preventDefault();
        if (!titulo.trim()) return;
        setSalvando(true);
        router.patch(
            `/painel/transcricoes/${job.id}`,
            { title: titulo.trim() },
            {
                preserveScroll: true,
                onSuccess: () => {
                    setAberto(false);
                    setSalvando(false);
                    toast.success('Título atualizado.');
                },
                onError: () => setSalvando(false),
            },
        );
    }

    return (
        <Dialog open={aberto} onOpenChange={setAberto}>
            <DialogTrigger asChild>
                <Button size="sm" variant="ghost" title="Editar título da aula" aria-label="Editar título">
                    <PencilIcon />
                </Button>
            </DialogTrigger>
            <DialogContent>
                <form onSubmit={salvar} className="grid gap-4">
                    <DialogHeader>
                        <DialogTitle>Editar título da aula</DialogTitle>
                        <DialogDescription>
                            Organize com o nome da aula e módulo para facilitar seus estudos e a criação do e-book.
                        </DialogDescription>
                    </DialogHeader>
                    <Field>
                        <FieldLabel htmlFor={`titulo-${job.id}`}>Nome da aula / Módulo</FieldLabel>
                        <Input
                            id={`titulo-${job.id}`}
                            value={titulo}
                            onChange={(e) => setTitulo(e.target.value)}
                            placeholder="Ex: [Mód. 3 - Criação e Identidade] Como clonar vídeos de Canais Dark"
                            autoFocus
                        />
                        <FieldDescription>
                            Dica: você pode colocar o módulo entre colchetes para agrupar depois.
                        </FieldDescription>
                    </Field>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => setAberto(false)}>
                            Cancelar
                        </Button>
                        <Button type="submit" disabled={salvando || !titulo.trim()}>
                            {salvando ? 'Salvando...' : 'Salvar título'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

function Controles({ job }: { job: Pick<Job, 'id' | 'status' | 'title' | 'source_url'> }) {
    const acao = (caminho: string) => router.post(`/painel/transcricoes/${job.id}/${caminho}`, {}, { preserveScroll: true });

    return (
        <div className="flex gap-1">
            <EditarTituloModal job={job} />
            {EM_ANDAMENTO.includes(job.status) && (
                <Button size="sm" variant="outline" onClick={() => acao('pausar')} title="Pausar">
                    <PauseIcon /> Pausar
                </Button>
            )}
            {job.status === 'paused' && (
                <Button size="sm" variant="outline" onClick={() => acao('retomar')} title="Retomar">
                    <PlayIcon /> Retomar
                </Button>
            )}
            {job.status === 'failed' && (
                <Button size="sm" variant="outline" onClick={() => acao('retomar')} title="Tentar de novo">
                    <RotateCcwIcon /> Tentar de novo
                </Button>
            )}
            <AlertDialog>
                <AlertDialogTrigger asChild>
                    <Button size="sm" variant="ghost" title="Apagar" aria-label="Apagar transcrição">
                        <Trash2Icon />
                    </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Apagar esta transcrição?</AlertDialogTitle>
                        <AlertDialogDescription>
                            {job.title || job.source_url}
                            <br />
                            O texto sai da sua base de conhecimento e não dá para desfazer.
                            {EM_ANDAMENTO.includes(job.status) && ' Se estiver andando, o Mac para no próximo passo.'}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancelar</AlertDialogCancel>
                        <AlertDialogAction onClick={() => router.delete(`/painel/transcricoes/${job.id}`, { preserveScroll: true })}>
                            Apagar
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}

export function formatarTamanho(bytes: number | null): string | null {
    if (!bytes) return null;
    const mb = bytes / 1024 / 1024;
    return mb >= 1024 ? `${(mb / 1024).toFixed(1).replace('.', ',')} GB` : `${Math.max(1, Math.round(mb))} MB`;
}

export function BotoesDownload({ job }: { job: Pick<Job, 'id' | 'status' | 'media_path' | 'media_bytes'> }) {
    const pronto = job.status === 'done';
    const tamanho = formatarTamanho(job.media_bytes);
    return (
        <div className="flex flex-wrap gap-1">
            {pronto && job.media_path && (
                <Button asChild size="sm" variant="secondary" title="Baixar o arquivo da aula">
                    <a href={`/painel/transcricoes/${job.id}/aula`}>
                        <DownloadIcon /> Aula{tamanho && ` (${tamanho})`}
                    </a>
                </Button>
            )}
            {(['md', 'txt', 'srt'] as const).map((formato) => (
                <Button key={formato} asChild={pronto} size="sm" variant={formato === 'md' ? 'default' : 'outline'} disabled={!pronto}>
                    {pronto ? <a href={`/painel/transcricoes/${job.id}/download/${formato}`}>.{formato}</a> : <span>.{formato}</span>}
                </Button>
            ))}
        </div>
    );
}

export default function TranscricaoLocal() {
    const { props } = usePage<PageProps>();
    const { auth, flash } = props;
    const jobs = props.jobs?.data ?? [];
    const pagina = props.jobs;
    const { data, setData, post, processing, reset, errors } = useForm({ url: '', title: '' });

    const [selecionados, setSelecionados] = useState<number[]>([]);
    const [modalEbookAberto, setModalEbookAberto] = useState(false);
    const [tituloEbook, setTituloEbook] = useState('E-book - Transcrições de Aulas');
    const [exportando, setExportando] = useState(false);

    const concluidosDestaPagina = jobs.filter((j) => j.status === 'done');
    const todosConcluidosSelecionados =
        concluidosDestaPagina.length > 0 && concluidosDestaPagina.every((j) => selecionados.includes(j.id));

    function alternarTodos() {
        if (todosConcluidosSelecionados) {
            setSelecionados([]);
        } else {
            setSelecionados(concluidosDestaPagina.map((j) => j.id));
        }
    }

    function alternarSelecao(id: number) {
        setSelecionados((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    }

    async function baixarEbook(e: React.FormEvent) {
        e.preventDefault();
        if (selecionados.length === 0) return;
        setExportando(true);
        try {
            const csrfToken = (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement)?.content || '';
            const resp = await fetch('/painel/transcricoes/ebook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': csrfToken,
                    Accept: 'text/markdown',
                },
                body: JSON.stringify({
                    ids: selecionados,
                    titulo: tituloEbook,
                }),
            });

            if (!resp.ok) {
                toast.error('Erro ao gerar o e-book.');
                return;
            }

            const blob = await resp.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const disposition = resp.headers.get('content-disposition');
            let filename = `${tituloEbook.toLowerCase().replace(/[^a-z0-9]/gi, '-')}.md`;
            if (disposition && disposition.indexOf('filename=') !== -1) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            toast.success(`E-book gerado com sucesso com ${selecionados.length} aula(s)!`);
            setModalEbookAberto(false);
        } catch {
            toast.error('Não foi possível baixar o e-book.');
        } finally {
            setExportando(false);
        }
    }

    useEffect(() => {
        if (flash?.success) toast.success(flash.success);
        if (flash?.error) toast.error(flash.error, { style: { whiteSpace: 'pre-line' } });
    }, [flash?.success, flash?.error]);

    // Enquanto houver job andando, a lista se atualiza sozinha.
    useEffect(() => {
        if (!jobs.some((j) => EM_ANDAMENTO.includes(j.status))) return;
        const interval = setInterval(() => router.reload({ only: ['jobs'] }), 3000);
        return () => clearInterval(interval);
    }, [jobs]);

    function enviar(e: React.FormEvent) {
        e.preventDefault();
        post('/painel/transcricoes', { preserveScroll: true, onSuccess: () => reset('url', 'title') });
    }

    return (
        <>
            <Head title="Transcrições" />
            <AppShell
                title="Transcrições"
                user={auth?.user ?? null}
                description="Base de conhecimento: cole o link de um vídeo ou áudio e o texto fica guardado aqui para ler e buscar quando quiser."
            >
                <Card className="max-w-3xl">
                    <CardContent className="pt-6">
                        <form onSubmit={enviar} className="grid gap-4">
                            <Field>
                                <FieldLabel htmlFor="url">Link do vídeo ou áudio</FieldLabel>
                                <Input
                                    id="url"
                                    type="url"
                                    placeholder="YouTube, TikTok, Instagram, Vimeo..."
                                    value={data.url}
                                    onChange={(e) => setData('url', e.target.value)}
                                />
                                <FieldDescription>
                                    Quem baixa e transcreve é o seu Mac — ele precisa estar ligado. Site que pede login (curso, Vimeo) usa o cookies.txt salvo em ~/.config/canaldecortes/.
                                </FieldDescription>
                                {errors.url && <p className="text-xs text-red-600">{errors.url}</p>}
                            </Field>
                            <Field>
                                <FieldLabel htmlFor="title">Título ou Nome da aula (opcional)</FieldLabel>
                                <Input
                                    id="title"
                                    type="text"
                                    placeholder="Ex: [Mód. 3 - Criação e Identidade] Como clonar vídeos de Canais Dark"
                                    value={data.title}
                                    onChange={(e) => setData('title', e.target.value)}
                                />
                                <FieldDescription>
                                    Deixe em branco para detectar automaticamente ou especifique o módulo e a aula.
                                </FieldDescription>
                                {errors.title && <p className="text-xs text-red-600">{errors.title}</p>}
                            </Field>
                            <div>
                                <Button type="submit" disabled={processing || !data.url}>
                                    Transcrever
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>

                <Card className="max-w-3xl">
                    <CardContent className="grid grid-cols-1 gap-4 pt-6">
                        <BuscaTranscricoes>
                        {concluidosDestaPagina.length > 0 && (
                            <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3 text-xs text-muted-foreground">
                                <div className="flex items-center gap-2">
                                    <Checkbox
                                        id="select-all"
                                        checked={todosConcluidosSelecionados}
                                        onCheckedChange={alternarTodos}
                                    />
                                    <label htmlFor="select-all" className="cursor-pointer select-none">
                                        {todosConcluidosSelecionados ? 'Desmarcar todas' : 'Selecionar todas para E-book'}
                                    </label>
                                </div>
                                {selecionados.length > 0 && (
                                    <span className="font-medium text-foreground">
                                        {selecionados.length} {selecionados.length === 1 ? 'aula selecionada' : 'aulas selecionadas'}
                                    </span>
                                )}
                            </div>
                        )}

                        {selecionados.length > 0 && (
                            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-primary/40 bg-primary/10 p-3 text-sm">
                                <div className="flex items-center gap-2">
                                    <BookOpenIcon className="size-4 text-primary" />
                                    <span className="font-medium text-foreground">
                                        {selecionados.length} aula(s) prontas para o E-book
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button size="sm" variant="ghost" onClick={() => setSelecionados([])}>
                                        Limpar
                                    </Button>
                                    <Button size="sm" onClick={() => setModalEbookAberto(true)} className="gap-1.5">
                                        <BookOpenIcon className="size-3.5" />
                                        Gerar E-book (.md)
                                    </Button>
                                </div>
                            </div>
                        )}

                        {jobs.length === 0 && (
                            <p className="text-sm text-muted-foreground">
                                Nenhuma transcrição ainda.
                            </p>
                        )}

                        {jobs.map((job) => (
                            <div key={job.id} className="grid gap-2 border-b pb-4 last:border-b-0 last:pb-0">
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex min-w-0 items-start gap-3">
                                        {job.status === 'done' && (
                                            <div className="pt-0.5">
                                                <Checkbox
                                                    checked={selecionados.includes(job.id)}
                                                    onCheckedChange={() => alternarSelecao(job.id)}
                                                    aria-label={`Selecionar aula ${job.title || job.id} para e-book`}
                                                />
                                            </div>
                                        )}
                                        <div className="grid min-w-0 gap-1">
                                            {job.status === 'done' ? (
                                                <Link href={`/painel/transcricoes/${job.id}`} className="truncate font-medium hover:underline">
                                                    {job.title || job.source_url}
                                                </Link>
                                            ) : (
                                                <span className="truncate font-medium" title={job.source_url}>
                                                    {job.title || job.source_url}
                                                </span>
                                            )}
                                            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                                {job.platform && <Badge variant="secondary">{job.platform}</Badge>}
                                                {formatarDuracao(job.duration_seconds) && <span>{formatarDuracao(job.duration_seconds)}</span>}
                                                <span>{new Date(job.created_at).toLocaleDateString('pt-BR')}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex shrink-0 flex-wrap justify-end gap-2">
                                        {job.status === 'done' && <BotoesDownload job={job} />}
                                        <Controles job={job} />
                                    </div>
                                </div>

                                {job.status === 'done' && job.excerpt && (
                                    <p className="line-clamp-2 text-sm text-muted-foreground">{job.excerpt}</p>
                                )}

                                {COM_BARRA.includes(job.status) && (
                                    <>
                                        <Progress value={job.progress_percent} className={job.status === 'paused' ? 'opacity-50' : undefined} />
                                        <div className="flex justify-between text-xs text-muted-foreground">
                                            <span>{STATUS_LABELS[job.status]}</span>
                                            <span className="tabular-nums">{job.progress_percent}%</span>
                                        </div>
                                    </>
                                )}

                                {job.status === 'failed' && (
                                    <p className="text-xs text-red-600">
                                        {STATUS_LABELS.failed}: {job.error_message ?? 'sem mensagem'}
                                    </p>
                                )}
                                {/* Concluída com aviso: o texto foi salvo, o arquivo da aula não. */}
                                {job.status === 'done' && job.error_message && (
                                    <p className="text-xs text-amber-700 dark:text-amber-400">{job.error_message}</p>
                                )}
                            </div>
                        ))}

                        {pagina && pagina.last_page > 1 && (
                            <div className="flex items-center justify-between border-t pt-4 text-xs text-muted-foreground">
                                <span>
                                    Página {pagina.current_page} de {pagina.last_page} ({pagina.total} transcrições)
                                </span>
                                <div className="flex gap-2">
                                    <Button asChild={!!pagina.prev_page_url} size="sm" variant="outline" disabled={!pagina.prev_page_url}>
                                        {pagina.prev_page_url ? <Link href={pagina.prev_page_url}>Anterior</Link> : <span>Anterior</span>}
                                    </Button>
                                    <Button asChild={!!pagina.next_page_url} size="sm" variant="outline" disabled={!pagina.next_page_url}>
                                        {pagina.next_page_url ? <Link href={pagina.next_page_url}>Próxima</Link> : <span>Próxima</span>}
                                    </Button>
                                </div>
                            </div>
                        )}
                        </BuscaTranscricoes>
                    </CardContent>
                </Card>

                {/* Modal de exportação de E-book */}
                <Dialog open={modalEbookAberto} onOpenChange={setModalEbookAberto}>
                    <DialogContent>
                        <form onSubmit={baixarEbook} className="grid gap-4">
                            <DialogHeader>
                                <DialogTitle>Gerar E-book de Estudos</DialogTitle>
                                <DialogDescription>
                                    As {selecionados.length} aulas selecionadas serão organizadas em um único arquivo Markdown (.md) com sumário e capítulos completos.
                                </DialogDescription>
                            </DialogHeader>
                            <Field>
                                <FieldLabel htmlFor="ebook-title">Título do E-book</FieldLabel>
                                <Input
                                    id="ebook-title"
                                    value={tituloEbook}
                                    onChange={(e) => setTituloEbook(e.target.value)}
                                    placeholder="Ex: Fórmula YouTube 2026 - Módulo 3"
                                    autoFocus
                                />
                                <FieldDescription>
                                    Esse título será a capa principal do arquivo.
                                </FieldDescription>
                            </Field>
                            <DialogFooter>
                                <Button type="button" variant="outline" onClick={() => setModalEbookAberto(false)}>
                                    Cancelar
                                </Button>
                                <Button type="submit" disabled={exportando || !tituloEbook.trim()}>
                                    {exportando ? 'Compilando e-book...' : 'Baixar E-book (.md)'}
                                </Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </AppShell>
        </>
    );
}
