import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ThemeToggle() {
    const [isDark, setIsDark] = useState(true);

    useEffect(() => {
        const saved = localStorage.getItem('theme');
        if (saved) {
            const dark = saved === 'dark';
            setIsDark(dark);
            document.documentElement.classList.toggle('dark', dark);
        } else {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            setIsDark(prefersDark);
            document.documentElement.classList.toggle('dark', prefersDark);
        }
    }, []);

    const toggle = () => {
        const next = !isDark;
        setIsDark(next);
        document.documentElement.classList.toggle('dark', next);
        localStorage.setItem('theme', next ? 'dark' : 'light');
    };

    return (
        <Button
            variant="outline"
            size="icon"
            onClick={toggle}
            className="h-9 w-9 rounded-xl border-border hover:bg-accent transition-colors"
            title="Alternar tema claro / escuro"
        >
            {isDark ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-zinc-600" />}
        </Button>
    );
}
