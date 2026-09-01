import type { ReactNode } from 'react';

/**
 * Header de seção configurável por rota: subtítulo + área de ações (1+ botões).
 * Cada página compõe o que precisa via props, igual um slot de layout — não
 * existe um "layout" compartilhado automático (Inertia não tem isso pronto
 * como o App Router do Next.js), então esse componente é a forma prática de
 * ter a mesma aparência/local em todas as páginas sem repetir o markup.
 */
export function PageHeader({ description, actions }: { description?: ReactNode; actions?: ReactNode }) {
    if (!description && !actions) return null;

    return (
        <div className="flex flex-wrap items-center justify-between gap-3">
            {description && <p className="text-sm text-muted-foreground">{description}</p>}
            {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
    );
}
