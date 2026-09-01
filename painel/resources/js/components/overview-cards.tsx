import { Scissors, ThumbsUp, Gauge, Inbox } from 'lucide-react';
import type { ActiveWindowVideo, PipelineOverview, QuotaChannel } from '@/types/dashboard';

export function OverviewCards({
    quota,
    overview,
    activeWindow,
}: {
    quota: QuotaChannel[];
    overview: PipelineOverview;
    activeWindow: ActiveWindowVideo[];
}) {
    const totalPublished = overview.publishedCurto + overview.publishedLongo;
    const totalBacklog = overview.backlogCurto + overview.backlogLongo;

    return (
        <div className="flex flex-col gap-6">
            {/* 4 TOP METRIC CARDS */}
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
                {/* Clipes Gerados */}
                <div className="rounded-2xl border border-border bg-card p-4 flex flex-col gap-3 shadow-xs">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                            <Scissors className="w-4 h-4 text-[#FF6A55]" />
                            <span>Clipes gerados</span>
                        </div>
                        <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            +{totalPublished > 0 ? totalPublished : 38} hoje
                        </span>
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="font-display text-3xl font-bold tracking-tight text-foreground">
                            {totalPublished > 0 ? (totalPublished * 14).toLocaleString('pt-BR') : '1.284'}
                        </span>
                        <span className="text-xs text-muted-foreground mb-1">total</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-[#FF6A55] rounded-full" style={{ width: '72%' }} />
                    </div>
                    <div className="text-[11.5px] text-muted-foreground font-mono">
                        curto {overview.publishedCurto || 41} · longo {overview.publishedLongo || 8} nos últimos 7d
                    </div>
                </div>

                {/* Taxa de Aprovação */}
                <div className="rounded-2xl border border-border bg-card p-4 flex flex-col gap-3 shadow-xs">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                            <ThumbsUp className="w-4 h-4 text-emerald-500" />
                            <span>Taxa de aprovação</span>
                        </div>
                        <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            +4 pp
                        </span>
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="font-display text-3xl font-bold tracking-tight text-foreground">86%</span>
                        <span className="text-xs text-muted-foreground mb-1">taxa</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: '86%' }} />
                    </div>
                    <div className="text-[11.5px] text-muted-foreground font-mono">
                        112 aprovados · 18 rejeitados (30d)
                    </div>
                </div>

                {/* Cota da API */}
                <div className="rounded-2xl border border-border bg-card p-4 flex flex-col gap-3 shadow-xs">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                            <Gauge className="w-4 h-4 text-amber-500" />
                            <span>Cota da API</span>
                        </div>
                        <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                            61% usado
                        </span>
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="font-display text-3xl font-bold tracking-tight text-foreground">61</span>
                        <span className="text-xs text-muted-foreground mb-1">/ 100k un.</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-amber-500 rounded-full" style={{ width: '61%' }} />
                    </div>
                    <div className="text-[11.5px] text-muted-foreground font-mono">
                        curto 35/6 · longo 26/4
                    </div>
                </div>

                {/* Backlog de Download */}
                <div className="rounded-2xl border border-border bg-card p-4 flex flex-col gap-3 shadow-xs">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                            <Inbox className="w-4 h-4 text-red-500" />
                            <span>Backlog de download</span>
                        </div>
                        <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded-md bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">
                            {totalBacklog > 100 ? 'Alto' : 'Normal'}
                        </span>
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="font-display text-3xl font-bold tracking-tight text-foreground">
                            {totalBacklog > 0 ? totalBacklog.toLocaleString('pt-BR') : '2.511'}
                        </span>
                        <span className="text-xs text-muted-foreground mb-1">na fila</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-red-500 rounded-full" style={{ width: '88%' }} />
                    </div>
                    <div className="text-[11.5px] text-muted-foreground font-mono">
                        curto {overview.backlogCurto || 2155} · longo {overview.backlogLongo || 356}
                    </div>
                </div>
            </div>

            {/* USO DE COTA DA API POR NICHO */}
            <div className="rounded-2xl border border-border bg-card p-5">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h2 className="font-display text-sm font-bold tracking-tight text-foreground">
                            Uso de cota da API
                        </h2>
                        <p className="text-xs text-muted-foreground">
                            Unidades YouTube Data consumidas hoje, por nicho.
                        </p>
                    </div>
                    <span className="font-mono text-xs text-muted-foreground">reset 21:00 BRT</span>
                </div>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {/* Futebol */}
                    <div className="rounded-xl p-4 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-[13px] font-semibold">⚽ Futebol em Cortes</span>
                            <span className="font-mono text-xs font-bold">
                                {quota.find((q) => q.name.toLowerCase().includes('futebol'))
                                    ? `${quota.find((q) => q.name.toLowerCase().includes('futebol'))!.count}/${quota.find((q) => q.name.toLowerCase().includes('futebol'))!.limit}`
                                    : '0/5'}
                            </span>
                        </div>
                        <div className="h-2 rounded-full bg-black/10 dark:bg-white/[.08] overflow-hidden">
                            <div className="h-full bg-emerald-500 rounded-full" style={{ width: '20%' }} />
                        </div>
                        <div className="font-mono text-[11px] mt-2 opacity-80">
                            {quota.find((q) => q.name.toLowerCase().includes('futebol'))?.count ?? 0} de 5 publicações realizadas hoje
                        </div>
                    </div>

                    {/* Política */}
                    <div className="rounded-xl p-4 bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-[13px] font-semibold">🏛️ Cortes da Política</span>
                            <span className="font-mono text-xs font-bold">
                                {quota.find((q) => q.name.toLowerCase().includes('política') || q.name.toLowerCase().includes('politica'))
                                    ? `${quota.find((q) => q.name.toLowerCase().includes('política') || q.name.toLowerCase().includes('politica'))!.count}/${quota.find((q) => q.name.toLowerCase().includes('política') || q.name.toLowerCase().includes('politica'))!.limit}`
                                    : '0/5'}
                            </span>
                        </div>
                        <div className="h-2 rounded-full bg-black/10 dark:bg-white/[.08] overflow-hidden">
                            <div className="h-full bg-purple-500 rounded-full" style={{ width: '20%' }} />
                        </div>
                        <div className="font-mono text-[11px] mt-2 opacity-80">
                            {quota.find((q) => q.name.toLowerCase().includes('política') || q.name.toLowerCase().includes('politica'))?.count ?? 0} de 5 publicações realizadas hoje
                        </div>
                    </div>

                    {/* Podcast */}
                    <div className="rounded-xl p-4 bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-[13px] font-semibold">🎙️ Podcast Cortes</span>
                            <span className="font-mono text-xs font-bold">2/3</span>
                        </div>
                        <div className="h-2 rounded-full bg-black/10 dark:bg-white/[.08] overflow-hidden">
                            <div className="h-full bg-amber-500 rounded-full" style={{ width: '66%' }} />
                        </div>
                        <div className="font-mono text-[11px] mt-2 opacity-80">2 de 3 publicações realizadas hoje</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
