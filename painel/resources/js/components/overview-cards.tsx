import { Scissors, ThumbsUp, Gauge, Inbox } from 'lucide-react';
import type { PipelineOverview, QuotaChannel } from '@/types/dashboard';

export function OverviewCards({ quota, overview }: { quota: QuotaChannel[]; overview: PipelineOverview }) {
    const totalPublished = overview.publishedCurto + overview.publishedLongo;
    const totalBacklog = overview.backlogCurto + overview.backlogLongo;
    const totalPublishedToday = quota.reduce((acc, q) => acc + (q.count || 0), 0);
    const totalLimitToday = quota.reduce((acc, q) => acc + (q.limit || 5), 0);
    const quotaPercent =
        totalLimitToday > 0 ? Math.min(100, Math.round((totalPublishedToday / totalLimitToday) * 100)) : 0;

    return (
        <div className="flex flex-col gap-6">
            {/* 4 TOP METRIC CARDS */}
            <div className="grid w-full min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4">
                {/* Clipes Publicados */}
                <div className="flex min-w-0 flex-col gap-3 rounded-2xl border border-border bg-card p-4 shadow-xs">
                    <div className="flex min-w-0 items-start justify-between gap-2">
                        <div className="flex items-center gap-2 truncate text-xs font-medium text-muted-foreground">
                            <Scissors className="h-4 w-4 shrink-0 text-[#FF6A55]" />
                            <span className="truncate">Publicados (7d)</span>
                        </div>
                        <span className="shrink-0 rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[10.5px] font-semibold text-emerald-600 dark:text-emerald-400">
                            +{totalPublishedToday} hoje
                        </span>
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                            {totalPublished.toLocaleString('pt-BR')}
                        </span>
                        <span className="mb-1 text-xs text-muted-foreground">total 7d</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                        <div
                            className="h-full rounded-full bg-[#FF6A55]"
                            style={{ width: totalPublished > 0 ? '100%' : '0%' }}
                        />
                    </div>
                    <div className="truncate font-mono text-[11.5px] text-muted-foreground">
                        curto {overview.publishedCurto} · longo {overview.publishedLongo} nos últimos 7d
                    </div>
                </div>

                {/* Taxa de Aprovação */}
                <div className="flex min-w-0 flex-col gap-3 rounded-2xl border border-border bg-card p-4 shadow-xs">
                    <div className="flex min-w-0 items-start justify-between gap-2">
                        <div className="flex items-center gap-2 truncate text-xs font-medium text-muted-foreground">
                            <ThumbsUp className="h-4 w-4 shrink-0 text-emerald-500" />
                            <span className="truncate">Taxa de aprovação</span>
                        </div>
                        <span className="shrink-0 rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[10.5px] font-semibold text-emerald-600 dark:text-emerald-400">
                            Fila ativa
                        </span>
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                            {overview.approvalRate !== undefined && overview.approvalRate !== null
                                ? `${overview.approvalRate}%`
                                : totalPublished > 0
                                  ? '100%'
                                  : '—'}
                        </span>
                        <span className="mb-1 text-xs text-muted-foreground">taxa</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                        <div
                            className="h-full rounded-full bg-emerald-500 transition-all"
                            style={{
                                width:
                                    overview.approvalRate !== undefined && overview.approvalRate !== null
                                        ? `${overview.approvalRate}%`
                                        : totalPublished > 0
                                          ? '100%'
                                          : '0%',
                            }}
                        />
                    </div>
                    <div className="truncate font-mono text-[11.5px] text-muted-foreground">
                        {totalPublished > 0 ? `${totalPublished} clips publicados` : 'Aguardando aprovações'}
                    </div>
                </div>

                {/* Cota da API (Publicações de hoje) */}
                <div className="flex min-w-0 flex-col gap-3 rounded-2xl border border-border bg-card p-4 shadow-xs">
                    <div className="flex min-w-0 items-start justify-between gap-2">
                        <div className="flex items-center gap-2 truncate text-xs font-medium text-muted-foreground">
                            <Gauge className="h-4 w-4 shrink-0 text-amber-500" />
                            <span className="truncate">Cota de hoje</span>
                        </div>
                        <span className="shrink-0 rounded-md border border-amber-500/20 bg-amber-500/10 px-2 py-0.5 text-[10.5px] font-semibold text-amber-600 dark:text-amber-400">
                            {quotaPercent}% usado
                        </span>
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                            {totalPublishedToday}
                        </span>
                        <span className="mb-1 text-xs text-muted-foreground">/ {totalLimitToday} vídeos</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                        <div
                            className="h-full rounded-full bg-amber-500 transition-all"
                            style={{ width: `${quotaPercent}%` }}
                        />
                    </div>
                    <div
                        className="truncate font-mono text-[11.5px] text-muted-foreground"
                        title={
                            quota.length > 0
                                ? quota.map((q) => `${q.name}: ${q.count}/${q.limit}`).join(' · ')
                                : undefined
                        }
                    >
                        {quota.length > 0
                            ? quota
                                  .map(
                                      (q) =>
                                          `${q.niche === 'futebol' ? '⚽' : '🏛️'} ${q.name.split(' ')[0]}: ${q.count}/${q.limit}`,
                                  )
                                  .join(' · ')
                            : '0 de 5 limite diário por canal'}
                    </div>
                </div>

                {/* Backlog de Download */}
                <div className="flex min-w-0 flex-col gap-3 rounded-2xl border border-border bg-card p-4 shadow-xs">
                    <div className="flex min-w-0 items-start justify-between gap-2">
                        <div className="flex items-center gap-2 truncate text-xs font-medium text-muted-foreground">
                            <Inbox className="h-4 w-4 shrink-0 text-red-500" />
                            <span className="truncate">Backlog de download</span>
                        </div>
                        <span className="shrink-0 rounded-md border border-red-500/20 bg-red-500/10 px-2 py-0.5 text-[10.5px] font-semibold text-red-600 dark:text-red-400">
                            {totalBacklog > 50 ? 'Alto' : 'Normal'}
                        </span>
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                            {totalBacklog.toLocaleString('pt-BR')}
                        </span>
                        <span className="mb-1 text-xs text-muted-foreground">na fila</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                        <div
                            className="h-full rounded-full bg-red-500"
                            style={{
                                width: totalBacklog > 0 ? `${Math.min(100, Math.max(10, totalBacklog * 2))}%` : '0%',
                            }}
                        />
                    </div>
                    <div className="truncate font-mono text-[11.5px] text-muted-foreground">
                        curto {overview.backlogCurto} · longo {overview.backlogLongo} pendentes
                    </div>
                </div>
            </div>

            {/* USO DE COTA DA API POR CANAL DESTINO REAL */}
            {quota && quota.length > 0 && (
                <div className="rounded-2xl border border-border bg-card p-5">
                    <div className="mb-4 flex items-center justify-between">
                        <div>
                            <h2 className="font-display text-sm font-bold tracking-tight text-foreground">
                                Uso de cota da API (YouTube Shorts)
                            </h2>
                            <p className="text-xs text-muted-foreground">
                                Publicações realizadas hoje vs teto diário configurado por canal.
                            </p>
                        </div>
                        <span className="font-mono text-xs text-muted-foreground">reset 21:00 BRT</span>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {quota.map((ch) => {
                            const isPol =
                                (ch.niche ?? ch.name).toLowerCase().includes('política') ||
                                (ch.niche ?? ch.name).toLowerCase().includes('politica');
                            const isPod = (ch.niche ?? ch.name).toLowerCase().includes('podcast');
                            const pct = Math.min(100, Math.round(((ch.count || 0) / (ch.limit || 5)) * 100));

                            let themeClass =
                                'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
                            let barColor = 'bg-emerald-500';
                            let icon = '⚽';

                            if (isPol) {
                                themeClass =
                                    'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
                                barColor = 'bg-purple-500';
                                icon = '🏛️';
                            } else if (isPod) {
                                themeClass = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
                                barColor = 'bg-amber-500';
                                icon = '🎙️';
                            }

                            return (
                                <div key={ch.name} className={`rounded-xl border p-4 ${themeClass}`}>
                                    <div className="mb-2 flex items-center justify-between">
                                        <span className="truncate text-[13px] font-semibold" title={ch.name}>
                                            {icon} {ch.name}
                                        </span>
                                        <span className="shrink-0 font-mono text-xs font-bold">
                                            {ch.count}/{ch.limit}
                                        </span>
                                    </div>
                                    <div className="h-2 overflow-hidden rounded-full bg-black/10 dark:bg-white/[.08]">
                                        <div
                                            className={`h-full ${barColor} rounded-full transition-all`}
                                            style={{ width: `${pct}%` }}
                                        />
                                    </div>
                                    <div className="mt-2 font-mono text-[11px] opacity-80">
                                        {ch.count} de {ch.limit} publicações realizadas hoje ({pct}%)
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
