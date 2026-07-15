import { useEffect } from 'react';
import { Head, usePage } from '@inertiajs/react';
import { toast } from 'sonner';

import { ActiveWindowTable } from '@/components/active-window-table';
import { AppSidebar } from '@/components/app-sidebar';
import { ClipQueueTabs } from '@/components/clip-queue-tabs';
import { OverviewCards } from '@/components/overview-cards';
import { PageHeader } from '@/components/page-header';
import { SiteHeader } from '@/components/site-header';
import { Toaster } from '@/components/ui/sonner';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
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
            <Toaster />
            <SidebarProvider
                style={
                    {
                        '--sidebar-width': 'calc(var(--spacing) * 72)',
                        '--header-height': 'calc(var(--spacing) * 12)',
                    } as React.CSSProperties
                }
            >
                <AppSidebar variant="inset" user={auth.user} />
                <SidebarInset>
                    <SiteHeader title="Dashboard" />
                    <div className="flex flex-1 flex-col">
                        <div className="@container/main flex flex-1 flex-col gap-2">
                            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                                <div className="px-4 lg:px-6">
                                    <PageHeader description="Central de controle do pipeline: baixa → transcreve → IA seleciona momentos → corta → publica. Clips com o mesmo título vindo do mesmo vídeo não são duplicados — veja a coluna &quot;Trecho&quot;." />
                                </div>
                                <OverviewCards quota={quota} overview={overview} />
                                <div className="px-4 lg:px-6">
                                    <h2 className="mb-3 text-sm font-medium">Janela de download ativa</h2>
                                    <ActiveWindowTable videos={activeWindow} />
                                </div>
                                <ClipQueueTabs
                                    pendingClips={pendingClips}
                                    queuedClips={queuedClips}
                                    failures={failures}
                                    failedSourceVideoCount={failedSourceVideoCount}
                                />
                            </div>
                        </div>
                    </div>
                </SidebarInset>
            </SidebarProvider>
        </>
    );
}
