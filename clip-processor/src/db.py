"""
db.py — Módulo de acesso ao banco de dados (MySQL e PostgreSQL) para o daemon clip-processor.

Exporta:
  - get_db_driver(conn=None): retorna o driver ativo ('mysql' ou 'pgsql')
  - get_db_connection(): abre conexão com MySQL (pymysql) ou PostgreSQL (psycopg2)
  - update_status(conn, video_id, status, local_path=None): atualiza status de vídeo
  - insert_video(conn, video_id, channel_id, title, published_at): insere vídeo novo
  - fetch_used_moments(conn, source_video_id): busca intervalos já registrados do vídeo
  - recover_stuck_downloads(conn): redefine vídeos presos em 'downloading' para 'pending'
  - recover_stuck_transcribing(conn): redefine vídeos presos em 'transcribing' para 'downloaded'
  - recover_stuck_selecting(conn): redefine vídeos presos em 'selecting' para 'downloaded'
  - reconcile_source_video_status(conn, source_video_id): libera fonte se todos os clips falharem
  - recover_stuck_publishing(conn): redefine clips presos em 'publishing' para 'pending'
  - recover_cutting_on_boot(conn): redefine clips interrompidos em 'cutting' para 'pending_cut'

Convenções:
  - Quem chama é responsável por fechar a conexão (não fechar dentro das funções)
  - Logging via print simples para stdout (sem biblioteca de logging)
  - Cada função usa `with conn.cursor() as cur:` e faz commit explícito
"""

from __future__ import annotations

import os
from datetime import datetime

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [DB] {msg}')


def get_db_driver(conn=None) -> str:
    """Retorna o driver de banco de dados ativo: 'mysql' ou 'pgsql'.

    Detecta por atributo na conexão se fornecida, ou pelas variáveis de ambiente:
      - DB_CONNECTION / DB_DRIVER (ex: 'pgsql', 'postgres', 'postgresql', 'mysql')
      - Presença de POSTGRES_HOST / PGHOST
    """
    if conn is not None:
        driver = getattr(conn, '_driver', None)
        if driver:
            return driver
        conn_type = type(conn).__module__
        if 'psycopg2' in conn_type:
            return 'pgsql'
        if 'pymysql' in conn_type:
            return 'mysql'

    env_driver = (os.environ.get('DB_CONNECTION') or os.environ.get('DB_DRIVER', '')).lower()
    if env_driver in ('pgsql', 'postgres', 'postgresql'):
        return 'pgsql'
    if env_driver == 'mysql':
        return 'mysql'

    if (os.environ.get('POSTGRES_HOST') or os.environ.get('PGHOST')) and not os.environ.get(
        'MYSQL_HOST'
    ):
        return 'pgsql'

    return 'mysql'


class PostgresCursorWrapper:
    """Wrapper para cursor do psycopg2 para uniformidade com pymysql.

    - Garante compatibilidade de `cur.lastrowid` capturando id de INSERTs
    - Converte aspas invertidas (backticks do MySQL como `key`) para aspas duplas ANSI ("key")
    """

    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        # Converte backticks para aspas duplas padrão ANSI/PostgreSQL
        query_mod = query.replace('`key`', '"key"')

        # Se for INSERT sem RETURNING, anexa RETURNING id para popular lastrowid
        is_insert = query_mod.strip().upper().startswith('INSERT INTO')
        if (
            is_insert
            and 'RETURNING' not in query_mod.upper()
            and 'ON CONFLICT' not in query_mod.upper()
        ):
            query_mod += ' RETURNING id'
            res = self._cursor.execute(query_mod, params)
            try:
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row['id'] if isinstance(row, dict) else row[0]
            except Exception:
                self.lastrowid = None
            return res

        return self._cursor.execute(query_mod, params)

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._cursor.__exit__(exc_type, exc_val, exc_tb)


