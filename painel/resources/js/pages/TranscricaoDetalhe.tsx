import { Fragment, useEffect, useMemo, useRef, useState } from 'react';
import { Head, Link, router, usePage } from '@inertiajs/react';
import { PencilIcon } from 'lucide-react';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
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
import { AppShell } from '@/layouts/app-shell';
import { BotoesDownload, formatarDuracao } from '@/pages/TranscricaoLocal';
import type { FocoDetalhe } from '@/types/busca-transcricoes';

type Job = {
    id: number;
    source_url: string;
    title: string | null;
    platform: string | null;
    duration_seconds: number | null;
    status: 'pending' | 'downloading' | 'transcribing' | 'paused' | 'done' | 'failed';
    transcript_text: string | null;
    media_path: string | null;
    media_bytes: number | null;
    created_at: string;
};

type PageProps = {
    auth?: { user: { name: string; email: string } | null };
    job: Job;
    focus?: FocoDetalhe | null;
};

/** Minúsculas e sem acento, unidade a unidade, para manter os índices do original. */
function normalizar(texto: string): string {
    return texto
        .split('')
        .map((c) => (c.normalize('NFD')[0] ?? c).toLowerCase()[0] ?? c)
        .join('');
}

function termosDaBusca(q: string | null | undefined): string[] {
    if (!q) return [];
    return Array.from(new Set(normalizar(q).split(/[^\p{L}\p{N}]+/u).filter((t) => t.length >= 3)));
}

/** Parágrafo a focar: o que mais casa com os termos; empate (ou sem termos) vai pela posição estimada em `t`. */
function escolherParagrafo(paragrafos: string[], termos: string[], t: number | null, duracao: number | null): number | null {
    if (paragrafos.length === 0) return null;
    const total = paragrafos.reduce((n, p) => n + p.length, 0) || 1;
    let alvo: number | null = null;
    if (t !== null && duracao && duracao > 0) {
        const posicao = Math.min(1, Math.max(0, t / duracao)) * total;
        let acumulado = 0;
        alvo = paragrafos.length - 1;
        for (let i = 0; i < paragrafos.length; i++) {
            acumulado += paragrafos[i].length;
            if (acumulado >= posicao) {
                alvo = i;
                break;
            }
        }
    }
    const notas = paragrafos.map((p) => {
        const n = normalizar(p);
        return termos.filter((termo) => n.includes(termo)).length;
    });
    const melhor = Math.max(0, ...notas);
    if (melhor === 0) return alvo;
    const candidatos = notas.flatMap((nota, i) => (nota === melhor ? [i] : []));
    if (alvo === null) return candidatos[0];
    return candidatos.reduce((a, b) => (Math.abs(b - alvo) < Math.abs(a - alvo) ? b : a));
}

/** Divide o parágrafo em pedaços, marcando as ocorrências dos termos (sem HTML cru). */
function comDestaque(texto: string, termos: string[]) {
    if (termos.length === 0) return texto;
    const n = normalizar(texto);
    const marcado = new Array<boolean>(texto.length).fill(false);
    for (const termo of termos) {
        for (let i = n.indexOf(termo); i !== -1; i = n.indexOf(termo, i + termo.length)) {
            for (let k = i; k < i + termo.length; k++) marcado[k] = true;
        }
    }
    const partes: React.ReactNode[] = [];
    let inicio = 0;
    for (let i = 1; i <= texto.length; i++) {
        if (i === texto.length || marcado[i] !== marcado[inicio]) {
            const trecho = texto.slice(inicio, i);
            partes.push(
                marcado[inicio] ? (
                    <mark key={inicio} className="rounded-sm bg-yellow-300/40 px-0.5 text-foreground dark:bg-yellow-400/30">
                        {trecho}
                    </mark>
                ) : (
                    <Fragment key={inicio}>{trecho}</Fragment>
                ),
            );
            inicio = i;
        }
    }
    return partes;
}

