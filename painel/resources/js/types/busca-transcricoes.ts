// Contrato do endpoint GET /painel/transcricoes/busca (JSON). Fixo: ver
// Docs/sistema/SISTEMA-BUSCA-TRANSCRICOES.md.

export type ModoBusca = 'hibrida' | 'semantica' | 'texto';

export type BuscaHit = {
    chunk_id: number;
    chunk_index: number;
    start_seconds: number | null;
    end_seconds: number | null;
    /** Já escapado pelo servidor; só <mark> é liberado. Nunca injetar como HTML. */
    snippet: string;
    score: number;
    /** Link interno (/painel/transcricoes/{id}?t=..&q=..) ou URL externa com tempo. */
    link: string;
};

export type BuscaResultado = {
    job_id: number;
    title: string | null;
    platform: string | null;
    source_url: string;
    duration_seconds: number | null;
    score: number;
    hits: BuscaHit[];
};

export type BuscaResposta = {
    query: string;
    mode: ModoBusca;
    /** Modo que de fato rodou; difere de `mode` quando a semântica caiu para texto. */
    mode_used: ModoBusca;
    degraded: boolean;
    results: BuscaResultado[];
};

/** Props opcionais do detalhe: para onde rolar e o que destacar. */
export type FocoDetalhe = { t: number | null; q: string | null };
