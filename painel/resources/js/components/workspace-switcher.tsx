import * as React from 'react';
import { router } from '@inertiajs/react';
import { CheckIcon, ChevronsUpDownIcon } from 'lucide-react';

import { BrandMark, useBrand } from '@/components/brand-logo';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar } from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

export type Workspace = {
    key: string;
    name: string;
    tagline: string;
    /** Página aberta ao trocar para esta área. */
    home: string;
    /** Ícone próprio; sem ele usa a marca do servidor (BrandMark). */
    icon?: React.ElementType;
    gradient?: string;
};

function WorkspaceMark({ workspace, className, iconClassName }: { workspace: Workspace; className?: string; iconClassName?: string }) {
    if (!workspace.icon) {
        return <BrandMark className={className} iconClassName={iconClassName} />;
    }

    const Icon = workspace.icon;
    return (
        <div
            className={cn('flex aspect-square items-center justify-center text-white shadow-sm', className)}
            style={{ background: workspace.gradient }}
        >
            <Icon className={iconClassName} />
        </div>
    );
}

/** Seletor de área no topo da sidebar (padrão team-switcher do shadcn sidebar-07). */
export function WorkspaceSwitcher({ workspaces, active }: { workspaces: Workspace[]; active: Workspace }) {
    const { isMobile } = useSidebar();
    const brand = useBrand();
    // A área principal herda nome/tagline da marca resolvida no servidor (host/APP_BRAND).
    const label = (w: Workspace) => (w.icon ? w : { ...w, name: brand.name, tagline: brand.tagline });

    return (
        <SidebarMenu>
            <SidebarMenuItem>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <SidebarMenuButton
                            size="lg"
                            className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                        >
                            <WorkspaceMark workspace={active} className="size-9 rounded-xl" iconClassName="size-4.5" />
                            <div className="grid flex-1 text-left text-sm leading-tight">
                                <span className="truncate font-display font-bold text-foreground">{label(active).name}</span>
                                <span className="truncate text-xs text-muted-foreground">{label(active).tagline}</span>
                            </div>
                            <ChevronsUpDownIcon className="ml-auto size-4 text-muted-foreground" />
                        </SidebarMenuButton>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                        className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                        align="start"
                        side={isMobile ? 'bottom' : 'right'}
                        sideOffset={4}
                    >
                        <DropdownMenuLabel className="text-xs text-muted-foreground">Áreas</DropdownMenuLabel>
                        {workspaces.map((workspace) => (
                            <DropdownMenuItem
                                key={workspace.key}
                                onClick={() => workspace.key !== active.key && router.visit(workspace.home)}
                                className="cursor-pointer gap-2 p-2"
                            >
                                <WorkspaceMark workspace={workspace} className="size-7 rounded-lg" iconClassName="size-3.5" />
                                <div className="grid flex-1 leading-tight">
                                    <span className="text-sm font-medium">{label(workspace).name}</span>
                                    <span className="text-xs text-muted-foreground">{label(workspace).tagline}</span>
                                </div>
                                {workspace.key === active.key && <CheckIcon className="ml-auto size-4" />}
                            </DropdownMenuItem>
                        ))}
                    </DropdownMenuContent>
                </DropdownMenu>
            </SidebarMenuItem>
        </SidebarMenu>
    );
}
