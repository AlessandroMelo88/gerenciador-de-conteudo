import { useForm } from '@inertiajs/react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';

export function LoginForm({ className, ...props }: React.ComponentProps<'form'>) {
    const { data, setData, post, processing, errors } = useForm({
        email: '',
        password: '',
        remember: false,
    });

    function submit(e: React.FormEvent) {
        e.preventDefault();
        post('/login');
    }

    return (
        <form className={cn('flex flex-col gap-6', className)} onSubmit={submit} {...props}>
            <FieldGroup>
                <div className="flex flex-col items-center gap-1 text-center">
                    <h1 className="text-2xl font-bold">Canal de Cortes</h1>
                    <p className="text-sm text-balance text-muted-foreground">Entre com seu e-mail e senha</p>
                </div>
                <Field>
                    <FieldLabel htmlFor="email">E-mail</FieldLabel>
                    <Input
                        id="email"
                        type="email"
                        autoFocus
                        required
                        className="bg-background"
                        value={data.email}
                        onChange={(e) => setData('email', e.target.value)}
                    />
                    {errors.email && <p className="text-sm text-destructive">{errors.email}</p>}
                </Field>
                <Field>
                    <FieldLabel htmlFor="password">Senha</FieldLabel>
                    <Input
                        id="password"
                        type="password"
                        required
                        className="bg-background"
                        value={data.password}
                        onChange={(e) => setData('password', e.target.value)}
                    />
                </Field>
                <Field>
                    <Button type="submit" disabled={processing}>
                        {processing ? 'Entrando…' : 'Entrar'}
                    </Button>
                </Field>
            </FieldGroup>
        </form>
    );
}
