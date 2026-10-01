"""
metrics_collector.py — coleta de visualizações dos clips publicados (YouTube Data API v3).

Job periódico (APScheduler, a cada hora). Para cada clip ``published`` com
``youtube_video_id``, lê ``videos.list`` part=statistics e grava UMA linha por clip por
coleta em ``clip_metrics`` (histórico, nunca sobrescreve).

Frequência (decidida pela idade do clip, a partir de ``published_at``):
  - menos de 7 dias: a cada 6 h;
  - de 7 a 30 dias: 1x por dia;
  - mais de 30 dias: para de coletar.

Credenciais: reaproveita o token OAuth por canal-destino do ``YouTubeUploader``
(``/app/youtube/token-{slug}.json``). O escopo ``youtube.force-ssl`` que o token já tem
cobre a leitura de ``videos.list``; nenhum fluxo OAuth novo é necessário.

Cota: ``videos.list`` custa 1 unidade por chamada (até 50 ids), no projeto GCP do canal.
Há um teto diário de chamadas por canal (``METRICS_MAX_CALLS_PER_CHANNEL_DAY``).

Falha de API/banco NUNCA propaga: é logada e o ciclo segue (não pode derrubar o pipeline).
"""
import logging
import os
from datetime import datetime, timedelta, timezone

from src.uploader import YouTubeUploader

logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # limite do videos.list
FRESH_DAYS = 7
STOP_DAYS = 30
FRESH_INTERVAL = timedelta(hours=6)
OLD_INTERVAL = timedelta(hours=24)
# Folga: o job roda de hora em hora; sem ela, uma coleta de 5h59 espera mais uma hora inteira.
SLACK = timedelta(minutes=5)

_calls_today: dict[tuple[str, str], int] = {}


def collector_enabled() -> bool:
    """METRICS_COLLECTOR_ENABLED (default ligado) desliga o job sem mexer no resto."""
    return os.environ.get('METRICS_COLLECTOR_ENABLED', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}


def _max_calls_per_channel_day() -> int:
    try:
        return int(os.environ.get('METRICS_MAX_CALLS_PER_CHANNEL_DAY', '200'))
    except ValueError:
        return 200


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [METRICS] {msg}', flush=True)


def _as_utc(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)  # colunas timestamp guardam UTC
    return value.astimezone(timezone.utc)


def is_due(published_at, last_collected_at, now: datetime) -> bool:
    """Decide se o clip precisa de nova coleta agora (regra de frequência)."""
    published = _as_utc(published_at)
    if published is None:
        return False
    age = now - published
    if age > timedelta(days=STOP_DAYS):
        return False
    last = _as_utc(last_collected_at)
    if last is None:
        return True
    interval = FRESH_INTERVAL if age < timedelta(days=FRESH_DAYS) else OLD_INTERVAL
    return now - last >= interval - SLACK


def _fetch_candidates(conn, now: datetime) -> list[dict]:
    cutoff = now - timedelta(days=STOP_DAYS)
    with conn.cursor() as cur:
        cur.execute(
            'SELECT gc.id, gc.youtube_video_id, gc.published_at, dc.slug AS channel_slug, '
            '(SELECT MAX(m.collected_at) FROM clip_metrics m WHERE m.generated_clip_id = gc.id) AS last_collected '
            'FROM generated_clips gc '
            'LEFT JOIN destination_channels dc ON dc.id = gc.destination_channel_id '
            "WHERE gc.status = 'published' AND gc.youtube_video_id IS NOT NULL "
            'AND gc.youtube_video_id <> %s AND gc.published_at >= %s',
            ('', cutoff),
        )
        return list(cur.fetchall())


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _insert_metrics(conn, rows: list[tuple]) -> None:
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                'INSERT INTO clip_metrics (generated_clip_id, collected_at, views, likes, comments) '
                'VALUES (%s, %s, %s, %s, %s)',
                row,
            )
    conn.commit()


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _channel_has_budget(slug: str, now: datetime) -> bool:
    return _calls_today.get((slug, now.date().isoformat()), 0) < _max_calls_per_channel_day()


def _count_call(slug: str, now: datetime) -> None:
    key = (slug, now.date().isoformat())
    for old in [k for k in _calls_today if k[1] != key[1]]:
        del _calls_today[old]
    _calls_today[key] = _calls_today.get(key, 0) + 1


def _collect_channel(conn, slug: str | None, clips: list[dict], now: datetime, service_for) -> int:
    """Coleta os clips de um canal-destino. Devolve quantas linhas gravou."""
    budget_key = slug or '_legado'
    try:
        service = service_for(slug)
    except Exception as exc:
        _log(f'Canal {budget_key}: sem credencial utilizável ({exc}) — pulando')
        return 0

    saved = 0
    for batch in _chunks(clips, BATCH_SIZE):
        if not _channel_has_budget(budget_key, now):
            _log(f'Canal {budget_key}: teto diário de chamadas atingido — retoma amanhã')
            break
        by_video = {c['youtube_video_id']: c for c in batch}
        try:
            _count_call(budget_key, now)
            response = service.videos().list(
                part='statistics', id=','.join(by_video), maxResults=BATCH_SIZE,
            ).execute()
        except Exception as exc:
            _log(f'Canal {budget_key}: videos.list falhou ({exc}) — segue sem derrubar o ciclo')
            continue

        rows = []
        for item in (response or {}).get('items', []):
            clip = by_video.get(item.get('id'))
            stats = item.get('statistics') or {}
            views = _to_int(stats.get('viewCount'))
            if clip is None or views is None:
                continue
            rows.append((
                clip['id'], now, views,
                _to_int(stats.get('likeCount')), _to_int(stats.get('commentCount')),
            ))
        missing = len(by_video) - len(rows)
        if missing:
            _log(f'Canal {budget_key}: {missing} vídeo(s) sem estatística (apagado/privado?)')
        try:
            _insert_metrics(conn, rows)
            saved += len(rows)
        except Exception as exc:
            _log(f'Canal {budget_key}: falha ao gravar métricas ({exc})')
            try:
                conn.rollback()
            except Exception:
                pass
    return saved


def _default_service_for(slug: str | None):
    uploader = YouTubeUploader(channel_slug=slug) if slug else YouTubeUploader()
    return uploader._get_service()


def run_metrics_collection_once(conn=None, now: datetime | None = None, service_for=None) -> int:
    """Um ciclo de coleta. Nunca levanta exceção. Devolve o nº de linhas gravadas."""
    if not collector_enabled():
        return 0
    now = now or datetime.now(timezone.utc)
    service_for = service_for or _default_service_for
    owns_conn = conn is None
    try:
        if owns_conn:
            from src.db import get_db_connection
            conn = get_db_connection()
        candidates = [
            c for c in _fetch_candidates(conn, now)
            if c.get('youtube_video_id') and is_due(c.get('published_at'), c.get('last_collected'), now)
        ]
        if not candidates:
            return 0
        by_channel: dict[str | None, list[dict]] = {}
        for c in candidates:
            by_channel.setdefault(c.get('channel_slug'), []).append(c)
        total = 0
        for slug, clips in by_channel.items():
            total += _collect_channel(conn, slug, clips, now, service_for)
        _log(f'Coleta concluída: {total} clip(s) medidos de {len(candidates)} devidos')
        return total
    except Exception as exc:
        _log(f'Aviso: coleta de métricas falhou — {exc}')
        return 0
    finally:
        if owns_conn and conn is not None:
            try:
                conn.close()
            except Exception:
                pass
