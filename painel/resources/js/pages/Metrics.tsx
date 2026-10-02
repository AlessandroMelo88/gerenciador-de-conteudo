import type { ReactNode } from 'react';
import { Head, usePage } from '@inertiajs/react';
import { EyeIcon, ExternalLinkIcon } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AppShell } from '@/layouts/app-shell';

type FormatRow = {
    format: 'curto' | 'longo';
    label: string;
    clips: number;
    avgViews24h: number | null;
    clips24h: number;
    avgViews7d: number | null;
    clips7d: number;
    avgViewsNow: number | null;
    avgRetention: number | null;
};

type SourceRow = {
    source: string;
    clips: number;
    avgViewsNow: number | null;
    totalViews: number;
    shortClips: number;
    longClips: number;
    avgRetention: number | null;
};

type LowRow = {
    id: number;
    title: string;
    source: string;
    format: 'curto' | 'longo';
    views: number;
    retention: number | null;
    daysOnline: number;
    url: string | null;
};

type PageProps = {
    hasData: boolean;
    hasRetention: boolean;
    publishedClips: number;
    measuredClips: number;
    lastCollectedAt: string | null;
    lowViewsThreshold: number;
    byFormat: FormatRow[];
    bySource: SourceRow[];
    lowViews: LowRow[];
    auth: { user: { name: string; email: string } | null };
};

const formatNumber = (n: number | null) => (n === null ? '—' : n.toLocaleString('pt-BR'));

// Retenção como percentual. Sem medição é travessão: 0% seria uma medição, e não medimos nada.
const formatRetention = (v: number | null) => (v === null ? '—' : `${v.toFixed(1)}%`);

function SectionCard({ title, description, children }: { title: string; description: string; children: ReactNode }) {
    return (
        <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-xs min-w-0">
            <div className="px-5 pt-4 pb-3">
                <h2 className="font-display text-sm font-bold tracking-tight text-foreground">{title}</h2>
                <p className="text-xs text-muted-foreground">{description}</p>
            </div>
            {children}
        </div>
    );
}

function FormatCard({ row }: { row: FormatRow }) {
    return (
        <div className="rounded-2xl border border-border bg-card p-5 shadow-xs min-w-0 flex flex-col gap-4" data-testid={`format-${row.format}`}>
            <div className="flex items-center justify-between gap-2">
                <h3 className="font-display text-base font-bold text-foreground">{row.label}</h3>
                <Badge variant="outline" className="font-mono text-[10.5px]">
                    {formatNumber(row.clips)} clips medidos
                </Badge>
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                        {formatNumber(row.avgViews24h)}
                    </div>
                    <div className="text-xs text-muted-foreground">views em média no 1º dia</div>
                    <div className="text-[11px] text-muted-foreground font-mono">{row.clips24h} clips com 24 h</div>
                </div>
                <div>
                    <div className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                        {formatNumber(row.avgViews7d)}
                    </div>
                    <div className="text-xs text-muted-foreground">views em média aos 7 dias</div>
                    <div className="text-[11px] text-muted-foreground font-mono">{row.clips7d} clips com 7 dias</div>
                </div>
                <div>
                    <div className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                        {formatRetention(row.avgRetention)}
                    </div>
                    <div className="text-xs text-muted-foreground">do clip assistido, em média</div>
                    <div className="text-[11px] text-muted-foreground font-mono">quanto o trecho segura</div>
                </div>
            </div>
        </div>
    );
}