class PostgresConnectionWrapper:
    """Wrapper para conexão do psycopg2 expondo cursor com dicionário e atributo _driver."""

    def __init__(self, conn):
        self._conn = conn
        self._driver = 'pgsql'

    def cursor(self, *args, **kwargs):
        cur = self._conn.cursor(*args, **kwargs)
        return PostgresCursorWrapper(cur)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def get_db_connection():
    """Abre conexão com o banco de dados (MySQL ou PostgreSQL) usando variáveis de ambiente.

    Detecta o banco ativo via get_db_driver().

    Variáveis para MySQL:
      - MYSQL_HOST (default: localhost)
      - MYSQL_DATABASE (default: clips_automation)
      - MYSQL_USER (default: clips_user)
      - MYSQL_PASSWORD
      - MYSQL_PORT (default: 3306)

    Variáveis para PostgreSQL:
      - POSTGRES_HOST / PGHOST / DB_HOST (default: localhost)
      - POSTGRES_DB / POSTGRES_DATABASE / PGDATABASE (default: clips_automation)
      - POSTGRES_USER / PGUSER / DB_USERNAME (default: clips_user)
      - POSTGRES_PASSWORD / PGPASSWORD / DB_PASSWORD
      - POSTGRES_PORT / PGPORT / DB_PORT (default: 5432)

    Returns:
        Conexão aberta com autocommit=False e cursores em formato de dicionário
    """
    driver = get_db_driver()

    if driver == 'pgsql':
        if psycopg2 is None:
            raise ImportError(
                'psycopg2 não está instalado. Instale psycopg2-binary para suporte ao PostgreSQL.'
            )
        host = (
            os.environ.get('POSTGRES_HOST')
            or os.environ.get('PGHOST')
            or os.environ.get('DB_HOST', 'localhost')
        )
        database = (
            os.environ.get('POSTGRES_DB')
            or os.environ.get('POSTGRES_DATABASE')
            or os.environ.get('PGDATABASE')
            or os.environ.get('DB_DATABASE', 'clips_automation')
        )
        user = (
            os.environ.get('POSTGRES_USER')
            or os.environ.get('PGUSER')
            or os.environ.get('DB_USERNAME', 'clips_user')
        )
        password = (
            os.environ.get('POSTGRES_PASSWORD')
            or os.environ.get('PGPASSWORD')
            or os.environ.get('DB_PASSWORD', '')
        )
        port = int(
            os.environ.get('POSTGRES_PORT')
            or os.environ.get('PGPORT')
            or os.environ.get('DB_PORT', 5432)
        )

        raw_conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        raw_conn.autocommit = False
        wrapped_conn = PostgresConnectionWrapper(raw_conn)
        _log(f'Conexão PostgreSQL aberta: {user}@{host}:{port}/{database}')
        return wrapped_conn

    if pymysql is None:
        raise ImportError('pymysql não está instalado. Instale pymysql para suporte ao MySQL.')

    host = os.environ.get('MYSQL_HOST', 'localhost')
    database = os.environ.get('MYSQL_DATABASE', 'clips_automation')
    user = os.environ.get('MYSQL_USER', 'clips_user')
    password = os.environ.get('MYSQL_PASSWORD', '')
    port = int(os.environ.get('MYSQL_PORT', 3306))

    conn = pymysql.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        port=port,
        charset='utf8mb4',
        autocommit=False,
        connect_timeout=10,
        cursorclass=pymysql.cursors.DictCursor,
    )
    conn._driver = 'mysql'
    _log(f'Conexão MySQL aberta: {user}@{host}:{port}/{database}')
    return conn


def update_status(conn, video_id, status, local_path=None, clear_local_path=False):
    """Atualiza o status de um vídeo na tabela source_videos.

    `local_path=None` significa "não mexe na coluna" (compatibilidade com as
    chamadas antigas), então zerar a coluna precisa de um sinal próprio:
    `clear_local_path=True` grava NULL. Sem isso não havia como desocupar a
    janela de download — que conta `local_path IS NOT NULL` —, e vídeo com
    download falho segurava vaga pra sempre.

    Args:
        conn: conexão com banco ativa
        video_id: youtube_video_id do vídeo a atualizar
        status: novo status (ex: 'downloading', 'downloaded', 'failed')
        local_path: caminho local do arquivo (opcional, usado quando status='downloaded')
        clear_local_path: se True, seta local_path=NULL (ignora `local_path`)
    """
    if clear_local_path:
        sql = 'UPDATE source_videos SET status=%s, local_path=NULL WHERE youtube_video_id=%s'
        params = (status, video_id)
    elif local_path is not None:
        sql = 'UPDATE source_videos SET status=%s, local_path=%s WHERE youtube_video_id=%s'
        params = (status, local_path, video_id)
    else:
        sql = 'UPDATE source_videos SET status=%s WHERE youtube_video_id=%s'
        params = (status, video_id)

    with conn.cursor() as cur:
        cur.execute(sql, params)
    conn.commit()
    _log(f'Status atualizado: video_id={video_id} → {status}')


