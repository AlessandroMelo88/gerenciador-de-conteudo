import type { ElementType, ReactNode } from 'react';
import { Head, Link, router, usePage } from '@inertiajs/react';
import { ArrowLeftIcon, BadgeDollarSignIcon, MousePointerClickIcon, RadioIcon, UsersIcon } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AppShell } from '@/layouts/app-shell';

type ChannelClicks = { channel: string; clicks: number };

type ChannelRow = ChannelClicks & { uniqueVisitors: number };

type DayRow = { date: string; clicks: number };

type OfferRow = {
    id: number;
    title: string;
    niche: string;
    network: string;
    status: string;
    trackingUrl: string;
    clicks: number;
    uniqueVisitors: number;
    lastClickAt: string | null;
    channels: ChannelClicks[];
};

type PageProps = {
    days: number;
    periods: number[];
    totals: { clicks: number; uniqueVisitors: number; offersWithClicks: number; approvedOffers: number };
    byChannel: ChannelRow[];
    byDay: DayRow[];
    byOffer: OfferRow[];
    niches: { slug: string; label: string }[];
    auth: { user: { name: string; email: string } | null };
};

const BASE_URL = '/painel/ofertas/performance';

const CHANNEL_LABELS: Record<string, string> = {
    telegram: 'Telegram',
    youtube: 'YouTube',
    blog: 'Blog',
    bio: 'Bio',
    instagram: 'Instagram',
    tiktok: 'TikTok',
    outro: 'Outro',
    direto: 'Sem canal',
};

const chartConfig = {
    clicks: { label: 'Cliques', color: 'var(--chart-2)' },
} satisfies ChartConfig;

const channelLabel = (channel: string) => CHANNEL_LABELS[channel] ?? channel;

const formatNumber = (n: number) => n.toLocaleString('pt-BR');

/** 2026-09-15 → 15/09 */
const shortDate = (iso: string) => {
    const [, month, day] = iso.split('-');
    return `${day}/${month}`;
};

function StatCard({ icon: Icon, label, value, hint }: { icon: ElementType; label: string; value: string; hint: ReactNode }) {
    return (
        <div className="rounded-2xl border border-border bg-card p-4 flex flex-col gap-3 shadow-xs min-w-0">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground truncate">
                <Icon className="w-4 h-4 text-primary shrink-0" />
                <span className="truncate">{label}</span>
            </div>
            <span className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-foreground">{value}</span>
            <div className="text-[11.5px] text-muted-foreground font-mono truncate">{hint}</div>
        </div>
    );
}

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

