import { useEffect } from 'react';
import { Head, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AppShell } from '@/layouts/app-shell';

type PageProps = {
    auth: { user: { name: string; email: string } | null };
    flash: { success: string | null; error: string | null };
};

function PasswordTab() {
    const { data, setData, put, processing, errors, reset } = useForm({
        current_password: '',
        password: '',
        password_confirmation: '',
    });

    function submit(e: React.FormEvent) {
        e.preventDefault();
        put('/painel/configuracoes/senha', { onSuccess: () => reset() });
    }

    return (
        <Card className="max-w-md">
            <CardContent className="pt-6">
                <form onSubmit={submit} className="grid gap-4">
                    <Field>
                        <FieldLabel htmlFor="current_password">Senha atual</FieldLabel>
                        <Input
                            id="current_password"
                            type="password"
                            value={data.current_password}
                            onChange={(e) => setData('current_password', e.target.value)}
                        />
                        {errors.current_password && (
                            <p className="text-sm text-destructive">{errors.current_password}</p>
                        )}
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="password">Nova senha</FieldLabel>
                        <Input
                            id="password"
                            type="password"
                            value={data.password}
                            onChange={(e) => setData('password', e.target.value)}
                        />
                        {errors.password && <p className="text-sm text-destructive">{errors.password}</p>}
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="password_confirmation">Confirmar nova senha</FieldLabel>
                        <Input
                            id="password_confirmation"
                            type="password"
                            value={data.password_confirmation}
                            onChange={(e) => setData('password_confirmation', e.target.value)}
                        />
                    </Field>
                    <div>
                        <Button type="submit" disabled={processing}>
                            Atualizar senha
                        </Button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
}

function PlaceholderTab({ label }: { label: string }) {
    return (
        <Card className="max-w-md">
            <CardContent className="pt-6 text-sm text-muted-foreground">{label} — em construção.</CardContent>
        </Card>
    );
}

export default function Settings() {
    const { props } = usePage<PageProps>();
    const { auth, flash } = props;

    useEffect(() => {
        if (flash?.success) toast.success(flash.success);
        if (flash?.error) toast.error(flash.error);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [flash?.success, flash?.error]);

    return (
        <>
            <Head title="Configurações" />
            <AppShell title="Configurações" user={auth.user}>
                <Tabs defaultValue="senha">
                    <TabsList>
                        <TabsTrigger value="senha">Resetar senha</TabsTrigger>
                        <TabsTrigger value="perfil">Perfil</TabsTrigger>
                        <TabsTrigger value="redes">Redes</TabsTrigger>
                    </TabsList>
                    <TabsContent value="senha" className="mt-4">
                        <PasswordTab />
                    </TabsContent>
                    <TabsContent value="perfil" className="mt-4">
                        <PlaceholderTab label="Perfil" />
                    </TabsContent>
                    <TabsContent value="redes" className="mt-4">
                        <PlaceholderTab label="Redes" />
                    </TabsContent>
                </Tabs>
            </AppShell>
        </>
    );
}
