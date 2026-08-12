import { HardDriveIcon, DownloadIcon, LayersIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

export type StorageMetrics = {
    freeGb: number;
    totalGb: number;
    usedGb: number;
    usedPercentage: number;
    status: 'ok' | 'warning' | 'critical' | 'unknown';
};

export type DownloadWindowMetrics = {
    total: number;
    cap: number;
    curtoCount: number;
    curtoCap: number;
    longoCount: number;
    longoCap: number;
    processingCount: number;
};

export function VideoSummaryCards({
    storage,
    downloadWindow,
}: {
    storage?: StorageMetrics;
    downloadWindow?: DownloadWindowMetrics;
}) {
    if (!storage || !downloadWindow) return null;

    return (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 mb-6 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card *:data-[slot=card]:shadow-xs dark:*:data-[slot=card]:bg-card">
            <Card size="sm">
                <CardHeader className="gap-1">
                    <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 text-muted-foreground">
                            <HardDriveIcon className="h-4 w-4" />
                            <CardDescription className="text-xs font-medium">Armazenamento em Disco (HD)</CardDescription>
                        </div>
                        <Badge
                            variant={
                                storage.status === 'critical'
                                    ? 'destructive'
                                    : storage.status === 'warning'
                                    ? 'secondary'
                                    : 'outline'
                            }
                            className="shrink-0 text-[10px]"
                        >
                            {storage.status === 'critical'
                                ? 'Crítico'
                                : storage.status === 'warning'
                                ? 'Quase Cheio'
                                : 'Ok'}
                        </Badge>
                    </div>
                    <CardTitle className="text-2xl font-semibold tabular-nums tracking-tight">
                        {storage.freeGb} GB <span className="text-sm font-normal text-muted-foreground">livres</span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-0 space-y-1.5">
                    <Progress
                        value={storage.usedPercentage}
                        className={cn(
                            'h-1.5',
                            storage.status === 'critical' && '*:data-[slot=progress-indicator]:bg-destructive',
                            storage.status === 'warning' && '*:data-[slot=progress-indicator]:bg-amber-500'
                        )}
                    />
                    <div className="flex justify-between text-[11px] text-muted-foreground tabular-nums">
                        <span>Usado: {storage.usedGb} GB ({storage.usedPercentage}%)</span>
                        <span>Total: {storage.totalGb} GB</span>
                    </div>
                </CardContent>
            </Card>

            <Card size="sm">
                <CardHeader className="gap-1">
                    <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 text-muted-foreground">
                            <DownloadIcon className="h-4 w-4" />
                            <CardDescription className="text-xs font-medium">Janela de Processamento Ativa</CardDescription>
                        </div>
                        <Badge
                            variant={downloadWindow.processingCount > 0 ? 'default' : 'outline'}
                            className="shrink-0 text-[10px]"
                        >
                            {downloadWindow.processingCount > 0
                                ? `${downloadWindow.processingCount} em proc.`
                                : 'Janela com vaga'}
                        </Badge>
                    </div>
                    <CardTitle className="text-2xl font-semibold tabular-nums tracking-tight">
                        {downloadWindow.total}
                        <span className="text-sm font-normal text-muted-foreground">/{downloadWindow.cap} vídeos ativos</span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <p className="text-xs text-muted-foreground tabular-nums flex items-center gap-1">
                        <LayersIcon className="h-3 w-3 text-muted-foreground/70" />
                        curto {downloadWindow.curtoCount}/{downloadWindow.curtoCap}
                        <span className="mx-1.5 text-border">·</span>
                        longo {downloadWindow.longoCount}/{downloadWindow.longoCap}
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