export default function Metrics() {
    const { props } = usePage<PageProps>();
    const { hasData, hasRetention, publishedClips, measuredClips, lastCollectedAt, lowViewsThreshold, byFormat, bySource, lowViews, auth } = props;

    return (
        <>
            <Head title="Métricas" />
            <AppShell
                title="Métricas"
                user={auth.user}
                description="Quantas visualizações os clips publicados no YouTube estão tendo, por formato e por canal de origem."
                withToaster={false}
            >
                {!hasData ? (
                    <div className="rounded-2xl border border-dashed border-border bg-card px-6 py-12 text-center text-sm text-muted-foreground">
                        <EyeIcon className="mx-auto mb-3 h-6 w-6 text-primary" />
                        <p className="font-semibold text-foreground">Ainda sem dados.</p>
                        <p className="mt-1">
                            A primeira coleta roda em até 6 horas depois que houver clips publicados. O sistema consulta o YouTube
                            sozinho e esta tela se preenche. {publishedClips > 0 && `Já existem ${publishedClips} clips publicados esperando a primeira medição.`}
                        </p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-4">
                        <p className="text-xs text-muted-foreground">
                            {measuredClips} de {publishedClips} clips publicados já foram medidos. Última coleta: {lastCollectedAt ?? '—'} (horário de
                            Brasília). Os números são as visualizações que o próprio YouTube informa.
                        </p>

                        {!hasRetention && (
                            <p className="rounded-md border border-dashed border-muted-foreground/30 px-4 py-3 text-xs text-muted-foreground">
                                Retenção ainda não coletada. Os canais precisam ser reautorizados no Google com o escopo de
                                Analytics e a carga retroativa precisa rodar uma vez.
                            </p>
                        )}

                        <div className="grid gap-3 sm:gap-4 grid-cols-1 md:grid-cols-2 min-w-0">
                            {byFormat.map((row) => (
                                <FormatCard key={row.format} row={row} />
                            ))}
                        </div>

                        <SectionCard
                            title="Qual canal de origem rende mais"
                            description="De onde saíram os vídeos que viraram clips, do que mais para o que menos segura o espectador (retenção média por clip; sem retenção coletada, ordena por visualizações)."
                        >
                            <div className="overflow-x-auto">
                                <Table className="w-full text-xs">
                                    <TableHeader className="bg-muted/40">
                                        <TableRow>
                                            <TableHead className="px-5 py-3 font-semibold">#</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold">Canal de origem</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold text-right">Clips</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold text-right">Retenção média</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold text-right">Views por clip</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold text-right hidden md:table-cell">Views no total</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold hidden md:table-cell">Formatos</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {bySource.map((row, i) => (
                                            <TableRow key={row.source} className="hover:bg-muted/30">
                                                <TableCell className="px-5 py-3 font-mono text-muted-foreground">{i + 1}</TableCell>
                                                <TableCell className="px-5 py-3 font-semibold text-foreground">{row.source}</TableCell>
                                                <TableCell className="px-5 py-3 text-right font-mono">{formatNumber(row.clips)}</TableCell>
                                                <TableCell className="px-5 py-3 text-right font-mono font-semibold">{formatRetention(row.avgRetention)}</TableCell>
                                                <TableCell className="px-5 py-3 text-right font-mono">{formatNumber(row.avgViewsNow)}</TableCell>
                                                <TableCell className="px-5 py-3 text-right font-mono hidden md:table-cell">{formatNumber(row.totalViews)}</TableCell>
                                                <TableCell className="px-5 py-3 text-muted-foreground hidden md:table-cell">
                                                    {row.shortClips} Shorts · {row.longClips} longos
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </div>
                        </SectionCard>

                        <SectionCard
                            title="Clips que não pegaram"
                            description={`Publicados há mais de 2 dias e que ainda têm menos de ${lowViewsThreshold} visualizações. Ajudam a ver de onde não vale cortar.`}
                        >
                            {lowViews.length === 0 ? (
                                <p className="px-5 pb-5 text-sm text-muted-foreground">Nenhum clip nessa situação por enquanto.</p>
                            ) : (
                                <div className="overflow-x-auto">
                                    <Table className="w-full text-xs">
                                        <TableHeader className="bg-muted/40">
                                            <TableRow>
                                                <TableHead className="px-5 py-3 font-semibold">Clip</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold hidden md:table-cell">Canal de origem</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold text-right">Views</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold text-right">Retenção</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold text-right">Dias no ar</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {lowViews.map((clip) => (
                                                <TableRow key={clip.id} className="hover:bg-muted/30">
                                                    <TableCell className="px-5 py-3">
                                                        <div className="min-w-[200px] max-w-[420px] flex items-center gap-1.5">
                                                            <span className="font-semibold text-foreground truncate" title={clip.title}>
                                                                {clip.title}
                                                            </span>
                                                            <Badge variant="outline" className="text-[10.5px] shrink-0">
                                                                {clip.format === 'longo' ? 'Longo' : 'Short'}
                                                            </Badge>
                                                            {clip.url && (
                                                                <a
                                                                    href={clip.url}
                                                                    target="_blank"
                                                                    rel="noreferrer"
                                                                    aria-label="Abrir no YouTube"
                                                                    className="text-muted-foreground hover:text-foreground shrink-0"
                                                                >
                                                                    <ExternalLinkIcon className="h-3.5 w-3.5" />
                                                                </a>
                                                            )}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3 hidden md:table-cell text-muted-foreground">{clip.source}</TableCell>
                                                    <TableCell className="px-5 py-3 text-right font-mono font-semibold">{formatNumber(clip.views)}</TableCell>
                                                    <TableCell className="px-5 py-3 text-right font-mono">{formatRetention(clip.retention)}</TableCell>
                                                    <TableCell className="px-5 py-3 text-right font-mono">{clip.daysOnline}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            )}
                        </SectionCard>
                    </div>
                )}
            </AppShell>
        </>
    );
}
