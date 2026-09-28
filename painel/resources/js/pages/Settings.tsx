import { useEffect, useRef } from 'react';
import { Head, router, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';

import { ConfirmButton } from '@/components/confirm-button';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Field, FieldDescription, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { PasswordInput } from '@/components/ui/password-input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AppShell } from '@/layouts/app-shell';

type MediaKind = 'intro' | 'outro' | 'music';

type MediaAsset = {
    id: number;
    kind: MediaKind;
    name: string;
    format: 'curto' | 'longo' | null;
    durationSeconds: number | null;
    musicVolume: number | null;
    priority: number;
    active: boolean;
    fileName: string;
    destinationChannelId: number | null;
    destinationChannelName: string | null;
};

type DestinationChannel = { id: number; name: string };

type CookiesInfo = {
    exists: boolean;
    size: number;
    updated_at: string;
    lines: number;
} | null;

type PageProps = {
    auth: { user: { name: string; email: string } | null };
    flash: { success: string | null; error: string | null };
    mediaAssets?: MediaAsset[];
    destinationChannels?: DestinationChannel[];
    mediaConfiguration?: {
        introCount: number;
        outroCount: number;
        musicCount: number;
        ready: boolean;
    };
    settings?: {
        allow_local_download: boolean;
    };
    cookiesInfo?: CookiesInfo;
};

const KIND_LABEL: Record<MediaKind, string> = {
    intro: 'Intro',
    outro: 'Encerramento',
    music: 'Música de fundo',
};

function FormError({ message }: { message?: string }) {
    return message ? <p className="text-sm text-destructive">{message}</p> : null;
}

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
                        <PasswordInput
                            id="current_password"
                            value={data.current_password}
                            onChange={(e) => setData('current_password', e.target.value)}
                        />
                        <FormError message={errors.current_password} />
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="password">Nova senha</FieldLabel>
                        <PasswordInput
                            id="password"
                            value={data.password}
                            onChange={(e) => setData('password', e.target.value)}
                        />
                        <FormError message={errors.password} />
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="password_confirmation">Confirmar nova senha</FieldLabel>
                        <PasswordInput
                            id="password_confirmation"
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

function MediaStatus({ configuration }: { configuration: PageProps['mediaConfiguration'] }) {
    const entries = [
        ['Intro', configuration.introCount],
        ['Encerramento', configuration.outroCount],
        ['Música', configuration.musicCount],
    ] as const;

    return (
        <Card className={configuration.ready ? 'border-emerald-500/30' : 'border-amber-500/40'}>
            <CardHeader>
                <CardTitle>{configuration.ready ? 'Biblioteca pronta' : 'Configure a identidade dos vídeos'}</CardTitle>
                <CardDescription>
                    O pipeline escolhe automaticamente a identidade dos vídeos longos por canal e formato. Shorts são
                    verticais e não recebem intro nem encerramento.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid gap-3 sm:grid-cols-3">
                    {entries.map(([label, count]) => (
                        <div key={label} className="rounded-lg border bg-muted/30 p-3">
                            <div className="text-xs text-muted-foreground">{label}</div>
                            <div className="mt-1 flex items-center gap-2 text-lg font-semibold">
                                {count}
                                <Badge variant={count > 0 ? 'default' : 'secondary'}>
                                    {count > 0 ? 'configurado' : 'pendente'}
                                </Badge>
                            </div>
                        </div>
                    ))}
                </div>
                {!configuration.ready && (
                    <p className="mt-4 text-sm text-muted-foreground">
                        Adicione pelo menos uma intro, um encerramento e uma música antes de ligar o processamento
                        automático de vídeos longos.
                    </p>
                )}
            </CardContent>
        </Card>
    );
}

function MediaUploadForm({ destinationChannels }: { destinationChannels: DestinationChannel[] }) {
    const inputRef = useRef<HTMLInputElement>(null);
    const { data, setData, post, processing, errors, reset, transform } = useForm<{
        kind: MediaKind;
        name: string;
        file: File | null;
        destination_channel_id: string;
        format: string;
        duration_seconds: string;
        music_volume: string;
        priority: string;
        active: boolean;
    }>({
        kind: 'intro',
        name: '',
        file: null,
        destination_channel_id: 'global',
        format: 'all',
        duration_seconds: '3',
        music_volume: '0.12',
        priority: '0',
        active: true,
    });

    function submit(e: React.FormEvent) {
        e.preventDefault();
        transform((form) => ({
            ...form,
            destination_channel_id:
                form.destination_channel_id === 'global' ? null : Number(form.destination_channel_id),
            format: form.format === 'all' ? null : form.format,
            duration_seconds: form.kind === 'music' ? null : Number(form.duration_seconds || 3),
            music_volume: form.kind === 'music' ? Number(form.music_volume || 0.12) : null,
            priority: Number(form.priority || 0),
        }));
        post('/painel/configuracoes/midia', {
            forceFormData: true,
            preserveScroll: true,
            onSuccess: () => {
                reset();
                if (inputRef.current) inputRef.current.value = '';
            },
        });
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Adicionar mídia</CardTitle>
                <CardDescription>
                    Envie um vídeo ou imagem para intro/encerramento, ou um arquivo de áudio para trilha. A identidade é
                    aplicada somente aos vídeos longos; Shorts permanecem verticais sem intro nem encerramento. O
                    arquivo fica no volume compartilhado com o worker.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={submit} className="grid gap-4 lg:grid-cols-2">
                    <Field>
                        <FieldLabel>Tipo</FieldLabel>
                        <Select value={data.kind} onValueChange={(value) => setData('kind', value as MediaKind)}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="intro">Intro</SelectItem>
                                <SelectItem value="outro">Encerramento</SelectItem>
                                <SelectItem value="music">Música de fundo</SelectItem>
                            </SelectContent>
                        </Select>
                        <FormError message={errors.kind} />
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="media-name">Nome</FieldLabel>
                        <Input
                            id="media-name"
                            value={data.name}
                            placeholder="Ex.: Intro principal"
                            onChange={(e) => setData('name', e.target.value)}
                        />
                        <FormError message={errors.name} />
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="media-file">Arquivo</FieldLabel>
                        <Input
                            ref={inputRef}
                            id="media-file"
                            type="file"
                            accept={data.kind === 'music' ? 'audio/*' : 'video/*,image/*'}
                            onChange={(e) => setData('file', e.target.files?.[0] ?? null)}
                        />
                        <FieldDescription>MP4/MOV/WEBM, JPG/PNG ou MP3/WAV/M4A/OGG. Limite: 100 MB.</FieldDescription>
                        <FormError message={errors.file} />
                    </Field>
                    <Field>
                        <FieldLabel>Canal de destino</FieldLabel>
                        <Select
                            value={data.destination_channel_id}
                            onValueChange={(value) => setData('destination_channel_id', value)}
                        >
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="global">Global (fallback)</SelectItem>
                                {destinationChannels.map((channel) => (
                                    <SelectItem key={channel.id} value={String(channel.id)}>
                                        {channel.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <FormError message={errors.destination_channel_id} />
                    </Field>
                    <Field>
                        <FieldLabel>Formato</FieldLabel>
                        <Select value={data.format} onValueChange={(value) => setData('format', value)}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Todos os formatos</SelectItem>
                                <SelectItem value="curto">Curto / Shorts</SelectItem>
                                <SelectItem value="longo">Longo / horizontal</SelectItem>
                            </SelectContent>
                        </Select>
                        <FormError message={errors.format} />
                    </Field>
                    {data.kind !== 'music' ? (
                        <Field>
                            <FieldLabel htmlFor="duration-seconds">Duração para imagem (segundos)</FieldLabel>
                            <Input
                                id="duration-seconds"
                                type="number"
                                min="1"
                                max="60"
                                value={data.duration_seconds}
                                onChange={(e) => setData('duration_seconds', e.target.value)}
                            />
                            <FieldDescription>
                                Para vídeos, o worker respeita a duração do próprio arquivo.
                            </FieldDescription>
                            <FormError message={errors.duration_seconds} />
                        </Field>
                    ) : (
                        <Field>
                            <FieldLabel htmlFor="music-volume">Volume da música</FieldLabel>
                            <Input
                                id="music-volume"
                                type="number"
                                min="0.01"
                                max="1"
                                step="0.01"
                                value={data.music_volume}
                                onChange={(e) => setData('music_volume', e.target.value)}
                            />
                            <FieldDescription>
                                O valor recebe +20% no render (0.12 resulta em 14,4%); a trilha entra nos 15 s finais.
                            </FieldDescription>
                            <FormError message={errors.music_volume} />
                        </Field>
                    )}
                    <Field>
                        <FieldLabel htmlFor="media-priority">Prioridade</FieldLabel>
                        <Input
                            id="media-priority"
                            type="number"
                            min="0"
                            max="100"
                            value={data.priority}
                            onChange={(e) => setData('priority', e.target.value)}
                        />
                        <FieldDescription>Em empate de escopo, o maior valor vence.</FieldDescription>
                        <FormError message={errors.priority} />
                    </Field>
                    <div className="flex items-end lg:col-span-2">
                        <Button type="submit" disabled={processing || !data.file}>
                            {processing ? 'Enviando…' : 'Adicionar à biblioteca'}
                        </Button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
}

function MediaLibrary({ assets }: { assets: MediaAsset[] }) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Biblioteca configurada</CardTitle>
                <CardDescription>
                    Ative mais de uma mídia no mesmo escopo para o worker alternar entre elas automaticamente nos vídeos
                    longos.
                </CardDescription>
            </CardHeader>
            <CardContent>
                {assets.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Nenhuma mídia cadastrada ainda.</p>
                ) : (
                    <div className="overflow-x-auto rounded-lg border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Tipo</TableHead>
                                    <TableHead>Nome</TableHead>
                                    <TableHead>Escopo</TableHead>
                                    <TableHead>Prioridade</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Ações</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {assets.map((asset) => (
                                    <TableRow key={asset.id}>
                                        <TableCell>{KIND_LABEL[asset.kind]}</TableCell>
                                        <TableCell>
                                            <div className="font-medium">{asset.name}</div>
                                            <div className="text-xs text-muted-foreground">{asset.fileName}</div>
                                        </TableCell>
                                        <TableCell>
                                            <div>{asset.destinationChannelName ?? 'Global'}</div>
                                            <div className="text-xs text-muted-foreground">
                                                {asset.format === 'curto'
                                                    ? 'Shorts'
                                                    : asset.format === 'longo'
                                                      ? 'Longo'
                                                      : 'Todos'}
                                            </div>
                                        </TableCell>
                                        <TableCell>{asset.priority}</TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Switch
                                                    checked={asset.active}
                                                    aria-label={`Ativar ${asset.name}`}
                                                    onCheckedChange={(active) =>
                                                        router.patch(
                                                            `/painel/configuracoes/midia/${asset.id}`,
                                                            { active },
                                                            { preserveScroll: true },
                                                        )
                                                    }
                                                />
                                                <Badge variant={asset.active ? 'default' : 'secondary'}>
                                                    {asset.active ? 'Ativa' : 'Pausada'}
                                                </Badge>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <ConfirmButton
                                                variant="destructive"
                                                size="sm"
                                                description={`Remover a mídia "${asset.name}"? O arquivo também será apagado.`}
                                                onConfirm={() =>
                                                    router.delete(`/painel/configuracoes/midia/${asset.id}`)
                                                }
                                            >
                                                Remover
                                            </ConfirmButton>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

function MediaTab({
    assets,
    destinationChannels,
    configuration,
}: {
    assets: MediaAsset[];
    destinationChannels: DestinationChannel[];
    configuration: PageProps['mediaConfiguration'];
}) {
    return (
        <div className="grid gap-4">
            <MediaStatus configuration={configuration} />
            <MediaUploadForm destinationChannels={destinationChannels} />
            <MediaLibrary assets={assets} />
        </div>
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
    const { auth, flash, mediaAssets = [], destinationChannels = [], mediaConfiguration, settings, cookiesInfo } = props;

    useEffect(() => {
        if (flash?.success) toast.success(flash.success);
        if (flash?.error) toast.error(flash.error);
    }, [flash?.success, flash?.error]);

    return (
        <>
            <Head title="Configurações" />
            <AppShell
                title="Configurações"
                user={auth?.user ?? null}
                description="Identidade visual, mídia automática, cookies e configurações do sistema."
            >
                <Tabs defaultValue="sistema">
                    <TabsList>
                        <TabsTrigger value="sistema">Sistema</TabsTrigger>
                        <TabsTrigger value="midia">Mídia do canal</TabsTrigger>
                        <TabsTrigger value="senha">Resetar senha</TabsTrigger>
                        <TabsTrigger value="perfil">Perfil</TabsTrigger>
                        <TabsTrigger value="redes">Redes</TabsTrigger>
                    </TabsList>
                    <TabsContent value="sistema" className="mt-4">
                        <SystemTab initialSettings={settings} cookiesInfo={cookiesInfo} />
                    </TabsContent>
                    <TabsContent value="midia" className="mt-4">
                        <MediaTab
                            assets={mediaAssets}
                            destinationChannels={destinationChannels}
                            configuration={mediaConfiguration ?? { introCount: 0, outroCount: 0, musicCount: 0, ready: false }}
                        />
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
