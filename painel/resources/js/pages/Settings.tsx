import { useEffect } from 'react';
import { Head, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AppShell } from '@/layouts/app-shell';

type CookiesInfo = {
    exists: boolean;
    size: number;
    updated_at: string;
    lines: number;
} | null;

type PageProps = {
    auth: { user: { name: string; email: string } | null };
    flash: { success: string | null; error: string | null };
    settings?: {
        allow_local_download: boolean;
    };
    cookiesInfo?: CookiesInfo;
};

function SystemTab({ initialSettings, cookiesInfo }: { initialSettings?: { allow_local_download: boolean }; cookiesInfo?: CookiesInfo }) {
    const { data, setData, put, processing } = useForm({
        allow_local_download: initialSettings?.allow_local_download ?? false,
    });

    const cookiesForm = useForm<{
        cookies_content: string;
        cookies_file: File | null;
    }>({
        cookies_content: '',
        cookies_file: null,
    });

    function submit(e: React.FormEvent) {
        e.preventDefault();
        put('/painel/configuracoes/sistema');
    }

    function submitCookies(e: React.FormEvent) {
        e.preventDefault();
        cookiesForm.post('/painel/configuracoes/cookies', {
            onSuccess: () => {
                cookiesForm.reset();
            },
        });
    }

    return (
        <div className="grid max-w-2xl gap-6">
            <Card>
                <CardContent className="pt-6">
                    <form onSubmit={submit} className="grid gap-6">
                        <div className="flex items-center justify-between gap-4 rounded-lg border p-4">
                            <div className="space-y-1">
                                <FieldLabel className="text-base font-semibold">
                                    Permitir Processamento e Download Local
                                </FieldLabel>
                                <p className="text-sm text-muted-foreground">
                                    Quando ativado, permite que scripts executados localmente na sua máquina realizem testes de download e corte de vídeos.
                                </p>
                            </div>
                            <Switch
                                checked={data.allow_local_download}
                                onCheckedChange={(checked) => setData('allow_local_download', checked)}
                            />
                        </div>
                        <div>
                            <Button type="submit" disabled={processing}>
                                Salvar Configurações
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="pt-6">
                    <form onSubmit={submitCookies} className="grid gap-4">
                        <div className="space-y-1">
                            <h3 className="text-base font-semibold">Cookies do YouTube (yt-dlp)</h3>
                            <p className="text-sm text-muted-foreground">
                                O YouTube exige cookies de autenticação atualizados para permitir downloads no servidor em nuvem.
                            </p>
                        </div>

                        <div className="rounded-md bg-muted p-3 text-sm">
                            {cookiesInfo?.exists ? (
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2 font-medium text-emerald-600 dark:text-emerald-400">
                                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                                        Arquivo de cookies presente no servidor
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        Última atualização: {cookiesInfo.updated_at} ({Math.round(cookiesInfo.size / 1024)} KB, {cookiesInfo.lines} linhas)
                                    </p>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                                    <span className="h-2 w-2 rounded-full bg-amber-500" />
                                    Nenhum arquivo cookies.txt encontrado no servidor
                                </div>
                            )}
                        </div>

                        <Field>
                            <FieldLabel htmlFor="cookies_file">Carregar arquivo cookies.txt</FieldLabel>
                            <Input
                                id="cookies_file"
                                type="file"
                                accept=".txt"
                                onChange={(e) => {
                                    const file = e.target.files?.[0] || null;
                                    cookiesForm.setData('cookies_file', file);
                                }}
                            />
                        </Field>

                        <Field>
                            <FieldLabel htmlFor="cookies_content">Ou cole o texto dos cookies aqui</FieldLabel>
                            <textarea
                                id="cookies_content"
                                rows={4}
                                className="w-full rounded-md border bg-background p-2 text-xs font-mono"
                                placeholder="# Netscape HTTP Cookie File..."
                                value={cookiesForm.data.cookies_content}
                                onChange={(e) => cookiesForm.setData('cookies_content', e.target.value)}
                            />
                        </Field>

                        <div>
                            <Button type="submit" disabled={cookiesForm.processing}>
                                Atualizar Cookies
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}

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
    const { auth, flash, settings, cookiesInfo } = props;

    useEffect(() => {
        if (flash?.success) toast.success(flash.success);
        if (flash?.error) toast.error(flash.error);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [flash?.success, flash?.error]);

    return (
        <>
            <Head title="Configurações" />
            <AppShell title="Configurações" user={auth.user}>
                <Tabs defaultValue="sistema">
                    <TabsList>
                        <TabsTrigger value="sistema">Sistema</TabsTrigger>
                        <TabsTrigger value="senha">Resetar senha</TabsTrigger>
                        <TabsTrigger value="perfil">Perfil</TabsTrigger>
                        <TabsTrigger value="redes">Redes</TabsTrigger>
                    </TabsList>
                    <TabsContent value="sistema" className="mt-4">
                        <SystemTab initialSettings={settings} cookiesInfo={cookiesInfo} />
                    </TabsContent>
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
