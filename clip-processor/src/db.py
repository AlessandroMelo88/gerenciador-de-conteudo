"""
db.py — Módulo de acesso ao PostgreSQL para o daemon clip-processor.

Exporta:
  - get_db_connection(): abre conexão com o PostgreSQL via psycopg2
  - update_status(conn, video_id, status, local_path=None): atualiza status de vídeo
  - insert_video(conn, video_id, channel_id, title, published_at): insere vídeo novo
  - fetch_used_moments(conn, source_video_id): busca intervalos já registrados do vídeo
  - recover_stuck_downloads(conn): redefine vídeos presos em 'downloading' para 'pending'
  - recover_stuck_selecting(conn): redefine vídeos presos em 'selecting' para 'downloaded'
  - recover_cutting_on_boot(conn): redefine clips interrompidos em 'cutting' para 'pending_cut'

Convenções:
  - Quem chama é responsável por fechar a conexão (não fechar dentro das funções)
  - Logging via print simples para stdout (sem biblioteca de logging)
  - Cada função usa `with conn.cursor() as cur:` e faz commit explícito
"""

import os
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [DB] {msg}')


def get_db_connection():
    """Abre conexão com o PostgreSQL usando variáveis de ambiente.

    Variáveis de ambiente requeridas:
      - POSTGRES_HOST (default: localhost)
      - POSTGRES_DATABASE (default: clips_automation)
      - POSTGRES_USER (default: clips_user)
      - POSTGRES_PASSWORD

    Returns:
        psycopg2.extensions.connection: conexão aberta, autocommit=False
    """
    host = os.environ.get('POSTGRES_HOST', 'localhost')
    database = os.environ.get('POSTGRES_DATABASE', 'clips_automation')
    user = os.environ.get('POSTGRES_USER', 'clips_user')
    password = os.environ.get('POSTGRES_PASSWORD', '')

    conn = psycopg2.connect(
        host=host,
        dbname=database,
        user=user,
        password=password,
        connect_timeout=10,
        cursor_factory=RealDictCursor,
    )
    conn.autocommit = False
    _log(f'Conexão aberta: {user}@{host}/{database}')
    return conn


def update_status(conn, video_id, status, local_path=None, clear_local_path=False):
    """Atualiza o status de um vídeo na tabela source_videos.

    `local_path=None` significa "não mexe na coluna" (compatibilidade com as
    chamadas antigas), então zerar a coluna precisa de um sinal próprio:
    `clear_local_path=True` grava NULL. Sem isso não havia como desocupar a
    janela de download — que conta `local_path IS NOT NULL` —, e vídeo com
    download falho segurava vaga pra sempre.

    Args:
        conn: conexão PostgreSQL ativa
        video_id: youtube_video_id do vídeo a atualizar
        status: novo status (ex: 'downloading', 'downloaded', 'failed')
        local_path: caminho local do arquivo (opcional, usado quando status='downloaded')
        clear_local_path: se True, seta local_path=NULL (ignora `local_path`)
    """
    params: tuple[object, ...]
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

    Usa ON CONFLICT para ser idempotente — ignora duplicatas silenciosamente.

    Args:
        conn: conexão PostgreSQL ativa
        video_id: youtube_video_id único do vídeo
        channel_id: FK para source_channels.id
        title: título do vídeo
        published_at: data/hora de publicação (string ISO 8601 ou datetime)
        format: 'curto' ou 'longo' — decidido pelo poller com base na duração do vídeo fonte
    """
    sql = (
        'INSERT INTO source_videos '
        '(youtube_video_id, channel_id, title, published_at, status, format) '
        'VALUES (%s, %s, %s, %s, %s, %s) '
        'ON CONFLICT (youtube_video_id) DO NOTHING'
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
        conn: conexão PostgreSQL ativa
    """
    sql = "UPDATE source_videos SET status='pending' WHERE status='downloading'"

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            affected = cur.rowcount
        conn.commit()
        _log(f'recover_stuck_downloads: {affected} vídeo(s) redefinido(s) para pending')
    except psycopg2.OperationalError as exc:
        _log(f'AVISO: falha ao recuperar downloads presos: {exc}')
        raise


