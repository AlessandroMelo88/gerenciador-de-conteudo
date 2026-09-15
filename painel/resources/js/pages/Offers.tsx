import { useState } from 'react';
import { Head, router, useForm, usePage } from '@inertiajs/react';
import {
    ArchiveIcon,
    CheckIcon,
    CopyIcon,
    ExternalLinkIcon,
    ImageOffIcon,
    PencilIcon,
    PlusIcon,
    RotateCcwIcon,
    Trash2Icon,
    XIcon,
} from 'lucide-react';
import { toast } from 'sonner';

import { ConfirmButton } from '@/components/confirm-button';
import { NicheCombobox, type Niche } from '@/components/niche-combobox';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { AppShell } from '@/layouts/app-shell';

type OfferStatus = 'draft' | 'approved' | 'rejected' | 'archived';

type Offer = {
    id: number;
    network: string;
    externalId: string | null;
    niche: string;
    title: string;
    description: string | null;
    productUrl: string | null;
    affiliateUrl: string;
    trackingUrl: string;
    imageUrl: string | null;
    priceCents: number | null;
    currency: string;
    commissionPercent: number | null;
    ctaText: string | null;
    copyShort: string | null;
    copyLong: string | null;
    aiProvider: string | null;
    status: OfferStatus;
    clicksCount: number;
    createdAt: string | null;
    approvedAt: string | null;
};

type TabKey = 'todos' | OfferStatus;

type PageProps = {
    offers: Offer[];
    counts: { todos: number; draft: number; approved: number; rejected: number; archived: number };
    niches: Niche[];
    activeStatus: TabKey;
    auth: { user: { name: string; email: string } | null };
};

const BASE_URL = '/painel/ofertas';

const TABS: { key: TabKey; label: string; empty: string }[] = [
    { key: 'draft', label: 'Rascunhos', empty: 'Nenhum rascunho. Rode o affiliate-worker para buscar ofertas.' },
    { key: 'approved', label: 'Aprovadas', empty: 'Nenhuma oferta aprovada ainda. Revise os rascunhos e aprove as que valem divulgar.' },
    { key: 'rejected', label: 'Rejeitadas', empty: 'Nenhuma oferta rejeitada.' },
    { key: 'archived', label: 'Arquivadas', empty: 'Nenhuma oferta arquivada.' },
    { key: 'todos', label: 'Todas', empty: 'Nenhuma oferta cadastrada. Rode o affiliate-worker ou crie uma manualmente.' },
];

const STATUS_LABEL: Record<OfferStatus, string> = {
    draft: 'Rascunho',
    approved: 'Aprovada',
    rejected: 'Rejeitada',
    archived: 'Arquivada',
};

const STATUS_CLASS: Record<OfferStatus, string> = {
    draft: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
    approved: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    rejected: 'bg-destructive/10 text-destructive border-destructive/20',
    archived: 'bg-muted text-muted-foreground border-border',
};

/** Canais de divulgação — o backend registra o `?c=` de cada clique. */
const SHARE_CHANNELS: { key: string | null; label: string }[] = [
    { key: null, label: 'Link direto' },
    { key: 'telegram', label: 'Telegram' },
    { key: 'youtube', label: 'YouTube' },
    { key: 'blog', label: 'Blog' },
];

const GRADIENT = { background: 'linear-gradient(160deg,#FF6A55,#E23C33)', color: '#fff' };

function formatPrice(cents: number | null, currency: string): string {
    if (cents === null) return '—';
    try {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: currency || 'BRL' }).format(cents / 100);
    } catch {
        // Moeda inválida vinda da rede não pode derrubar a tabela inteira.
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);
    }
}

function timeAgo(iso: string | null): string {
    if (!iso) return '—';
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return '—';

    const seconds = Math.round((date.getTime() - Date.now()) / 1000);
    const rtf = new Intl.RelativeTimeFormat('pt-BR', { numeric: 'auto' });
    const steps: [Intl.RelativeTimeFormatUnit, number][] = [
        ['year', 31536000],
        ['month', 2592000],
        ['day', 86400],
        ['hour', 3600],
        ['minute', 60],
    ];
    for (const [unit, size] of steps) {
        if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
    }
    return 'agora';
}

/** Acrescenta `?c=<canal>` preservando query string que o link já tenha. */
function withChannel(url: string, channel: string | null): string {
    if (!channel) return url;
    try {
        const parsed = new URL(url, window.location.origin);
        parsed.searchParams.set('c', channel);
        return parsed.toString();
    } catch {
        return `${url}${url.includes('?') ? '&' : '?'}c=${encodeURIComponent(channel)}`;
    }
}