def insert_video(conn, video_id, channel_id, title, published_at, format='curto'):
    """Insere um novo vídeo na tabela source_videos com status 'pending'.

    Usa INSERT IGNORE no MySQL ou ON CONFLICT DO NOTHING no PostgreSQL para ser idempotente.

    Args:
        conn: conexão pymysql ou psycopg2 ativa
        video_id: youtube_video_id único do vídeo
        channel_id: FK para source_channels.id
        title: título do vídeo
        published_at: data/hora de publicação (string ISO 8601 ou datetime)
        format: 'curto' ou 'longo' — decidido pelo poller com base na duração do vídeo fonte
    """
    driver = get_db_driver(conn)
    if driver == 'pgsql':
        sql = (
            'INSERT INTO source_videos '
            '(youtube_video_id, channel_id, title, published_at, status, format) '
            'VALUES (%s, %s, %s, %s, %s, %s) '
            'ON CONFLICT (youtube_video_id) DO NOTHING'
        )
    else:
        sql = (
            'INSERT IGNORE INTO source_videos '
            '(youtube_video_id, channel_id, title, published_at, status, format) '
            'VALUES (%s, %s, %s, %s, %s, %s)'
        )
    params = (video_id, channel_id, title, published_at, 'pending', format)

    with conn.cursor() as cur:
        cur.execute(sql, params)
    conn.commit()
    _log(f'Vídeo inserido: {video_id} — "{title}"')


def fetch_used_moments(conn, source_video_id: int) -> list[dict]:
    """Busca os intervalos já registrados para um vídeo fonte.

    Inclui clips publicados, pendentes, rejeitados e falhos: qualquer linha
    com intervalo representa material que já foi usado ou reservado e não deve
    ser escolhido de novo durante uma reexecução da seleção.
    """
    sql = (
        'SELECT start_time, end_time, status '
        'FROM generated_clips '
        'WHERE source_video_id = %s '
        'AND start_time IS NOT NULL '
        'AND end_time IS NOT NULL '
        'ORDER BY start_time ASC, end_time ASC'
    )

    with conn.cursor() as cur:
        cur.execute(sql, (source_video_id,))
        return list(cur.fetchall() or [])


def recover_stuck_downloads(conn):
    """Redefine vídeos presos em status 'downloading' de volta para 'pending'.

    Executado na inicialização do daemon para recuperar falhas de sessões anteriores.

    Args:
        conn: conexão pymysql ou psycopg2 ativa
    """
    sql = "UPDATE source_videos SET status='pending' WHERE status='downloading'"

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            affected = cur.rowcount
        conn.commit()
        _log(f'recover_stuck_downloads: {affected} vídeo(s) redefinido(s) para pending')
    except Exception as exc:
        _log(f'AVISO: falha ao recuperar downloads presos: {exc}')
        raise


def recover_stuck_transcribing(conn):
    """Recupera transcrições interrompidas pelo worker de IA.

    Com a etapa de IA em processo separado, uma queda do container pode deixar
    a fonte em ``transcribing``. Raw existente volta para ``downloaded`` para
    nova tentativa; sem raw, o estado terminal ``failed`` evita ocupar a fila.
    O limite de duas horas não atropela uma transcrição legítima em andamento.
    """
    driver = get_db_driver(conn)
    if driver == 'pgsql':
        sql_with_file = (
            "UPDATE source_videos SET status='downloaded' "
            "WHERE status='transcribing' AND local_path IS NOT NULL "
            "AND updated_at < NOW() - (%s * INTERVAL '1 hour')"
        )
        sql_without_file = (
            "UPDATE source_videos SET status='failed' "
            "WHERE status='transcribing' AND local_path IS NULL "
            "AND updated_at < NOW() - (%s * INTERVAL '1 hour')"
        )
    else:
        sql_with_file = (
            "UPDATE source_videos SET status='downloaded' "
            "WHERE status='transcribing' AND local_path IS NOT NULL "
            'AND updated_at < DATE_SUB(NOW(), INTERVAL %s HOUR)'
        )
        sql_without_file = (
            "UPDATE source_videos SET status='failed' "
            "WHERE status='transcribing' AND local_path IS NULL "
            'AND updated_at < DATE_SUB(NOW(), INTERVAL %s HOUR)'
        )

    try:
        with conn.cursor() as cur:
            cur.execute(sql_with_file, (SELECTING_STUCK_HOURS,))
            with_file = cur.rowcount
            cur.execute(sql_without_file, (SELECTING_STUCK_HOURS,))
            without_file = cur.rowcount
        conn.commit()
        if with_file or without_file:
            _log(
                f'recover_stuck_transcribing: {with_file} vídeo(s) voltaram para downloaded; '
                f'{without_file} sem raw foram para failed'
            )
    except Exception as exc:
        _log(f'AVISO: falha ao recuperar transcrições presas: {exc}')
        raise


