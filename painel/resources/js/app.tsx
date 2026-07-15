import '../css/app.css';

import { createInertiaApp } from '@inertiajs/react';
import type { ResolvedComponent } from '@inertiajs/react';
import { createRoot } from 'react-dom/client';
import { resolvePageComponent } from 'laravel-vite-plugin/inertia-helpers';
import { TooltipProvider } from '@/components/ui/tooltip';

createInertiaApp({
    resolve: (name) =>
        // resolvePageComponent<T> tipa `pages` como Record<string, Promise<T> | (() => Promise<T>)>,
        // mas o glob real produz módulos `{ default: Component }` — incompatibilidade conhecida
        // entre @inertiajs/react e laravel-vite-plugin/inertia-helpers, sem impacto em runtime.
        resolvePageComponent(
            `./pages/${name}.tsx`,
            import.meta.glob('./pages/**/*.tsx'),
        ) as Promise<ResolvedComponent>,
    setup({ el, App, props }) {
        if (!el) return;
        createRoot(el).render(
            <TooltipProvider>
                <App {...props} />
            </TooltipProvider>,
        );
    },
});
