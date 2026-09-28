import { useEffect, useState } from 'react';
import { Head, Link, router, useForm, usePage } from '@inertiajs/react';
import { DownloadIcon, PauseIcon, PlayIcon, RotateCcwIcon, Trash2Icon } from 'lucide-react';
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
import { Field, FieldDescription, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
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
    busca?: string;
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

function Controles({ job }: { job: Pick<Job, 'id' | 'status' | 'title' | 'source_url'> }) {
    const acao = (caminho: string) => router.post(`/painel/transcricoes/${job.id}/${caminho}`, {}, { preserveScroll: true });

    return (
        <div className="flex gap-1">
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
    const [busca, setBusca] = useState(props.busca ?? '');
    const { data, setData, post, processing, reset, errors } = useForm({ url: '' });

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
        post('/painel/transcricoes', { preserveScroll: true, onSuccess: () => reset('url') });
    }

    function buscar(e: React.FormEvent) {
        e.preventDefault();
        router.get('/painel/transcricoes', busca ? { q: busca } : {}, { preserveState: true, replace: true });
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
                            <div>
                                <Button type="submit" disabled={processing || !data.url}>
                                    Transcrever
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>

                <Card className="max-w-3xl">
                    <CardContent className="grid gap-4 pt-6">
                        <form onSubmit={buscar} className="flex gap-2">
                            <Input
                                type="search"
                                placeholder="Buscar no título ou no que foi dito..."
                                value={busca}
                                onChange={(e) => setBusca(e.target.value)}
                            />
                            <Button type="submit" variant="outline">
                                Buscar
                            </Button>
                        </form>

                        {jobs.length === 0 && (
                            <p className="text-sm text-muted-foreground">
                                {props.busca ? `Nada encontrado para "${props.busca}".` : 'Nenhuma transcrição ainda.'}
                            </p>
                        )}

                        {jobs.map((job) => (
                            <div key={job.id} className="grid gap-2 border-b pb-4 last:border-b-0 last:pb-0">
                                <div className="flex items-start justify-between gap-3">
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
                    </CardContent>
                </Card>
            </AppShell>
        </>
    );
}
