import * as React from 'react';
import { Link, usePage } from '@inertiajs/react';

import { NavUser } from '@/components/nav-user';
import { WorkspaceSwitcher, type Workspace } from '@/components/workspace-switcher';
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
    BadgeDollarSignIcon,
    ClapperboardIcon,
    LayoutDashboardIcon,
    LinkIcon,
    RadioTowerIcon,
    TvIcon,
    BookOpenIcon,
    SparklesIcon,
    BotIcon,
    BookmarkIcon,
    ChartColumnIcon,
    HandCoinsIcon,
} from 'lucide-react';

type NavItem = {
    title: string;
    url: string;
    icon: React.ElementType;
    /** Rotas fora do SPA Inertia precisam de <a> normal, não <Link>. */
    external?: boolean;
};

// Dourado escuro: #b8860b no tema escuro (4,7:1 sobre o bg-muted) e um tom mais
// fechado no claro, onde o #b8860b cairia para 3,0:1 e ficaria ilegível.
const BADGE_CLASSES =
    'font-mono text-[10.5px] font-semibold px-1.5 py-0.5 rounded-md bg-muted text-[#8a6508] dark:text-[#b8860b]';

type SidebarItem = NavItem & { badge?: string | number };

const clipItems: SidebarItem[] = [
    { title: 'Dashboard', url: '/painel', icon: LayoutDashboardIcon, badge: 9 },
    { title: 'Assistente IA', url: '/painel/assistente', icon: BotIcon, badge: 'LLaMA' },
    { title: 'Canais Destino', url: '/painel/canais-destino', icon: TvIcon, badge: 3 },
    { title: 'Canais Fonte', url: '/painel/canais-fonte', icon: RadioTowerIcon, badge: 32 },
    { title: 'Vídeos', url: '/painel/videos', icon: ClapperboardIcon, badge: '2620' },
    { title: 'Processar Vídeo', url: '/painel/processar-video', icon: LinkIcon },
    { title: 'Transcrições', url: '/painel/transcricoes', icon: AudioLinesIcon },
    { title: 'Links Úteis', url: '/painel/links-uteis', icon: BookmarkIcon },
    { title: 'Documentação', url: '/painel/documentacao', icon: BookOpenIcon },
];

const affiliateItems: SidebarItem[] = [
    { title: 'Ofertas', url: '/painel/ofertas', icon: BadgeDollarSignIcon },
    { title: 'Performance', url: '/painel/ofertas/performance', icon: ChartColumnIcon },
];

const WORKSPACES: (Workspace & { items: SidebarItem[]; matches: (path: string) => boolean })[] = [
    { key: 'clipes', name: 'Canal de Cortes', tagline: 'Pipeline de clipes', home: '/painel', items: clipItems, matches: () => true },
    {
        key: 'afiliados',
        name: 'Afiliados',
        tagline: 'Pipeline de afiliados',
        home: '/painel/ofertas',
        icon: HandCoinsIcon,
        gradient: 'linear-gradient(160deg, #34D399, #059669)',
        items: affiliateItems,
        matches: (path) => path.startsWith('/painel/ofertas'),
    },
];

const WORKSPACE_KEY = 'painel.workspace';

/** Área da página atual; páginas comuns (Configurações) mantêm a última área usada. */
function resolveWorkspace(path: string) {
    const clipes = WORKSPACES[0];
    const specific = WORKSPACES.find((w) => w !== clipes && w.matches(path));
    const isShared = path.startsWith('/painel/configuracoes');

    if (isShared) {
        try {
            return WORKSPACES.find((w) => w.key === window.localStorage.getItem(WORKSPACE_KEY)) ?? clipes;
        } catch {
            return clipes;
        }
    }

    const active = specific ?? clipes;
    try {
        window.localStorage.setItem(WORKSPACE_KEY, active.key);
    } catch {
        // storage bloqueado: só perde a lembrança da área nas páginas comuns
    }
    return active;
}

export function AppSidebar({
    user,
    ...props
}: React.ComponentProps<typeof Sidebar> & { user: { name: string; email: string } | null }) {
    const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
    const workspace = resolveWorkspace(currentPath);
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
                <WorkspaceSwitcher workspaces={WORKSPACES} active={workspace} />
            </SidebarHeader>
            <SidebarContent>
                <SidebarMenu className="px-2 gap-1">
                    {workspace.items.map((item) => (
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
                                            <span className={BADGE_CLASSES}>
                                                {item.badge}
                                            </span>
                                        )}
                                    </a>
                                ) : (
                                    <Link href={item.url} className="flex items-center w-full">
                                        <item.icon className="size-4.5 mr-2" />
                                        <span className="flex-1">{item.title}</span>
                                        {item.badge && (
                                            <span className={BADGE_CLASSES}>
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
                {/* Workers Status Box (Dinâmico) — só na área de clipes */}
                {workspace.key === 'clipes' && (
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
                )}
                <NavUser user={user} />
            </SidebarFooter>
            <SidebarRail />
        </Sidebar>
    );
}
