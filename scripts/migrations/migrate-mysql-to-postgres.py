#!/usr/bin/env python3
"""Copia dados do banco MySQL legado para o PostgreSQL novo.

Este script é deliberadamente separado do runtime. Ele usa os dois drivers só
durante a migração, mantém IDs existentes, faz upsert por chave primária e
recalibra as sequences do PostgreSQL. Não apaga nada no banco de origem.
"""

from __future__ import annotations

import os
import re

import psycopg2
import pymysql
from psycopg2 import sql


TABLE_ORDER = (
    'source_channels',
    'source_videos',
    'destination_channels',
    'generated_clips',
    'niches',
    'users',
    'password_reset_tokens',
    'sessions',
    'cache',
    'cache_locks',
    'jobs',
    'job_batches',
    'failed_jobs',
    'transcription_jobs',
)

BOOLEAN_COLUMNS = {
    ('source_channels', 'active'),
    ('source_channels', 'blacklisted'),
    ('source_videos', 'paused'),
    ('destination_channels', 'active'),
    ('destination_channels', 'oauth_expired_flag'),
}


def quote_identifier(name: str) -> str:
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
        raise ValueError(f'Identificador inesperado: {name!r}')
    return name


def bool_value(table: str, column: str, value):
    if (table, column) not in BOOLEAN_COLUMNS or value is None:
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {'', '0', 'false', 'no', 'off'}
    return bool(value)


def fetch_mysql_rows(conn, table: str) -> list[dict]:
    with conn.cursor() as cur:
        # quote_identifier() validates the name; use MySQL's identifier quoting
        # instead of double quotes, which can be parsed as string literals.
        cur.execute(f'SELECT * FROM `{quote_identifier(table)}`')
        return list(cur.fetchall())


def postgres_columns(conn, table: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def postgres_primary_key(conn, table: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON kcu.constraint_name = tc.constraint_name
             AND kcu.table_schema = tc.table_schema
             AND kcu.table_name = tc.table_name
            WHERE tc.table_schema = 'public'
              AND tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
            """,
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def postgres_table_exists(conn, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
            """,
            (table,),
        )
        return cur.fetchone() is not None


def mysql_table_exists(conn, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = %s
            """,
            (table,),
        )
        return cur.fetchone() is not None


def migrate_table(mysql_conn, postgres_conn, table: str) -> int:
    if not mysql_table_exists(mysql_conn, table):
        print(f'[migrate] {table}: não existe na origem — ignorada')
        return 0
    if not postgres_table_exists(postgres_conn, table):
        print(f'[migrate] {table}: não existe no PostgreSQL — execute panel-init antes')
        return 0

    source_rows = fetch_mysql_rows(mysql_conn, table)
    if not source_rows:
        print(f'[migrate] {table}: 0 linhas')
        return 0

    target_cols = postgres_columns(postgres_conn, table)
    primary_key = postgres_primary_key(postgres_conn, table)
    if not primary_key:
        raise RuntimeError(f'{table}: tabela sem chave primária; recusa migração ambígua')

    columns = [column for column in target_cols if column in source_rows[0]]
    if not columns:
        raise RuntimeError(f'{table}: nenhuma coluna compatível')

    quoted_table = sql.Identifier(table)
    quoted_columns = sql.SQL(', ').join(sql.Identifier(column) for column in columns)
    placeholders = sql.SQL(', ').join(sql.Placeholder() for _ in columns)
    update_columns = [column for column in columns if column not in primary_key]
    if update_columns:
        update_clause = sql.SQL(', ').join(
            sql.SQL('{} = EXCLUDED.{}').format(
                sql.Identifier(column), sql.Identifier(column)
            )
            for column in update_columns
        )
        conflict_clause = sql.SQL('ON CONFLICT ({}) DO UPDATE SET {}').format(
            sql.SQL(', ').join(sql.Identifier(column) for column in primary_key),
            update_clause,
        )
    else:
        conflict_clause = sql.SQL('ON CONFLICT ({}) DO NOTHING').format(
            sql.SQL(', ').join(sql.Identifier(column) for column in primary_key),
        )

    statement = sql.SQL(
        'INSERT INTO {} ({}) VALUES ({}) {}'
    ).format(quoted_table, quoted_columns, placeholders, conflict_clause)

    with postgres_conn.cursor() as cur:
        for row in source_rows:
            values = [bool_value(table, column, row.get(column)) for column in columns]
            cur.execute(statement, values)
    postgres_conn.commit()

    if 'id' in columns:
        with postgres_conn.cursor() as cur:
            cur.execute("SELECT pg_get_serial_sequence(%s, 'id')", (f'public.{table}',))
            sequence_row = cur.fetchone()

        if sequence_row and sequence_row[0]:
            with postgres_conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        'SELECT setval(%s, GREATEST(COALESCE(MAX(id), 1), 1), true) FROM {}'
                    ).format(sql.Identifier(table)),
                    (sequence_row[0],),
                )
            postgres_conn.commit()

    print(f'[migrate] {table}: {len(source_rows)} linha(s) copiadas')
    return len(source_rows)


def connect_mysql():
    return pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'canaldecortes-mysql-1'),
        port=int(os.environ.get('MYSQL_PORT', '3306')),
        database=os.environ.get('MYSQL_DATABASE', 'clips_automation'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD') or os.environ.get('MYSQL_ROOT_PASSWORD', ''),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def connect_postgres():
    return psycopg2.connect(
        host=os.environ.get('PGHOST', 'postgres'),
        port=int(os.environ.get('PGPORT', '5432')),
        dbname=os.environ.get('PGDATABASE', 'clips_automation'),
        user=os.environ.get('PGUSER', 'clips_user'),
        password=os.environ.get('PGPASSWORD') or os.environ.get('CLIPS_DB_PASSWORD', ''),
    )


def main() -> int:
    if os.environ.get('CONFIRM_MIGRATION') != 'I_UNDERSTAND':
        raise SystemExit(
            'Defina CONFIRM_MIGRATION=I_UNDERSTAND para copiar os dados do MySQL legado.'
        )

    mysql_conn = connect_mysql()
    postgres_conn = connect_postgres()
    try:
        total = 0
        for table in TABLE_ORDER:
            total += migrate_table(mysql_conn, postgres_conn, table)
        print(f'[migrate] concluído: {total} linha(s) processadas; origem intacta')
    finally:
        mysql_conn.close()
        postgres_conn.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
