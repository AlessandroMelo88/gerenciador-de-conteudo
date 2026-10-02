"""
retention_collector.py — retenção diária dos clips publicados (YouTube Analytics API v2).

Irmão do ``metrics_collector.py``, com a mesma regra de ouro: NENHUMA exceção propaga. O que
falha é logado e o ciclo segue; uma melhoria de qualidade jamais pode virar indisponibilidade.

Diferença para o ``metrics_collector``: lá o grão é snapshot do contador cumulativo
(``videos.list`` part=statistics, append-only); aqui é relatório POR DIA (``reports.query``,
upsert). O YouTube revisa o número de um dia depois de fechá-lo, então a última leitura daquele
dia é a que vale.

``average_view_percentage`` é a nota de retenção: a única métrica que mede o que o selector de
fato decide — se o TRECHO escolhido é bom (SPEC-001).

Credenciais: o mesmo token OAuth por canal-destino do ``YouTubeUploader``
(``/app/youtube/token-{slug}.json``). Exige o escopo ``yt-analytics.readonly``; token antigo sem
ele falha só aqui, e a publicação segue intacta.
"""
import os
from datetime import datetime

# Métricas pedidas à API. A ordem aqui é só o que se PEDE: a leitura é sempre por columnHeaders.
METRICAS = [
    'views',
    'estimatedMinutesWatched',
    'averageViewDuration',
    'averageViewPercentage',
    'likes',
    'comments',
    'shares',
    'subscribersGained',
]

# De-para entre o nome da coluna da API e a coluna de `clip_daily_metrics`.
COLUNAS = {
    'video': 'youtube_video_id',
    'day': 'date',
    'views': 'views',
    'estimatedMinutesWatched': 'estimated_minutes_watched',
    'averageViewDuration': 'average_view_duration',
    'averageViewPercentage': 'average_view_percentage',
    'likes': 'likes',
    'comments': 'comments',
    'shares': 'shares',
    'subscribersGained': 'subscribers_gained',
}


def collector_enabled() -> bool:
    """RETENTION_COLLECTOR_ENABLED (default ligado) desliga o job sem mexer no resto."""
    return os.environ.get('RETENTION_COLLECTOR_ENABLED', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [RETENCAO] {msg}', flush=True)


def parse_report(response) -> list[dict]:
    """Normaliza a resposta de reports.query nas chaves de `clip_daily_metrics`.

    Lê SEMPRE por `columnHeaders`: a API não garante devolver as colunas na ordem pedida, e ler
    por posição gravaria a retenção na coluna de views.
    """
    response = response or {}
    cabecalhos = [c.get('name') for c in response.get('columnHeaders') or []]
    linhas = []
    for row in response.get('rows') or []:
        linha = {}
        for nome, valor in zip(cabecalhos, row):
            coluna = COLUNAS.get(nome)
            if coluna is not None:
                linha[coluna] = valor
        linhas.append(linha)
    return linhas
