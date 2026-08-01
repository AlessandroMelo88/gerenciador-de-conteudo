import type { CSSProperties, ReactNode } from 'react';

import { AppSidebar } from '@/components/app-sidebar';
import { SiteHeader } from '@/components/site-header';
import { Toaster } from '@/components/ui/sonner';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

type AppShellProps = {
    title: string;
    user: { name: string; email: string } | null;
    description?: ReactNode;
    actions?: ReactNode;
    children: ReactNode;
    /** Inclui Toaster (default true). Páginas sem toast podem desligar. */
    withToaster?: boolean;
};

const shellStyle = {
    '--sidebar-width': 'calc(var(--spacing) * 72)',
    '--header-height': 'calc(var(--spacing) * 12)',
} as CSSProperties;

/**
 * Shell único do painel: sidebar inset + header customizável por página.
 * Cada page passa title/description/actions; o padding do conteúdo é uniforme.
 */
export function AppShell({
    title,
    user,
    description,
    actions,
    children,
    withToaster = true,
}: AppShellProps) {
    return (
        <SidebarProvider style={shellStyle}>
            {withToaster && <Toaster />}
            <AppSidebar variant="inset" user={user} />
            <SidebarInset>
                <SiteHeader title={title} description={description} actions={actions} />
                <div className="flex flex-1 flex-col gap-4 px-4 py-4 md:gap-6 md:py-6 lg:px-6">{children}</div>
            </SidebarInset>
        </SidebarProvider>
    );
}
