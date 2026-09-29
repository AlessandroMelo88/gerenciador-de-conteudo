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
        <header className="sticky top-0 z-30 flex min-h-[64px] shrink-0 flex-col justify-center border-b bg-background/85 px-3 py-2.5 backdrop-blur-xl transition-[width,height] ease-linear sm:px-4 sm:py-3 lg:px-6">
            <div className="flex w-full items-center gap-2.5 sm:gap-3">
                <SidebarTrigger className="-ml-1 shrink-0 text-muted-foreground hover:text-foreground" />
                <div className="min-w-0 flex-1">
                    <h1 className="truncate font-display text-base font-bold tracking-tight text-foreground sm:text-lg">
                        {title}
                    </h1>
                    {description && (
                        <p className="hidden truncate text-xs text-muted-foreground sm:block">{description}</p>
                    )}
                </div>

                {/* Quota badges rápidos no topo */}
                <div className="hidden shrink-0 items-center gap-2 border-r border-border pr-3 xl:flex">
                    <span className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 font-mono text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                        ⚽ Futebol: 0/5
                    </span>
                    <span className="rounded-lg border border-purple-500/20 bg-purple-500/10 px-2.5 py-1 font-mono text-[11px] font-medium text-purple-600 dark:text-purple-400">
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
