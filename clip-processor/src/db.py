"""
db.py — Módulo de acesso ao MySQL para o daemon clip-processor.

Exporta:
  - get_db_connection(): abre conexão com o MySQL via pymysql
  - update_status(conn, video_id, status, local_path=None): atualiza status de vídeo
  - insert_video(conn, video_id, channel_id, title, published_at): insere vídeo novo
  - recover_stuck_downloads(conn): redefine vídeos presos em 'downloading' para 'pending'
  - recover_stuck_selecting(conn): redefine vídeos presos em 'selecting' para 'downloaded'

Convenções:
  - Quem chama é responsável por fechar a conexão (não fechar dentro das funções)
  - Logging via print simples para stdout (sem biblioteca de logging)
  - Cada função usa `with conn.cursor() as cur:` e faz commit explícito
"""
import os
import pymysql
from datetime import datetime


def _log(msg: str) -> None:
    """Loga mensagem com timestamp para stdout."""
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [DB] {msg}')


def get_db_connection():
    """Abre conexão com o MySQL usando variáveis de ambiente.

    Variáveis de ambiente requeridas:
      - MYSQL_HOST (default: localhost)
      - MYSQL_DATABASE (default: clips_automation)
      - MYSQL_USER (default: clips_user)
      - MYSQL_PASSWORD

    Returns:
        pymysql.connections.Connection: conexão aberta, autocommit=False
    """
    host = os.environ.get('MYSQL_HOST', 'localhost')
    database = os.environ.get('MYSQL_DATABASE', 'clips_automation')
    user = os.environ.get('MYSQL_USER', 'clips_user')
    password = os.environ.get('MYSQL_PASSWORD', '')

    conn = pymysql.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        charset='utf8mb4',
        autocommit=False,
        connect_timeout=10,
        cursorclass=pymysql.cursors.DictCursor,
    )
    _log(f'Conexão aberta: {user}@{host}/{database}')
    return conn


def update_status(conn, video_id, status, local_path=None):
    """Atualiza o status de um vídeo na tabela source_videos.

    Args:
        conn: conexão pymysql ativa
        video_id: youtube_video_id do vídeo a atualizar
        status: novo status (ex: 'downloading', 'downloaded', 'failed')
        local_path: caminho local do arquivo (opcional, usado quando status='downloaded')
    """
    if local_path is not None:
        sql = (
            'UPDATE source_videos '
            'SET status=%s, local_path=%s '
            'WHERE youtube_video_id=%s'
        )
        params = (status, local_path, video_id)
    else:
        sql = (
            'UPDATE source_videos '
            'SET status=%s '
            'WHERE youtube_video_id=%s'
        )
        params = (status, video_id)

    with conn.cursor() as cur:
        cur.execute(sql, params)
    conn.commit()
    _log(f'Status atualizado: video_id={video_id} → {status}')


def insert_video(conn, video_id, channel_id, title, published_at, format='curto'):
    """Insere um novo vídeo na tabela source_videos com status 'pending'.

    Usa INSERT IGNORE para ser idempotente — ignora duplicatas silenciosamente.

    Args:
        conn: conexão pymysql ativa
        video_id: youtube_video_id único do vídeo
        channel_id: FK para source_channels.id
        title: título do vídeo
        published_at: data/hora de publicação (string ISO 8601 ou datetime)
        format: 'curto' ou 'longo' — decidido pelo poller com base na duração do vídeo fonte
    """
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


def recover_stuck_downloads(conn):
    """Redefine vídeos presos em status 'downloading' de volta para 'pending'.

    Executado na inicialização do daemon para recuperar falhas de sessões anteriores.

    Args:
        conn: conexão pymysql ativa
    """
    sql = (
        "UPDATE source_videos "
        "SET status='pending' "
        "WHERE status='downloading'"
    )

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            affected = cur.rowcount
        conn.commit()
        _log(f'recover_stuck_downloads: {affected} vídeo(s) redefinido(s) para pending')
    except pymysql.OperationalError as exc:
        _log(f'AVISO: falha ao recuperar downloads presos: {exc}')
        raise


# Horas sem progresso antes de considerar um 'selecting' travado.
SELECTING_STUCK_HOURS = 2


def recover_stuck_selecting(conn):
    """Devolve vídeos presos em 'selecting' para 'downloaded' (reprocessa a IA).

    'selecting' não tinha recuperação: um vídeo que travasse na etapa de IA
    (queda do MySQL, container morto no meio) ficava preso pra sempre segurando
    um slot da janela de download — com as duas janelas cheias de linha morta,
    o pipeline parava de baixar qualquer coisa.

    Só considera travado o que não recebe update há SELECTING_STUCK_HOURS, pra
    não atropelar seleção legitimamente em curso. O arquivo já está em disco,
    então volta pra 'downloaded' e não pra 'pending' — não rebaixa à toa.

    Também libera 'selecting' sem nenhum clip gerado (IA devolveu 0 momentos
    válidos e o status ficou preso) — esses não precisam esperar 2h.

    Args:
        conn: conexão pymysql ativa
    """
    sql_stuck = (
        "UPDATE source_videos "
        "SET status='downloaded' "
        "WHERE status='selecting' "
        "AND local_path IS NOT NULL "
        "AND updated_at < DATE_SUB(NOW(), INTERVAL %s HOUR)"
    )
    sql_empty = (
        "UPDATE source_videos sv "
        "SET sv.status='downloaded' "
        "WHERE sv.status='selecting' "
        "AND sv.local_path IS NOT NULL "
        "AND NOT EXISTS ("
        "  SELECT 1 FROM generated_clips gc WHERE gc.source_video_id = sv.id"
        ")"
    )

    try:
        with conn.cursor() as cur:
            cur.execute(sql_stuck, (SELECTING_STUCK_HOURS,))
            stuck = cur.rowcount
            cur.execute(sql_empty)
            empty = cur.rowcount
        conn.commit()
        _log(
            f'recover_stuck_selecting: {stuck} travado(s) + {empty} sem clip '
            f'redefinido(s) para downloaded'
        )
    except pymysql.OperationalError as exc:
        _log(f'AVISO: falha ao recuperar seleções presas: {exc}')
        raise
