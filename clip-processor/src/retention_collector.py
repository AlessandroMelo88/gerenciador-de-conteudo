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
from datetime import datetime, timedelta, timezone

BATCH_SIZE = 50          # ids por chamada, como no metrics_collector
STOP_DAYS = 30           # janela de coleta por clip, alinhada ao metrics_collector

# Chamadas já gastas hoje, por canal. Zera sozinho na virada do dia.
_calls_today: dict[tuple[str, str], int] = {}

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


# Colunas gravadas, na ordem usada tanto pelo UPDATE quanto pelo INSERT.
_GRAVAVEIS = [
    'views', 'estimated_minutes_watched', 'average_view_duration', 'average_view_percentage',
    'likes', 'comments', 'shares', 'subscribers_gained',
]


def upsert_linhas(conn, por_clip: dict, linhas: list[dict]) -> int:
    """Grava as linhas do relatório, uma por clip por dia.

    Upsert à mão (UPDATE e, se não afetou linha, INSERT) porque `db.py` fala PostgreSQL e MySQL:
    `ON CONFLICT` e `ON DUPLICATE KEY` são de um dialeto só. O volume é pequeno — a janela de
    coleta é de 30 dias — então duas idas ao banco por linha não pesam.
    """
    gravadas = 0
    with conn.cursor() as cur:
        for linha in linhas:
            clip_id = por_clip.get(linha.get('youtube_video_id'))
            if clip_id is None or not linha.get('date'):
                continue
            valores = [linha.get(coluna) for coluna in _GRAVAVEIS]

            sets = ', '.join(f'{coluna} = %s' for coluna in _GRAVAVEIS)
            cur.execute(
                f'UPDATE clip_daily_metrics SET {sets} WHERE generated_clip_id = %s AND date = %s',
                valores + [clip_id, linha['date']],
            )
            if cur.rowcount == 0:
                colunas = ', '.join(['generated_clip_id', 'date'] + _GRAVAVEIS)
                marcas = ', '.join(['%s'] * (len(_GRAVAVEIS) + 2))
                cur.execute(
                    f'INSERT INTO clip_daily_metrics ({colunas}) VALUES ({marcas})',
                    [clip_id, linha['date']] + valores,
                )
            gravadas += 1
    conn.commit()
    return gravadas


def _max_calls_per_channel_day() -> int:
    try:
        return int(os.environ.get('RETENTION_MAX_CALLS_PER_CHANNEL_DAY', '200'))
    except ValueError:
        return 200


def _channel_has_budget(slug: str, now: datetime) -> bool:
    return _calls_today.get((slug, now.date().isoformat()), 0) < _max_calls_per_channel_day()


def _count_call(slug: str, now: datetime) -> None:
    key = (slug, now.date().isoformat())
    for old in [k for k in _calls_today if k[1] != key[1]]:
        del _calls_today[old]
    _calls_today[key] = _calls_today.get(key, 0) + 1


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _fetch_candidates(conn, now: datetime, dias: int) -> list[dict]:
    cutoff = now - timedelta(days=dias)
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.youtube_video_id, gc.published_at, dc.slug AS channel_slug '
            'FROM generated_clips gc '
            'LEFT JOIN destination_channels dc ON dc.id = gc.destination_channel_id '
            "WHERE gc.status = 'published' AND gc.youtube_video_id IS NOT NULL "
            'AND gc.youtube_video_id <> %s AND gc.published_at >= %s',
            ('', cutoff),
        )
        return list(cur.fetchall())


def _as_date(value) -> str:
    if isinstance(value, str):
        return value[:10]
    return value.strftime('%Y-%m-%d')


def _collect_channel(conn, slug, clips: list[dict], now: datetime, service_for) -> int:
    budget_key = slug or '_legado'
    try:
        service = service_for(slug)
    except Exception as exc:
        _log(f'Canal {budget_key}: sem credencial utilizável ({exc}) — pulando')
        return 0

    inicio = _as_date(min(c['published_at'] for c in clips))
    fim = _as_date(now - timedelta(days=1))  # o dia de hoje ainda não fechou na Analytics
    gravadas = 0

    for lote in _chunks(clips, BATCH_SIZE):
        if not _channel_has_budget(budget_key, now):
            _log(f'Canal {budget_key}: teto diário de chamadas atingido — retoma amanhã')
            break
        por_clip = {c['youtube_video_id']: c['id'] for c in lote}
        try:
            _count_call(budget_key, now)
            resposta = service.reports().query(
                ids='channel==MINE',
                startDate=inicio,
                endDate=fim,
                dimensions='video,day',
                metrics=','.join(METRICAS),
                filters='video==' + ','.join(por_clip),
                maxResults=200,
            ).execute()
        except Exception as exc:
            _log(f'Canal {budget_key}: reports.query falhou ({exc}) — segue sem derrubar o ciclo')
            continue

        linhas = parse_report(resposta)
        if not linhas:
            continue
        try:
            gravadas += upsert_linhas(conn, por_clip, linhas)
        except Exception as exc:
            _log(f'Canal {budget_key}: falha ao gravar retenção ({exc})')
            try:
                conn.rollback()
            except Exception:
                pass
    return gravadas


def _default_service_for(slug):
    """Reusa o token do uploader e abre o serviço de Analytics com as mesmas credenciais."""
    from googleapiclient.discovery import build

    from src.uploader import YouTubeUploader

    uploader = YouTubeUploader(channel_slug=slug) if slug else YouTubeUploader()
    return build('youtubeAnalytics', 'v2', credentials=uploader._load_credentials())


def run_retention_collection_once(conn=None, now=None, service_for=None, dias=None) -> int:
    """Um ciclo de coleta. Nunca levanta exceção. Devolve o nº de linhas gravadas."""
    if not collector_enabled():
        return 0
    now = now or datetime.now(timezone.utc)
    dias = STOP_DAYS if dias is None else dias
    service_for = service_for or _default_service_for
    owns_conn = conn is None
    try:
        if owns_conn:
            from src.db import get_db_connection
            conn = get_db_connection()
        candidatos = [c for c in _fetch_candidates(conn, now, dias) if c.get('youtube_video_id')]
        if not candidatos:
            return 0
        por_canal: dict = {}
        for c in candidatos:
            por_canal.setdefault(c.get('channel_slug'), []).append(c)
        total = 0
        for slug, clips in por_canal.items():
            total += _collect_channel(conn, slug, clips, now, service_for)
        _log(f'Coleta concluída: {total} linha(s) de retenção de {len(candidatos)} clip(s)')
        return total
    except Exception as exc:
        _log(f'Aviso: coleta de retenção falhou — {exc}')
        return 0
    finally:
        if owns_conn and conn is not None:
            try:
                conn.close()
            except Exception:
                pass