export default function TranscricaoDetalhe() {
    const { props } = usePage<PageProps>();
    const { auth, job, focus } = props;
    const titulo = job.title || `Transcrição ${job.id}`;
    const paragrafos = useMemo(() => (job.transcript_text ?? '').split(/\n{2,}/).filter(Boolean), [job.transcript_text]);
    const termos = useMemo(() => termosDaBusca(focus?.q), [focus?.q]);
    const focado = useMemo(
        () => (focus && (focus.t !== null || termos.length > 0) ? escolherParagrafo(paragrafos, termos, focus.t, job.duration_seconds) : null),
        [focus, paragrafos, termos, job.duration_seconds],
    );
    const refFocado = useRef<HTMLParagraphElement | null>(null);

    const [modalEditarAberto, setModalEditarAberto] = useState(false);
    const [novoTitulo, setNovoTitulo] = useState(job.title || '');
    const [salvando, setSalvando] = useState(false);

    useEffect(() => {
        setNovoTitulo(job.title || '');
    }, [job.title]);

    function salvarTitulo(e: React.FormEvent) {
        e.preventDefault();
        if (!novoTitulo.trim()) return;
        setSalvando(true);
        router.patch(
            `/painel/transcricoes/${job.id}`,
            { title: novoTitulo.trim() },
            {
                preserveScroll: true,
                onSuccess: () => {
                    setModalEditarAberto(false);
                    setSalvando(false);
                    toast.success('Título atualizado.');
                },
                onError: () => setSalvando(false),
            },
        );
    }

    useEffect(() => {
        if (focado === null || !refFocado.current) return;
        const reduzido = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
        // Numa navegação do Inertia (clique no minuto do resultado), o Inertia zera a rolagem
        // logo depois de montar a página e desfaz o scrollIntoView; por isso o pequeno atraso.
        const espera = setTimeout(() => {
            refFocado.current?.scrollIntoView({ behavior: reduzido ? 'auto' : 'smooth', block: 'center' });
        }, 120);
        return () => clearTimeout(espera);
    }, [focado]);

    return (
        <>
            <Head title={titulo} />
            <AppShell title={titulo} user={auth?.user ?? null}>
                <div className="grid max-w-3xl gap-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <Button asChild variant="ghost" size="sm">
                            <Link href="/painel/transcricoes">← Transcrições</Link>
                        </Button>
                        <div className="flex flex-wrap items-center gap-2">
                            <Button size="sm" variant="outline" onClick={() => setModalEditarAberto(true)} className="gap-1.5">
                                <PencilIcon className="size-3.5" />
                                Renomear aula
                            </Button>
                            <BotoesDownload job={job} />
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                        {job.platform && <Badge variant="secondary">{job.platform}</Badge>}
                        {formatarDuracao(job.duration_seconds) && <span>{formatarDuracao(job.duration_seconds)}</span>}
                        <a href={job.source_url} target="_blank" rel="noreferrer noopener" className="truncate underline">
                            {job.source_url}
                        </a>
                    </div>

                    {/* Modal para editar título */}
                    <Dialog open={modalEditarAberto} onOpenChange={setModalEditarAberto}>
                        <DialogContent>
                            <form onSubmit={salvarTitulo} className="grid gap-4">
                                <DialogHeader>
                                    <DialogTitle>Editar título da aula</DialogTitle>
                                    <DialogDescription>
                                        Ajuste o nome da aula e módulo para manter seus estudos e e-books organizados.
                                    </DialogDescription>
                                </DialogHeader>
                                <Field>
                                    <FieldLabel htmlFor="detalhe-titulo">Nome da aula / Módulo</FieldLabel>
                                    <Input
                                        id="detalhe-titulo"
                                        value={novoTitulo}
                                        onChange={(e) => setNovoTitulo(e.target.value)}
                                        placeholder="Ex: [Mód. 3 - Criação e Identidade] Como clonar vídeos de Canais Dark"
                                        autoFocus
                                    />
                                    <FieldDescription>
                                        Exemplo: [Mód. 3 - Criação e Identidade] Como clonar vídeos de Canais Dark
                                    </FieldDescription>
                                </Field>
                                <DialogFooter>
                                    <Button type="button" variant="outline" onClick={() => setModalEditarAberto(false)}>
                                        Cancelar
                                    </Button>
                                    <Button type="submit" disabled={salvando || !novoTitulo.trim()}>
                                        {salvando ? 'Salvando...' : 'Salvar título'}
                                    </Button>
                                </DialogFooter>
                            </form>
                        </DialogContent>
                    </Dialog>

                    <Card>
                        <CardContent className="grid gap-4 pt-6 leading-relaxed">
                            {paragrafos.length === 0 ? (
                                <p className="text-sm text-muted-foreground">Sem texto — a transcrição ainda não terminou ou falhou.</p>
                            ) : (
                                paragrafos.map((p, i) => (
                                    <p
                                        key={i}
                                        ref={i === focado ? refFocado : undefined}
                                        tabIndex={i === focado ? -1 : undefined}
                                        aria-current={i === focado ? 'location' : undefined}
                                        className={
                                            i === focado
                                                ? '-mx-3 scroll-mt-24 rounded-md bg-accent px-3 py-2 ring-2 ring-ring/60 outline-none'
                                                : undefined
                                        }
                                    >
                                        {comDestaque(p, termos)}
                                    </p>
                                ))
                            )}
                        </CardContent>
                    </Card>
                </div>
            </AppShell>
        </>
    );
}
