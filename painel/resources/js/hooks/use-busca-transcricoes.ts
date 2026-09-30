import { useEffect, useRef, useState } from 'react';

import type { BuscaResposta, ModoBusca } from '@/types/busca-transcricoes';

export const BUSCA_MIN_CARACTERES = 2;
const DEBOUNCE_MS = 350;

export type EstadoBusca =
    | { fase: 'ociosa' }
    | { fase: 'carregando'; anterior: BuscaResposta | null }
    | { fase: 'ok'; resposta: BuscaResposta }
    | { fase: 'erro'; mensagem: string };

/**
 * Busca nas transcrições com debounce. Cada nova consulta cancela a anterior
 * (AbortController), então uma resposta lenta nunca sobrescreve a mais nova.
 * `tentativa` existe só para o botão "Tentar de novo" disparar outra busca.
 */
export function useBuscaTranscricoes(consulta: string, modo: ModoBusca, tentativa = 0): EstadoBusca {
    const [estado, setEstado] = useState<EstadoBusca>({ fase: 'ociosa' });
    const ultima = useRef<BuscaResposta | null>(null);

    useEffect(() => {
        const q = consulta.trim();
        if (q.length < BUSCA_MIN_CARACTERES) {
            ultima.current = null;
            setEstado({ fase: 'ociosa' });
            return;
        }

        const controle = new AbortController();
        const espera = setTimeout(async () => {
            setEstado({ fase: 'carregando', anterior: ultima.current });
            try {
                const params = new URLSearchParams({ q, modo, limit: '20' });
                const resp = await fetch(`/painel/transcricoes/busca?${params}`, {
                    signal: controle.signal,
                    credentials: 'same-origin',
                    headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                });
                if (!resp.ok) {
                    throw new Error(
                        resp.status === 401 || resp.status === 419 ? 'Sessão expirada. Recarregue a página.' : `Erro ${resp.status} na busca.`,
                    );
                }
                const json = (await resp.json()) as BuscaResposta;
                ultima.current = json;
                setEstado({ fase: 'ok', resposta: json });
            } catch (e) {
                if (controle.signal.aborted) return;
                setEstado({ fase: 'erro', mensagem: e instanceof Error ? e.message : 'Não foi possível buscar agora.' });
            }
        }, DEBOUNCE_MS);

        return () => {
            clearTimeout(espera);
            controle.abort();
        };
    }, [consulta, modo, tentativa]);

    return estado;
}
