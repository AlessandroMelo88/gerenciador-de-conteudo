import type { ReactNode } from 'react';
import { Link } from '@inertiajs/react';
import { Plus } from 'lucide-react';

import { ThemeToggle } from '@/components/theme-toggle';
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
        <header className="sticky top-0 z-30 flex min-h-[74px] shrink-0 flex-col justify-center border-b bg-background/85 px-4 py-3 backdrop-blur-xl transition-[width,height] ease-linear lg:px-8">
            <div className="flex w-full items-center gap-3">
                <SidebarTrigger className="-ml-1 md:hidden" />
                <div className="min-w-0 flex-1">
                    <h1 className="truncate font-display text-lg font-bold tracking-tight text-foreground">{title}</h1>
                    {description && <p className="truncate text-xs text-muted-foreground">{description}</p>}
                </div>
                
                {/* Quota badges rápidos no topo */}
                <div className="hidden lg:flex items-center gap-2 pr-3 border-r border-border">
                    <span className="font-mono text-[11px] px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-medium">
                        ⚽ Futebol: 0/5
                    </span>
                    <span className="font-mono text-[11px] px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 font-medium">
                        🏛️ Política: 0/5
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <ThemeToggle />
                    {actions ? (
                        actions
                    ) : (
                        <Link
                            href="/painel/canais-destino"
                            className="inline-flex h-9 items-center gap-2 rounded-xl px-3.5 text-xs font-semibold text-white shadow-sm transition hover:brightness-105"
                            style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)' }}
                        >
                            <Plus className="h-4 w-4" />
                            <span className="hidden sm:inline">Novo canal</span>
                        </Link>
                    )}
                </div>
            </div>
        </header>
    );
}
