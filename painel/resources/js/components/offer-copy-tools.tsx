import { useRef, useState, type ReactNode } from 'react';
import { InfoIcon, Loader2Icon, SparklesIcon } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

export type OfferCopy = { cta_text: string; copy_short: string; copy_long: string };

/** Ícone "i" com balão explicativo: abre ao passar o mouse e também ao clicar (toque no celular). */
export function InfoHint({ title, children }: { title: string; children: ReactNode }) {
    const [open, setOpen] = useState(false);
    const pinned = useRef(false);

    return (
        <Popover
            open={open}
            onOpenChange={(value) => {
                pinned.current = value;
                setOpen(value);
            }}
        >
            <PopoverTrigger
                type="button"
                aria-label={title}
                className="inline-flex size-4 items-center justify-center rounded-full text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                onMouseEnter={() => setOpen(true)}
                onMouseLeave={() => !pinned.current && setOpen(false)}
                onClick={(e) => {
                    // Clique fixa o balão aberto; clicar de novo fecha.
                    e.preventDefault();
                    pinned.current = !pinned.current;
                    setOpen(pinned.current);
                }}
            >
                <InfoIcon className="size-3.5" />
            </PopoverTrigger>
            <PopoverContent side="top" align="end" className="w-72 text-sm" onOpenAutoFocus={(e) => e.preventDefault()}>
                <p className="mb-1 font-semibold">{title}</p>
                <div className="space-y-1.5 text-muted-foreground">{children}</div>
            </PopoverContent>
        </Popover>
    );
}

export function CtaHint() {
    return (
        <InfoHint title="O que é CTA?">
            <p>
                <strong className="text-foreground">CTA</strong> (call to action, ou chamada para ação) é a frase curta que diz
                ao leitor o que fazer agora, normalmente no botão ou logo antes do link.
            </p>
            <p>Bons exemplos: “Garanta o seu”, “Ver oferta”, “Quero conhecer”. Até 60 caracteres, um verbo no começo.</p>
        </InfoHint>
    );
}

type Source = { affiliateUrl: string; productUrl?: string; title?: string; niche?: string };

/**
 * Lê a página do produto (ou o link de afiliado) no servidor e preenche CTA + textos
 * com copy de venda. Substitui o que estiver escrito, com "Desfazer" no aviso.
 */
export function GenerateCopyButton({
    source,
    current,
    onGenerated,
}: {
    source: Source;
    current: OfferCopy;
    onGenerated: (copy: OfferCopy, provider: string | null) => void;
}) {
    const [loading, setLoading] = useState(false);
    const hasUrl = Boolean(source.productUrl?.trim() || source.affiliateUrl.trim());

    async function generate() {
        setLoading(true);
        try {
            const response = await fetch('/painel/ofertas/gerar-copy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Accept: 'application/json',
                    'X-CSRF-TOKEN': (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement)?.content || '',
                },
                body: JSON.stringify({
                    affiliate_url: source.affiliateUrl.trim() || null,
                    product_url: source.productUrl?.trim() || null,
                    title: source.title?.trim() || null,
                    niche: source.niche || null,
                }),
            });
            const body = await response.json().catch(() => ({}));

            if (!response.ok) {
                const validation = body.errors ? (Object.values(body.errors)[0] as string[])[0] : null;
                toast.error(validation || body.message || 'Não foi possível gerar o texto');
                return;
            }

            const previous = { ...current };
            const hadText = Boolean(previous.cta_text || previous.copy_short || previous.copy_long);
            onGenerated({ cta_text: body.cta_text, copy_short: body.copy_short, copy_long: body.copy_long }, body.provider);
            toast.success('Texto gerado com IA. Revise antes de salvar.', {
                action: hadText ? { label: 'Desfazer', onClick: () => onGenerated(previous, null) } : undefined,
            });
        } catch {
            toast.error('Falha de rede ao gerar o texto');
        } finally {
            setLoading(false);
        }
    }

    return (
        <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={generate}
            disabled={loading || !hasUrl}
            title={hasUrl ? 'Gera CTA, texto curto e texto longo a partir da página' : 'Preencha o link de afiliado ou a página do produto'}
            className="h-7 gap-1.5 text-xs"
        >
            {loading ? <Loader2Icon className="size-3.5 animate-spin" /> : <SparklesIcon className="size-3.5 text-violet-500" />}
            {loading ? 'Gerando…' : 'Gerar com IA'}
        </Button>
    );
}
