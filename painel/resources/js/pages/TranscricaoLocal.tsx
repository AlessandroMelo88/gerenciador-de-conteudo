import { useEffect } from 'react';
import { Head, router, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { AppShell } from '@/layouts/app-shell';

type Job = {
    id: number;
    youtube_url: string;
    status: 'pending' | 'downloading' | 'transcribing' | 'done' | 'failed';
    progress_percent: number;
    srt_path: string | null;
    error_message: string | null;
};

type PageProps = {
    auth?: { user: { name: string; email: string } | null };
    flash?: { success: string | null; error: string | null };
    jobs?: Job[];
};

const STATUS_LABELS: Record<Job['status'], string> = {
    pending: 'Pendente',
    downloading: 'Baixando áudio',
    transcribing: 'Transcrevendo',
    done: 'Concluído',
    failed: 'Falhou',
};

export default function TranscricaoLocal() {
    const { props } = usePage<PageProps>();
    const auth = props?.auth;
    const flash = props?.flash;
    const jobs = props?.jobs ?? [];
    const { data, setData, post, processing, reset } = useForm({
        url: '',
    });

    useEffect(() => {
        if (flash?.success) toast.success(flash.success);
        if (flash?.error) toast.error(flash.error, { style: { whiteSpace: 'pre-line' } });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [flash?.success, flash?.error]);

    useEffect(() => {
        const hasPendingJob = jobs.some((j) => ['pending', 'downloading', 'transcribing'].includes(j.status));
        if (!hasPendingJob) return;

        const interval = setInterval(() => {
            router.reload({ only: ['jobs'] });
        }, 3000);

        return () => clearInterval(interval);
    }, [jobs]);

    function submit(e: React.FormEvent) {
        e.preventDefault();
        post('/painel/transcricoes', {
            preserveScroll: true,
            onSuccess: () => reset('url'),
        });
    }

    return (
        <>
            <Head title="Transcrição Local" />
            <AppShell
                title="Transcrição Local"
                user={auth.user}
                description="Transcreve localmente (whisper-cpp) sem consumir cota do YouTube nem entrar na fila de aprovação de clips."
            >
                <Card className="max-w-2xl">
                    <CardContent className="pt-6">
                        <form onSubmit={submit} className="grid gap-6">
                            <Field>
                                <FieldLabel htmlFor="url">URL do YouTube</FieldLabel>
                                <Input
                                    id="url"
                                    type="url"
                                    placeholder="https://www.youtube.com/watch?v=..."
                                    value={data.url}
                                    onChange={(e) => setData('url', e.target.value)}
                                />
                            </Field>
                            <div>
                                <Button type="submit" disabled={processing}>
                                    Transcrever
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>

                <Card className="max-w-2xl">
                    <CardContent className="pt-6">
                        <div className="grid gap-4">
                            {jobs.length === 0 && (
                                <p className="text-sm text-muted-foreground">Nenhuma transcrição ainda.</p>
                            )}
                            {jobs.map((job) => (
                                <div key={job.id} className="grid gap-2 border-b pb-4 last:border-b-0 last:pb-0">
                                    <div className="flex items-center justify-between gap-2">
                                        <span className="truncate text-sm" title={job.youtube_url}>
                                            {job.youtube_url}
                                        </span>
                                        <Button asChild size="sm" disabled={job.status !== 'done'}>
                                            <a href={`/painel/transcricoes/${job.id}/download`}>Baixar .srt</a>
                                        </Button>
                                    </div>
                                    <Progress value={job.progress_percent} />
                                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                                        <span>{STATUS_LABELS[job.status]}</span>
                                        <span>{job.progress_percent}%</span>
                                    </div>
                                    {job.status === 'failed' && job.error_message && (
                                        <p className="text-xs text-red-600">{job.error_message}</p>
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </AppShell>
        </>
    );
}
