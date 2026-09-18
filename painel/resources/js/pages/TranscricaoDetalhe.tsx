import { Head, Link, usePage } from '@inertiajs/react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { AppShell } from '@/layouts/app-shell';
import { BotoesDownload, formatarDuracao } from '@/pages/TranscricaoLocal';

type Job = {
    id: number;
    source_url: string;
    title: string | null;
    platform: string | null;
    duration_seconds: number | null;
    status: 'pending' | 'downloading' | 'transcribing' | 'done' | 'failed';
    transcript_text: string | null;
    created_at: string;
};

type PageProps = {
    auth?: { user: { name: string; email: string } | null };
    job: Job;
};

export default function TranscricaoDetalhe() {
    const { props } = usePage<PageProps>();
    const { auth, job } = props;
    const titulo = job.title || `Transcrição ${job.id}`;
    const paragrafos = (job.transcript_text ?? '').split(/\n{2,}/).filter(Boolean);

    return (
        <>
            <Head title={titulo} />
            <AppShell title={titulo} user={auth?.user ?? null}>
                <div className="grid max-w-3xl gap-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <Button asChild variant="ghost" size="sm">
                            <Link href="/painel/transcricoes">← Transcrições</Link>
                        </Button>
                        <BotoesDownload job={job} />
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                        {job.platform && <Badge variant="secondary">{job.platform}</Badge>}
                        {formatarDuracao(job.duration_seconds) && <span>{formatarDuracao(job.duration_seconds)}</span>}
                        <a href={job.source_url} target="_blank" rel="noreferrer noopener" className="truncate underline">
                            {job.source_url}
                        </a>
                    </div>

                    <Card>
                        <CardContent className="grid gap-4 pt-6 leading-relaxed">
                            {paragrafos.length === 0 ? (
                                <p className="text-sm text-muted-foreground">Sem texto — a transcrição ainda não terminou ou falhou.</p>
                            ) : (
                                paragrafos.map((p, i) => <p key={i}>{p}</p>)
                            )}
                        </CardContent>
                    </Card>
                </div>
            </AppShell>
        </>
    );
}
