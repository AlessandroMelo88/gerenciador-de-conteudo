import * as React from 'react';
import { Link } from '@inertiajs/react';

import { NavUser } from '@/components/nav-user';
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarRail,
} from '@/components/ui/sidebar';
import {
    AudioLinesIcon,
    ClapperboardIcon,
    LayoutDashboardIcon,
    LinkIcon,
    RadioTowerIcon,
    TvIcon,
    BookOpenIcon,
} from 'lucide-react';

type NavItem = {
    title: string;
    url: string;
    icon: React.ElementType;
    /** Rotas fora do SPA Inertia (Filament/Livewire) precisam de <a> normal, não <Link>. */
    external?: boolean;
};

const navItems: NavItem[] = [
    { title: 'Dashboard', url: '/painel', icon: LayoutDashboardIcon },
    { title: 'Canais Destino', url: '/painel/canais-destino', icon: TvIcon },
    { title: 'Canais Fonte', url: '/painel/canais-fonte', icon: RadioTowerIcon },
    { title: 'Vídeos', url: '/painel/videos', icon: ClapperboardIcon },
    { title: 'Processar Vídeo', url: '/painel/processar-video', icon: LinkIcon },
    { title: 'Transcrição Local', url: '/painel/transcricoes', icon: AudioLinesIcon },
    { title: 'Documentação', url: '/painel/documentacao', icon: BookOpenIcon },
];

export function AppSidebar({
    user,
    ...props
}: React.ComponentProps<typeof Sidebar> & { user: { name: string; email: string } | null }) {
    const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';

    return (
        <Sidebar collapsible="icon" {...props}>
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton size="lg" asChild>
                            <Link href="/painel">
                                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                                    <ClapperboardIcon className="size-4" />
                                </div>
                                <div className="grid flex-1 text-left text-sm leading-tight">
                                    <span className="truncate font-semibold">Canal de Cortes</span>
                                    <span className="truncate text-xs text-muted-foreground">Pipeline de clips</span>
                                </div>
                            </Link>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>
            <SidebarContent>
                <SidebarMenu className="px-2">
                    {navItems.map((item) => (
                        <SidebarMenuItem key={item.url}>
                            <SidebarMenuButton asChild isActive={currentPath === item.url} tooltip={item.title}>
                                {item.external ? (
                                    <a href={item.url}>
                                        <item.icon />
                                        <span>{item.title}</span>
                                    </a>
                                ) : (
                                    <Link href={item.url}>
                                        <item.icon />
                                        <span>{item.title}</span>
                                    </Link>
                                )}
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                    ))}
                </SidebarMenu>
            </SidebarContent>
            <SidebarFooter>
                <NavUser user={user} />
            </SidebarFooter>
            <SidebarRail />
        </Sidebar>
    );
}
