import { useState } from 'react';
import { Head, router, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';
import { Landmark, Trophy, Mic, PlusCircle, Trash2, Edit2, Search, Sparkles } from 'lucide-react';

import { ConfirmButton } from '@/components/confirm-button';
import { NicheCombobox, type Niche } from '@/components/niche-combobox';
import { PromptProfileSelect, type PromptProfile } from '@/components/prompt-profile-select';
import { ChannelTemplateModal, type TemplateConfig } from '@/components/channel-template-modal';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { AppShell } from '@/layouts/app-shell';

type DestinationChannel = {
    id: number;
    slug: string;
    name: string;
    niche: string;
    promptProfileId: number | null;
    promptProfileName: string | null;
    youtubeChannelId: string;
    creditTemplate: string | null;
    templateConfig?: TemplateConfig | null;
    active: boolean;
    oauthStatus: 'authorized' | 'expired' | 'missing';
    hasWatermark: boolean;
    watermarkUrl?: string | null;
};

type PageProps = {
    channels: DestinationChannel[];
    niches: Niche[];
    promptProfiles?: PromptProfile[];
    auth?: { user: { name: string; email: string } | null };
    flash?: { success: string | null; error: string | null };
};

function NicheIcon({ niche }: { niche: string }) {
    const n = (niche ?? '').toLowerCase();
    if (n.includes('política') || n.includes('politica')) return <Landmark className="h-5 w-5 text-white" />;
    if (n.includes('podcast')) return <Mic className="h-5 w-5 text-white" />;
    return <Trophy className="h-5 w-5 text-white" />;
}

function NicheBadge({ niche }: { niche: string }) {
    const n = (niche ?? '').toLowerCase();
    if (n.includes('política') || n.includes('politica')) {
        return (
            <span className="rounded-lg border border-purple-500/20 bg-purple-500/10 px-2.5 py-1 text-[11px] font-semibold text-purple-600 dark:text-purple-400">
                🏛️ Política
            </span>
        );
    }
    if (n.includes('podcast')) {
        return (
            <span className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-2.5 py-1 text-[11px] font-semibold text-amber-600 dark:text-amber-400">
                🎙️ Podcast
            </span>
        );
    }
    return (
        <span className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
            ⚽ Futebol
        </span>
    );
}

function ChannelDialog({
    channel,
    niches,
    promptProfiles,
    trigger,
}: {
    channel?: DestinationChannel;
    niches: Niche[];
    promptProfiles: PromptProfile[];
    trigger: React.ReactNode;
}) {
    const [open, setOpen] = useState(false);
    const isEdit = !!channel;
    const { data, setData, post, put, processing, errors, reset } = useForm({
        slug: channel?.slug ?? '',
        name: channel?.name ?? '',
        niche: channel?.niche ?? '',
        prompt_profile_id: channel?.promptProfileId ? String(channel.promptProfileId) : '',
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
                        <NicheCombobox niches={niches} value={data.niche} onChange={(val) => setData('niche', val)} />
                        {errors.niche && <p className="text-xs text-destructive">{errors.niche}</p>}
                    </Field>

                    <Field>
                        <FieldLabel>Perfil de prompt</FieldLabel>
                        <PromptProfileSelect
                            profiles={promptProfiles}
                            value={data.prompt_profile_id}
                            niche={data.niche}
                            onChange={(v) => setData('prompt_profile_id', v)}
                        />
                        <p className="text-xs text-muted-foreground">
                            Define os prompts de seleção, metadata e thumbnail deste canal.
                        </p>
                        {errors.prompt_profile_id && (
                            <p className="text-sm text-destructive">{errors.prompt_profile_id}</p>
                        )}
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
                    <Field className="flex flex-row items-center justify-between">
                        <FieldLabel htmlFor="active">Ativo</FieldLabel>
                        <Switch id="active" checked={data.active} onCheckedChange={(v) => setData('active', v)} />
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
    const { channels, niches, promptProfiles = [] } = props;
    const auth = props?.auth;
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [activeTab, setActiveTab] = useState<string>('todos');
    const [search, setSearch] = useState('');
    const [templateModalChannel, setTemplateModalChannel] = useState<DestinationChannel | null>(null);

    const toggleActive = (channel: DestinationChannel) => {
        router.put(
            `/painel/canais-destino/${channel.id}`,
            { active: !channel.active },
            {
                preserveScroll: true,
                onSuccess: () => toast.success(`Canal ${!channel.active ? 'ativado' : 'pausado'}`),
            },
        );
    };

    const deleteChannel = (channel: DestinationChannel) => {
        router.delete(`/painel/canais-destino/${channel.id}`, {
            preserveScroll: true,
            onSuccess: () => toast.success('Canal excluído com sucesso'),
        });
    };

    const counts = {
        todos: channels.length,
        futebol: channels.filter((c) => (c.niche ?? '').toLowerCase() === 'futebol').length,
        politica: channels.filter(
            (c) =>
                (c.niche ?? '').toLowerCase().includes('politica') ||
                (c.niche ?? '').toLowerCase().includes('política'),
        ).length,
        podcast: channels.filter((c) => (c.niche ?? '').toLowerCase() === 'podcast').length,
    };

    const filtered = channels.filter((c) => {
        const matchesTab =
            activeTab === 'todos' ||
            (activeTab === 'futebol' && (c.niche ?? '').toLowerCase() === 'futebol') ||
            (activeTab === 'politica' &&
                ((c.niche ?? '').toLowerCase().includes('politica') ||
                    (c.niche ?? '').toLowerCase().includes('política'))) ||
            (activeTab === 'podcast' && (c.niche ?? '').toLowerCase() === 'podcast');

        const matchesSearch =
            search === '' ||
            c.name.toLowerCase().includes(search.toLowerCase()) ||
            c.slug.toLowerCase().includes(search.toLowerCase()) ||
            c.youtubeChannelId.toLowerCase().includes(search.toLowerCase());

        return matchesTab && matchesSearch;
    });

    return (
        <>
            <Head title="Canais Destino" />
            <AppShell
                title="Canais Destino"
                user={auth?.user ?? null}
                description="Canais do YouTube onde os clipes aprovados são publicados. Cada canal possui sua própria cota e autorização OAuth."
                actions={
                    <ChannelDialog
                        niches={niches}
                        promptProfiles={promptProfiles}
                        trigger={
                            <Button
                                style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)', color: '#fff' }}
                                className="shadow-sm hover:brightness-105"
                            >
                                <PlusCircle className="mr-1.5 h-4 w-4" /> Novo Canal Destino
                            </Button>
                        }
                    />
                }
            >
                <div className="flex flex-col gap-4">
                    {/* Subtabs de nicho + Toggle Quadro/Tabela + Busca */}
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex w-fit flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-1.5">
                            <button
                                type="button"
                                onClick={() => setActiveTab('todos')}
                                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                                    activeTab === 'todos'
                                        ? 'bg-primary text-primary-foreground shadow-sm'
                                        : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                                }`}
                            >
                                <span>Todos</span>
                                <span className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[10px]">
                                    {counts.todos}
                                </span>
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('futebol')}
                                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                                    activeTab === 'futebol'
                                        ? 'bg-emerald-600 text-white shadow-sm'
                                        : 'text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400'
                                }`}
                            >
                                <span>⚽ Futebol</span>
                                <span className="rounded-md bg-emerald-500/20 px-1.5 py-0.5 font-mono text-[10px]">
                                    {counts.futebol}
                                </span>
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('politica')}
                                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                                    activeTab === 'politica'
                                        ? 'bg-purple-600 text-white shadow-sm'
                                        : 'text-purple-600 hover:bg-purple-500/10 dark:text-purple-400'
                                }`}
                            >
                                <span>🏛️ Política</span>
                                <span className="rounded-md bg-purple-500/20 px-1.5 py-0.5 font-mono text-[10px]">
                                    {counts.politica}
                                </span>
                            </button>
                            {counts.podcast > 0 && (
                                <button
                                    type="button"
                                    onClick={() => setActiveTab('podcast')}
                                    className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                                        activeTab === 'podcast'
                                            ? 'bg-amber-600 text-white shadow-sm'
                                            : 'text-amber-600 hover:bg-amber-500/10 dark:text-amber-400'
                                    }`}
                                >
                                    <span>🎙️ Podcast</span>
                                    <span className="rounded-md bg-amber-500/20 px-1.5 py-0.5 font-mono text-[10px]">
                                        {counts.podcast}
                                    </span>
                                </button>
                            )}
                        </div>

                        <div className="flex items-center gap-3">
                            <div className="flex overflow-hidden rounded-lg border bg-card p-0.5">
                                <button
                                    type="button"
                                    onClick={() => setViewMode('grid')}
                                    className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                                        viewMode === 'grid'
                                            ? 'bg-primary text-primary-foreground shadow-sm'
                                            : 'text-muted-foreground hover:text-foreground'
                                    }`}
                                    title="Modo Quadro"
                                >
                                    ⊞ Quadro
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setViewMode('list')}
                                    className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                                        viewMode === 'list'
                                            ? 'bg-primary text-primary-foreground shadow-sm'
                                            : 'text-muted-foreground hover:text-foreground'
                                    }`}
                                    title="Modo Tabela"
                                >
                                    ☰ Tabela
                                </button>
                            </div>

                            <div className="relative">
                                <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    placeholder="Buscar canal..."
                                    className="h-10 w-[200px] rounded-xl bg-card pr-3 pl-9 text-xs"
                                />
                            </div>
                        </div>
                    </div>

                    {viewMode === 'grid' ? (
                        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
                            {filtered.map((channel) => {
                                const isPol =
                                    (channel.niche ?? '').toLowerCase().includes('política') ||
                                    (channel.niche ?? '').toLowerCase().includes('politica');
                                const bgGrad = isPol
                                    ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)'
                                    : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';
                                const isAuth = channel.oauthStatus === 'authorized';

                                return (
                                    <div
                                        key={channel.id}
                                        className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-5 shadow-xs transition-all hover:border-primary/30"
                                    >
                                        <div className="flex items-start gap-3">
                                            {channel.hasWatermark && channel.watermarkUrl ? (
                                                <img
                                                    src={channel.watermarkUrl}
                                                    alt={channel.name}
                                                    className="h-11 w-11 shrink-0 rounded-xl border border-border bg-black/20 object-cover shadow-sm"
                                                />
                                            ) : (
                                                <div
                                                    className="grid h-11 w-11 shrink-0 place-items-center rounded-xl shadow-sm"
                                                    style={{ background: bgGrad }}
                                                >
                                                    <NicheIcon niche={channel.niche} />
                                                </div>
                                            )}
                                            <div className="min-w-0 flex-1">
                                                <div className="truncate text-sm font-bold tracking-tight text-foreground">
                                                    {channel.name}
                                                </div>
                                                <div className="truncate font-mono text-[11px] text-muted-foreground">
                                                    {channel.slug}
                                                </div>
                                            </div>
                                            <NicheBadge niche={channel.niche} />
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <span
                                                className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11.5px] font-semibold ${
                                                    isAuth
                                                        ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                                                        : 'border-red-500/20 bg-red-500/10 text-red-600 dark:text-red-400'
                                                }`}
                                            >
                                                <span
                                                    className={`h-1.5 w-1.5 rounded-full ${isAuth ? 'bg-emerald-500' : 'bg-red-500'}`}
                                                />
                                                {isAuth ? 'OAuth autorizado' : 'Sem autorização'}
                                            </span>
                                            <span
                                                className="truncate font-mono text-[10.5px] text-muted-foreground"
                                                title={channel.youtubeChannelId}
                                            >
                                                {channel.youtubeChannelId}
                                            </span>
                                        </div>

                                        <div className="rounded-xl border border-border bg-muted/40 p-3">
                                            <div className="mb-2 flex items-center justify-between text-xs">
                                                <span className="text-muted-foreground">Cota diária restante</span>
                                                <span className="font-mono font-semibold text-foreground">
                                                    5 de 5 slots
                                                </span>
                                            </div>
                                            <div className="h-1.5 overflow-hidden rounded-full bg-black/10 dark:bg-white/[.08]">
                                                <div
                                                    className="h-full rounded-full bg-emerald-500"
                                                    style={{ width: '100%' }}
                                                />
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2 border-t border-border/60 pt-2">
                                            <Switch
                                                checked={channel.active}
                                                onCheckedChange={() => toggleActive(channel)}
                                            />
                                            <span className="text-xs font-medium text-foreground">
                                                {channel.active ? 'Ativo' : 'Pausado'}
                                            </span>
                                            <div className="flex-1" />
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setTemplateModalChannel(channel)}
                                                className="h-8 rounded-lg border-amber-500/30 px-2.5 text-xs text-amber-600 hover:bg-amber-500/10 dark:text-amber-400"
                                            >
                                                <Sparkles className="mr-1 h-3.5 w-3.5 text-amber-500" /> Template 9:16
                                            </Button>
                                            <ChannelDialog
                                                channel={channel}
                                                niches={niches}
                                                promptProfiles={promptProfiles}
                                                trigger={
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        className="h-8 rounded-lg px-3 text-xs"
                                                    >
                                                        <Edit2 className="mr-1 h-3.5 w-3.5" /> Editar
                                                    </Button>
                                                }
                                            />
                                            <ConfirmButton
                                                variant="destructive"
                                                size="sm"
                                                className="h-8 w-8 rounded-lg p-0"
                                                description={`Excluir canal "${channel.name}"?`}
                                                onConfirm={() => deleteChannel(channel)}
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </ConfirmButton>
                                        </div>
                                    </div>
                                );
                            })}

                            {/* Card de Adicionar Canal */}
                            <ChannelDialog
                                niches={niches}
                                promptProfiles={promptProfiles}
                                trigger={
                                    <div className="flex min-h-[220px] cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-border/80 p-8 text-center transition-colors hover:border-primary/50">
                                        <div className="grid h-12 w-12 place-items-center rounded-xl bg-muted/60">
                                            <PlusCircle className="h-6 w-6 text-muted-foreground" />
                                        </div>
                                        <div>
                                            <div className="text-sm font-bold text-foreground">Conectar Novo Canal</div>
                                            <div className="mt-0.5 text-xs text-muted-foreground">
                                                Cadastre um canal do YouTube para receber clipes
                                            </div>
                                        </div>
                                    </div>
                                }
                            />
                        </div>
                    ) : (
                        <div className="overflow-hidden rounded-2xl border border-border bg-card">
                            <Table>
                                <TableHeader>
                                    <TableRow className="hover:bg-transparent">
                                        <TableHead className="px-5 py-3.5 text-xs font-semibold">Canal</TableHead>
                                        <TableHead className="px-5 py-3.5 text-xs font-semibold">Nicho</TableHead>
                                        <TableHead className="px-5 py-3.5 text-xs font-semibold">
                                            Status OAuth
                                        </TableHead>
                                        <TableHead className="px-5 py-3.5 text-xs font-semibold">Channel ID</TableHead>
                                        <TableHead className="px-5 py-3.5 text-xs font-semibold">Ativo</TableHead>
                                        <TableHead className="px-5 py-3.5 text-right text-xs font-semibold">
                                            Ações
                                        </TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filtered.map((channel) => {
                                        const isPol =
                                            (channel.niche ?? '').toLowerCase().includes('política') ||
                                            (channel.niche ?? '').toLowerCase().includes('politica');
                                        const bgGrad = isPol
                                            ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)'
                                            : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';
                                        const isAuth = channel.oauthStatus === 'authorized';
                                        return (
                                            <TableRow key={channel.id} className="hover:bg-muted/30">
                                                <TableCell className="px-5 py-3">
                                                    <div className="flex items-center gap-3">
                                                        {channel.hasWatermark && channel.watermarkUrl ? (
                                                            <img
                                                                src={channel.watermarkUrl}
                                                                alt={channel.name}
                                                                className="h-8 w-8 shrink-0 rounded-lg border border-border bg-black/20 object-cover"
                                                            />
                                                        ) : (
                                                            <div
                                                                className="grid h-8 w-8 shrink-0 place-items-center rounded-lg"
                                                                style={{ background: bgGrad }}
                                                            >
                                                                <NicheIcon niche={channel.niche} />
                                                            </div>
                                                        )}
                                                        <div>
                                                            <div className="font-semibold text-foreground">
                                                                {channel.name}
                                                            </div>
                                                            <div className="font-mono text-[11px] text-muted-foreground">
                                                                {channel.slug}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="px-5 py-3">
                                                    <NicheBadge niche={channel.niche} />
                                                </TableCell>
                                                <TableCell className="px-5 py-3">
                                                    <span
                                                        className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-semibold ${
                                                            isAuth
                                                                ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                                                                : 'border-red-500/20 bg-red-500/10 text-red-600 dark:text-red-400'
                                                        }`}
                                                    >
                                                        <span
                                                            className={`h-1.5 w-1.5 rounded-full ${isAuth ? 'bg-emerald-500' : 'bg-red-500'}`}
                                                        />
                                                        {isAuth ? 'Autorizado' : 'Pendente'}
                                                    </span>
                                                </TableCell>
                                                <TableCell className="px-5 py-3 font-mono text-muted-foreground">
                                                    {channel.youtubeChannelId}
                                                </TableCell>
                                                <TableCell className="px-5 py-3">
                                                    <Switch
                                                        checked={channel.active}
                                                        onCheckedChange={() => toggleActive(channel)}
                                                    />
                                                </TableCell>
                                                <TableCell className="px-5 py-3 text-right">
                                                    <div className="flex items-center justify-end gap-1.5">
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() => setTemplateModalChannel(channel)}
                                                            className="h-8 rounded-lg border-amber-500/30 px-2.5 text-xs text-amber-600 hover:bg-amber-500/10 dark:text-amber-400"
                                                            title="Personalizar Template 9:16"
                                                        >
                                                            <Sparkles className="mr-1 h-3.5 w-3.5 text-amber-500" />{' '}
                                                            Template
                                                        </Button>
                                                        <ChannelDialog
                                                            channel={channel}
                                                            niches={niches}
                                                            promptProfiles={promptProfiles}
                                                            trigger={
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="h-8 rounded-lg px-2.5 text-xs"
                                                                >
                                                                    <Edit2 className="h-3.5 w-3.5" />
                                                                </Button>
                                                            }
                                                        />
                                                        <ConfirmButton
                                                            variant="destructive"
                                                            size="sm"
                                                            className="h-8 w-8 rounded-lg p-0"
                                                            description={`Excluir canal "${channel.name}"?`}
                                                            onConfirm={() => deleteChannel(channel)}
                                                        >
                                                            <Trash2 className="h-3.5 w-3.5" />
                                                        </ConfirmButton>
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </div>
            </AppShell>

            {/* Modal do Estúdio de Template 9:16 por Canal */}
            <ChannelTemplateModal
                channel={templateModalChannel}
                open={!!templateModalChannel}
                onOpenChange={(open) => !open && setTemplateModalChannel(null)}
            />
        </>
    );
}
