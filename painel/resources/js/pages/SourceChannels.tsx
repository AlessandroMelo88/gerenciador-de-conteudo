import { useState } from 'react';
import { Head, router, useForm, usePage } from '@inertiajs/react';
import { Search, Plus, Trash2, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';

import { ConfirmButton } from '@/components/confirm-button';
import { NicheCombobox, type Niche } from '@/components/niche-combobox';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
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

function NicheBadge({ niche }: { niche: string }) {
    const n = (niche ?? '').toLowerCase();
    if (n.includes('política') || n.includes('politica')) {
        return (
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                🏛️ Política
            </span>
        );
    }
    if (n.includes('podcast')) {
        return (
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                🎙️ Podcast
            </span>
        );
    }
    return (
        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            ⚽ Futebol
        </span>
    );
}

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
                toast.success('Canal fonte cadastrado com sucesso');
            },
            onError: () => toast.error('Erro ao cadastrar canal fonte'),
        });
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button
                    style={{ background: 'linear-gradient(160deg,#FF6A55,#E23C33)', color: '#fff' }}
                    className="shadow-sm hover:brightness-105"
                >
                    <Plus className="w-4 h-4 mr-1.5" /> Novo Canal Fonte
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle className="font-display font-bold">Adicionar Canal Fonte</DialogTitle>
                </DialogHeader>
                <form onSubmit={submit} className="space-y-4">
                    <Field>
                        <FieldLabel>URL ou Handle do Canal YouTube</FieldLabel>
                        <Input
                            value={data.url}
                            onChange={(e) => setData('url', e.target.value)}
                            placeholder="https://www.youtube.com/@Canal ou @Canal"
                            required
                        />
                        {errors.url && <p className="text-xs text-destructive">{errors.url}</p>}
                    </Field>

                    <Field>
                        <FieldLabel>Nicho Alvo</FieldLabel>
                        <NicheCombobox
                            niches={niches}
                            value={data.target_niche}
                            onChange={(val) => setData('target_niche', val)}
                        />
                        {errors.target_niche && <p className="text-xs text-destructive">{errors.target_niche}</p>}
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
                            Salvar Canal
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

