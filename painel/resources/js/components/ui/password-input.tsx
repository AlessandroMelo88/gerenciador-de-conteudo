import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';

/**
 * Campo de senha com botão de olho para mostrar/esconder.
 *
 * O botão fica fora da ordem de tabulação (tabIndex -1) para não atrapalhar
 * quem preenche o formulário pelo teclado, e o estado volta a "escondido"
 * sempre que o componente é remontado.
 */
export function PasswordInput({ className, ...props }: React.ComponentProps<typeof Input>) {
    const [visible, setVisible] = useState(false);

    return (
        <div className="relative">
            <Input
                {...props}
                type={visible ? 'text' : 'password'}
                className={cn('pr-10', className)}
            />
            <button
                type="button"
                tabIndex={-1}
                onClick={() => setVisible((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
                aria-label={visible ? 'Esconder senha' : 'Ver senha'}
            >
                {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
        </div>
    );
}