# Horas sem progresso antes de considerar um 'selecting' travado.
SELECTING_STUCK_HOURS = 2


def recover_stuck_selecting(conn):
    """Devolve vídeos presos em 'selecting' para 'downloaded' (reprocessa a IA).

    'selecting' não tinha recuperação: um vídeo que travasse na etapa de IA
    (queda do PostgreSQL, container morto no meio) ficava preso pra sempre segurando
    um slot da janela de download — com as duas janelas cheias de linha morta,
    o pipeline parava de baixar qualquer coisa.

    Só considera travado o que não recebe update há SELECTING_STUCK_HOURS, pra
    não atropelar seleção legitimamente em curso. O arquivo já está em disco,
    então volta pra 'downloaded' e não pra 'pending' — não rebaixa à toa.

    Também libera 'selecting' sem nenhum clip gerado (IA devolveu 0 momentos
    válidos e o status ficou preso) — esses não precisam esperar 2h.

    Terceiro caso: 'selecting' com local_path NULL. A limpeza de disco
    (`delete_source_video_file` e a purga de vídeos antigos no internal_api)
    zera `local_path` sem tocar em `status`, então o registro fica preso num
    estado que as duas queries acima nunca alcançam — elas exigem
    `local_path IS NOT NULL`, e nenhum restart resolve. Sem o raw em disco não
    existe seleção pra reprocessar, então vai para 'failed': é o estado honesto
    (o insumo não existe mais) e libera a vaga da janela. O registro continua no
    banco, com os clips que já tiverem sido gerados.

    Args:
        conn: conexão PostgreSQL ativa
    """
    sql_stuck = (
        'UPDATE source_videos '
        "SET status='downloaded' "
        "WHERE status='selecting' "
        'AND local_path IS NOT NULL '
        "AND updated_at < NOW() - (%s * INTERVAL '1 hour')"
    )
    # Um clip pode ter sido criado e falhar no corte (por exemplo, por asset
    # obrigatório ausente). Nesse caso o vídeo-fonte continua em `selecting`,
    # mas já não existe trabalho recuperável para ele. Sem esta saída, a
    # janela permanece ocupada até o timeout e o registro fica parecendo uma
    # seleção ativa.
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
    sql_empty = (
        'UPDATE source_videos '
        "SET status='downloaded' "
        "WHERE status='selecting' "
        'AND local_path IS NOT NULL '
        'AND NOT EXISTS ('
        '  SELECT 1 FROM generated_clips gc WHERE gc.source_video_id = source_videos.id'
        ')'
    )

    sql_no_file = (
        'UPDATE source_videos '
        "SET status='failed' "
        "WHERE status='selecting' "
        'AND local_path IS NULL '
        "AND updated_at < NOW() - (%s * INTERVAL '1 hour')"
    )

    try:
        with conn.cursor() as cur:
            cur.execute(sql_terminal)
            terminal = cur.rowcount
            cur.execute(sql_stuck, (SELECTING_STUCK_HOURS,))
            stuck = cur.rowcount
            cur.execute(sql_empty)
            empty = cur.rowcount
            cur.execute(sql_no_file, (SELECTING_STUCK_HOURS,))
            no_file = cur.rowcount
        conn.commit()
        _log(
            f'recover_stuck_selecting: {terminal} terminal(is) redefinido(s) para failed; '
            f'{stuck} travado(s) + {empty} sem clip redefinido(s) para downloaded; '
            f'{no_file} sem arquivo redefinido(s) para failed'
        )
    except psycopg2.OperationalError as exc:
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
    sql = (
        'UPDATE generated_clips '
        "SET status='pending' "
        "WHERE status='publishing' "
        "AND updated_at < NOW() - INTERVAL '15 minutes'"
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
        conn: conexão PostgreSQL ativa
    """
    sql = "UPDATE generated_clips SET status='pending_cut' WHERE status='cutting'"

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            affected = cur.rowcount
        conn.commit()
        _log(f'recover_cutting_on_boot: {affected} clip(s) redefinido(s) para pending_cut')
    except psycopg2.OperationalError as exc:
        _log(f'AVISO: falha ao recuperar clips em cutting: {exc}')
        raise
