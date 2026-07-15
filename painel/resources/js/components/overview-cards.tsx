import { Badge } from '@/components/ui/badge';
import { Card, CardAction, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { PipelineOverview, QuotaChannel } from '@/types/dashboard';

export function OverviewCards({ quota, overview }: { quota: QuotaChannel[]; overview: PipelineOverview }) {
    const totalPublished = overview.publishedCurto + overview.publishedLongo;
    const longoShare = totalPublished > 0 ? Math.round((overview.publishedLongo / totalPublished) * 100) : 0;
    const totalBacklog = overview.backlogCurto + overview.backlogLongo;

    return (
        <div className="grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4 dark:*:data-[slot=card]:bg-card">
            {quota.length === 0 && (
                <Card className="@container/card">
                    <CardHeader>
                        <CardDescription>Cota de uploads</CardDescription>
                        <CardTitle className="text-2xl font-semibold">—</CardTitle>
                        <CardAction>
                            <Badge variant="outline">Nenhum canal ativo</Badge>
                        </CardAction>
                    </CardHeader>
                </Card>
            )}
            {quota.map((channel) => (
                <Card key={channel.name} className="@container/card">
                    <CardHeader>
                        <CardDescription>{channel.name} — uploads hoje</CardDescription>
                        <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
                            {channel.count}/{channel.limit}
                        </CardTitle>
                        <CardAction>
                            <Badge variant={channel.count >= channel.limit ? 'destructive' : 'outline'}>
                                {channel.count >= channel.limit ? 'Cota atingida' : 'Disponível'}
                            </Badge>
                        </CardAction>
                    </CardHeader>
                </Card>
            ))}
            <Card className="@container/card">
                <CardHeader>
                    <CardDescription>Publicados (7 dias)</CardDescription>
                    <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
                        {overview.publishedCurto} curto / {overview.publishedLongo} longo
                    </CardTitle>
                    <CardAction>
                        <Badge variant="outline">{longoShare}% longo</Badge>
                    </CardAction>
                </CardHeader>
            </Card>
            <Card className="@container/card">
                <CardHeader>
                    <CardDescription>Backlog aguardando download</CardDescription>
                    <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
                        {overview.backlogCurto} curto / {overview.backlogLongo} longo
                    </CardTitle>
                    <CardAction>
                        <Badge variant={totalBacklog > 200 ? 'destructive' : 'outline'}>
                            {totalBacklog} no total
                        </Badge>
                    </CardAction>
                </CardHeader>
            </Card>
        </div>
    );
}
