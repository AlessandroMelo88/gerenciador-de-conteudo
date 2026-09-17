"""
fair_queue.py — Justiça por canal de origem na fila de download.

A janela de download é por nicho (`DOWNLOAD_WINDOW_PER_CHANNEL` × canais destino
ativos). Sem teto por canal de origem, um canal que publica 50 vídeos por dia
ocupa as vagas todas e os outros nunca baixam. Aqui mora a regra pura — sem
banco, sem rede — usada tanto pelo `pipeline_runner` (no servidor) quanto pelo
`local_download_worker` (no Mac, que é quem baixa de verdade).

Exporta:
- channel_cap(window, active_channels, override=None) -> int
- fair_pick(candidates, occupancy, deficit, cap) -> list[dict]
"""
import math


def channel_cap(window: int, active_channels: int, override: int | None = None) -> int:
    """Quantas vagas da janela um único canal de origem pode ocupar.

    Divide a janela pelos canais ativos do nicho, arredondando para cima (senão
    sobra vaga sem dono quando a divisão não é exata) e nunca menos que 1 — com
    mais canais que vagas, cada um ainda tem direito a uma.
    `override` (env) vence o cálculo. Sem canal ativo, não limita nada.
    """
    if override is not None:
        return max(1, int(override))
    if active_channels <= 0:
        return window
    return max(1, math.ceil(window / active_channels))


def fair_pick(candidates: list[dict], occupancy: dict, deficit: int, cap: int) -> list[dict]:
    """Escolhe até `deficit` vídeos intercalando canais de origem.

    Devolve os próprios dicts de entrada, na ordem escolhida — cada chamador usa
    os campos que precisa (o pipeline só o youtube_video_id, o worker a linha toda).

    `candidates` vem na ordem de prioridade do SQL (priority, queue_position,
    published_at) e preserva essa ordem dentro de cada canal — o round-robin só
    decide de qual canal sai o próximo, nunca qual vídeo daquele canal.

    `occupancy` é quantas vagas cada canal já ocupa agora; conta contra o `cap`
    e define quem começa a rodada: canal com menos vagas ocupadas vem primeiro,
    que é o anti-fome. Empate mantém a ordem de chegada no SQL.

    Vaga que sobra (canal sem mais candidatos) volta para quem ainda tem fila,
    respeitando o teto — janela ociosa não ajuda ninguém.
    """
    queues: dict = {}
    arrival: list = []
    for video in candidates:
        key = video.get('channel_id')
        if key not in queues:
            queues[key] = []
            arrival.append(key)
        queues[key].append(video)

    order = sorted(arrival, key=lambda k: (occupancy.get(k, 0), arrival.index(k)))
    taken: dict = {}
    picked: list[dict] = []

    while order and len(picked) < deficit:
        rodada_rendeu = False
        for key in list(order):
            if len(picked) >= deficit:
                break
            if occupancy.get(key, 0) + taken.get(key, 0) >= cap:
                order.remove(key)
                continue
            picked.append(queues[key].pop(0))
            taken[key] = taken.get(key, 0) + 1
            rodada_rendeu = True
            if not queues[key]:
                order.remove(key)
        if not rodada_rendeu:
            break

    return picked
