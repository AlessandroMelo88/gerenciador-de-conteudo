import { Head } from '@inertiajs/react';

import { BrandMark, useBrand } from '@/components/brand-logo';
import { LoginForm } from '@/components/login-form';
import { FilmIcon, ScissorsIcon, SparklesIcon } from 'lucide-react';

export default function LoginPage() {
    const brand = useBrand();

    return (
        <>
            <Head title="Login" />
            <div className="grid min-h-svh lg:grid-cols-2">
                <div className="flex flex-col gap-4 p-6 md:p-10">
                    <div className="flex justify-center gap-2 md:justify-start">
                        <div className="flex items-center gap-2 font-medium font-display">
                            <BrandMark className="size-6 rounded-md" iconClassName="size-4" />
                            {brand.name}
                        </div>
                    </div>
                    <div className="flex flex-1 items-center justify-center">
                        <div className="w-full max-w-xs">
                            <LoginForm />
                        </div>
                    </div>
                </div>
                <div className="relative hidden flex-col items-center justify-center gap-6 bg-muted lg:flex">
                    <BrandMark className="size-20 rounded-2xl" iconClassName="size-10" />
                    {brand.key === 'canaldecortes' ? (
                        <>
                            <div className="flex items-center gap-6 text-muted-foreground">
                                <FilmIcon className="size-6" />
                                <SparklesIcon className="size-6" />
                                <ScissorsIcon className="size-6" />
                            </div>
                            <p className="max-w-xs text-center text-sm text-muted-foreground">
                                Baixa → transcreve → IA seleciona momentos → corta → publica.
                            </p>
                        </>
                    ) : (
                        <p className="max-w-xs text-center text-sm text-muted-foreground">{brand.tagline}</p>
                    )}
                </div>
            </div>
        </>
    );
}
