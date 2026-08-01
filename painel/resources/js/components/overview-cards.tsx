import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import type { ActiveWindowVideo, PipelineOverview, QuotaChannel } from '@/types/dashboard';
import { cn } from '@/lib/utils';

const WINDOW_CURTO = 6;
const WINDOW_LONGO = 4;

function quotaTone(count: number, limit: number): 'ok' | 'warn' | 'full' {
    if (limit <= 0 || count >= limit) return 'full';
    if (count / limit >= 0.8) return 'warn';
    return 'ok';
}

function FormatSplit({
    curto,
    longo,
    curtoCap,
    longoCap,
}: {
    curto: number;
    longo: number;
    curtoCap?: number;
    longoCap?: number;
}) {
    return (
        <p className="text-xs text-muted-foreground tabular-nums">
            curto {curto}
            {curtoCap != null ? `/${curtoCap}` : ''}
            <span className="mx-1.5 text-border">·</span>
            longo {longo}
            {longoCap != null ? `/${longoCap}` : ''}
        </p>
    );
}

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
    const longoShare = totalPublished > 0 ? Math.round((overview.publishedLongo / totalPublished) * 100) : 0;
    const totalBacklog = overview.backlogCurto + overview.backlogLongo;
    const windowCurto = activeWindow.filter((v) => v.format === 'curto').length;
    const windowLongo = activeWindow.filter((v) => v.format === 'longo').length;
    const windowTotal = activeWindow.length;
    const windowCap = WINDOW_CURTO + WINDOW_LONGO;
    const processingCount = activeWindow.filter((v) =>
        ['downloading', 'transcribing', 'selecting'].includes(v.status),
    ).length;

    return (
        <div className="grid grid-cols-2 gap-2 lg:grid-cols-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card *:data-[slot=card]:shadow-xs dark:*:data-[slot=card]:bg-card">
            {quota.length === 0 && (
                <Card size="sm">
                    <CardHeader className="gap-0.5">
                        <div className="flex items-start justify-between gap-2">
                            <CardDescription className="text-xs">Cota de uploads</CardDescription>
                            <Badge variant="outline" className="shrink-0 text-[10px]">
                                Sem canal
                            </Badge>
                        </div>
                        <CardTitle className="text-xl font-semibold tabular-nums">—</CardTitle>
                    </CardHeader>
                </Card>
            )}
            {quota.map((channel) => {
                const tone = quotaTone(channel.count, channel.limit);
                const pct = channel.limit > 0 ? Math.min(100, Math.round((channel.count / channel.limit) * 100)) : 0;
                return (
                    <Card key={channel.name} size="sm">
                        <CardHeader className="gap-0.5">
                            <div className="flex items-start justify-between gap-2">
                                <CardDescription className="line-clamp-1 text-xs">
                                    {channel.name} — hoje
                                </CardDescription>
                                <Badge
                                    variant={tone === 'full' ? 'destructive' : 'outline'}
                                    className="shrink-0 text-[10px]"
                                >
                                    {tone === 'full' ? 'Cheia' : tone === 'warn' ? 'Quase' : 'Ok'}
                                </Badge>
                            </div>
                            <CardTitle className="text-xl font-semibold tabular-nums tracking-tight">
                                {channel.count}
                                <span className="text-sm font-normal text-muted-foreground">/{channel.limit}</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-0">
                            <Progress
                                value={pct}
                                className={cn(
                                    'h-1',
                                    tone === 'full' && '*:data-[slot=progress-indicator]:bg-destructive',
                                    tone === 'warn' && '*:data-[slot=progress-indicator]:bg-amber-500',
                                )}
                            />
                        </CardContent>
                    </Card>
                );
            })}

            <Card size="sm">
                <CardHeader className="gap-0.5">
                    <div className="flex items-start justify-between gap-2">
                        <CardDescription className="text-xs">Janela de download</CardDescription>
                        <Badge variant={processingCount > 0 ? 'default' : 'outline'} className="shrink-0 text-[10px]">
                            {processingCount > 0 ? `${processingCount} proc.` : 'Ociosa'}
                        </Badge>
                    </div>
                    <CardTitle className="text-xl font-semibold tabular-nums tracking-tight">
                        {windowTotal}
                        <span className="text-sm font-normal text-muted-foreground">/{windowCap}</span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <FormatSplit
                        curto={windowCurto}
                        longo={windowLongo}
                        curtoCap={WINDOW_CURTO}
                        longoCap={WINDOW_LONGO}
                    />
                </CardContent>
            </Card>

            <Card size="sm">
                <CardHeader className="gap-0.5">
                    <div className="flex items-start justify-between gap-2">
                        <CardDescription className="text-xs">Publicados (7d)</CardDescription>
                        <Badge variant="outline" className="shrink-0 text-[10px]">
                            {longoShare}% longo
                        </Badge>
                    </div>
                    <CardTitle className="text-xl font-semibold tabular-nums tracking-tight">
                        {totalPublished}
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <FormatSplit curto={overview.publishedCurto} longo={overview.publishedLongo} />
                </CardContent>
            </Card>

            <Card size="sm">
                <CardHeader className="gap-0.5">
                    <div className="flex items-start justify-between gap-2">
                        <CardDescription className="text-xs">Backlog download</CardDescription>
                        <Badge
                            variant={totalBacklog > 200 ? 'destructive' : 'outline'}
                            className="shrink-0 text-[10px]"
                        >
                            {totalBacklog > 200 ? 'Alto' : 'Fila'}
                        </Badge>
                    </div>
                    <CardTitle className="text-xl font-semibold tabular-nums tracking-tight">
                        {totalBacklog}
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <FormatSplit curto={overview.backlogCurto} longo={overview.backlogLongo} />
                </CardContent>
            </Card>
        </div>
    );
}
