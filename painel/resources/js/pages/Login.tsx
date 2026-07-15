import { Head } from '@inertiajs/react';

import { LoginForm } from '@/components/login-form';
import { ClapperboardIcon, FilmIcon, ScissorsIcon, SparklesIcon } from 'lucide-react';

export default function LoginPage() {
    return (
        <>
            <Head title="Login" />
            <div className="grid min-h-svh lg:grid-cols-2">
                <div className="flex flex-col gap-4 p-6 md:p-10">
                    <div className="flex justify-center gap-2 md:justify-start">
                        <div className="flex items-center gap-2 font-medium">
                            <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
                                <ClapperboardIcon className="size-4" />
                            </div>
                            Canal de Cortes
                        </div>
                    </div>
                    <div className="flex flex-1 items-center justify-center">
                        <div className="w-full max-w-xs">
                            <LoginForm />
                        </div>
                    </div>
                </div>
                <div className="relative hidden flex-col items-center justify-center gap-6 bg-muted lg:flex">
                    <div className="flex size-20 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                        <ClapperboardIcon className="size-10" />
                    </div>
                    <div className="flex items-center gap-6 text-muted-foreground">
                        <FilmIcon className="size-6" />
                        <SparklesIcon className="size-6" />
                        <ScissorsIcon className="size-6" />
                    </div>
                    <p className="max-w-xs text-center text-sm text-muted-foreground">
                        Baixa → transcreve → IA seleciona momentos → corta → publica.
                    </p>
                </div>
            </div>
        </>
    );
}
