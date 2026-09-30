import { useState } from 'react';
import { AlertTriangleIcon, Loader2Icon, SearchIcon } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { BUSCA_MIN_CARACTERES, useBuscaTranscricoes } from '@/hooks/use-busca-transcricoes';
import type { ModoBusca } from '@/types/busca-transcricoes';
import { ResultadoBusca } from './ResultadoBusca';

const MODOS: { valor: ModoBusca; rotulo: string; dica: string }[] = [
    { valor: 'hibrida', rotulo: 'Híbrida', dica: 'Junta as duas: acha a palavra exata e também o sentido. Recomendada.' },
    { valor: 'semantica', rotulo: 'Semântica', dica: 'Busca pelo sentido, mesmo que a palavra não apareça.' },
    { valor: 'texto', rotulo: 'Texto', dica: 'Só a palavra escrita, sem acento e sem plural.' },
];

/**
 * Campo de busca + seletor de modo + resultados por trecho. Enquanto não há
 * consulta (menos de 2 caracteres), renderiza `children` (a lista normal).
 */
export function BuscaTranscricoes({ children }: { children: React.ReactNode }) {
    const [consulta, setConsulta] = useState('');
    const [modo, setModo] = useState<ModoBusca>('hibrida');
    const [tentativa, setTentativa] = useState(0);
    const estado = useBuscaTranscricoes(consulta, modo, tentativa);
    const ativa = consulta.trim().length >= BUSCA_MIN_CARACTERES;
    const resposta = estado.fase === 'ok' ? estado.resposta : estado.fase === 'carregando' ? estado.anterior : null;
    const carregando = estado.fase === 'carregando';
    const dicaDoModo = MODOS.find((m) => m.valor === modo)?.dica;

    return (
        <>
            <div className="grid grid-cols-1 gap-2">
                <div className="flex flex-col gap-2 sm:flex-row">
                    <div className="relative flex-1">
                        <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
                        <Input
                            type="search"
                            aria-label="Buscar nas transcrições"
                            placeholder="Buscar no que foi dito... (ex.: como validar uma oferta)"
                            className="pl-9"
                            value={consulta}
                            onChange={(e) => setConsulta(e.target.value)}
                        />
                    </div>
                    <ToggleGroup
                        type="single"
                        variant="outline"
                        size="sm"
                        value={modo}
                        onValueChange={(v) => v && setModo(v as ModoBusca)}
                        aria-label="Modo de busca"
                        className="self-start"
                    >
                        {MODOS.map((m) => (
                            <ToggleGroupItem key={m.valor} value={m.valor} title={m.dica} aria-label={`${m.rotulo}: ${m.dica}`}>
                                {m.rotulo}
                            </ToggleGroupItem>
                        ))}
                    </ToggleGroup>
                </div>
                <p className="text-xs text-muted-foreground">{dicaDoModo}</p>
            </div>

            {!ativa && children}

            {ativa && (
                <div className="grid grid-cols-1 gap-4" aria-busy={carregando}>
                    <p className="sr-only" role="status" aria-live="polite">
                        {carregando ? 'Buscando...' : resposta ? `${resposta.results.length} transcrições encontradas.` : ''}
                    </p>

                    {resposta?.degraded && (
                        <div
                            role="status"
                            className="flex items-start gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-800 dark:text-amber-300"
                        >
                            <AlertTriangleIcon className="mt-0.5 size-3.5 shrink-0" aria-hidden />
                            <span>Busca semântica indisponível; mostrando busca por texto.</span>
                        </div>
                    )}

                    {carregando && (!resposta || resposta.results.length === 0) && (
                        <p className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Loader2Icon className="size-4 animate-spin" aria-hidden /> Buscando...
                        </p>
                    )}

                    {estado.fase === 'erro' && (
                        <div role="alert" className="flex flex-wrap items-center gap-3 text-sm text-red-600">
                            <span>{estado.mensagem}</span>
                            <Button size="sm" variant="outline" onClick={() => setTentativa((n) => n + 1)}>
                                Tentar de novo
                            </Button>
                        </div>
                    )}

                    {resposta && resposta.results.length === 0 && !carregando && (
                        <p className="text-sm text-muted-foreground">
                            Nada encontrado para &ldquo;{resposta.query}&rdquo;.
                            {modo === 'texto' && ' Tente o modo Híbrida, que também entende o sentido da frase.'}
                        </p>
                    )}

                    {resposta && resposta.results.length > 0 && (
                        <div className={carregando ? 'grid grid-cols-1 gap-4 opacity-60 transition-opacity' : 'grid grid-cols-1 gap-4'}>
                            {resposta.results.map((r) => (
                                <ResultadoBusca key={r.job_id} resultado={r} />
                            ))}
                        </div>
                    )}
                </div>
            )}
        </>
    );
}
