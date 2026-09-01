import { useState } from 'react';
import { Head, router, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';
import { Landmark, Trophy, Mic, PlusCircle, Trash2, Edit2, KeyRound } from 'lucide-react';

import { ConfirmButton } from '@/components/confirm-button';
import { NicheCombobox, type Niche } from '@/components/niche-combobox';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { AppShell } from '@/layouts/app-shell';

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

function NicheIcon({ niche }: { niche: string }) {
    const n = niche.toLowerCase();
    if (n.includes('política') || n.includes('politica')) return <Landmark className="w-5 h-5 text-white" />;
    if (n.includes('podcast')) return <Mic className="w-5 h-5 text-white" />;
    return <Trophy className="w-5 h-5 text-white" />;
}

function NicheBadge({ niche }: { niche: string }) {
    const n = niche.toLowerCase();
    if (n.includes('política') || n.includes('politica')) {
        return (
            <span className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                🏛️ Política
            </span>
        );
    }
    if (n.includes('podcast')) {
        return (
            <span className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                🎙️ Podcast
            </span>
        );
    }
    return (
        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            ⚽ Futebol
        </span>
    );
}

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

    const submit = (e: React.FormEvent) => {
        e.preventDefault();
        const options = {
            onSuccess: () => {
                setOpen(false);
                if (!isEdit) reset();
                toast.success(isEdit ? 'Canal atualizado com sucesso' : 'Canal criado com sucesso');
            },
            onError: () => toast.error('Verifique os campos do formulário'),
        };
        if (isEdit) {
            put(`/painel/canais-destino/${channel.id}`, options);
        } else {
            post('/painel/canais-destino', options);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>{trigger}</DialogTrigger>
            <DialogContent className="w-full max-w-lg overflow-x-hidden">
                <DialogHeader>
                    <DialogTitle className="font-display font-bold">
                        {isEdit ? 'Editar Canal Destino' : 'Novo Canal Destino'}
                    </DialogTitle>
                </DialogHeader>
                <form onSubmit={submit} className="space-y-4">
                    <Field>
                        <FieldLabel>Nome do Canal</FieldLabel>
                        <Input
                            value={data.name}
                            onChange={(e) => setData('name', e.target.value)}
                            placeholder="Ex: Futebol em Cortes"
                            required
                        />
                        {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
                    </Field>

                    <Field>
                        <FieldLabel>Slug (identificador único)</FieldLabel>
                        <Input
                            value={data.slug}
                            onChange={(e) => setData('slug', e.target.value)}
                            placeholder="Ex: futebol-em-cortes"
                            required
                            disabled={isEdit}
                            className="font-mono text-xs"
                        />
                        {errors.slug && <p className="text-xs text-destructive">{errors.slug}</p>}
                    </Field>

                    <Field>
                        <FieldLabel>Nicho</FieldLabel>
                        <NicheCombobox
                            niches={niches}
                            value={data.niche}
                            onChange={(val) => setData('niche', val)}
                        />
                        {errors.niche && <p className="text-xs text-destructive">{errors.niche}</p>}
                    </Field>

                    <Field>
                        <FieldLabel>YouTube Channel ID</FieldLabel>
                        <Input
                            value={data.youtube_channel_id}
                            onChange={(e) => setData('youtube_channel_id', e.target.value)}
                            placeholder="Ex: UCcyeBQFAkUNeDJbBM7JJqLw"
                            required
                            className="font-mono text-xs"
                        />
                        {errors.youtube_channel_id && (
                            <p className="text-xs text-destructive">{errors.youtube_channel_id}</p>
                        )}
                    </Field>

                    <Field>
                        <FieldLabel>Template de Créditos na Descrição</FieldLabel>
                        <Textarea
                            value={data.credit_template}
                            onChange={(e) => setData('credit_template', e.target.value)}
                            rows={2}
                            placeholder="Créditos: @{channel_handle}"
                        />
                    </Field>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            Cancelar
                        </Button>
                        <Button
                            type="submit"
                            disabled={processing}
                            style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)', color: '#fff' }}
                        >
                            {isEdit ? 'Salvar Alterações' : 'Criar Canal'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

export default function DestinationChannels() {
    const { props } = usePage<PageProps>();
    const { channels, niches, auth } = props;

    const toggleActive = (channel: DestinationChannel) => {
        router.put(
            `/painel/canais-destino/${channel.id}`,
            { active: !channel.active },
            {
                preserveScroll: true,
                onSuccess: () => toast.success(`Canal ${!channel.active ? 'ativado' : 'pausado'}`),
            }
        );
    };

    const deleteChannel = (channel: DestinationChannel) => {
        router.delete(`/painel/canais-destino/${channel.id}`, {
            preserveScroll: true,
            onSuccess: () => toast.success('Canal excluído com sucesso'),
        });
    };

    return (
        <>
            <Head title="Canais Destino" />
            <AppShell
                title="Canais Destino"
                user={auth.user}
                description="Canais do YouTube onde os clipes aprovados são publicados. Cada canal possui sua própria cota e autorização OAuth."
            >
                <div className="grid gap-6 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                    {channels.map((channel) => {
                        const isPol = channel.niche.toLowerCase().includes('política') || channel.niche.toLowerCase().includes('politica');
                        const bgGrad = isPol ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)' : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';
                        const isAuth = channel.oauthStatus === 'authorized';

                        return (
                            <div
                                key={channel.id}
                                className="rounded-2xl border border-border bg-card p-5 flex flex-col gap-4 shadow-xs hover:border-primary/30 transition-all"
                            >
                                <div className="flex items-start gap-3">
                                    <div className="w-11 h-11 rounded-xl grid place-items-center shrink-0 shadow-sm" style={{ background: bgGrad }}>
                                        <NicheIcon niche={channel.niche} />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <div className="font-bold text-sm tracking-tight truncate text-foreground">{channel.name}</div>
                                        <div className="font-mono text-[11px] text-muted-foreground truncate">{channel.slug}</div>
                                    </div>
                                    <NicheBadge niche={channel.niche} />
                                </div>

                                <div className="flex items-center gap-2">
                                    <span
                                        className={`flex items-center gap-1.5 text-[11.5px] font-semibold px-2.5 py-1 rounded-lg border ${
                                            isAuth
                                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                                                : 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20'
                                        }`}
                                    >
                                        <span className={`w-1.5 h-1.5 rounded-full ${isAuth ? 'bg-emerald-500' : 'bg-red-500'}`} />
                                        {isAuth ? 'OAuth autorizado' : 'Sem autorização'}
                                    </span>
                                    <span className="font-mono text-[10.5px] text-muted-foreground truncate" title={channel.youtubeChannelId}>
                                        {channel.youtubeChannelId}
                                    </span>
                                </div>

                                <div className="rounded-xl border border-border bg-muted/40 p-3">
                                    <div className="flex items-center justify-between text-xs mb-2">
                                        <span className="text-muted-foreground">Cota diária</span>
                                        <span className="font-mono font-semibold text-foreground">5 de 5 slots</span>
                                    </div>
                                    <div className="h-1.5 rounded-full bg-black/10 dark:bg-white/[.08] overflow-hidden">
                                        <div className="h-full rounded-full bg-emerald-500" style={{ width: '100%' }} />
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 pt-2 border-t border-border/60">
                                    <Switch
                                        checked={channel.active}
                                        onCheckedChange={() => toggleActive(channel)}
                                    />
                                    <span className="text-xs font-medium text-foreground">
                                        {channel.active ? 'Ativo' : 'Pausado'}
                                    </span>
                                    <div className="flex-1" />
                                    <ChannelDialog
                                        channel={channel}
                                        niches={niches}
                                        trigger={
                                            <Button variant="outline" size="sm" className="h-8 px-3 rounded-lg text-xs">
                                                <Edit2 className="w-3.5 h-3.5 mr-1" /> Editar
                                            </Button>
                                        }
                                    />
                                    <ConfirmButton
                                        variant="destructive"
                                        size="sm"
                                        className="h-8 w-8 p-0 rounded-lg"
                                        description={`Excluir canal "${channel.name}"?`}
                                        onConfirm={() => deleteChannel(channel)}
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </ConfirmButton>
                                </div>
                            </div>
                        );
                    })}

                    {/* Card de Adicionar Canal */}
                    <ChannelDialog
                        niches={niches}
                        trigger={
                            <button
                                type="button"
                                className="rounded-2xl border-2 border-dashed border-border p-6 min-h-[200px] grid place-items-center text-muted-foreground hover:border-primary hover:text-primary transition-all group"
                            >
                                <div className="flex flex-col items-center gap-2">
                                    <PlusCircle className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" />
                                    <span className="text-sm font-semibold">Adicionar canal destino</span>
                                </div>
                            </button>
                        }
                    />
                </div>
            </AppShell>
        </>
    );
}