export default function OfferPerformance() {
    const { props } = usePage<PageProps>();
    const { days, periods, totals, byChannel, byDay, byOffer, niches, auth } = props;

    const nicheLabel = (slug: string) => niches.find((n) => n.slug === slug)?.label ?? slug;
    const topChannel = byChannel[0];
    const share = (clicks: number) => (totals.clicks > 0 ? Math.round((clicks / totals.clicks) * 100) : 0);

    const changePeriod = (value: number) => {
        router.get(BASE_URL, { days: value }, { preserveState: true, preserveScroll: true });
    };

    return (
        <>
            <Head title="Performance de ofertas" />
            <AppShell
                title="Performance de ofertas"
                user={auth.user}
                description="Cliques nos links rastreáveis /o/…, por oferta, canal de divulgação e dia."
                actions={
                    <Button variant="outline" size="sm" className="h-9 gap-1.5 rounded-xl" asChild>
                        <Link href="/painel/ofertas">
                            <ArrowLeftIcon className="w-4 h-4" /> Ofertas
                        </Link>
                    </Button>
                }
                withToaster={false}
            >
                <div className="flex flex-col gap-4">
                    <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-2xl border border-border bg-card w-fit">
                        {periods.map((value) => (
                            <button
                                key={value}
                                type="button"
                                onClick={() => changePeriod(value)}
                                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                                    days === value
                                        ? 'bg-primary text-primary-foreground shadow-sm'
                                        : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                                }`}
                            >
                                {value} dias
                            </button>
                        ))}
                    </div>

                    <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 min-w-0 w-full">
                        <StatCard
                            icon={MousePointerClickIcon}
                            label="Cliques"
                            value={formatNumber(totals.clicks)}
                            hint={`últimos ${days} dias`}
                        />
                        <StatCard
                            icon={UsersIcon}
                            label="Visitantes únicos"
                            value={formatNumber(totals.uniqueVisitors)}
                            hint="contados por hash, sem IP"
                        />
                        <StatCard
                            icon={BadgeDollarSignIcon}
                            label="Ofertas com clique"
                            value={formatNumber(totals.offersWithClicks)}
                            hint={`${formatNumber(totals.approvedOffers)} aprovadas no total`}
                        />
                        <StatCard
                            icon={RadioIcon}
                            label="Canal líder"
                            value={topChannel ? channelLabel(topChannel.channel) : '—'}
                            hint={topChannel ? `${share(topChannel.clicks)}% dos cliques` : 'sem cliques no período'}
                        />
                    </div>

                    {totals.clicks === 0 ? (
                        <div className="rounded-2xl border border-dashed border-border bg-card px-6 py-12 text-center text-sm text-muted-foreground">
                            Nenhum clique nos últimos {days} dias. Divulgue o link rastreável das ofertas aprovadas com
                            <span className="font-mono"> ?c=telegram</span>, <span className="font-mono">?c=youtube</span> etc. para
                            saber de onde vem cada clique.
                        </div>
                    ) : (
                        <>
                            <div className="grid gap-4 lg:grid-cols-3 min-w-0">
                                <div className="lg:col-span-2 min-w-0">
                                    <SectionCard title="Cliques por dia" description={`Últimos ${days} dias, dias sem clique aparecem zerados.`}>
                                        <div className="px-3 pb-4">
                                            <ChartContainer config={chartConfig} className="aspect-auto h-56 w-full">
                                                <BarChart data={byDay} margin={{ left: 0, right: 8 }}>
                                                    <CartesianGrid vertical={false} />
                                                    <XAxis
                                                        dataKey="date"
                                                        tickLine={false}
                                                        axisLine={false}
                                                        tickMargin={8}
                                                        minTickGap={24}
                                                        tickFormatter={shortDate}
                                                    />
                                                    <YAxis allowDecimals={false} tickLine={false} axisLine={false} width={32} />
                                                    <ChartTooltip
                                                        cursor={false}
                                                        content={<ChartTooltipContent labelFormatter={(label) => shortDate(String(label))} />}
                                                    />
                                                    <Bar dataKey="clicks" fill="var(--color-clicks)" radius={4} />
                                                </BarChart>
                                            </ChartContainer>
                                        </div>
                                    </SectionCard>
                                </div>

                                <SectionCard title="Por canal" description="Origem vem do parâmetro ?c= do link.">
                                    <Table className="w-full text-xs">
                                        <TableHeader className="bg-muted/40">
                                            <TableRow>
                                                <TableHead className="px-5 py-3 font-semibold">Canal</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold text-right">Cliques</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold text-right">Únicos</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {byChannel.map((row) => (
                                                <TableRow key={row.channel} className="hover:bg-muted/30">
                                                    <TableCell className="px-5 py-3">
                                                        <div className="font-semibold text-foreground">{channelLabel(row.channel)}</div>
                                                        <div className="mt-1.5 h-1.5 rounded-full bg-muted overflow-hidden">
                                                            <div className="h-full bg-primary rounded-full" style={{ width: `${share(row.clicks)}%` }} />
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3 text-right font-mono">
                                                        {formatNumber(row.clicks)}
                                                        <div className="text-[10.5px] text-muted-foreground">{share(row.clicks)}%</div>
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3 text-right font-mono">{formatNumber(row.uniqueVisitors)}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </SectionCard>
                            </div>

                            <SectionCard title="Por oferta" description="As 100 ofertas com mais cliques no período.">
                                <div className="overflow-x-auto">
                                    <Table className="w-full text-xs">
                                        <TableHeader className="bg-muted/40">
                                            <TableRow>
                                                <TableHead className="px-5 py-3 font-semibold">Oferta</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold text-right">Cliques</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold text-right">Únicos</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold hidden md:table-cell">Canais</TableHead>
                                                <TableHead className="px-5 py-3 font-semibold hidden lg:table-cell">Último clique</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {byOffer.map((offer) => (
                                                <TableRow key={offer.id} className="hover:bg-muted/30">
                                                    <TableCell className="px-5 py-3">
                                                        <div className="min-w-[220px] max-w-[420px]">
                                                            <div className="font-semibold text-foreground truncate" title={offer.title}>
                                                                {offer.title}
                                                            </div>
                                                            <div className="mt-1 flex flex-wrap items-center gap-1.5">
                                                                <Badge variant="outline" className="text-[10.5px]">
                                                                    {offer.network}
                                                                </Badge>
                                                                <span className="text-[11px] text-muted-foreground">{nicheLabel(offer.niche)}</span>
                                                                {offer.status !== 'approved' && (
                                                                    <span className="text-[11px] text-amber-600 dark:text-amber-400">{offer.status}</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3 text-right font-mono font-semibold">{formatNumber(offer.clicks)}</TableCell>
                                                    <TableCell className="px-5 py-3 text-right font-mono">{formatNumber(offer.uniqueVisitors)}</TableCell>
                                                    <TableCell className="px-5 py-3 hidden md:table-cell">
                                                        <div className="flex flex-wrap gap-1">
                                                            {offer.channels.map((c) => (
                                                                <span
                                                                    key={c.channel}
                                                                    className="rounded-md bg-muted text-muted-foreground px-1.5 py-0.5 text-[10.5px] font-mono"
                                                                >
                                                                    {channelLabel(c.channel)} {c.clicks}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3 hidden lg:table-cell text-muted-foreground whitespace-nowrap">
                                                        {offer.lastClickAt ?? '—'}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            </SectionCard>
                        </>
                    )}
                </div>
            </AppShell>
        </>
    );
}
