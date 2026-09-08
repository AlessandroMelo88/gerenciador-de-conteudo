import * as React from 'react';
import { Link, usePage } from '@inertiajs/react';

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
    SparklesIcon,
    BotIcon,
    BookmarkIcon,
} from 'lucide-react';

type NavItem = {
    title: string;
    url: string;
    icon: React.ElementType;
    /** Rotas fora do SPA Inertia precisam de <a> normal, não <Link>. */
    external?: boolean;
};

const navItems: (NavItem & { badge?: string | number })[] = [
    { title: 'Dashboard', url: '/painel', icon: LayoutDashboardIcon, badge: 9 },
    { title: 'Assistente IA', url: '/painel/assistente', icon: BotIcon, badge: 'LLaMA' },
    { title: 'Canais Destino', url: '/painel/canais-destino', icon: TvIcon, badge: 3 },
    { title: 'Canais Fonte', url: '/painel/canais-fonte', icon: RadioTowerIcon, badge: 32 },
    { title: 'Vídeos', url: '/painel/videos', icon: ClapperboardIcon, badge: '2620' },
    { title: 'Processar Vídeo', url: '/painel/processar-video', icon: LinkIcon },
    { title: 'Transcrição Local', url: '/painel/transcricoes', icon: AudioLinesIcon },
    { title: 'Links Úteis', url: '/painel/links-uteis', icon: BookmarkIcon },
    { title: 'Documentação', url: '/painel/documentacao', icon: BookOpenIcon },
];

export function AppSidebar({
    user,
    ...props
}: React.ComponentProps<typeof Sidebar> & { user: { name: string; email: string } | null }) {
    const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
    const { props: pageProps } = usePage<{
        workers?: { downloader: string; transcriber: string; cutter: string };
    }>();

    const workers = pageProps.workers || {
        downloader: '35/61',
        transcriber: '1 ativo',
        cutter: 'ocioso',
    };

    return (
        <Sidebar collapsible="icon" {...props}>
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton size="lg" asChild>
                            <Link href="/painel">
                                <div
                                    className="flex aspect-square size-9 items-center justify-center rounded-xl text-white shadow-sm"
                                    style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)' }}
                                >
                                    <ClapperboardIcon className="size-4.5" />
                                </div>
                                <div className="grid flex-1 text-left text-sm leading-tight">
                                    <span className="truncate font-display font-bold text-foreground">Canal de Cortes</span>
                                    <span className="truncate text-xs text-muted-foreground">Pipeline de clipes</span>
                                </div>
                            </Link>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>
            <SidebarContent>
                <SidebarMenu className="px-2 gap-1">
                    {navItems.map((item) => (
                        <SidebarMenuItem key={item.url}>
                            <SidebarMenuButton
                                asChild
                                isActive={currentPath === item.url}
                                tooltip={item.title}
                                className="h-10 rounded-xl text-[13.5px] font-medium justify-between"
                            >
                                {item.external ? (
                                    <a href={item.url} className="flex items-center w-full">
                                        <item.icon className="size-4.5 mr-2" />
                                        <span className="flex-1">{item.title}</span>
                                        {item.badge && (
                                            <span className="font-mono text-[10.5px] px-1.5 py-0.5 rounded-md bg-muted text-muted-foreground">
                                                {item.badge}
                                            </span>
                                        )}
                                    </a>
                                ) : (
                                    <Link href={item.url} className="flex items-center w-full">
                                        <item.icon className="size-4.5 mr-2" />
                                        <span className="flex-1">{item.title}</span>
                                        {item.badge && (
                                            <span className="font-mono text-[10.5px] px-1.5 py-0.5 rounded-md bg-muted text-muted-foreground">
                                                {item.badge}
                                            </span>
                                        )}
                                    </Link>
                                )}
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                    ))}
                </SidebarMenu>
            </SidebarContent>
            <SidebarFooter className="p-3 flex flex-col gap-2">
                {/* Workers Status Box (Dinâmico) */}
                <div className="rounded-xl border border-border bg-card/60 p-3 flex flex-col gap-2 text-xs">
                    <div className="flex items-center justify-between text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                        <span>Workers</span>
                        <span className="flex items-center gap-1.5 text-emerald-500 normal-case tracking-normal">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>3 online
                        </span>
                    </div>
                    <div className="flex items-center gap-2 text-[12px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <span className="flex-1 text-foreground/80">downloader</span>
                        <span className="font-mono text-[10.5px] text-muted-foreground">{workers.downloader}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[12px]">
                        <span className={`w-1.5 h-1.5 rounded-full ${workers.transcriber !== 'ocioso' && workers.transcriber !== 'idle' ? 'bg-amber-500' : 'bg-emerald-500'}`}></span>
                        <span className="flex-1 text-foreground/80">transcriber</span>
                        <span className="font-mono text-[10.5px] text-muted-foreground">{workers.transcriber}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[12px]">
                        <span className={`w-1.5 h-1.5 rounded-full ${workers.cutter !== 'ocioso' && workers.cutter !== 'idle' ? 'bg-amber-500' : 'bg-emerald-500'}`}></span>
                        <span className="flex-1 text-foreground/80">cutter · uploader</span>
                        <span className="font-mono text-[10.5px] text-muted-foreground">{workers.cutter}</span>
                    </div>
                </div>
                <NavUser user={user} />
            </SidebarFooter>
            <SidebarRail />
        </Sidebar>
    );
}
