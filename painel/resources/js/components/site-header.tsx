import type { ReactNode } from 'react';

import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';

export function SiteHeader({
    title,
    description,
    actions,
}: {
    title: string;
    description?: ReactNode;
    actions?: ReactNode;
}) {
    return (
        <header className="flex shrink-0 flex-col gap-2 border-b px-4 py-3 transition-[width,height] ease-linear lg:px-6 group-has-data-[collapsible=icon]/sidebar-wrapper:h-auto">
            <div className="flex w-full items-center gap-1 lg:gap-2">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
                <h1 className="min-w-0 flex-1 truncate text-base font-medium">{title}</h1>
                {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
            </div>
            {description && <p className="max-w-3xl text-sm text-muted-foreground">{description}</p>}
        </header>
    );
}
