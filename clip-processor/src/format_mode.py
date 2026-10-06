"""
format_mode.py — modo de formato longo por canal destino (`destination_channels.long_format_mode`).

Valores:
  auto       (padrão) a duração da fonte decide: < MIN_LONGFORM_SECONDS = curto, senão longo
             (e fonte longa NÃO gera Shorts) — comportamento histórico, intacto.
  short_only fonte longa também gera Shorts, nunca longo.
  both       fonte longa gera Shorts E um longo; fonte curta gera só Shorts.

A ligação fonte → canal destino é pelo nicho: source_channels.target_niche = destination_channels.niche
(a mesma resolução de selector._lookup_destination_channel_id). Com mais de um canal destino ativo no
nicho vale a regra MAIS CONSERVADORA: short_only > auto > both (qualquer short_only impede o longo;
`both` só vale se TODOS os canais ativos do nicho pedirem `both`).

Tolerância: a coluna pode não existir ainda (migration não rodada), vir NULL ou com valor inválido —
tudo isso vira `auto`, sem exceção, para nunca derrubar a ingestão.
"""
from datetime import datetime

from src.db import get_db_driver

MODE_AUTO = 'auto'
MODE_SHORT_ONLY = 'short_only'
MODE_BOTH = 'both'
VALID_MODES = (MODE_AUTO, MODE_SHORT_ONLY, MODE_BOTH)

# Menor = mais conservador.
_CONSERVATISM = {MODE_SHORT_ONLY: 0, MODE_AUTO: 1, MODE_BOTH: 2}

_column_cache: dict[tuple[str, str], bool] = {}


def _log(msg: str) -> None:
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [FMT] {msg}', flush=True)


def normalize_mode(value) -> str:
    """Valor desconhecido, NULL ou vazio → 'auto'."""
    if isinstance(value, str):
        v = value.strip().lower()
        if v in VALID_MODES:
            return v
    return MODE_AUTO


def column_exists(conn, table: str, column: str) -> bool:
    """True se a coluna existe no schema atual. Só cacheia o positivo (a migration pode rodar depois).

    Usa information_schema (sem erro de SQL, então não aborta a transação do PostgreSQL).
    Qualquer falha → False.
    """
    key = (table, column)
    if _column_cache.get(key):
        return True
    schema = 'DATABASE()' if get_db_driver(conn) == 'mysql' else 'current_schema()'
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT 1 AS present FROM information_schema.columns '
                f'WHERE table_schema = {schema} AND table_name = %s AND column_name = %s',
                (table, column),
            )
            found = cur.fetchone() is not None
    except Exception as exc:  # noqa: BLE001 - a checagem nunca derruba o pipeline
        _log(f'AVISO: não consegui checar a coluna {table}.{column}: {exc}')
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        return False
    if found:
        _column_cache[key] = True
    return found


def generated_clips_has_format(conn) -> bool:
    return column_exists(conn, 'generated_clips', 'format')


def clip_format_sql(conn, clip_alias: str = 'gc', source_alias: str = 'sv') -> str:
    """Expressão SQL do formato do clip: `generated_clips.format` (fonte da verdade) com queda para
    `source_videos.format`. Sem a coluna ainda, só o da fonte (comportamento antigo)."""
    if generated_clips_has_format(conn):
        return f'COALESCE({clip_alias}.format, {source_alias}.format)'
    return f'{source_alias}.format'


def get_long_format_mode(conn, niche) -> str:
    """Modo efetivo do nicho (regra conservadora com vários canais ativos). Nunca levanta."""
    if conn is None or not niche:
        return MODE_AUTO
    if not column_exists(conn, 'destination_channels', 'long_format_mode'):
        return MODE_AUTO
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT long_format_mode FROM destination_channels '
                'WHERE niche = %s AND active = TRUE',
                (niche,),
            )
            rows = cur.fetchall() or []
    except Exception as exc:  # noqa: BLE001
        _log(f'AVISO: falha ao ler long_format_mode do nicho {niche}: {exc} — usando auto')
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        return MODE_AUTO
    modes = []
    for row in rows:
        value = row.get('long_format_mode') if hasattr(row, 'get') else None
        modes.append(normalize_mode(value))
    if not modes:
        return MODE_AUTO
    mode = min(modes, key=lambda m: _CONSERVATISM[m])
    if len(set(modes)) > 1:
        _log(f'Nicho {niche} tem canais com modos diferentes {sorted(set(modes))} — vale o mais conservador: {mode}')
    return mode


# --------------------------------------------------------------- privacidade do upload

PRIVACY_PRIVATE = 'private'
PRIVACY_PUBLIC = 'public'
VALID_PRIVACY = (PRIVACY_PRIVATE, PRIVACY_PUBLIC)


def normalize_privacy(value) -> str | None:
    """Valor desconhecido, NULL ou vazio → None (quem chama decide o que herdar)."""
    if isinstance(value, str):
        v = value.strip().lower()
        if v in VALID_PRIVACY:
            return v
    return None


def clip_privacy_sql(conn, clip_alias: str = 'gc') -> str:
    """Expressão SQL da privacidade escolhida na aprovação do clip.

    Sem a coluna (migration não rodada), devolve NULL literal: o uploader cai no padrão do canal
    e, não havendo, na env — exatamente o comportamento de antes da coluna existir.
    """
    if column_exists(conn, 'generated_clips', 'privacy_status'):
        return f'{clip_alias}.privacy_status'
    return 'NULL'


def channel_privacy_sql(conn, channel_alias: str = '') -> str:
    """Expressão SQL do padrão de privacidade do canal destino, tolerante à coluna ausente."""
    if column_exists(conn, 'destination_channels', 'default_privacy'):
        prefixo = f'{channel_alias}.' if channel_alias else ''
        return f'{prefixo}default_privacy'
    return 'NULL'