/**
 * Clipboard API só existe em contexto seguro (https/localhost). O painel pode
 * ser aberto por http na rede, então cai para o textarea + execCommand.
 */
async function copyToClipboard(text: string, successMessage: string) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
        } else {
            const el = document.createElement('textarea');
            el.value = text;
            el.setAttribute('readonly', '');
            el.style.position = 'fixed';
            el.style.opacity = '0';
            document.body.appendChild(el);
            el.select();
            const ok = document.execCommand('copy');
            document.body.removeChild(el);
            if (!ok) throw new Error('execCommand falhou');
        }
        toast.success(successMessage);
    } catch {
        toast.error('Não foi possível copiar. Copie manualmente: ' + text);
    }
}

/** Toast a partir do flash do backend, com texto padrão se ele não mandar nada. */
function flashToast(page: { props: Record<string, unknown> }, fallback: string) {
    const flash = page.props.flash as { success?: string | null; error?: string | null } | undefined;
    if (flash?.error) toast.error(flash.error);
    else toast.success(flash?.success || fallback);
}

function firstError(errors: Record<string, string>): string {
    return Object.values(errors)[0] ?? 'Erro ao salvar a oferta';
}

function StatusBadge({ status }: { status: OfferStatus }) {
    return (
        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${STATUS_CLASS[status]}`}>
            {STATUS_LABEL[status]}
        </span>
    );
}

function OfferThumb({ offer, size = 'sm' }: { offer: Offer; size?: 'sm' | 'lg' }) {
    const [broken, setBroken] = useState(false);
    const box = size === 'lg' ? 'w-20 h-20 rounded-xl' : 'w-11 h-11 rounded-lg';

    if (!offer.imageUrl || broken) {
        return (
            <span className={`${box} grid place-items-center bg-muted text-muted-foreground shrink-0 border border-border`}>
                <ImageOffIcon className="w-4 h-4" />
            </span>
        );
    }
    return (
        <img
            src={offer.imageUrl}
            alt=""
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setBroken(true)}
            className={`${box} object-cover shrink-0 border border-border bg-muted`}
        />
    );
}

/** Dropdown com o link rastreável puro e as variantes por canal. */
function CopyLinkMenu({ offer, label = 'Copiar link' }: { offer: Offer; label?: string }) {
    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="h-8 px-2.5 text-xs gap-1.5">
                    <CopyIcon className="w-3.5 h-3.5" /> {label}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuLabel className="text-xs">Link rastreável</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {SHARE_CHANNELS.map((ch) => (
                    <DropdownMenuItem
                        key={ch.label}
                        onSelect={() =>
                            copyToClipboard(
                                withChannel(offer.trackingUrl, ch.key),
                                ch.key ? `Link para ${ch.label} copiado` : 'Link rastreável copiado',
                            )
                        }
                    >
                        {ch.label}
                        {ch.key && <span className="ml-auto font-mono text-[10px] text-muted-foreground">?c={ch.key}</span>}
                    </DropdownMenuItem>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

function CreateOfferDialog({ niches }: { niches: Niche[] }) {
    const [open, setOpen] = useState(false);
    const { data, setData, post, processing, errors, reset, clearErrors } = useForm({
        title: '',
        affiliate_url: '',
        niche: niches[0]?.slug ?? '',
        product_url: '',
        cta_text: '',
        copy_short: '',
        copy_long: '',
    });

    function submit(e: React.FormEvent) {
        e.preventDefault();
        post(BASE_URL, {
            preserveScroll: true,
            onSuccess: (page) => {
                setOpen(false);
                reset();
                flashToast(page, 'Oferta criada como rascunho');
            },
            onError: () => toast.error('Erro ao criar oferta'),
        });
    }

    return (
        <Dialog
            open={open}
            onOpenChange={(value) => {
                setOpen(value);
                if (!value) clearErrors();
            }}
        >
            <DialogTrigger asChild>
                <Button style={GRADIENT} className="shadow-sm hover:brightness-105">
                    <PlusIcon className="w-4 h-4 mr-1.5" /> Nova oferta
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="font-display font-bold">Nova oferta</DialogTitle>
                </DialogHeader>
                <form onSubmit={submit} className="space-y-4">
                    <Field>
                        <FieldLabel htmlFor="new-offer-title">Título</FieldLabel>
                        <Input
                            id="new-offer-title"
                            value={data.title}
                            onChange={(e) => setData('title', e.target.value)}
                            required
                        />
                        {errors.title && <p className="text-xs text-destructive">{errors.title}</p>}
                    </Field>

                    <Field>
                        <FieldLabel htmlFor="new-offer-affiliate">Link de afiliado</FieldLabel>
                        <Input
                            id="new-offer-affiliate"
                            type="url"
                            value={data.affiliate_url}
                            onChange={(e) => setData('affiliate_url', e.target.value)}
                            placeholder="https://…"
                            required
                        />
                        {errors.affiliate_url && <p className="text-xs text-destructive">{errors.affiliate_url}</p>}
                    </Field>

                    <Field>
                        <FieldLabel>Nicho</FieldLabel>
                        <NicheCombobox niches={niches} value={data.niche} onChange={(val) => setData('niche', val)} />
                        {errors.niche && <p className="text-xs text-destructive">{errors.niche}</p>}
                    </Field>

                    <Field>
                        <FieldLabel htmlFor="new-offer-product">Página do produto (opcional)</FieldLabel>
                        <Input
                            id="new-offer-product"
                            type="url"
                            value={data.product_url}
                            onChange={(e) => setData('product_url', e.target.value)}
                            placeholder="https://…"
                        />
                        {errors.product_url && <p className="text-xs text-destructive">{errors.product_url}</p>}
                    </Field>

                    <Field>
                        <FieldLabel htmlFor="new-offer-cta">Chamada (CTA, opcional)</FieldLabel>
                        <Input
                            id="new-offer-cta"
                            value={data.cta_text}
                            onChange={(e) => setData('cta_text', e.target.value)}
                            placeholder="Ex.: Garanta o seu com desconto"
                        />
                        {errors.cta_text && <p className="text-xs text-destructive">{errors.cta_text}</p>}
                    </Field>

                    <Field>
                        <FieldLabel htmlFor="new-offer-short">Texto curto (opcional)</FieldLabel>
                        <Textarea
                            id="new-offer-short"
                            rows={3}
                            value={data.copy_short}
                            onChange={(e) => setData('copy_short', e.target.value)}
                        />
                        {errors.copy_short && <p className="text-xs text-destructive">{errors.copy_short}</p>}
                    </Field>

                    <Field>
                        <FieldLabel htmlFor="new-offer-long">Texto longo (opcional)</FieldLabel>
                        <Textarea
                            id="new-offer-long"
                            rows={5}
                            value={data.copy_long}
                            onChange={(e) => setData('copy_long', e.target.value)}
                        />
                        {errors.copy_long && <p className="text-xs text-destructive">{errors.copy_long}</p>}
                    </Field>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            Cancelar
                        </Button>
                        <Button type="submit" disabled={processing} style={GRADIENT}>
                            Salvar oferta
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

/**
 * Formulário de revisão. Montado com `key={offer.id}` para o useForm nascer
 * com os valores da oferta aberta, sem sincronizar estado na mão.
 */
function OfferEditForm({ offer, niches, onDone }: { offer: Offer; niches: Niche[]; onDone: () => void }) {
    const { data, setData, put, processing, errors, isDirty } = useForm({
        title: offer.title,
        niche: offer.niche,
        cta_text: offer.ctaText ?? '',
        copy_short: offer.copyShort ?? '',
        copy_long: offer.copyLong ?? '',
        affiliate_url: offer.affiliateUrl,
    });

    const isApproved = offer.status === 'approved';

    function submit(e: React.FormEvent) {
        e.preventDefault();
        put(`${BASE_URL}/${offer.id}`, {
            preserveScroll: true,
            onSuccess: (page) => {
                flashToast(page, 'Oferta atualizada');
                onDone();
            },
            onError: (errs) => toast.error(firstError(errs)),
        });
    }

    /** Texto curto (o que está no formulário, mesmo não salvo) + link do canal. */
    function copyShortWithLink(channel: string | null, label: string) {
        const link = withChannel(offer.trackingUrl, channel);
        const text = data.copy_short.trim() ? `${data.copy_short.trim()}\n\n${link}` : link;
        copyToClipboard(text, `Texto curto + link (${label}) copiado`);
    }

    return (
        <form onSubmit={submit} className="flex flex-1 flex-col min-h-0">
            <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-5">
                {/* Resumo somente leitura do que veio do worker */}
                <div className="flex gap-3 rounded-xl border border-border bg-muted/30 p-3">
                    <OfferThumb offer={offer} size="lg" />
                    <div className="min-w-0 flex-1 space-y-1.5 text-xs">
                        <div className="flex flex-wrap items-center gap-1.5">
                            <StatusBadge status={offer.status} />
                            <Badge variant="outline" className="text-[11px]">
                                {offer.network}
                            </Badge>
                            {offer.aiProvider && (
                                <Badge variant="secondary" className="text-[11px]">
                                    IA: {offer.aiProvider}
                                </Badge>
                            )}
                        </div>
                        <div className="text-foreground">
                            <span className="font-semibold">{formatPrice(offer.priceCents, offer.currency)}</span>
                            {offer.commissionPercent !== null && (
                                <span className="text-muted-foreground"> · comissão {offer.commissionPercent}%</span>
                            )}
                            <span className="text-muted-foreground"> · {offer.clicksCount} cliques</span>
                        </div>
                        <div className="flex flex-wrap gap-3">
                            {offer.productUrl && (
                                <a
                                    href={offer.productUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-primary hover:underline"
                                >
                                    Produto <ExternalLinkIcon className="w-3 h-3" />
                                </a>
                            )}
                            <a
                                href={offer.affiliateUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-primary hover:underline"
                            >
                                Link de afiliado <ExternalLinkIcon className="w-3 h-3" />
                            </a>
                        </div>
                        {offer.externalId && (
                            <div className="font-mono text-[10.5px] text-muted-foreground truncate">
                                ID na rede: {offer.externalId}
                            </div>
                        )}
                    </div>
                </div>

                {offer.description && (
                    <p className="text-xs text-muted-foreground whitespace-pre-line line-clamp-6">{offer.description}</p>
                )}

                <Field>
                    <FieldLabel htmlFor="edit-offer-title">Título</FieldLabel>
                    <Input id="edit-offer-title" value={data.title} onChange={(e) => setData('title', e.target.value)} required />
                    {errors.title && <p className="text-xs text-destructive">{errors.title}</p>}
                </Field>

                <Field>
                    <FieldLabel>Nicho</FieldLabel>
                    <NicheCombobox niches={niches} value={data.niche} onChange={(val) => setData('niche', val)} />
                    {errors.niche && <p className="text-xs text-destructive">{errors.niche}</p>}
                </Field>

                <Field>
                    <FieldLabel htmlFor="edit-offer-cta">Chamada (CTA)</FieldLabel>
                    <Input id="edit-offer-cta" value={data.cta_text} onChange={(e) => setData('cta_text', e.target.value)} />
                    {errors.cta_text && <p className="text-xs text-destructive">{errors.cta_text}</p>}
                </Field>

                <Field>
                    <FieldLabel htmlFor="edit-offer-short">Texto curto — Telegram / comentário fixado</FieldLabel>
                    <Textarea
                        id="edit-offer-short"
                        rows={4}
                        value={data.copy_short}
                        onChange={(e) => setData('copy_short', e.target.value)}
                    />
                    {errors.copy_short && <p className="text-xs text-destructive">{errors.copy_short}</p>}
                </Field>

                <Field>
                    <FieldLabel htmlFor="edit-offer-long">Texto longo — descrição / blog</FieldLabel>
                    <Textarea
                        id="edit-offer-long"
                        rows={7}
                        value={data.copy_long}
                        onChange={(e) => setData('copy_long', e.target.value)}
                    />
                    {errors.copy_long && <p className="text-xs text-destructive">{errors.copy_long}</p>}
                </Field>

                <Field>
                    <FieldLabel htmlFor="edit-offer-affiliate">Link de afiliado</FieldLabel>
                    <Input
                        id="edit-offer-affiliate"
                        type="url"
                        value={data.affiliate_url}
                        onChange={(e) => setData('affiliate_url', e.target.value)}
                        required
                    />
                    {errors.affiliate_url && <p className="text-xs text-destructive">{errors.affiliate_url}</p>}
                </Field>

                {!isApproved && (
                    <p className="text-[11px] text-muted-foreground">
                        O link rastreável só redireciona depois que a oferta é aprovada.
                    </p>
                )}
            </div>

            <SheetFooter className="border-t border-border flex-row flex-wrap justify-between gap-2">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button type="button" variant="outline" size="sm" disabled={!isApproved} className="gap-1.5">
                            <CopyIcon className="w-3.5 h-3.5" /> Copiar texto curto + link
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start">
                        <DropdownMenuLabel className="text-xs">Link anexado ao final</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {SHARE_CHANNELS.map((ch) => (
                            <DropdownMenuItem key={ch.label} onSelect={() => copyShortWithLink(ch.key, ch.label)}>
                                {ch.label}
                            </DropdownMenuItem>
                        ))}
                    </DropdownMenuContent>
                </DropdownMenu>
                <Button type="submit" size="sm" disabled={processing || !isDirty} style={GRADIENT}>
                    Salvar
                </Button>
            </SheetFooter>
        </form>
    );
}

export default function Offers() {
    const { props } = usePage<PageProps>();
    const { offers, counts, niches, activeStatus, auth } = props;

    // Guarda só o id: a oferta exibida vem sempre das props mais recentes.
    const [editingId, setEditingId] = useState<number | null>(null);
    const editing = offers.find((o) => o.id === editingId) ?? null;

    const nicheLabel = (slug: string) => niches.find((n) => n.slug === slug)?.label ?? slug;
    const currentTab = TABS.find((t) => t.key === activeStatus) ?? TABS[0];

    const changeTab = (status: TabKey) => {
        router.get(BASE_URL, { status }, { preserveState: true, preserveScroll: true });
    };

    const setStatus = (offer: Offer, status: OfferStatus, message: string) => {
        router.put(
            `${BASE_URL}/${offer.id}`,
            { status },
            {
                preserveScroll: true,
                onSuccess: (page) => flashToast(page, message),
                onError: (errs) => toast.error(firstError(errs)),
            },
        );
    };

    const destroy = (offer: Offer) => {
        router.delete(`${BASE_URL}/${offer.id}`, {
            preserveScroll: true,
            onSuccess: (page) => {
                if (editingId === offer.id) setEditingId(null);
                flashToast(page, 'Oferta removida');
            },
            onError: (errs) => toast.error(firstError(errs)),
        });
    };

    return (
        <>
            <Head title="Ofertas" />
            <AppShell
                title="Ofertas"
                user={auth.user}
                description="Ofertas de afiliados chegam como rascunho do worker local. Só as aprovadas geram link rastreável."
                actions={<CreateOfferDialog niches={niches} />}
            >
                <div className="flex flex-col gap-4">
                    {/* Tabs de status com contagem vinda do backend */}
                    <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-2xl border border-border bg-card w-fit">
                        {TABS.map((tab) => (
                            <button
                                key={tab.key}
                                type="button"
                                onClick={() => changeTab(tab.key)}
                                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                                    activeStatus === tab.key
                                        ? 'bg-primary text-primary-foreground shadow-sm'
                                        : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                                }`}
                            >
                                <span>{tab.label}</span>
                                <span className="rounded-md bg-muted text-muted-foreground px-1.5 py-0.5 text-[10px] font-mono">
                                    {counts[tab.key]}
                                </span>
                            </button>
                        ))}
                    </div>

                    {offers.length === 0 ? (
                        <div className="rounded-2xl border border-dashed border-border bg-card px-6 py-12 text-center text-sm text-muted-foreground">
                            {currentTab.empty}
                        </div>
                    ) : (
                        <div className="rounded-2xl border border-border bg-card overflow-hidden shadow-xs">
                            <div className="overflow-x-auto">
                                <Table className="w-full text-xs">
                                    <TableHeader className="bg-muted/40">
                                        <TableRow>
                                            <TableHead className="px-5 py-3 font-semibold">Oferta</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold">Preço</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold text-right">Cliques</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold hidden lg:table-cell">IA</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold hidden md:table-cell">Criada</TableHead>
                                            <TableHead className="px-5 py-3 font-semibold text-right">Ações</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {offers.map((offer) => (
                                            <TableRow key={offer.id} className="hover:bg-muted/30">
                                                <TableCell className="px-5 py-3">
                                                    <div className="flex items-center gap-3 min-w-[240px] max-w-[420px]">
                                                        <OfferThumb offer={offer} />
                                                        <div className="min-w-0">
                                                            <button
                                                                type="button"
                                                                onClick={() => setEditingId(offer.id)}
                                                                className="block w-full text-left font-semibold text-foreground truncate hover:text-primary"
                                                                title={offer.title}
                                                            >
                                                                {offer.title}
                                                            </button>
                                                            <div className="mt-1 flex flex-wrap items-center gap-1.5">
                                                                <Badge variant="outline" className="text-[10.5px]">
                                                                    {offer.network}
                                                                </Badge>
                                                                <span className="text-[11px] text-muted-foreground">
                                                                    {nicheLabel(offer.niche)}
                                                                </span>
                                                                {activeStatus === 'todos' && <StatusBadge status={offer.status} />}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="px-5 py-3 whitespace-nowrap">
                                                    <div className="font-semibold text-foreground">
                                                        {formatPrice(offer.priceCents, offer.currency)}
                                                    </div>
                                                    <div className="text-[11px] text-muted-foreground">
                                                        {offer.commissionPercent !== null
                                                            ? `${offer.commissionPercent}% comissão`
                                                            : 'comissão —'}
                                                    </div>
                                                </TableCell>
                                                <TableCell className="px-5 py-3 text-right font-mono">{offer.clicksCount}</TableCell>
                                                <TableCell className="px-5 py-3 hidden lg:table-cell text-muted-foreground">
                                                    {offer.aiProvider ?? 'manual'}
                                                </TableCell>
                                                <TableCell
                                                    className="px-5 py-3 hidden md:table-cell text-muted-foreground whitespace-nowrap"
                                                    title={offer.createdAt ?? undefined}
                                                >
                                                    {timeAgo(offer.createdAt)}
                                                </TableCell>
                                                <TableCell className="px-5 py-3 text-right">
                                                    <div className="flex items-center justify-end gap-1.5">
                                                        {offer.status === 'draft' && (
                                                            <>
                                                                <Button
                                                                    size="sm"
                                                                    className="h-8 px-2.5 text-xs gap-1 bg-emerald-600 text-white hover:bg-emerald-700"
                                                                    onClick={() => setStatus(offer, 'approved', 'Oferta aprovada')}
                                                                >
                                                                    <CheckIcon className="w-3.5 h-3.5" /> Aprovar
                                                                </Button>
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="h-8 px-2.5 text-xs gap-1"
                                                                    onClick={() => setStatus(offer, 'rejected', 'Oferta rejeitada')}
                                                                >
                                                                    <XIcon className="w-3.5 h-3.5" /> Rejeitar
                                                                </Button>
                                                            </>
                                                        )}
                                                        {offer.status === 'approved' && (
                                                            <>
                                                                <CopyLinkMenu offer={offer} />
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="h-8 px-2.5 text-xs gap-1"
                                                                    onClick={() => setStatus(offer, 'archived', 'Oferta arquivada')}
                                                                >
                                                                    <ArchiveIcon className="w-3.5 h-3.5" /> Arquivar
                                                                </Button>
                                                            </>
                                                        )}
                                                        {(offer.status === 'rejected' || offer.status === 'archived') && (
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                className="h-8 px-2.5 text-xs gap-1"
                                                                onClick={() => setStatus(offer, 'draft', 'Oferta voltou para rascunho')}
                                                            >
                                                                <RotateCcwIcon className="w-3.5 h-3.5" /> Voltar para rascunho
                                                            </Button>
                                                        )}
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="h-8 w-8 p-0"
                                                            onClick={() => setEditingId(offer.id)}
                                                            title="Revisar e editar"
                                                            aria-label="Revisar e editar"
                                                        >
                                                            <PencilIcon className="w-3.5 h-3.5" />
                                                        </Button>
                                                        {/* ConfirmButton não aceita className; tamanho vem do size */}
                                                        <ConfirmButton
                                                            variant="destructive"
                                                            size="icon-sm"
                                                            description={`Apagar a oferta "${offer.title}"? Os cliques registrados dela também deixam de aparecer.`}
                                                            onConfirm={() => destroy(offer)}
                                                        >
                                                            <Trash2Icon className="w-3.5 h-3.5" />
                                                        </ConfirmButton>
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </div>
                        </div>
                    )}
                </div>

                <Sheet open={editing !== null} onOpenChange={(open) => !open && setEditingId(null)}>
                    <SheetContent side="right" className="w-full data-[side=right]:sm:max-w-xl p-0 gap-0">
                        {editing && (
                            <>
                                <SheetHeader className="border-b border-border pr-12">
                                    <SheetTitle className="font-display font-bold truncate">{editing.title}</SheetTitle>
                                    <SheetDescription>Revise os textos gerados antes de divulgar.</SheetDescription>
                                </SheetHeader>
                                <OfferEditForm
                                    key={editing.id}
                                    offer={editing}
                                    niches={niches}
                                    onDone={() => setEditingId(null)}
                                />
                            </>
                        )}
                    </SheetContent>
                </Sheet>
            </AppShell>
        </>
    );
}