# Horas sem progresso antes de considerar um 'selecting' travado.
SELECTING_STUCK_HOURS = 2


def recover_stuck_selecting(conn):
    """Devolve vídeos presos em 'selecting' para 'downloaded' (reprocessa a IA).

    'selecting' não tinha recuperação: um vídeo que travasse na etapa de IA
    (queda do MySQL/PostgreSQL, container morto no meio) ficava preso pra sempre segurando
    um slot da janela de download — com as duas janelas cheias de linha morta,
    o pipeline parava de baixar qualquer coisa.

    Só considera travado o que não recebe update há SELECTING_STUCK_HOURS E NÃO
    possui clips gerados em generated_clips. Vídeos que já possuem clips gerados
    NÃO devem ser resetados para 'downloaded', pois isso causa reprocessamento
    em loop e duplicação de clips caso o operador fique sem aprovar/postar.

    Terceiro caso: 'selecting' com local_path NULL. A limpeza de disco
    (`delete_source_video_file` e a purga de vídeos antigos no internal_api)
    zera `local_path` sem tocar em `status`, então o registro fica preso num
    estado que a query com `local_path IS NOT NULL` nunca alcança. Sem o raw em
    disco não existe seleção pra reprocessar, então vai para 'failed': é o estado
    honesto (o insumo não existe mais) e libera a vaga da janela. O registro
    continua no banco, com os clips que já tiverem sido gerados.

    Args:
        conn: conexão pymysql ou psycopg2 ativa
    """
    driver = get_db_driver(conn)
    if driver == 'pgsql':
        sql_stuck = (
            'UPDATE source_videos '
            "SET status='downloaded' "
            "WHERE status='selecting' "
            'AND local_path IS NOT NULL '
            "AND updated_at < (NOW() - (%s * INTERVAL '1 hour')) "
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc WHERE gc.source_video_id = source_videos.id'
            ')'
        )
        sql_terminal = (
            'UPDATE source_videos '
            "SET status='failed' "
            "WHERE status='selecting' "
            'AND EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            '  WHERE gc.source_video_id = source_videos.id'
            ') '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            '  WHERE gc.source_video_id = source_videos.id '
            "  AND gc.status IN ('pending_cut', 'cutting', 'pending', 'approved', 'publishing')"
            ') '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            "  WHERE gc.source_video_id = source_videos.id AND gc.status = 'published'"
            ')'
        )
        sql_no_file = (
            'UPDATE source_videos '
            "SET status='failed' "
            "WHERE status='selecting' "
            'AND local_path IS NULL '
            "AND updated_at < (NOW() - (%s * INTERVAL '1 hour'))"
        )
    else:
        sql_stuck = (
            'UPDATE source_videos sv '
            "SET sv.status='downloaded' "
            "WHERE sv.status='selecting' "
            'AND sv.local_path IS NOT NULL '
            'AND sv.updated_at < DATE_SUB(NOW(), INTERVAL %s HOUR) '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc WHERE gc.source_video_id = sv.id'
            ')'
        )
        sql_terminal = (
            'UPDATE source_videos sv '
            "SET sv.status='failed' "
            "WHERE sv.status='selecting' "
            'AND EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            '  WHERE gc.source_video_id = sv.id'
            ') '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            '  WHERE gc.source_video_id = sv.id '
            "  AND gc.status IN ('pending_cut', 'cutting', 'pending', 'approved', 'publishing')"
            ') '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            "  WHERE gc.source_video_id = sv.id AND gc.status = 'published'"
            ')'
        )
        sql_no_file = (
            'UPDATE source_videos '
            "SET status='failed' "
            "WHERE status='selecting' "
            'AND local_path IS NULL '
            'AND updated_at < DATE_SUB(NOW(), INTERVAL %s HOUR)'
        )

    try:
        with conn.cursor() as cur:
            cur.execute(sql_terminal)
            terminal = cur.rowcount
            cur.execute(sql_stuck, (SELECTING_STUCK_HOURS,))
            stuck = cur.rowcount
            cur.execute(sql_no_file, (SELECTING_STUCK_HOURS,))
            no_file = cur.rowcount
        conn.commit()
        _log(
            f'recover_stuck_selecting: {terminal} terminal(is) para failed; '
            f'{stuck} travado(s) sem clip para downloaded, {no_file} sem arquivo para failed'
        )
    except Exception as exc:
        _log(f'AVISO: falha ao recuperar seleções presas: {exc}')
        raise


