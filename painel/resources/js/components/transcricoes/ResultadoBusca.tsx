import { Fragment } from 'react';
import { Link } from '@inertiajs/react';
import { ClockIcon } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import type { BuscaHit, BuscaResultado } from '@/types/busca-transcricoes';

const ENTIDADES: Record<string, string> = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#039;': "'", '&#39;': "'" };

function decodificar(texto: string): string {
    return texto.replace(/&(amp|lt|gt|quot|#0?39);/g, (m) => ENTIDADES[m] ?? m);
}

/** 812.4 -> "13:32"; a partir de 1h -> "1:03:45". */
export function formatarTempo(segundos: number | null): string | null {
    if (segundos === null || segundos === undefined || Number.isNaN(segundos)) return null;
    const total = Math.max(0, Math.floor(segundos));
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const ss = String(total % 60).padStart(2, '0');
    return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${ss}` : `${m}:${ss}`;
}

/**
 * Quebra o snippet do servidor em texto e destaques. Só a tag <mark> é
 * reconhecida; qualquer outra coisa vira texto puro (o React escapa na
 * renderização). Não usa dangerouslySetInnerHTML.
 */
export function partesDoSnippet(snippet: string): { texto: string; destaque: boolean }[] {
    const partes: { texto: string; destaque: boolean }[] = [];
    const re = /<mark>([\s\S]*?)<\/mark>/g;
    let ultimo = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(snippet)) !== null) {
        if (m.index > ultimo) partes.push({ texto: decodificar(snippet.slice(ultimo, m.index)), destaque: false });
        partes.push({ texto: decodificar(m[1]), destaque: true });
        ultimo = m.index + m[0].length;
    }
    if (ultimo < snippet.length) partes.push({ texto: decodificar(snippet.slice(ultimo)), destaque: false });
    return partes;
}

export function Snippet({ texto }: { texto: string }) {
    return (
        <>
            {partesDoSnippet(texto).map((p, i) =>
                p.destaque ? (
                    <mark key={i} className="rounded-sm bg-yellow-300/40 px-0.5 text-foreground dark:bg-yellow-400/30">
                        {p.texto}
                    </mark>
                ) : (
                    <Fragment key={i}>{p.texto}</Fragment>
                ),
            )}
        </>
    );
}

function LinkDoTrecho({ hit, rotulo }: { hit: BuscaHit; rotulo: string }) {
    const tempo = formatarTempo(hit.start_seconds);
    const classe =
        'inline-flex shrink-0 items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium tabular-nums hover:bg-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring';
    const conteudo = (
        <>
            <ClockIcon className="size-3" aria-hidden />
            {tempo ?? 'Abrir'}
        </>
    );
    const aria = tempo ? `Abrir ${rotulo} em ${tempo}` : `Abrir ${rotulo}`;
    if (/^https?:\/\//i.test(hit.link)) {
        return (
            <a href={hit.link} target="_blank" rel="noreferrer noopener" className={classe} aria-label={aria}>
                {conteudo}
            </a>
        );
    }
    return (
        <Link href={hit.link} className={classe} aria-label={aria}>
            {conteudo}
        </Link>
    );
}

export function ResultadoBusca({ resultado }: { resultado: BuscaResultado }) {
    const titulo = resultado.title || resultado.source_url;
    const hits = resultado.hits.slice(0, 3);

    return (
        <article className="grid min-w-0 grid-cols-1 gap-2 border-b pb-4 last:border-b-0 last:pb-0" aria-label={titulo}>
            <div className="flex flex-wrap items-center gap-2">
                <Link href={`/painel/transcricoes/${resultado.job_id}`} className="min-w-0 truncate font-medium hover:underline">
                    {titulo}
                </Link>
                {resultado.platform && <Badge variant="secondary">{resultado.platform}</Badge>}
            </div>
            <ul className="grid grid-cols-1 gap-2">
                {hits.map((hit) => (
                    <li key={hit.chunk_id} className="flex items-start gap-3">
                        <LinkDoTrecho hit={hit} rotulo={titulo} />
                        <p className="min-w-0 text-sm leading-relaxed text-muted-foreground">
                            <Snippet texto={hit.snippet} />
                        </p>
                    </li>
                ))}
            </ul>
        </article>
    );
}
