import { useState } from 'react';
import { Head, router, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';

import { AppSidebar } from '@/components/app-sidebar';
import { SiteHeader } from '@/components/site-header';
import { PageHeader } from '@/components/page-header';
import { ConfirmButton } from '@/components/confirm-button';
import { NicheCombobox, type Niche } from '@/components/niche-combobox';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { Switch } from '@/components/ui/switch';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { Toaster } from '@/components/ui/sonner';

type DestinationChannel = {
    id: number;
    slug: string;
    name: string;
    niche: string;
    youtubeChannelId: string;
    creditTemplate: string | null;
    active: boolean;
    oauthStatus: 'authorized' | 'expired' | 'missing';
    hasWatermark: boolean;
};

type PageProps = {
    channels: DestinationChannel[];
    niches: Niche[];
    auth: { user: { name: string; email: string } | null };
    flash: { success: string | null; error: string | null };
};

const OAUTH_LABEL: Record<string, string> = {
    authorized: 'Autorizado',
    expired: 'Expirado',
    missing: 'Sem autorização',
};

function ChannelDialog({
    channel,
    niches,
    trigger,
}: {
    channel?: DestinationChannel;
    niches: Niche[];
    trigger: React.ReactNode;
}) {
    const [open, setOpen] = useState(false);
    const isEdit = !!channel;
    const { data, setData, post, put, processing, errors, reset } = useForm({
        slug: channel?.slug ?? '',
        name: channel?.name ?? '',
        niche: channel?.niche ?? '',
        youtube_channel_id: channel?.youtubeChannelId ?? '',
        credit_template: channel?.creditTemplate ?? 'Créditos: @{channel_handle}',
        active: channel?.active ?? true,
    });
    const [watermark, setWatermark] = useState<File | null>(null);

    function submit(e: React.FormEvent) {
        e.preventDefault();
        const onSuccess = () => {
            setOpen(false);
            reset();
            if (watermark && channel) {
                const fd = new FormData();
                fd.append('watermark', watermark);
                router.post(`/painel/canais-destino/${channel.id}/watermark`, fd);
            }
        };
        if (isEdit) {
            put(`/painel/canais-destino/${channel.id}`, { onSuccess });
        } else {
            post('/painel/canais-destino', { onSuccess });
        }
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>{trigger}</DialogTrigger>
            <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle>{isEdit ? `Editar ${channel!.name}` : 'Adicionar canal-destino'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={submit} className="grid gap-4">
                    <Field>
                        <FieldLabel htmlFor="slug">Slug</FieldLabel>
                        <Input id="slug" value={data.slug} onChange={(e) => setData('slug', e.target.value)} />
                        <p className="text-xs text-muted-foreground">Identificador único (ex: futebol-em-cortes)</p>
                        {errors.slug && <p className="text-sm text-destructive">{errors.slug}</p>}
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="name">Nome</FieldLabel>
                        <Input id="name" value={data.name} onChange={(e) => setData('name', e.target.value)} />
                        {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
                    </Field>
                    <Field>
                        <FieldLabel>Nicho</FieldLabel>
                        <NicheCombobox niches={niches} value={data.niche} onChange={(v) => setData('niche', v)} />
                        {errors.niche && <p className="text-sm text-destructive">{errors.niche}</p>}
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="ytid">YouTube Channel ID (UC...)</FieldLabel>
                        <Input
                            id="ytid"
                            value={data.youtube_channel_id}
                            onChange={(e) => setData('youtube_channel_id', e.target.value)}
                        />
                        <p className="text-xs text-muted-foreground">
                            O ID do canal no YouTube (começa com &quot;UC&quot;). Se o canal ainda não existe, crie-o
                            primeiro em studio.youtube.com — o painel não cria canais novos no YouTube, só publica
                            neles.
                        </p>
                        {errors.youtube_channel_id && (
                            <p className="text-sm text-destructive">{errors.youtube_channel_id}</p>
                        )}
                    </Field>
                    <Field>
                        <FieldLabel htmlFor="credit">Template de créditos</FieldLabel>
                        <Textarea
                            id="credit"
                            value={data.credit_template ?? ''}
                            onChange={(e) => setData('credit_template', e.target.value)}
                        />
                        <p className="text-xs text-muted-foreground">Placeholder disponível: {'{channel_handle}'}</p>
                    </Field>
                    <Field className="flex flex-row items-center justify-between">
                        <FieldLabel htmlFor="active">Ativo</FieldLabel>
                        <Switch id="active" checked={data.active} onCheckedChange={(v) => setData('active', v)} />
                    </Field>
                    {isEdit && (
                        <Field>
                            <FieldLabel htmlFor="watermark">Marca d&apos;água (overlay nos vídeos)</FieldLabel>
                            <Input
                                id="watermark"
                                type="file"
                                accept="image/png"
                                onChange={(e) => setWatermark(e.target.files?.[0] ?? null)}
                            />
                            <p className="text-xs text-muted-foreground">
                                PNG com fundo transparente, aplicado automaticamente no canto superior direito de todo
                                vídeo cortado deste canal. Isso NÃO é o ícone/capa do canal no YouTube — a API do
                                YouTube não permite trocar ícone/capa por código, isso só dá pra fazer manualmente em
                                studio.youtube.com. {channel?.hasWatermark && '(já tem uma marca d\'água salva)'}
                            </p>
                        </Field>
                    )}
                    {isEdit && (
                        <Field>
                            <FieldLabel>Autorização OAuth</FieldLabel>
                            <p className="text-xs text-muted-foreground">
                                Não dá pra autorizar com 1 clique pelo painel: o YouTube exige que <em>você mesmo</em>{' '}
                                faça login na sua conta Google e aprove o acesso — isso roda por um comando
                                interativo no terminal, uma vez por canal.
                            </p>
                            <ol className="list-decimal pl-5 text-xs text-muted-foreground">
                                <li>Abra um terminal no servidor e rode o comando abaixo</li>
                                <li>Abra a URL impressa no navegador, faça login e autorize</li>
                                <li>Cole de volta no terminal a URL completa para onde o navegador tentou redirecionar</li>
                            </ol>
                            <CopyCommand slug={channel!.slug} />
                        </Field>
                    )}
                    <DialogFooter>
                        <Button type="submit" disabled={processing}>
                            {isEdit ? 'Salvar' : 'Adicionar'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

function CopyCommand({ slug }: { slug: string }) {
    const [copied, setCopied] = useState(false);
    const command = `docker exec -it clip-processor python -m src.youtube_oauth --channel ${slug}`;

    return (
        <div className="flex items-center gap-2">
            <pre className="flex-1 overflow-x-auto rounded bg-muted px-3 py-2 text-xs">{command}</pre>
            <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                    navigator.clipboard.writeText(command).catch(() => {});
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1500);
                }}
            >
                {copied ? 'Copiado!' : 'Copiar'}
            </Button>
        </div>
    );
}

export default function DestinationChannels() {
    const { props } = usePage<PageProps>();
    const { channels, niches, auth } = props;

    return (
        <>
            <Head title="Canais Destino" />
            <Toaster />
            <SidebarProvider>
                <AppSidebar user={auth.user} />
                <SidebarInset>
                    <SiteHeader title="Canais Destino" />
                    <div className="flex flex-1 flex-col gap-4 p-4">
                        <PageHeader
                            description="Canais do YouTube onde os clips são publicados."
                            actions={
                                <ChannelDialog
                                    niches={niches}
                                    trigger={<Button>Novo Canal Destino</Button>}
                                />
                            }
                        />
                        <div className="overflow-x-auto rounded-lg border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Slug</TableHead>
                                        <TableHead>Nome</TableHead>
                                        <TableHead>Nicho</TableHead>
                                        <TableHead>OAuth</TableHead>
                                        <TableHead>Ativo</TableHead>
                                        <TableHead>YT Channel ID</TableHead>
                                        <TableHead>Ações</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {channels.map((c) => (
                                        <TableRow key={c.id}>
                                            <TableCell>{c.slug}</TableCell>
                                            <TableCell>{c.name}</TableCell>
                                            <TableCell>
                                                <Badge variant="secondary">{c.niche}</Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant={
                                                        c.oauthStatus === 'authorized'
                                                            ? 'default'
                                                            : c.oauthStatus === 'expired'
                                                              ? 'destructive'
                                                              : 'secondary'
                                                    }
                                                >
                                                    {OAUTH_LABEL[c.oauthStatus]}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Switch
                                                    checked={c.active}
                                                    onCheckedChange={(v) =>
                                                        router.put(
                                                            `/painel/canais-destino/${c.id}`,
                                                            { active: v },
                                                            { preserveScroll: true },
                                                        )
                                                    }
                                                />
                                            </TableCell>
                                            <TableCell
                                                className="cursor-pointer font-mono text-xs text-muted-foreground"
                                                onClick={() => {
                                                    navigator.clipboard.writeText(c.youtubeChannelId).catch(() => {});
                                                    toast.success('Copiado');
                                                }}
                                            >
                                                {c.youtubeChannelId}
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex gap-2">
                                                    <ChannelDialog
                                                        channel={c}
                                                        niches={niches}
                                                        trigger={
                                                            <Button variant="outline" size="sm">
                                                                Editar
                                                            </Button>
                                                        }
                                                    />
                                                    <ConfirmButton
                                                        variant="destructive"
                                                        size="sm"
                                                        description={`Apagar o canal-destino "${c.name}"? Essa ação não pode ser desfeita.`}
                                                        onConfirm={() =>
                                                            router.delete(`/painel/canais-destino/${c.id}`)
                                                        }
                                                    >
                                                        Apagar
                                                    </ConfirmButton>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                </SidebarInset>
            </SidebarProvider>
        </>
    );
}
