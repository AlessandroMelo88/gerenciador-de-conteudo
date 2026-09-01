import { useEffect } from 'react';
import { Head, useForm, usePage } from '@inertiajs/react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Field, FieldLabel } from '@/components/ui/field';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';
import { AppShell } from '@/layouts/app-shell';

type PageProps = {
    auth: { user: { name: string; email: string } | null };
    flash: { success: string | null; error: string | null };
};

export default function ProcessVideo() {
    const { props } = usePage<PageProps>();
    const { auth, flash } = props;
    const { data, setData, post, processing, reset } = useForm({
        format: 'curto',
        urls: '',
    });

    useEffect(() => {
        if (flash?.success) toast.success(flash.success);
        if (flash?.error) toast.error(flash.error, { style: { whiteSpace: 'pre-line' } });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [flash?.success, flash?.error]);

    function submit(e: React.FormEvent) {
        e.preventDefault();
        post('/painel/processar-video', {
            preserveScroll: true,
            onSuccess: () => reset('urls'),
        });
    }

    return (
        <>
            <Head title="Processar Vídeo" />
            <AppShell
                title="Processar Vídeo Manualmente"
                user={auth.user}
                description="Enfileira URLs na fila normal do pipeline (download → transcrição → seleção → corte)."
            >
                <Card className="max-w-2xl">
                    <CardContent className="pt-6">
                        <form onSubmit={submit} className="grid gap-6">
                            <Field>
                                <FieldLabel>Formato</FieldLabel>
                                <RadioGroup
                                    value={data.format}
                                    onValueChange={(v) => setData('format', v)}
                                    className="gap-3"
                                >
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem value="curto" id="curto" />
                                        <Label htmlFor="curto">
                                            Curto (shorts — vários momentos de 15s a 3min, vertical)
                                        </Label>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem value="longo" id="longo" />
                                        <Label htmlFor="longo">
                                            Longo (1 segmento de 10 a 20min — análise/entrevista, horizontal)
                                        </Label>
                                    </div>
                                </RadioGroup>
                            </Field>
                            <Field>
                                <FieldLabel htmlFor="urls">URLs do YouTube (uma por linha)</FieldLabel>
                                <Textarea
                                    id="urls"
                                    rows={6}
                                    placeholder={
                                        'https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...'
                                    }
                                    value={data.urls}
                                    onChange={(e) => setData('urls', e.target.value)}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Cole um ou mais links de vídeos do YouTube, um por linha. Cada vídeo entra na
                                    fila normal do pipeline no formato escolhido acima.
                                </p>
                            </Field>
                            <div>
                                <Button type="submit" disabled={processing}>
                                    Enfileirar vídeo(s)
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            </AppShell>
        </>
    );
}
