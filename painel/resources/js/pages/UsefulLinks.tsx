import * as React from 'react';
import { Head, usePage } from '@inertiajs/react';
import { CalculatorIcon, ArrowUpRightIcon } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AppShell } from '@/layouts/app-shell';

type PageProps = {
    auth: { user: { name: string; email: string } | null };
    categories: Array<{
        name: string;
        description: string;
        links: Array<{
            title: string;
            url: string;
            description: string;
            badge?: string;
            tag: string;
        }>;
    }>;
};

export default function UsefulLinks({ categories }: PageProps) {
    const { props } = usePage<PageProps>();

    // Calculadora Rápida Interativa
    const [views, setViews] = React.useState<number>(200000);
    const [format, setFormat] = React.useState<'long' | 'short'>('long');
    const [customRpm, setCustomRpm] = React.useState<number>(2.0);

    const exchangeRate = 5.65; // Cotação USD -> BRL aproximada

    const rpm = format === 'long' ? customRpm || 2.0 : 0.035;

    const estimatedUSD = (views / 1000) * rpm;
    const estimatedBRL = estimatedUSD * exchangeRate;

    return (
        <>
            <Head title="Links Úteis & Calculadoras" />
            <AppShell
                title="Links Úteis & Ferramentas"
                user={props.auth.user}
                description="Calculadoras de ganhos por visualizações, painéis do YouTube Analytics, AdSense e consoles de IA."
                withToaster={false}
            >
                <div className="mx-auto flex w-full max-w-5xl flex-col gap-8 pb-12">
                    {/* Widget: Calculadora de Ganhos Integrada */}
                    <Card className="overflow-hidden border-primary/30 bg-gradient-to-br from-card via-card to-primary/5 shadow-sm">
                        <CardHeader className="border-b border-border/60 bg-muted/20 p-4 pb-3 md:p-6">
                            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                                <div className="flex items-center gap-3">
                                    <div className="flex size-10 items-center justify-center rounded-xl bg-primary/20 text-primary">
                                        <CalculatorIcon className="size-5" />
                                    </div>
                                    <div>
                                        <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                                            Simulador Rápido de Faturamento YouTube
                                            <Badge variant="secondary" className="font-mono text-[11px]">
                                                Estimativa RPM
                                            </Badge>
                                        </CardTitle>
                                        <CardDescription className="text-xs">
                                            Calcule o faturamento estimado com base no volume mensal de visualizações e
                                            formato de vídeo.
                                        </CardDescription>
                                    </div>
                                </div>
                                <Tabs
                                    value={format}
                                    onValueChange={(val) => {
                                        setFormat(val as 'long' | 'short');
                                        if (val === 'long') setCustomRpm(2.0);
                                    }}
                                    className="w-full sm:w-auto"
                                >
                                    <TabsList className="grid w-full grid-cols-2">
                                        <TabsTrigger value="long" className="text-xs">
                                            Vídeos Longos (7-20m)
                                        </TabsTrigger>
                                        <TabsTrigger value="short" className="text-xs">
                                            Shorts (9:16)
                                        </TabsTrigger>
                                    </TabsList>
                                </Tabs>
                            </div>
                        </CardHeader>
                        <CardContent className="grid grid-cols-1 items-center gap-6 p-4 md:grid-cols-12 md:p-6">
                            <div className="flex flex-col gap-4 md:col-span-7">
                                <div className="space-y-1.5">
                                    <Label className="flex items-center justify-between text-xs font-semibold text-foreground">
                                        <span>Visualizações Mensais:</span>
                                        <span className="font-mono font-bold text-primary">
                                            {views.toLocaleString('pt-BR')} views
                                        </span>
                                    </Label>
                                    <div className="flex gap-2">
                                        <Input
                                            type="number"
                                            value={views}
                                            onChange={(e) => setViews(Math.max(0, parseInt(e.target.value) || 0))}
                                            step={10000}
                                            className="h-10 font-mono text-sm"
                                        />
                                        <div className="flex gap-1">
                                            {[50000, 200000, 500000, 1000000].map((quickViews) => (
                                                <Button
                                                    key={quickViews}
                                                    type="button"
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => setViews(quickViews)}
                                                    className="h-10 px-2.5 font-mono text-xs"
                                                >
                                                    {quickViews >= 1000000
                                                        ? `${quickViews / 1000000}M`
                                                        : `${quickViews / 1000}k`}
                                                </Button>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {format === 'long' ? (
                                    <div className="space-y-1.5">
                                        <Label className="flex items-center justify-between text-xs font-semibold text-foreground">
                                            <span>RPM Estimado por 1.000 visualizações (USD):</span>
                                            <span className="font-mono text-muted-foreground">
                                                ${customRpm.toFixed(2)}
                                            </span>
                                        </Label>
                                        <div className="flex items-center gap-2">
                                            <Input
                                                type="number"
                                                step={0.1}
                                                min={0.5}
                                                max={10}
                                                value={customRpm}
                                                onChange={(e) => setCustomRpm(parseFloat(e.target.value) || 1.5)}
                                                className="h-9 w-28 font-mono text-sm"
                                            />
                                            <span className="text-xs text-muted-foreground">
                                                (Média Brasil para Futebol/Política: $1.50 a $3.50)
                                            </span>
                                        </div>
                                    </div>
                                ) : (
                                    <p className="rounded-lg border border-border bg-muted/40 p-2.5 text-xs text-muted-foreground">
                                        💡 <strong>YouTube Shorts:</strong> O pool de receita no Brasil remunera em
                                        média <strong>$0.02 a $0.06</strong> por 1.000 visualizações. O objetivo
                                        principal do Shorts é gerar inscritos e tráfego rápido para o canal.
                                    </p>
                                )}
                            </div>

                            <div className="flex flex-col justify-center gap-3 rounded-xl border border-border bg-card p-5 shadow-2xs md:col-span-5">
                                <div className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
                                    Receita Estimada Mensal
                                </div>
                                <div className="flex flex-col">
                                    <div className="flex items-baseline gap-1">
                                        <span className="font-display text-3xl font-extrabold text-foreground">
                                            $
                                            {estimatedUSD.toLocaleString('en-US', {
                                                minimumFractionDigits: 2,
                                                maximumFractionDigits: 2,
                                            })}
                                        </span>
                                        <span className="text-xs font-semibold text-muted-foreground">USD</span>
                                    </div>
                                    <div className="mt-0.5 flex items-center gap-1 text-sm font-semibold text-emerald-500">
                                        <span>
                                            ≈ R${' '}
                                            {estimatedBRL.toLocaleString('pt-BR', {
                                                minimumFractionDigits: 2,
                                                maximumFractionDigits: 2,
                                            })}
                                        </span>
                                        <span className="text-[11px] font-normal text-muted-foreground">
                                            (cotação R$ 5,65)
                                        </span>
                                    </div>
                                </div>
                                <div className="mt-1 border-t border-border pt-2.5 text-[11px] text-muted-foreground">
                                    * Valores médios de referência. Para projeções avançadas de CPM/CTR por nicho,
                                    utilize as calculadoras abaixo.
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Categorias de Links */}
                    <div className="flex flex-col gap-8">
                        {categories.map((cat, idx) => (
                            <div key={idx} className="flex flex-col gap-3">
                                <div>
                                    <h3 className="flex items-center gap-2 text-base font-semibold text-foreground md:text-lg">
                                        {cat.name}
                                    </h3>
                                    <p className="text-xs text-muted-foreground">{cat.description}</p>
                                </div>

                                <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2 lg:grid-cols-3">
                                    {cat.links.map((link, linkIdx) => (
                                        <Card
                                            key={linkIdx}
                                            className="group flex flex-col justify-between border-border/80 bg-card/60 shadow-2xs transition-all hover:border-primary/40 hover:bg-card/90 hover:shadow-xs"
                                        >
                                            <CardHeader className="p-4 pb-2">
                                                <div className="flex items-start justify-between gap-2">
                                                    <CardTitle className="flex items-center gap-1.5 text-sm font-semibold text-foreground transition-colors group-hover:text-primary">
                                                        <span>{link.title}</span>
                                                    </CardTitle>
                                                    {link.badge && (
                                                        <Badge
                                                            variant="secondary"
                                                            className="shrink-0 py-0 text-[10.5px] font-medium"
                                                        >
                                                            {link.badge}
                                                        </Badge>
                                                    )}
                                                </div>
                                                <CardDescription className="mt-1 text-xs leading-relaxed">
                                                    {link.description}
                                                </CardDescription>
                                            </CardHeader>
                                            <CardFooter className="mt-3 flex items-center justify-between border-t border-border/40 p-4 pt-2">
                                                <Badge
                                                    variant="outline"
                                                    className="font-mono text-[10px] text-muted-foreground"
                                                >
                                                    {link.tag}
                                                </Badge>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    asChild
                                                    className="h-7 gap-1 px-2 text-xs font-medium text-primary hover:bg-primary/10 hover:text-primary"
                                                >
                                                    <a href={link.url} target="_blank" rel="noopener noreferrer">
                                                        <span>Acessar</span>
                                                        <ArrowUpRightIcon className="size-3.5" />
                                                    </a>
                                                </Button>
                                            </CardFooter>
                                        </Card>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </AppShell>
        </>
    );
}
