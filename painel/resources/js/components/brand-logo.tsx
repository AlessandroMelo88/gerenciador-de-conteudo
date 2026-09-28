import { usePage } from '@inertiajs/react';
import { ClapperboardIcon, UmbrellaIcon } from 'lucide-react';

import { cn } from '@/lib/utils';

export type Brand = {
    key: string;
    name: string;
    tagline: string;
    icon: string;
    logo: string | null;
};

const FALLBACK: Brand = { key: 'canaldecortes', name: 'Canal de Cortes', tagline: 'Pipeline de clipes', icon: 'clapperboard', logo: null };

const ICONS = { clapperboard: ClapperboardIcon, umbrella: UmbrellaIcon } as const;

/** Marca resolvida no servidor (host/APP_BRAND), compartilhada pelo HandleInertiaRequests. */
export function useBrand(): Brand {
    const { props } = usePage<{ brand?: Brand }>();
    return props.brand ?? FALLBACK;
}

/**
 * Símbolo da marca: logo configurado ou ícone sobre o gradiente do tema
 * (--brand-logo-from/--brand-logo-to em app.css).
 */
export function BrandMark({ className, iconClassName }: { className?: string; iconClassName?: string }) {
    const brand = useBrand();
    const Icon = ICONS[brand.icon as keyof typeof ICONS] ?? ClapperboardIcon;

    if (brand.logo) {
        return <img src={brand.logo} alt={brand.name} className={cn('aspect-square object-contain', className)} />;
    }

    return (
        <div
            className={cn('flex aspect-square items-center justify-center text-white shadow-sm', className)}
            style={{ background: 'linear-gradient(160deg, var(--brand-logo-from), var(--brand-logo-to))' }}
        >
            <Icon className={iconClassName} />
        </div>
    );
}