def reconcile_source_video_status(conn, source_video_id: int | None) -> bool:
    """Libera uma fonte quando todos os seus clips terminaram sem publicar.

    A seleção deixa a fonte em ``selecting`` enquanto os clips passam por corte
    e publicação. Se o último clip falhar, não há outro worker que altere a
    fonte, então ela ficava presa nesse estado até o recovery periódico. Esta
    reconciliação é chamada logo após cada corte e continua protegida por um
    ``WHERE status='selecting'`` para não rebaixar uma fonte já publicada.
    """
    if source_video_id is None:
        return False

    driver = get_db_driver(conn)
    if driver == 'pgsql':
        sql = (
            'UPDATE source_videos '
            "SET status='failed' "
            "WHERE id=%s AND status='selecting' "
            'AND EXISTS ('
            '  SELECT 1 FROM generated_clips gc WHERE gc.source_video_id = source_videos.id'
            ') '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            '  WHERE gc.source_video_id = source_videos.id '
            "  AND gc.status IN ('pending_cut', 'cutting', 'pending', 'approved', 'publishing')"
            ') '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            "  WHERE gc.source_video_id = source_videos.id AND gc.status = 'published'"
            ')'
        )
    else:
        sql = (
            'UPDATE source_videos sv '
            "SET sv.status='failed' "
            "WHERE sv.id=%s AND sv.status='selecting' "
            'AND EXISTS ('
            '  SELECT 1 FROM generated_clips gc WHERE gc.source_video_id = sv.id'
            ') '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            '  WHERE gc.source_video_id = sv.id '
            "  AND gc.status IN ('pending_cut', 'cutting', 'pending', 'approved', 'publishing')"
            ') '
            'AND NOT EXISTS ('
            '  SELECT 1 FROM generated_clips gc '
            "  WHERE gc.source_video_id = sv.id AND gc.status = 'published'"
            ')'
        )

    with conn.cursor() as cur:
        cur.execute(sql, (source_video_id,))
        changed = cur.rowcount > 0
    conn.commit()
    if changed:
        _log(f'Fonte {source_video_id} liberada: todos os clips terminaram em falha')
    return changed


def recover_stuck_publishing(conn):
    """Devolve clips presos em 'publishing' para 'pending'.

    Se o container reiniciar ou cair durante upload, o clip não fica eternamente
    em status 'publishing'.
    """
    driver = get_db_driver(conn)
    if driver == 'pgsql':
        sql = (
            'UPDATE generated_clips '
            "SET status='pending' "
            "WHERE status='publishing' "
            "AND updated_at < NOW() - INTERVAL '15 minutes'"
        )
    else:
        sql = (
            'UPDATE generated_clips '
            "SET status='pending' "
            "WHERE status='publishing' "
            'AND updated_at < DATE_SUB(NOW(), INTERVAL 15 MINUTE)'
        )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            count = cur.rowcount
        conn.commit()
        if count > 0:
            _log(f'recover_stuck_publishing: {count} clip(s) redefinido(s) para pending')
    except Exception as exc:
        _log(f'AVISO: falha ao recuperar clips em publishing: {exc}')


def recover_cutting_on_boot(conn):
    """Devolve clips interrompidos em ``cutting`` para ``pending_cut``.

    Esta recuperação só deve ser chamada durante o boot. Um novo processo do
    daemon implica que o FFmpeg do processo anterior não existe mais; já o
    recovery periódico não pode tocar em ``cutting``, pois um corte legítimo
    pode durar mais de 30 minutos.

    Args:
        conn: conexão com banco ativa
    """
    sql = "UPDATE generated_clips SET status='pending_cut' WHERE status='cutting'"

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            affected = cur.rowcount
        conn.commit()
        _log(f'recover_cutting_on_boot: {affected} clip(s) redefinido(s) para pending_cut')
    except Exception as exc:
        _log(f'AVISO: falha ao recuperar clips em cutting: {exc}')
        raise
