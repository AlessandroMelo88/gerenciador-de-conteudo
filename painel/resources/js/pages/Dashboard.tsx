import { useEffect } from 'react';
import { Head, usePage } from '@inertiajs/react';
import { toast } from 'sonner';

import { ActiveWindowTable } from '@/components/active-window-table';
import { ClipQueueTabs } from '@/components/clip-queue-tabs';
import { OverviewCards } from '@/components/overview-cards';
import { AppShell } from '@/layouts/app-shell';
import type { DashboardPageProps } from '@/types/dashboard';

export default function Dashboard() {
    const { props } = usePage<DashboardPageProps>();
    const { quota, overview, pendingClips, queuedClips, failures, failedSourceVideoCount, activeWindow, auth, flash } =
        props;

    useEffect(() => {
        if (flash?.success) toast.success(flash.success);
        if (flash?.error) toast.error(flash.error);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <>
            <Head title="Dashboard" />
            <AppShell
                title="Dashboard"
                user={auth.user}
                description='Central de controle do pipeline: baixa → transcreve → IA seleciona momentos → corta → publica. Clips com o mesmo título vindo do mesmo vídeo não são duplicados — veja a coluna "Trecho".'
            >
                <OverviewCards quota={quota} overview={overview} activeWindow={activeWindow} />
                <div>
                    <h2 className="mb-3 text-sm font-medium">Janela de download ativa</h2>
                    <ActiveWindowTable videos={activeWindow} />
                </div>
                <ClipQueueTabs
                    pendingClips={pendingClips}
                    queuedClips={queuedClips}
                    failures={failures}
                    failedSourceVideoCount={failedSourceVideoCount}
                />
            </AppShell>
        </>
    );
}
