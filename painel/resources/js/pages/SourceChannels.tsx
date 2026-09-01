import { useState } from 'react';
import { Head, router, useForm, usePage } from '@inertiajs/react';

import { ConfirmButton } from '@/components/confirm-button';
import { NicheCombobox, type Niche } from '@/components/niche-combobox';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { AppShell } from '@/layouts/app-shell';

type SourceChannel = {
    id: number;
    channelName: string;
    channelHandle: string | null;
    targetNiche: string;
    active: boolean;
    blacklisted: boolean;
    createdAt: string | null;
};

type PageProps = {
    channels: SourceChannel[];
    niches: Niche[];
    activeTab: string;
    auth: { user: { name: string; email: string } | null };
};

function CreateChannelDialog({ niches }: { niches: Niche[] }) {
    const [open, setOpen] = useState(false);
    const { data, setData, post, processing, errors, reset } = useForm({
        url: '',
        target_niche: 'futebol',
    });

    function submit(e: React.FormEvent) {
        e.preventDefault();
        post('/painel/canais-fonte', {
            onSuccess: () => {
                setOpen(false);
                reset();
            },
        });
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button>Novo Canal Fonte</Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Adicionar canal-fonte</DialogTitle>
                </DialogHeader>
                <form onSubmit={submit} className="grid gap-4">
                    <Field>
                        <FieldLabel htmlFor="url">URL do canal YouTube</FieldLabel>
                        <Input
                            id="url"
                            placeholder="https://youtube.com/@..."
                            value={data.url}
                            onChange={(e) => setData('url', e.target.value)}
                        />
                        <p className="text-xs text-muted-foreground">
                            Ex: https://youtube.com/@sportv ou https://youtube.com/channel/UC...
                        </p>
                        {errors.url && <p className="text-sm text-destructive">{errors.url}</p>}
                    </Field>
                    <Field>
                        <FieldLabel>Nicho de destino</FieldLabel>
                        <NicheCombobox
                            niches={niches}
                            value={data.target_niche}
                            onChange={(v) => setData('target_niche', v)}
                        />
                    </Field>
                    <DialogFooter>
                        <Button type="submit" disabled={processing}>
                            Adicionar
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

export default function SourceChannels() {
    const { props } = usePage<PageProps>();
    const { channels, niches, activeTab, auth } = props;

    return (
        <>
            <Head title="Canais Fonte" />
            <AppShell
                title="Canais Fonte"
                user={auth.user}
                description="Canais do YouTube que o robô monitora pra encontrar conteúdo bruto. Formato curto/longo é decidido automaticamente pela duração do vídeo, não por canal."
                actions={<CreateChannelDialog niches={niches} />}
            >
                <Tabs
                    value={activeTab}
                    onValueChange={(tab) => router.get('/painel/canais-fonte', { tab }, { preserveState: true })}
                >
                    <TabsList>
                        <TabsTrigger value="todos">Todos</TabsTrigger>
                        {niches.map((n) => (
                            <TabsTrigger key={n.slug} value={n.slug}>
                                {n.label}
                            </TabsTrigger>
                        ))}
                    </TabsList>
                </Tabs>

                <div className="overflow-x-auto rounded-lg border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Nome</TableHead>
                                <TableHead>Handle</TableHead>
                                <TableHead>Nicho</TableHead>
                                <TableHead>Ativo</TableHead>
                                <TableHead>Blacklisted</TableHead>
                                <TableHead>Criado</TableHead>
                                <TableHead>Ações</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {channels.map((c) => (
                                <TableRow key={c.id}>
                                    <TableCell>{c.channelName}</TableCell>
                                    <TableCell className="text-muted-foreground">{c.channelHandle ?? '—'}</TableCell>
                                    <TableCell>
                                        <Badge variant="secondary">{c.targetNiche}</Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Switch
                                            checked={c.active}
                                            onCheckedChange={(v) =>
                                                router.put(
                                                    `/painel/canais-fonte/${c.id}`,
                                                    { active: v },
                                                    { preserveScroll: true },
                                                )
                                            }
                                        />
                                    </TableCell>
                                    <TableCell title="Afeta apenas novos vídeos. Para purgar a fila use SQL manual.">
                                        <Switch
                                            checked={c.blacklisted}
                                            onCheckedChange={(v) =>
                                                router.put(
                                                    `/painel/canais-fonte/${c.id}`,
                                                    { blacklisted: v },
                                                    { preserveScroll: true },
                                                )
                                            }
                                        />
                                    </TableCell>
                                    <TableCell className="text-muted-foreground">{c.createdAt ?? '—'}</TableCell>
                                    <TableCell>
                                        <ConfirmButton
                                            variant="destructive"
                                            size="sm"
                                            description={`Apagar o canal-fonte "${c.channelName}"? Essa ação não pode ser desfeita.`}
                                            onConfirm={() => router.delete(`/painel/canais-fonte/${c.id}`)}
                                        >
                                            Apagar
                                        </ConfirmButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            </AppShell>
        </>
    );
}