export default function SourceChannels() {
    const { props } = usePage<PageProps>();
    const { channels, niches, auth } = props;

    const [activeTab, setActiveTab] = useState<string>('todos');
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
    const [search, setSearch] = useState('');

    const toggle = (id: number, field: 'active' | 'blacklisted', current: boolean) => {
        router.put(
            `/painel/canais-fonte/${id}`,
            { [field]: !current },
            {
                preserveScroll: true,
                onSuccess: () => toast.success('Status atualizado com sucesso'),
            }
        );
    };

    const destroy = (id: number) => {
        router.delete(`/painel/canais-fonte/${id}`, {
            preserveScroll: true,
            onSuccess: () => toast.success('Canal fonte removido'),
        });
    };

    const counts = {
        todos: channels.length,
        futebol: channels.filter((c) => (c.targetNiche ?? '').toLowerCase() === 'futebol').length,
        politica: channels.filter((c) => (c.targetNiche ?? '').toLowerCase().includes('politica')).length,
        podcast: channels.filter((c) => (c.targetNiche ?? '').toLowerCase() === 'podcast').length,
    };

    const filtered = channels.filter((c) => {
        const matchesTab =
            activeTab === 'todos' ||
            (activeTab === 'futebol' && (c.targetNiche ?? '').toLowerCase() === 'futebol') ||
            (activeTab === 'politica' && (c.targetNiche ?? '').toLowerCase().includes('politica')) ||
            (activeTab === 'podcast' && (c.targetNiche ?? '').toLowerCase() === 'podcast');

        const matchesSearch =
            search === '' ||
            c.channelName.toLowerCase().includes(search.toLowerCase()) ||
            (c.channelHandle ?? '').toLowerCase().includes(search.toLowerCase());

        return matchesTab && matchesSearch;
    });

    return (
        <>
            <Head title="Canais Fonte" />
            <AppShell
                title="Canais Fonte"
                user={auth.user}
                description="Canais do YouTube monitorados pelo robô para encontrar matéria-prima bruta. O robô balanceia downloads entre os nichos."
                actions={<CreateChannelDialog niches={niches} />}
            >
                <div className="flex flex-col gap-4">
                    {/* Subtabs de nicho + Toggle Cards/Lista + Busca */}
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-2xl border border-border bg-card w-fit">
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
                                <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-mono">
                                    {counts.todos}
                                </span>
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('futebol')}
                                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                                    activeTab === 'futebol'
                                        ? 'bg-emerald-600 text-white shadow-sm'
                                        : 'text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10'
                                }`}
                            >
                                <span>⚽ Futebol</span>
                                <span className="rounded-md bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-mono">
                                    {counts.futebol}
                                </span>
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('politica')}
                                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                                    activeTab === 'politica'
                                        ? 'bg-purple-600 text-white shadow-sm'
                                        : 'text-purple-600 dark:text-purple-400 hover:bg-purple-500/10'
                                }`}
                            >
                                <span>🏛️ Política</span>
                                <span className="rounded-md bg-purple-500/20 px-1.5 py-0.5 text-[10px] font-mono">
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
                                            : 'text-amber-600 dark:text-amber-400 hover:bg-amber-500/10'
                                    }`}
                                >
                                    <span>🎙️ Podcast</span>
                                    <span className="rounded-md bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-mono">
                                        {counts.podcast}
                                    </span>
                                </button>
                            )}
                        </div>

                        <div className="flex items-center gap-3">
                            <div className="flex rounded-lg border bg-card p-0.5 overflow-hidden">
                                <button
                                    type="button"
                                    onClick={() => setViewMode('grid')}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
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
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
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
                                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    placeholder="Buscar canal ou handle…"
                                    className="h-10 w-[220px] pl-9 pr-3 rounded-xl text-xs bg-card"
                                />
                            </div>
                        </div>
                    </div>

                    {viewMode === 'grid' ? (
                        <div className="grid gap-5 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                            {filtered.map((channel) => {
                                const isPol = (channel.targetNiche ?? '').toLowerCase().includes('politica');
                                const bgGrad = isPol ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)' : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';
                                const initials = channel.channelName
                                    .split(' ')
                                    .map((w) => w[0])
                                    .slice(0, 2)
                                    .join('');

                                return (
                                    <div
                                        key={channel.id}
                                        className="rounded-2xl border border-border bg-card p-5 flex flex-col gap-4 shadow-xs hover:border-primary/30 transition-all"
                                    >
                                        <div className="flex items-start gap-3">
                                            <span
                                                className="w-11 h-11 rounded-xl grid place-items-center text-xs font-bold text-white shrink-0 shadow-sm"
                                                style={{ background: bgGrad }}
                                            >
                                                {initials}
                                            </span>
                                            <div className="min-w-0 flex-1">
                                                <div className="font-bold text-sm tracking-tight truncate text-foreground">
                                                    {channel.channelName}
                                                </div>
                                                <div className="font-mono text-[11px] text-muted-foreground truncate">
                                                    {channel.channelHandle ?? '—'}
                                                </div>
                                            </div>
                                            <NicheBadge niche={channel.targetNiche} />
                                        </div>

                                        <div className="flex items-center justify-between text-xs py-2 px-3 rounded-xl bg-muted/40 border border-border">
                                            <span className="text-muted-foreground">Status no Robô:</span>
                                            <span className="font-semibold text-foreground">
                                                {channel.active ? '🟢 Monitorando' : '⏸️ Pausado'}
                                            </span>
                                        </div>

                                        <div className="flex items-center gap-3 pt-2 border-t border-border/60">
                                            <div className="flex items-center gap-2">
                                                <Switch
                                                    checked={channel.active}
                                                    onCheckedChange={() => toggle(channel.id, 'active', channel.active)}
                                                />
                                                <span className="text-xs text-foreground">Ativo</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Switch
                                                    checked={channel.blacklisted}
                                                    onCheckedChange={() => toggle(channel.id, 'blacklisted', channel.blacklisted)}
                                                    className="data-[state=checked]:bg-destructive"
                                                />
                                                <span className="text-xs text-destructive">Bloquear</span>
                                            </div>
                                            <div className="flex-1" />
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="h-8 px-2.5 text-xs text-primary border-primary/30 hover:bg-primary/10 gap-1.5"
                                                onClick={() => {
                                                    const prompt = `Faça uma análise estratégica completa da estrutura de conteúdo do canal "${channel.channelName}" (${channel.channelHandle || 'YouTube'}) no nicho de ${channel.targetNiche}. Quais são as fórmulas de títulos, ganchos nos primeiros 3 segundos, formatos de corte e temas de maior engajamento para modelarmos no nosso canal?`;
                                                    router.visit(`/painel/assistente?prompt=${encodeURIComponent(prompt)}`);
                                                }}
                                                title="Analisar Estrutura com IA"
                                            >
                                                <span>🧠 Analisar IA</span>
                                            </Button>
                                            <ConfirmButton
                                                variant="destructive"
                                                size="sm"
                                                className="h-8 w-8 p-0 rounded-lg"
                                                description={`Remover o canal fonte "${channel.channelName}"?`}
                                                onConfirm={() => destroy(channel.id)}
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </ConfirmButton>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-xs">
                            <div className="overflow-x-auto">
                                <Table className="w-full text-xs">
                                    <TableHeader className="bg-muted/40">
                                        <TableRow>
                                            <TableHead className="px-5 py-3 font-semibold">Canal</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold">Nicho</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold">Ativo</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold">Blacklist</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold text-right">Ações</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {filtered.map((channel) => {
                                            const isPol = (channel.targetNiche ?? '').toLowerCase().includes('politica');
                                            const bgGrad = isPol ? 'linear-gradient(150deg,#2b1d4a,#4c2a80)' : 'linear-gradient(150deg,#0f3d2e,#0b5d43)';
                                            const initials = channel.channelName
                                                .split(' ')
                                                .map((w) => w[0])
                                                .slice(0, 2)
                                                .join('');

                                            return (
                                                <TableRow key={channel.id} className="hover:bg-muted/30">
                                                    <TableCell className="px-5 py-3">
                                                        <div className="flex items-center gap-3">
                                                            <span
                                                                className="w-8 h-8 rounded-full grid place-items-center text-[11px] font-bold text-white shrink-0 shadow-sm"
                                                                style={{ background: bgGrad }}
                                                            >
                                                                {initials}
                                                            </span>
                                                            <div className="min-w-0">
                                                                <div className="font-semibold text-foreground truncate">
                                                                    {channel.channelName}
                                                                </div>
                                                                <div className="font-mono text-[11px] text-muted-foreground truncate">
                                                                    {channel.channelHandle ?? '—'}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3">
                                                        <NicheBadge niche={channel.targetNiche} />
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3">
                                                        <Switch
                                                            checked={channel.active}
                                                            onCheckedChange={() => toggle(channel.id, 'active', channel.active)}
                                                        />
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3">
                                                        <Switch
                                                            checked={channel.blacklisted}
                                                            onCheckedChange={() =>
                                                                toggle(channel.id, 'blacklisted', channel.blacklisted)
                                                            }
                                                            className="data-[state=checked]:bg-destructive"
                                                        />
                                                    </TableCell>
                                                    <TableCell className="px-5 py-3 text-right">
                                                        <div className="flex items-center justify-end gap-1.5">
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                className="h-8 px-2.5 text-xs text-primary border-primary/30 hover:bg-primary/10 gap-1"
                                                                onClick={() => {
                                                                    const prompt = `Faça uma análise estratégica completa da estrutura de conteúdo do canal "${channel.channelName}" (${channel.channelHandle || 'YouTube'}) no nicho de ${channel.targetNiche}. Quais são as fórmulas de títulos, ganchos nos primeiros 3 segundos, formatos de corte e temas de maior engajamento para modelarmos no nosso canal?`;
                                                                    router.visit(`/painel/assistente?prompt=${encodeURIComponent(prompt)}`);
                                                                }}
                                                                title="Analisar Estrutura com IA"
                                                            >
                                                                <span>🧠 Analisar IA</span>
                                                            </Button>
                                                            <ConfirmButton
                                                                variant="destructive"
                                                                size="sm"
                                                                className="h-8 w-8 p-0 rounded-lg"
                                                                description={`Remover o canal fonte "${channel.channelName}"?`}
                                                                onConfirm={() => destroy(channel.id)}
                                                            >
                                                                <Trash2 className="w-3.5 h-3.5" />
                                                            </ConfirmButton>
                                                        </div>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })}
                                    </TableBody>
                                </Table>
                            </div>
                        </div>
                    )}
                </div>
            </AppShell>
        </>
    );
}
